"""Ablation experiment for Member 2 (Tran Gia Bao - Shape B Single Agent).

Investigates the cost, model-call, and correctness impact of the final 'draft'
response step in the Single ReAct Agent pipeline (R4: Evaluation Confounders).

CLI:
    python -m bonus.jay_ablation --out reports/jay_ablation.json
"""

from __future__ import annotations

import argparse
import json
import math
import sqlite3
import tempfile
from pathlib import Path
from typing import Any

import lab8.shapes.single as single_module
from lab8.benchmark import run_benchmark
from lab8.config_loader import repo_path
from lab8.console import utf8_stdio
from lab8.db import connect, init_store, load_json, load_jsonl
from lab8.durability import committed_audit_count, get_refund


def _normalize_audit_record(row: sqlite3.Row | dict[str, Any]) -> dict[str, Any]:
    """Normalize an audit row into a comparable dictionary with parsed details."""
    raw_details = row["details_json"]
    if isinstance(raw_details, str):
        try:
            details_obj = json.loads(raw_details)
        except (json.JSONDecodeError, TypeError):
            details_obj = raw_details
    else:
        details_obj = raw_details
    return {
        "audit_key": row["audit_key"],
        "claim_id": row["claim_id"],
        "event_type": row["event_type"],
        "details": details_obj,
    }


def _canonical_audit_list(rows: list[Any]) -> list[dict[str, Any]]:
    """Produce a stably sorted list of normalized audits, independent of SQL order and JSON key order."""
    normalized = [_normalize_audit_record(r) for r in rows]
    # Sort deterministically by canonical json representation with sorted keys
    normalized.sort(key=lambda item: json.dumps(item, sort_keys=True, ensure_ascii=False))
    return normalized


def _inspect_trial_db(store_path: Path, claim_id: str) -> dict[str, Any]:
    """Extract complete financial and audit snapshot from SQLite store for a trial."""
    conn = connect(store_path)
    try:
        refund_rows = [
            dict(r)
            for r in conn.execute(
                "SELECT claim_id, order_id, idempotency_key, amount_vnd, status "
                "FROM refund_ledger WHERE claim_id = ?",
                (claim_id,),
            ).fetchall()
        ]
        refund_rows.sort(key=lambda r: (r["claim_id"], r["idempotency_key"]))
        audit_committed = committed_audit_count(conn, claim_id)
        policy_denied_rows = [
            dict(r)
            for r in conn.execute(
                "SELECT audit_key, claim_id, event_type, details_json "
                "FROM audit_events WHERE claim_id = ? AND event_type = 'policy_denied'",
                (claim_id,),
            ).fetchall()
        ]
        canonical_denied = _canonical_audit_list(policy_denied_rows)
        return {
            "refund_rows": refund_rows,
            "refund_count": len(refund_rows),
            "refund_amount_vnd": sum(int(r["amount_vnd"]) for r in refund_rows),
            "audit_committed_count": audit_committed,
            "policy_denied_count": len(canonical_denied),
            "policy_denied_audits": canonical_denied,
        }
    finally:
        conn.close()


def run_paired_db_verification(
    claims: list[dict[str, Any]],
    world: dict[str, Any],
    seeds: list[int],
) -> tuple[bool, list[dict[str, Any]]]:
    """Run baseline and treatment on separate fresh DBs per (claim, seed) pair and compare."""
    mismatches: list[dict[str, Any]] = []

    original_complete = single_module.complete

    def patched_complete(budget, *, seed: int, purpose: str, prompt: str):
        if purpose == "draft":
            return ""
        return original_complete(budget, seed=seed, purpose=purpose, prompt=prompt)

    with tempfile.TemporaryDirectory(prefix="lab8-ablation-verify-") as tmp:
        tmp_dir = Path(tmp)
        for claim in claims:
            claim_id = claim["claim_id"]
            for seed in seeds:
                # 1. Baseline trial run on fresh DB
                base_store = tmp_dir / f"base-{claim_id}-{seed}.sqlite"
                init_store(base_store, world, claims).close()
                base_res = single_module.run_claim(claim_id, seed=seed, store_path=str(base_store))
                base_db_state = _inspect_trial_db(base_store, claim_id)

                # 2. Treatment trial run on separate fresh DB
                treat_store = tmp_dir / f"treat-{claim_id}-{seed}.sqlite"
                init_store(treat_store, world, claims).close()
                single_module.complete = patched_complete
                try:
                    treat_res = single_module.run_claim(claim_id, seed=seed, store_path=str(treat_store))
                finally:
                    single_module.complete = original_complete
                treat_db_state = _inspect_trial_db(treat_store, claim_id)

                # 3. Direct verification of status, proposal, ledger, and audits
                diffs: list[str] = []
                if base_res.status != treat_res.status:
                    diffs.append(f"status: base={base_res.status} vs treat={treat_res.status}")
                if base_res.proposal_amount != treat_res.proposal_amount:
                    diffs.append(f"proposal_amount: base={base_res.proposal_amount} vs treat={treat_res.proposal_amount}")
                if base_db_state["refund_count"] != treat_db_state["refund_count"]:
                    diffs.append(f"refund_count: base={base_db_state['refund_count']} vs treat={treat_db_state['refund_count']}")
                if base_db_state["refund_amount_vnd"] != treat_db_state["refund_amount_vnd"]:
                    diffs.append(f"refund_amount_vnd: base={base_db_state['refund_amount_vnd']} vs treat={treat_db_state['refund_amount_vnd']}")
                if base_db_state["audit_committed_count"] != treat_db_state["audit_committed_count"]:
                    diffs.append(f"audit_committed: base={base_db_state['audit_committed_count']} vs treat={treat_db_state['audit_committed_count']}")
                if base_db_state["policy_denied_count"] != treat_db_state["policy_denied_count"]:
                    diffs.append(f"policy_denied_count: base={base_db_state['policy_denied_count']} vs treat={treat_db_state['policy_denied_count']}")
                if base_db_state["policy_denied_audits"] != treat_db_state["policy_denied_audits"]:
                    diffs.append(
                        f"policy_denied_audits: base={base_db_state['policy_denied_audits']} "
                        f"vs treat={treat_db_state['policy_denied_audits']}"
                    )

                if diffs:
                    mismatches.append({
                        "claim_id": claim_id,
                        "seed": seed,
                        "differences": diffs,
                    })

    return (len(mismatches) == 0, mismatches)


def run_ablation(
    cases_path: Path,
    world_path: Path,
    seeds: list[int],
) -> dict[str, Any]:
    world = load_json(world_path)
    claims = load_jsonl(cases_path)

    # 1. Arm 1: Baseline (Single with decide + draft)
    baseline_report = run_benchmark(
        world=world,
        claims=claims,
        shapes=["single"],
        seeds=seeds,
    )
    baseline_single = baseline_report["by_shape"]["single"]

    # 2. Arm 2: Treatment (Single without draft step)
    original_complete = single_module.complete

    def patched_complete(budget, *, seed: int, purpose: str, prompt: str):
        if purpose == "draft":
            return ""
        return original_complete(budget, seed=seed, purpose=purpose, prompt=prompt)

    single_module.complete = patched_complete
    try:
        treatment_report = run_benchmark(
            world=world,
            claims=claims,
            shapes=["single"],
            seeds=seeds,
        )
    finally:
        single_module.complete = original_complete

    treatment_single = treatment_report["by_shape"]["single"]

    # 3. Direct Paired Database & Ledger Verification
    paired_db_ok, db_mismatches = run_paired_db_verification(claims, world, seeds)

    # 4. Compute Deltas
    model_calls_delta = treatment_single["mean_model_calls"] - baseline_single["mean_model_calls"]
    cost_delta = treatment_single["cost_per_success_vnd"] - baseline_single["cost_per_success_vnd"]
    pass_rate_delta = treatment_single["pass_rate"] - baseline_single["pass_rate"]
    pass_5_delta = treatment_single["pass_5"] - baseline_single["pass_5"]

    # 5. Dynamic Evidence-Based Conclusion
    total_trials = len(claims) * len(seeds)
    model_calls_exact_minus_one = math.isclose(model_calls_delta, -1.0, rel_tol=0.0, abs_tol=1e-9)

    if not paired_db_ok:
        conclusion_status = "that_bai"
        conclusion = (
            f"Bác bỏ giả thuyết (Thất bại): Phát hiện {len(db_mismatches)}/{total_trials} cặp trial có sự sai lệch "
            f"về kết quả nghiệp vụ, số tiền hoàn trong ledger hoặc nội dung audit event giữa hai nhánh. "
            f"Các vi phạm đầu tiên: {db_mismatches[:3]}."
        )
    elif pass_rate_delta < 0 or pass_5_delta < 0 or treatment_single["pass_rate"] < 1.0:
        conclusion_status = "that_bai"
        conclusion = (
            f"Bác bỏ giả thuyết (Thất bại): Tỉ lệ pass bị suy giảm khi bỏ draft "
            f"(baseline pass={baseline_single['pass_rate']}, treatment pass={treatment_single['pass_rate']})."
        )
    elif not model_calls_exact_minus_one:
        conclusion_status = "that_bai"
        conclusion = (
            f"Bác bỏ giả thuyết (Thất bại): Số lượt gọi model không giảm đúng 1.0 "
            f"(delta thực tế: {model_calls_delta:.4f}, mức kỳ vọng: -1.0000)."
        )
    elif cost_delta >= 0:
        conclusion_status = "that_bai"
        conclusion = (
            f"Bác bỏ giả thuyết (Thất bại): Chi phí mô phỏng không giảm (delta={cost_delta:.2f} VND)."
        )
    elif total_trials < 10:
        conclusion_status = "chua_du_du_lieu"
        conclusion = (
            f"Chưa đủ dữ liệu: Thử nghiệm chỉ chạy trên {total_trials} trials, "
            f"chưa đủ số lượng thống kê tối thiểu để đưa ra kết luận tin cậy."
        )
    else:
        conclusion_status = "thanh_cong"
        conclusion = (
            f"Xác nhận giả thuyết (Đạt): Bỏ bước draft giúp giảm đúng 1.0 lượt gọi model "
            f"(mean_model_calls delta={model_calls_delta:.4f}, kỳ vọng: -1.0000) và giảm chi phí mô phỏng "
            f"(cost/success delta={cost_delta:.2f} VND). Toàn bộ 100% kết quả nghiệp vụ (status, "
            f"proposal_amount, số dòng và số tiền refund trong refund_ledger, số audit refund_committed, "
            f"và audit policy_denied đã chuẩn hóa nội dung) được bảo toàn tuyệt đối trên cả {total_trials} cặp database độc lập."
        )

    ablation_result = {
        "title": "Ablation Study: Controlled Evaluation of Final Draft LLM Call in Single ReAct Agent",
        "research_question_id": "R4",
        "question": (
            "Sau khi đã xác định quote và trạng thái duyệt tiền, lời gọi model soạn câu trả lời 'draft' "
            "ở cuối pipeline có làm tăng độ chính xác nghiệp vụ hay chỉ làm tăng chi phí mô phỏng?"
        ),
        "source_citation": "Zhang et al., EMNLP 2026, https://aclanthology.org/2026.emnlp-main.798/",
        "hypothesis": (
            "Đối với Single ReAct Agent, bước gọi model soạn draft ở cuối không can thiệp vào logic tính quote hay "
            "duyệt chi; khi loại bỏ (treatment), pass rate và pass^5 giữ nguyên 1.0, mean_model_calls giảm đúng 1.0, "
            "cost/success giảm tương ứng, và toàn bộ số tiền cùng sự kiện audit trên DB được bảo toàn tuyệt đối."
        ),
        "conclusion_status": conclusion_status,
        "conclusion": conclusion,
        "controlled_variables": {
            "seeds": seeds,
            "claims_count": len(claims),
            "pricing": baseline_report["controlled_variables"]["pricing"],
            "model_backend": baseline_report["controlled_variables"]["model_backend"],
            "read_tools": ["lookup_order", "compute_compensation"],
            "max_steps": 8,
            "isolation": "fresh_sqlite_per_trial",
        },
        "independent_variable": "Tắt lời gọi complete(..., purpose='draft') ở cuối pipeline của Single Agent",
        "baseline_summary": {
            "pass_rate": baseline_single["pass_rate"],
            "pass_5": baseline_single["pass_5"],
            "mean_model_calls": baseline_single["mean_model_calls"],
            "mean_tool_calls": baseline_single["mean_tool_calls"],
            "cost_per_success_vnd": baseline_single["cost_per_success_vnd"],
            "mean_steps": baseline_single["mean_steps"],
        },
        "treatment_summary": {
            "pass_rate": treatment_single["pass_rate"],
            "pass_5": treatment_single["pass_5"],
            "mean_model_calls": treatment_single["mean_model_calls"],
            "mean_tool_calls": treatment_single["mean_tool_calls"],
            "cost_per_success_vnd": treatment_single["cost_per_success_vnd"],
            "mean_steps": treatment_single["mean_steps"],
        },
        "delta": {
            "pass_rate_diff": pass_rate_delta,
            "pass_5_diff": pass_5_delta,
            "mean_model_calls_diff": model_calls_delta,
            "cost_per_success_vnd_diff": cost_delta,
            "paired_db_verification_passed": paired_db_ok,
            "db_mismatches_count": len(db_mismatches),
            "db_mismatches": db_mismatches,
        },
        "limitations": (
            "Thử nghiệm chạy trên MockLLM với giá token VND giả lập; latency là unavailable. "
            "Trong sản phẩm thương mại thật, lời phản hồi tự nhiên soạn cho khách hàng đem lại giá trị UX "
            "dù không làm thay đổi bản ghi giao dịch trong ledger."
        ),
        "baseline_report": baseline_report,
        "treatment_report": treatment_report,
    }
    return ablation_result


def main() -> None:
    utf8_stdio()
    default_cases = repo_path("data", "public_claims.jsonl")
    default_world = repo_path("data", "public_world_state.json")

    parser = argparse.ArgumentParser(description="Run controlled ablation on Single Agent")
    parser.add_argument("--cases", default=default_cases, help="Path to claims JSONL")
    parser.add_argument("--world", default=default_world, help="Path to world JSON")
    parser.add_argument("--seeds", default="11,22,33,44,55", help="Comma-separated seeds")
    parser.add_argument("--out", default="reports/jay_ablation.json", help="Output JSON path")
    args = parser.parse_args()

    seeds = [int(s.strip()) for s in args.seeds.split(",") if s.strip()]
    cases_path = Path(args.cases)
    world_path = Path(args.world)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    result = run_ablation(cases_path, world_path, seeds)
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    print("=== ABLATION EXPERIMENT RESULT ===")
    print(f"Status:                     {result['conclusion_status'].upper()}")
    print(f"Baseline mean_model_calls:  {result['baseline_summary']['mean_model_calls']:.2f}")
    print(f"Treatment mean_model_calls: {result['treatment_summary']['mean_model_calls']:.2f} (delta: {result['delta']['mean_model_calls_diff']:.4f})")
    print(f"Baseline cost/success:      {result['baseline_summary']['cost_per_success_vnd']:.2f} VND")
    print(f"Treatment cost/success:     {result['treatment_summary']['cost_per_success_vnd']:.2f} VND (delta: {result['delta']['cost_per_success_vnd_diff']:.2f} VND)")
    print(f"Pass rate:                  {result['treatment_summary']['pass_rate']} (delta: {result['delta']['pass_rate_diff']})")
    print(f"Paired DB & Ledger checks:  {'PASS (0 mismatches)' if result['delta']['paired_db_verification_passed'] else 'FAIL'}")
    print(f"Conclusion:                 {result['conclusion']}")
    print(f"Wrote ablation report to:   {out_path}")


if __name__ == "__main__":
    main()
