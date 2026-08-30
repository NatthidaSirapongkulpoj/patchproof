# Verified Repair Readiness Rate (VRRR)

## Purpose

PatchProof evaluates more than whether an agent can produce a functionally correct code patch.

The user problem is not simply:

> Can an agent generate a patch that passes tests?

The user problem is:

> Can an engineer receive a repair that is correct, independently verified, supported by reproducible evidence, and ready for safe human review?

The frozen Codex baseline achieved 12/12 successful cases on `benchmark-v1`, producing a correctness ceiling.

Verified Task Success Rate (VTSR) therefore remains an important correctness guardrail, but VTSR alone cannot measure the additional user value PatchProof is designed to provide.

PatchProof uses **Verified Repair Readiness Rate (VRRR)** as its primary user-success metric for the final workflow.

---

## Metric Definition

A case is **review ready** only when all six gates pass:

1. `correctness_pass`
2. `regression_pass`
3. `patch_policy_pass`
4. `independent_verification_pass`
5. `evidence_integrity_pass`
6. `review_artifact_complete`

The metric is:

    VRRR = review_ready_cases / evaluated_cases * 100

A case fails VRRR if any required gate is false.

There is no partial credit at the case level.

---

## Gate 1 — Correctness Pass

Field:

    correctness_pass

Pass condition:

The frozen hidden acceptance evaluator for the case passes.

The source of truth is the unchanged `benchmark-v1` hidden evaluator.

This gate must not be inferred from an agent's statement that the repair is correct.

It must be backed by evaluator evidence collected only after the PatchProof workflow has completed.

---

## Gate 2 — Regression Pass

Field:

    regression_pass

Pass condition:

The visible/regression test suite for the repaired repository passes.

This gate checks that the repair preserves behavior that was already expected to work.

A patch does not qualify as review ready if it fixes the target behavior while breaking existing tested behavior.

---

## Gate 3 — Patch Policy Pass

Field:

    patch_policy_pass

Pass condition:

The existing PatchProof patch-policy evaluator passes.

The repair must not modify prohibited files, including:

- visible tests,
- hidden evaluator files,
- benchmark definitions,
- evaluator semantics,
- files outside the permitted production-code scope.

For official benchmark repair stages, production changes are restricted to the allowed `app/` scope.

This gate protects benchmark integrity and keeps patches within the intended review scope.

---

## Gate 4 — Independent Verification Pass

Field:

    independent_verification_pass

Pass condition:

A verifier role that is logically distinct from the repair-generation role evaluates the produced repair and issues an explicit passing decision.

The verifier operates after a repair attempt.

The verifier may inspect:

- the public issue contract,
- the production-code diff,
- relevant production files,
- visible tests,
- public repository context,
- recorded non-hidden test evidence.

The verifier may execute relevant visible checks.

The verifier must not receive:

- hidden acceptance tests,
- hidden oracle implementation,
- hidden evaluator output,
- precomputed hidden-test knowledge.

The verifier produces a structured result containing at minimum:

- decision,
- findings,
- checks performed,
- evidence references.

The gate passes only when the final verifier decision is explicitly `pass`.

A repair agent reviewing its own work does not satisfy this gate.

---

## Gate 5 — Evidence Integrity Pass

Field:

    evidence_integrity_pass

Pass condition:

Every verification claim in the final review artifact is backed by recorded evidence.

Evidence records should support fields such as:

- `evidence_id`
- `timestamp`
- `role`
- `attempt`
- `event_type`
- `command`
- `output`
- `exit_code`
- `decision`

For example, a final artifact must not claim:

    Tests passed.

unless an actual recorded test execution supports that statement.

The gate fails if:

- a verification claim has no evidence reference,
- an evidence reference does not resolve,
- a claimed command was not recorded,
- a reported result conflicts with the recorded result,
- required verification evidence is missing.

This gate is intended to distinguish reproducible verification from unsupported agent confidence.

---

## Gate 6 — Review Artifact Complete

Field:

    review_artifact_complete

Pass condition:

The final structured artifact contains all required non-empty review fields.

### Required Field 1 — Root Cause

Field:

    root_cause

Explains the defect that caused the reported behavior.

It must provide an actual causal explanation rather than merely restating the issue.

### Required Field 2 — Changed Files

Field:

    changed_files

Lists the production files actually modified by the repair.

### Required Field 3 — Behavior Fixed

Field:

    behavior_fixed

Describes the externally observable behavior corrected by the repair.

### Required Field 4 — Verification Performed

Field:

    verification_performed

Lists checks actually executed.

Every verification item must reference recorded evidence.

### Required Field 5 — Verification Results

Field:

    verification_results

Reports the actual results of the recorded verification checks.

Every reported verification result must reference recorded evidence.

### Required Field 6 — Remaining Risk

Field:

    remaining_risk

Explicitly states residual uncertainty or risk.

The field remains required even when the conclusion is:

    No known remaining risk within the evaluated scope.

### Required Field 7 — Human Review Action

Field:

    human_review_action

States what a human reviewer should do next.

Examples include:

    Review the diff and verification evidence before merging.

or:

    Do not merge yet; verifier findings require another repair attempt.

PatchProof never automatically deploys or merges consequential changes.

---

## Review-Ready Decision

The deterministic decision is:

    review_ready =
        correctness_pass
        AND regression_pass
        AND patch_policy_pass
        AND independent_verification_pass
        AND evidence_integrity_pass
        AND review_artifact_complete

A functionally correct patch can therefore fail VRRR when it lacks independent verification, defensible evidence, or a complete human-review artifact.

---

## Relationship Between VTSR and VRRR

### Verified Task Success Rate

VTSR measures functional repair success:

    VTSR = successful_correctness_cases / evaluated_cases * 100

The frozen Codex baseline achieved:

    12 / 12 = 100% VTSR

VTSR remains a correctness guardrail.

PatchProof must not improve VRRR by sacrificing functional correctness.

### Verified Repair Readiness Rate

VRRR measures whether the repair can be handed to a human reviewer with defensible and reproducible evidence.

VRRR adds requirements not captured by VTSR alone:

- independent verification,
- evidence integrity,
- complete review artifact,
- remaining-risk disclosure,
- explicit human-review action.

The PatchProof objective is:

    Maintain correctness while increasing verified repair readiness.

---

## Frozen Baseline

The official frozen baseline is:

    Execution mode: codex-cli
    Model: gpt-5.6-sol
    Prompt version: codex-baseline-v1
    Benchmark: benchmark-v1
    Cases: PP-01 through PP-12
    Successful cases: 12
    VTSR: 100%

The frozen baseline must not be:

- weakened retroactively,
- rerun to cherry-pick failures,
- altered after observing final results,
- evaluated with different correctness cases.

If evidence required by VRRR is absent from a baseline artifact, absence of evidence is not counted as success for that gate.

This does not mean the baseline repair is functionally incorrect.

It means the recorded baseline artifact does not establish that additional review-readiness property.

---

## Final Workflow

Official PatchProof final runs use the same frozen `benchmark-v1` cases.

The final workflow may contain:

1. Investigator
2. Repair Agent
3. Independent Verifier
4. Bounded Repair Retry
5. Evidence Reporter
6. Human Review Checkpoint

The hidden acceptance evaluator remains unchanged.

Hidden evaluation occurs only after the agentic workflow has completed.

---

## Investigator Requirement

The investigator is a diagnostic role.

It may inspect:

- issue text,
- repository structure,
- production code,
- visible tests.

It identifies:

- likely root cause,
- relevant files,
- behavioral contracts,
- repair risks.

The investigator must not modify production code.

The workflow should enforce or verify this requirement rather than relying solely on prompt instructions.

---

## Repair Agent Requirement

The repair agent receives public repository context and the investigation artifact.

It may:

- inspect production code,
- inspect visible tests,
- modify permitted production files,
- run visible tests.

It must not receive:

- hidden tests,
- hidden oracle logic,
- hidden evaluator results.

It should make the smallest plausible correct repair.

---

## Independent Verifier Requirement

The verifier is logically distinct from repair generation.

It evaluates the resulting patch after a repair attempt.

The verifier may:

- inspect the diff,
- inspect relevant code,
- inspect visible tests,
- run public/visible checks,
- evaluate issue-derived behavioral contracts.

The verifier must not use hidden-test information.

If the repair does not pass verification, the verifier returns structured actionable feedback.

---

## Bounded Retry Rule

PatchProof permits a maximum of:

    2 total repair attempts

This means:

    initial repair attempt = 1
    maximum verifier-triggered retry = 1

Every repair attempt must be recorded.

At minimum, the trajectory must preserve:

- attempt number,
- reason,
- verifier feedback,
- resulting decision.

A workflow must never silently perform repair attempt 3.

If verification still fails after attempt 2, the workflow ends without claiming review readiness.

A case that passes verification on attempt 1 must not perform an unnecessary second repair.

---

## Evidence Reporter Requirement

The evidence reporter creates a machine-readable review artifact.

Required fields are:

- `root_cause`
- `changed_files`
- `behavior_fixed`
- `verification_performed`
- `verification_results`
- `remaining_risk`
- `human_review_action`

Verification claims must resolve to recorded trajectory evidence.

The evidence reporter must not invent test executions or verification results.

---

## Human Review Checkpoint

PatchProof is a repair-assistance workflow, not an autonomous deployment workflow.

Before frozen hidden evaluation, an artifact may contain:

    ready_for_human_review = false

because all six VRRR gates, including frozen hidden correctness, have not yet been computed.

After final evaluation, review readiness is determined from the six deterministic VRRR gates.

PatchProof never automatically merges or deploys the resulting repair.

---

## Trajectory Requirements

Final runs preserve enough information to reconstruct representative agent trajectories.

Trajectory records should support:

- `run_id`
- `case_id`
- `timestamp`
- `role`
- `attempt`
- `event_type`
- `command`
- `output`
- `exit_code`
- `decision`
- `evidence_id`

A possible successful trajectory is:

    issue
      |
      v
    investigator
      |
      v
    repair attempt 1
      |
      v
    independent verifier
      |
      +---- pass ----> evidence reporter
      |
      +---- fail ----> verifier feedback
                          |
                          v
                     repair attempt 2
                          |
                          v
                     verifier
                          |
                          v
                     evidence reporter
                          |
                          v
                     human review checkpoint

Not every case is expected to use the retry path.

---

## Deterministic Scoring

VRRR is computed by code from recorded workflow artifacts and frozen evaluator results.

VRRR must not depend on a human manually deciding whether an output "looks good."

At minimum, the scorer validates:

- required artifact fields exist,
- required fields are non-empty,
- required evidence references resolve,
- evaluator gates are true,
- verifier decision is explicit,
- verifier decision is passing,
- verification claims are supported by evidence.

The final summary reports both VTSR and VRRR over the same official final case set.

---

## Evaluation Integrity

The following rules apply to official final evaluation:

1. `benchmark-v1` remains frozen.
2. PP-01 through PP-12 remain the official correctness cases.
3. Hidden evaluator semantics remain unchanged.
4. Hidden tests are unavailable during investigation.
5. Hidden tests are unavailable during repair.
6. Hidden tests are unavailable during independent verification.
7. Hidden evaluator output is unavailable before workflow completion.
8. Official final runs are not rerun to cherry-pick better outcomes.
9. Infrastructure failures that occur before agentic repair materially begins may be documented and retried as infrastructure failures.
10. Once an official repair run materially begins, its observed outcome is retained.
11. Failures are reported as observed.
12. Metric definitions are not changed after final results solely to improve reported performance.
13. Case-specific hidden-oracle logic must not be added to the workflow.
14. Precomputed solution patches must not be embedded into prompts or implementation.

---

## Success Criteria Defined Before Final Evaluation

This specification is frozen before official PatchProof final benchmark execution.

The intended success criteria are:

1. Preserve VTSR at the highest achievable level.
2. Increase VRRR relative to the frozen baseline.
3. Produce independent verifier evidence for every official final case.
4. Produce complete review artifacts for every official final case.
5. Produce no unsupported verification claims.
6. Keep all repair attempts within the bounded retry policy.
7. Preserve `benchmark-v1` and evaluator semantics unchanged.

The observed final results must be reported even if these goals are not achieved.

---

## Primary Evaluation Question

The primary PatchProof evaluation question is:

> Of the repair tasks evaluated, how many ended with a functionally correct, regression-safe, policy-compliant, independently verified repair whose claims are backed by reproducible evidence and whose final artifact is complete enough for explicit human review?

The answer is measured by **Verified Repair Readiness Rate (VRRR)**.

---

## Interpretation

PatchProof is built around the engineering distinction:

    Correct patch != Verified review-ready repair

A frontier coding agent may already be highly capable of producing functionally correct patches.

PatchProof targets the remaining bottleneck:

- proving what changed,
- proving what was checked,
- detecting unsupported confidence,
- bounding repair retries,
- recording verifier feedback,
- disclosing remaining uncertainty,
- handing a human reviewer a reproducible evidence package.

The metric therefore rewards not merely patch generation, but trustworthy repair completion.
