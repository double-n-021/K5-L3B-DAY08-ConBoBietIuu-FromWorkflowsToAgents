"""Shape B — one ReAct agent. (Student work: Tran Gia Bao - 2A202603914).

Uses `lab8.runtime.run_react` with max_steps=8 and worker=True.
The ReAct callback `decide` only picks read tools (lookup_order, compute_compensation).
It must never call `issue_refund`.
Only the host writes to the database, enforcing caps, policies, and idempotency.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from lab8.db import connect
from lab8.durability import InjectedCrash, issue_refund
from lab8.mock_llm import complete
from lab8.runtime import run_react
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish
from lab8.tools import get_claim_view, tool_cost
from lab8.trace import Trace


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    conn = connect(store_path)
    try:
        return _run(conn, claim_id, seed=seed, crash_at=crash_at)
    finally:
        conn.close()


def _run(
    conn: sqlite3.Connection,
    claim_id: str,
    *,
    seed: int,
    crash_at: str | None,
) -> RunResult:
    budget = Budget()
    run_id = make_run_id("single", claim_id, seed)
    trace = Trace(run_id)

    # 1. Inspect claim view
    budget.add_tool(tool_cost())
    claim = get_claim_view(conn, claim_id)
    if not claim.get("found"):
        trace.add("error", {"reason": "unknown_claim", "claim_id": claim_id})
        return finish(
            conn,
            shape="single",
            claim_id=claim_id,
            seed=seed,
            status="failed",
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason="unknown_claim",
        )

    # Trace safe claim summary (redact ticket text & secrets)
    trace.add(
        "claim",
        {
            "found": True,
            "claim_id": claim["claim_id"],
            "principal_id": claim.get("principal_id"),
            "order_id": claim.get("order_id"),
        },
    )

    if not claim.get("order_id"):
        complete(budget, seed=seed, purpose="draft", prompt="needs_info")
        trace.add("decision", {"status": "needs_info"})
        return finish(
            conn,
            shape="single",
            claim_id=claim_id,
            seed=seed,
            status="needs_info",
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason="missing_order_id",
        )

    # 2. Bounded ReAct loop with max_steps=8, worker=True
    step_count = 0
    order_view: dict[str, Any] | None = None
    quote_payload: dict[str, Any] | None = None

    def decide(obs: dict[str, Any]) -> dict[str, Any]:
        nonlocal step_count, order_view, quote_payload
        step_count += 1
        last_tool = obs.get("last_tool")
        last_result = obs.get("last_result")

        # Simulate LLM thinking step & account for model calls in budget
        complete(
            budget,
            seed=seed,
            purpose="decide",
            prompt=f"step={step_count}|tool={last_tool or 'none'}",
        )

        if last_tool is None:
            # Step 1: Look up order under authenticated principal scope
            return {
                "tool": "lookup_order",
                "args": {
                    "order_id": claim.get("order_id"),
                    "principal_id": claim["principal_id"],
                },
            }

        if last_tool == "lookup_order":
            order_view = last_result or {}
            trace.add(
                "lookup_order",
                {
                    "visible": order_view.get("visible"),
                    "reason": order_view.get("reason"),
                },
            )
            if not order_view.get("visible"):
                return {"final": {"status": "escalated", "reason": order_view.get("reason")}}

            # Step 2: Compute compensation using true order data
            return {
                "tool": "compute_compensation",
                "args": {"order": order_view["order"]},
            }

        if last_tool == "compute_compensation":
            quote_payload = last_result or {}
            trace.add(
                "quote",
                {
                    "amount_vnd": quote_payload.get("amount_vnd"),
                    "reason": quote_payload.get("reason"),
                    "clause_ids": quote_payload.get("clause_ids"),
                },
            )
            # Step 3: Conclude ReAct loop with quote payload
            return {"final": {"status": "done", "quote": quote_payload}}

        return {"final": {"status": "failed", "error_reason": "unexpected_tool"}}

    react_result = run_react(
        conn,
        budget,
        observation={"claim": claim},
        decide=decide,
        max_steps=8,
        worker=True,
    )

    if react_result.get("stopped") == "step_cap":
        complete(budget, seed=seed, purpose="draft", prompt="failed")
        trace.add("error", {"reason": "step_cap"})
        return finish(
            conn,
            shape="single",
            claim_id=claim_id,
            seed=seed,
            status="failed",
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason="step_cap",
        )

    final_info = react_result.get("final", {})
    final_status = final_info.get("status")

    if final_status == "escalated":
        complete(budget, seed=seed, purpose="draft", prompt="escalated")
        trace.add("decision", {"status": "escalated"})
        return finish(
            conn,
            shape="single",
            claim_id=claim_id,
            seed=seed,
            status="escalated",
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason=final_info.get("reason"),
        )

    if final_status == "failed":
        complete(budget, seed=seed, purpose="draft", prompt="failed")
        trace.add("decision", {"status": "failed"})
        return finish(
            conn,
            shape="single",
            claim_id=claim_id,
            seed=seed,
            status="failed",
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason=final_info.get("error_reason"),
        )

    # 3. Handle quote and host refund issuance
    quote_info = final_info.get("quote", {})
    proposal = int(quote_info.get("amount_vnd", 0))

    if proposal <= 0:
        complete(budget, seed=seed, purpose="draft", prompt="denied")
        trace.add("decision", {"status": "denied", "proposal_amount": 0})
        return finish(
            conn,
            shape="single",
            claim_id=claim_id,
            seed=seed,
            status="denied",
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason=quote_info.get("reason"),
        )

    # If quote > 0, host validates approval, cap, and idempotency
    try:
        outcome = issue_refund(conn, claim_id, proposal, crash_at=crash_at)
    except InjectedCrash:
        trace.add("crash", {"at": crash_at})
        trace.write()
        raise

    if not outcome["ok"]:
        status = "failed" if outcome.get("conflict") else "denied"
        complete(
            budget,
            seed=seed,
            purpose="draft",
            prompt=f"proposal={proposal}|status={status}",
        )
        trace.add(
            "decision",
            {
                "status": status,
                "proposal_amount": proposal,
                "reason": outcome.get("reason"),
            },
        )
        return finish(
            conn,
            shape="single",
            claim_id=claim_id,
            seed=seed,
            status=status,
            proposal_amount=proposal,
            budget=budget,
            trace=trace,
            error_reason=outcome.get("reason"),
        )

    complete(
        budget,
        seed=seed,
        purpose="draft",
        prompt=f"proposal={proposal}|status=resolved",
    )
    trace.add(
        "decision",
        {
            "status": "resolved",
            "proposal_amount": proposal,
        },
    )
    return finish(
        conn,
        shape="single",
        claim_id=claim_id,
        seed=seed,
        status="resolved",
        proposal_amount=proposal,
        budget=budget,
        trace=trace,
        error_reason=None,
    )
