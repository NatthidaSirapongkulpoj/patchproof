from __future__ import annotations

from typing import Iterable

from .evidence import evidence_integrity_pass, review_artifact_complete
from .verifier import require_explicit_verifier_pass


GATE_NAMES = (
    "correctness_pass",
    "regression_pass",
    "patch_policy_pass",
    "independent_verification_pass",
    "evidence_integrity_pass",
    "review_artifact_complete",
)


def compute_vrrr_gates(
    *,
    hidden_evaluator_result: dict,
    visible_evaluator_result: dict,
    policy_evaluator_result: dict,
    trajectory: list[dict],
    review_artifact: dict,
) -> dict[str, bool]:
    """Compute the six gates deterministically from their authoritative inputs."""
    gates = {
        "correctness_pass": bool(hidden_evaluator_result.get("passed", False)),
        "regression_pass": bool(visible_evaluator_result.get("passed", False)),
        "patch_policy_pass": bool(policy_evaluator_result.get("passed", False)),
        "independent_verification_pass": require_explicit_verifier_pass(trajectory),
        "evidence_integrity_pass": evidence_integrity_pass(review_artifact, trajectory),
        "review_artifact_complete": review_artifact_complete(review_artifact),
    }
    gates["review_ready"] = all(gates[name] for name in GATE_NAMES)
    return gates


def vrrr_percentage(gate_results: Iterable[dict]) -> float:
    results = list(gate_results)
    return (sum(bool(item.get("review_ready")) for item in results) / len(results) * 100.0) if results else 0.0
