from __future__ import annotations

from copy import deepcopy

from patchproof.final.vrrr import GATE_NAMES, compute_vrrr_gates


def inputs() -> dict:
    trajectory = [
        {
            "role": "verifier",
            "event_type": "decision",
            "decision": "pass",
            "evidence_id": "verify-1",
        },
        {"role": "verifier", "event_type": "test", "evidence_id": "tests-1"},
    ]
    artifact = {
        "root_cause": "bad boundary",
        "changed_files": ["app/main.py"],
        "behavior_fixed": "boundary handled",
        "verification_performed": [{"check": "tests", "evidence_id": "tests-1"}],
        "verification_results": [{"result": "pass", "evidence_id": "verify-1"}],
        "remaining_risk": "low",
        "human_review_action": "review diff",
    }
    return {
        "hidden_evaluator_result": {"passed": True},
        "visible_evaluator_result": {"passed": True},
        "policy_evaluator_result": {"passed": True},
        "trajectory": trajectory,
        "review_artifact": artifact,
    }


def test_vrrr_all_pass_case() -> None:
    gates = compute_vrrr_gates(**inputs())
    assert all(gates[name] for name in GATE_NAMES)
    assert gates["review_ready"] is True


def test_one_failed_gate_makes_review_ready_false() -> None:
    for source in ("hidden_evaluator_result", "visible_evaluator_result", "policy_evaluator_result"):
        values = deepcopy(inputs())
        values[source]["passed"] = False
        assert compute_vrrr_gates(**values)["review_ready"] is False


def test_missing_evidence_reference_fails_integrity() -> None:
    values = inputs()
    values["review_artifact"]["verification_results"][0]["evidence_id"] = "missing"
    gates = compute_vrrr_gates(**values)
    assert gates["evidence_integrity_pass"] is False
    assert gates["review_ready"] is False


def test_incomplete_review_artifact_fails_completeness() -> None:
    values = inputs()
    values["review_artifact"]["remaining_risk"] = ""
    assert compute_vrrr_gates(**values)["review_artifact_complete"] is False
