"""Member 3 (Tran Thi Ha Anh): orchestrator security — handoff allowlist, trace contract, no leaks.

T05: order belongs to another principal -> escalated, no refund, no PII from that order in trace.
T10: normal paid claim -> resolved once, handoff stays inside handoff.v1 allowlist, no canary.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from lab8.handoff import ALLOWED_FIELDS, READONLY_TOOLS, WRITE_TOOLS
from lab8.shapes.orchestrator import run_claim
from tests.conftest import BY_ID


def _load_trace(result) -> dict:
    path = Path(result.trace_path)
    assert path.is_file(), "trace_path must point to a file written in this run"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["run_id"] == result.run_id
    assert isinstance(data["events"], list) and data["events"]
    return data


def _assert_no_forbidden(claim_id: str, result, trace: dict) -> None:
    blob = json.dumps(trace, ensure_ascii=False) + json.dumps(result.__dict__, ensure_ascii=False, default=str)
    assert "CANARY_SECRET_" not in blob
    assert "parent_secret" not in blob
    assert "raw_headers" not in blob
    for needle in BY_ID[claim_id]["expected"]["forbid_substrings"]:
        assert needle not in blob, f"trace/result leaked {needle!r}"


@pytest.mark.parametrize("claim_id", ["C-005", "C-010"])
def test_trace_contract_and_no_secret_or_pii(public_db, claim_id):
    result = run_claim(claim_id, seed=11, store_path=str(public_db))
    trace = _load_trace(result)
    _assert_no_forbidden(claim_id, result, trace)


def test_t05_other_principal_order_is_escalated_without_refund(public_db):
    result = run_claim("C-005", seed=11, store_path=str(public_db))
    assert result.status == "escalated"
    assert result.proposal_amount == 0
    assert result.refund_effects == []
    assert result.committed_audit_count == 0


def test_t10_handoff_is_allowlisted_and_readonly(public_db):
    result = run_claim("C-010", seed=22, store_path=str(public_db))
    assert result.status == "resolved"
    assert result.proposal_amount == 35000

    trace = _load_trace(result)
    handoffs = [e for e in trace["events"] if e.get("kind") == "handoff"]
    assert len(handoffs) == 1
    handoff = handoffs[0]["payload"]
    assert set(handoff) <= ALLOWED_FIELDS
    assert handoff["contract_version"] == "handoff.v1"
    assert set(handoff["allowed_tools"]) <= READONLY_TOOLS
    assert not set(handoff["allowed_tools"]) & WRITE_TOOLS
    # Ticket text is user data, never forwarded to the investigator.
    assert BY_ID["C-010"]["ticket"] not in json.dumps(handoff, ensure_ascii=False)


def test_t10_rerun_is_idempotent_across_seeds(public_db):
    first = run_claim("C-010", seed=11, store_path=str(public_db))
    second = run_claim("C-010", seed=55, store_path=str(public_db))
    assert first.status == second.status == "resolved"
    assert len(second.refund_effects) == 1
    assert second.refund_effects[0]["amount_vnd"] == 35000
    assert second.committed_audit_count == 1
