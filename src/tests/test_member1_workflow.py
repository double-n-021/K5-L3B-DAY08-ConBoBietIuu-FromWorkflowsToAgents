"""Unit and integration tests for Shape A (workflow) — Member 1 (Bui Dang Nhat Nguyen)."""

from __future__ import annotations

import time

import pytest

from lab8.db import connect, init_store
from lab8.durability import InjectedCrash
from lab8.metrics import artifact_blob, check_trace, trial_pass
from lab8.shapes.workflow import run_claim
from tests.conftest import BY_ID, CLAIMS, WORLD


def _fresh_store(tmp_path, name: str):
    path = tmp_path / name
    init_store(path, WORLD, CLAIMS).close()
    return path


@pytest.mark.parametrize("seed", [11, 22, 33, 44, 55])
def test_workflow_ignores_inflated_ticket_delay_across_all_seeds(tmp_path, seed):
    """T02 (C-002): ticket claims 5 days delay, but DB order O-202 has delay_days=2 (< 3).
    Unlike swarm on seed 55, workflow must deterministically deny across all seeds.
    """
    store = _fresh_store(tmp_path, f"wf-t02-{seed}.sqlite")
    started = time.time()
    result = run_claim("C-002", seed=seed, store_path=str(store))
    conn = connect(store)
    try:
        passed, reason = trial_pass(result.as_dict(), BY_ID["C-002"]["expected"], conn, started_at=started)
    finally:
        conn.close()
    assert passed, reason
    assert result.status == "denied"
    assert result.proposal_amount == 0
    assert result.refund_effects == []


def test_workflow_per_order_cap_full_quote_and_denial(tmp_path):
    """T13 (C-013) and T14 (C-014): workflow passes full quote so host enforces per-order cap."""
    store_t13 = _fresh_store(tmp_path, "wf-t13.sqlite")
    started_t13 = time.time()
    res_t13 = run_claim("C-013", seed=11, store_path=str(store_t13))
    conn_t13 = connect(store_t13)
    try:
        passed_t13, reason_t13 = trial_pass(
            res_t13.as_dict(), BY_ID["C-013"]["expected"], conn_t13, started_at=started_t13
        )
    finally:
        conn_t13.close()
    assert passed_t13, reason_t13
    assert res_t13.status == "denied"
    assert res_t13.proposal_amount == 35000
    assert res_t13.refund_effects == []

    store_t14 = _fresh_store(tmp_path, "wf-t14.sqlite")
    started_t14 = time.time()
    res_t14 = run_claim("C-014", seed=11, store_path=str(store_t14))
    conn_t14 = connect(store_t14)
    try:
        passed_t14, reason_t14 = trial_pass(
            res_t14.as_dict(), BY_ID["C-014"]["expected"], conn_t14, started_at=started_t14
        )
    finally:
        conn_t14.close()
    assert passed_t14, reason_t14
    assert res_t14.status == "resolved"
    assert res_t14.proposal_amount == 150000
    assert len(res_t14.refund_effects) == 1
    assert int(res_t14.refund_effects[0]["amount_vnd"]) == 120000


def test_workflow_unknown_claim_and_trace_safety(tmp_path):
    """Unknown claim returns failed with valid trace; T05 and T10 do not leak secrets or PII."""
    store = _fresh_store(tmp_path, "wf-unknown.sqlite")
    started = time.time()
    res_unknown = run_claim("C-999", seed=11, store_path=str(store))
    assert res_unknown.status == "failed"
    assert res_unknown.error_reason == "unknown_claim"
    assert res_unknown.proposal_amount == 0
    assert check_trace(res_unknown.as_dict(), started_at=started) == (True, "ok")

    for cid in ("C-005", "C-010"):
        store_sec = _fresh_store(tmp_path, f"wf-{cid}.sqlite")
        started_sec = time.time()
        res_sec = run_claim(cid, seed=11, store_path=str(store_sec))
        blob = artifact_blob(res_sec.as_dict())
        for token in BY_ID[cid]["expected"]["forbid_substrings"]:
            assert token not in blob
        assert check_trace(res_sec.as_dict(), started_at=started_sec) == (True, "ok")


def test_workflow_idempotency_and_crash_resume(tmp_path):
    """T12 crash before checkpoint propagates InjectedCrash and resumes to exactly 1 refund."""
    store = _fresh_store(tmp_path, "wf-crash.sqlite")
    with pytest.raises(InjectedCrash):
        run_claim("C-012", seed=11, store_path=str(store), crash_at="after_effect_before_checkpoint")

    started = time.time()
    resumed = run_claim("C-012", seed=11, store_path=str(store), crash_at=None)
    conn = connect(store)
    try:
        passed, reason = trial_pass(resumed.as_dict(), BY_ID["C-012"]["expected"], conn, started_at=started)
        count = conn.execute("SELECT COUNT(*) AS n FROM refund_ledger WHERE claim_id = 'C-012'").fetchone()["n"]
    finally:
        conn.close()
    assert passed, reason
    assert count == 1
