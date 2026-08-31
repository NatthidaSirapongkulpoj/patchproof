# PatchProof

> **Verification-first agentic repair for Python APIs.**

**Patch generation is becoming the easy part. Verification debt is the new bottleneck.**

PatchProof is an agentic software-repair workflow for backend engineers maintaining Python API services under delivery pressure.

It takes a bug report and an isolated repository, then produces:

- a root-cause analysis,
- a minimal production patch,
- independent verification,
- evidence-linked verification claims,
- a structured review artifact,
- explicit remaining risk,
- and a human-review checkpoint.

PatchProof never merges or deploys the repair automatically.

---

## Final Result

PatchProof was evaluated on a frozen 12-case FastAPI and Flask benchmark.

```text
Final VTSR: 12 / 12 = 100%
Final VRRR: 12 / 12 = 100%
Missing cases: 0
```

Frozen final evidence:

```text
Commit: 2c3fda4
Tag:    final-v2
```

Official aggregate artifact:

```text
evidence/patchproof-final-summary.json
```

Frozen result:

```json
{
  "evaluated_case_count": 12,
  "successful_case_count": 12,
  "review_ready_case_count": 12,
  "vtsr_percentage": 100.0,
  "vrrr_percentage": 100.0,
  "missing_cases": []
}
```

---

## What Changed — In One Sentence

The baseline already generated correct patches on all 12 frozen cases; PatchProof's contribution is converting that correctness into a **fail-closed, independently verified, evidence-backed workflow that stops at a human-review checkpoint**.

---

# 1. The Problem

## Who has this problem?

Backend engineers maintaining small and medium Python API services.

A repair request often sounds straightforward:

> “Fix this endpoint without breaking existing behavior.”

Generating plausible code is increasingly inexpensive.

Approving that code safely is not.

Before reviewing a patch, an engineer still needs to know:

- What actually caused the bug?
- What existing behavior is contractual?
- Is the patch minimal?
- Did visible tests pass?
- Were important edge cases checked?
- Were regressions introduced?
- Did the patch touch forbidden files?
- Did an independent verifier inspect it?
- Is every verification claim backed by evidence?
- What uncertainty remains?
- What should the human reviewer examine?

Those steps are normally fragmented across repository inspection, test execution, manual reasoning, diff review, and documentation.

## The bottleneck

The bottleneck is not:

```text
Can an agent generate a plausible patch?
```

The bottleneck is:

```text
Can an engineer trust the evidence around that patch enough to review it?
```

A plausible repair can still:

- pass an obvious public test while breaking an edge case,
- convert unrelated exceptions into the wrong HTTP status,
- mutate persistent state before validation completes,
- duplicate work after a retry,
- modify unnecessary files,
- claim verification that never happened,
- or lose the evidence needed to audit what happened.

PatchProof treats **verification evidence as part of the deliverable**.

---

# 2. Product Principle

A correct patch is necessary.

A **verified, evidence-backed, human-review-ready repair** is the useful output.

PatchProof separates four responsibilities:

```text
Bug report + isolated repository
              |
              v
      +------------------+
      |   Investigator   |
      |    read-only     |
      +------------------+
              |
              | root cause
              | contracts
              | relevant files
              | proposed repair
              v
      +------------------+
      |   Repair Agent   |
      | workspace-write  |
      +------------------+
              |
              | minimal patch
              v
      +------------------+
      |   Independent    |
      |     Verifier     |
      |    read-only     |
      +------------------+
              |
              | evidence IDs
              | pass / retry
              v
      +------------------+
      | Evidence Reporter|
      |    read-only     |
      +------------------+
              |
              | canonical
              | review artifact
              v
      +------------------------+
      | Human Review Checkpoint|
      +------------------------+
              |
              v
       No automatic merge
       No automatic deploy
```

The number of agents is not the contribution.

The contribution is the separation of responsibilities, machine-validated evidence flow, fail-closed orchestration, and explicit human approval boundary.

---

# 3. Agent Roles

## 3.1 Investigator

**Permission model:** read-only

The Investigator reads:

- the bug report,
- production source,
- visible tests,
- repository structure.

It produces:

```text
root_cause
relevant_files
behavioral_contracts
proposed_repair
uncertainties
```

It does not modify production files.

This keeps diagnosis separate from implementation.

---

## 3.2 Repair Agent

**Permission model:** workspace write in the isolated repair repository

The Repair Agent receives the issue and investigation artifact.

It must:

- make the smallest correct production change,
- preserve existing behavior outside the reported defect,
- avoid modifying benchmark or evaluator files,
- avoid modifying tests,
- use visible checks where useful,
- never access hidden evaluator material,
- never merge,
- never deploy.

Repair attempts are bounded.

```text
Maximum repair attempts: 2
```

---

## 3.3 Independent Verifier

**Permission model:** read-only

The Verifier independently inspects the resulting repair.

It checks:

- the actual application diff,
- visible tests,
- reported behavioral contracts,
- issue-specific edge cases,
- regression-sensitive behavior,
- scope and minimality.

Verification claims must reference concrete evidence IDs.

A successful verification may contain no findings, but it must contain concrete verification evidence.

A failed verification cannot be unexplained: it must contain actionable findings or retry feedback.

---

## 3.4 Evidence Reporter

**Permission model:** read-only

The Evidence Reporter converts the verified run into a structured artifact for a human reviewer.

The canonical review artifact contains exactly:

```text
root_cause
changed_files
behavior_fixed
verification_performed
verification_results
remaining_risk
human_review_action
ready_for_human_review
```

Raw model output is not automatically trusted as evaluator input.

PatchProof separates:

```text
raw model output
        |
        v
strict normalization
        |
        v
canonical review artifact
```

Unknown top-level model fields are not silently promoted into evaluator truth.

---

# 4. Human Review Is a Feature

PatchProof deliberately stops before a consequential action.

The workflow may conclude:

```text
ready_for_human_review = true
```

but it does not:

```text
merge
deploy
approve production release
```

A qualified human reviewer remains responsible for the final decision.

Verification reduces uncertainty.

It does not replace engineering accountability.

---

# 5. Benchmark

PatchProof uses a frozen synthetic benchmark of 12 Python API repair tasks.

Frozen benchmark:

```text
Tag:    benchmark-v1
Commit: 361870b
```

Benchmark specification:

```text
benchmark/BENCHMARK_SPEC.md
```

Benchmark sanity evidence:

```text
evidence/benchmark-sanity.json
```

The benchmark was frozen before official baseline and final evaluation.

## Cases

| Case | Framework | Failure Mode |
|---|---|---|
| PP-01 | FastAPI | Reject order quantity below 1 |
| PP-02 | FastAPI | Pagination off-by-one |
| PP-03 | Flask | Missing resource must return 404 |
| PP-04 | Flask | Missing, malformed, or non-object JSON |
| PP-05 | FastAPI | Missing `await` in async behavior |
| PP-06 | FastAPI | Map domain `NotFoundError` to 404 without hiding unexpected failures |
| PP-07 | FastAPI | Multi-file email-normalization consistency |
| PP-08 | Flask | Cache identity must include query parameters |
| PP-09 | FastAPI | Regression trap: correct error response while preserving success contract |
| PP-10 | FastAPI | Parse environment timeout text as a number |
| PP-11 | Flask | Failed update must not partially mutate stored state |
| PP-12 | FastAPI | Idempotency across retry after persistence and response interruption |

---

# 6. Challenging Case: PP-12

PP-12 is the designated challenging case.

The defect involves idempotency when persistence succeeds but the response is interrupted.

A correct repair must ensure that:

- a request creates a job normally,
- the `Idempotency-Key` is associated before response interruption,
- retrying the same key returns the original job,
- a different key creates a different job,
- concurrent requests using the same key do not create duplicates,
- reset behavior clears idempotency state.

The final repair used a lock-protected get-or-create operation spanning:

```text
app/service.py
app/store.py
```

Final PP-12 result:

```text
success = true
visible tests = pass
hidden acceptance = pass
patch policy = pass
independent verification = pass
evidence integrity = pass
review artifact = complete
review ready = true
```

Official run:

```text
PP-12-patchproof-final-618832b5
```

---

# 7. Evaluation Design

## 7.1 Original correctness metric: VTSR

The original primary correctness metric is:

```text
Verified Task Success Rate (VTSR)
```

Definition:

```text
VTSR = successful cases / evaluated cases * 100
```

A case is successful only when the benchmark evaluator confirms:

```text
hidden acceptance
AND
visible regression tests
AND
patch policy
AND
timeout policy
```

---

# 8. Baseline

The official baseline used one general-purpose Codex repair agent on each of the same 12 frozen benchmark cases.

Model:

```text
gpt-5.6-sol
```

Baseline freeze:

```text
Commit: d82243e
Message: eval: freeze 12-case Codex baseline at 100 percent VTSR
```

Official baseline result:

```text
12 / 12 successful
VTSR = 100%
```

This result was important because it exposed a correctness ceiling.

A more elaborate workflow could not honestly claim an improvement from:

```text
100% correctness
```

to something higher.

Instead, the baseline revealed a different practical problem:

> A correct patch is not automatically an independently verified, evidence-backed, review-ready repair.

That observation changed the project direction.

---

# 9. Verified Repair Readiness Rate

After observing the baseline's 100% VTSR saturation, and **before the official final runs**, PatchProof defined and froze an additional metric:

```text
Verified Repair Readiness Rate (VRRR)
```

Specification:

```text
docs/VRRR_SPEC.md
```

VTSR remained the correctness guardrail.

VRRR asks whether a correct repair is also ready for responsible human review.

A case is review-ready only when all six readiness gates pass:

```text
correctness_pass
AND
regression_pass
AND
patch_policy_pass
AND
independent_verification_pass
AND
evidence_integrity_pass
AND
review_artifact_complete
```

Definition:

```text
VRRR = review-ready cases / evaluated cases * 100
```

## Timing disclosure

VRRR was **not** defined before the baseline.

It was introduced after the baseline exposed a correctness ceiling and was frozen before official final evaluation.

This distinction is intentional and part of the reported experiment history.

---

# 10. Baseline vs Final

## Headline comparison

| Metric | Simple Baseline | PatchProof Final v2 | Result |
|---|---:|---:|---|
| VTSR | 12/12 — 100% | 12/12 — 100% | Correctness ceiling preserved |
| Official VRRR | Not defined during baseline | 12/12 — 100% | Added readiness measurement |
| Independent verifier evidence | Absent from baseline workflow | Present in 12/12 final cases | Added |
| Evidence-linked review artifact | Absent from baseline workflow | Present in 12/12 final cases | Added |
| Hidden acceptance | 12/12 | 12/12 | Preserved |
| Regression checks | 12/12 | 12/12 | Preserved |
| Patch-policy compliance | 12/12 | 12/12 | Preserved |
| Explicit human-review checkpoint | No | Yes | Added |
| Bounded repair attempts | No final-v2 protocol | Maximum 2 | Added |
| Fail-closed recovery | No | Yes | Added |

## Interpreting the comparison

PatchProof does **not** claim that the final multi-agent workflow generated more correct patches than the baseline on this benchmark.

Both reached:

```text
VTSR = 100%
```

The final workflow instead adds a second layer of engineering guarantees around the repair:

```text
separate diagnosis
+
bounded implementation
+
independent verification
+
evidence-backed claims
+
strict review artifact
+
human checkpoint
```

Because the baseline predates VRRR, baseline VRRR is reported as:

```text
not originally measured
```

rather than pretending VRRR had been a pre-registered baseline metric.

The baseline workflow did not produce the distinct independent-verifier and canonical evidence-linked review artifacts required by the later-frozen readiness specification.

The official final workflow produced them for all 12 evaluated cases.

---

# 11. Official Final Results

| Case | Correctness | Regression | Policy | Independent Verification | Evidence Integrity | Review Artifact | Review Ready |
|---|---|---|---|---|---|---|---|
| PP-01 | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| PP-02 | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| PP-03 | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| PP-04 | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| PP-05 | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| PP-06 | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| PP-07 | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| PP-08 | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| PP-09 | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| PP-10 | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| PP-11 | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| PP-12 | PASS | PASS | PASS | PASS | PASS | PASS | PASS |

Aggregate:

```text
Evaluated:    12
Successful:   12
Review-ready: 12

VTSR: 100%
VRRR: 100%
```

---

# 12. Why This Output Is More Useful

A basic repair result answers:

```text
Did the patch pass?
```

PatchProof additionally answers:

```text
What caused the defect?

What production files changed?

What behavior was fixed?

What existing behavior was preserved?

What verification was actually performed?

Which evidence proves each verification claim?

Did an independent verifier inspect the result?

What uncertainty remains?

What should the human reviewer check next?
```

That is the product-level difference.

---

# 13. Evidence Integrity

PatchProof does not accept prose such as:

```text
"Tests passed."
```

as sufficient verification evidence.

Claims must reference evidence IDs recorded by the workflow.

Example:

```json
{
  "verification_performed": [
    {
      "evidence_id": "visible-tests-attempt-1",
      "description": "Ran the visible test suite."
    },
    {
      "evidence_id": "contract-check-attempt-1",
      "description": "Checked the issue-specific behavioral contract."
    }
  ],
  "verification_results": [
    {
      "evidence_id": "visible-tests-attempt-1",
      "result": "Visible tests passed."
    },
    {
      "evidence_id": "contract-check-attempt-1",
      "result": "Focused contract checks passed."
    }
  ]
}
```

A final case cannot become review-ready unless its required evidence references are backed by recorded trajectory evidence.

---

# 14. Fail-Closed Workflow Design

PatchProof prefers:

```text
stop with an explicit error
```

over:

```text
silently claim success from ambiguous state
```

This principle became especially important during official final evaluation.

Two real harness failures were preserved and converted into explicit recovery mechanisms.

---

# 15. PP-10: Verifier-Validation Shakedown

Official run:

```text
PP-10-patchproof-final-fdf23080
```

The repair had already executed.

The Independent Verifier returned:

```json
{
  "passed": true,
  "findings": [],
  "verification_evidence_ids": [
    "visible-tests-attempt-1",
    "contract-check-attempt-1"
  ],
  "retry_feedback": ""
}
```

The verifier had concrete evidence and passed the repair.

The harness nevertheless failed because the original validation logic incorrectly required non-empty findings for every verifier decision.

## What PatchProof did

It did **not** discard the original repair and rerun after seeing the result.

Instead:

1. the original verifier artifact was preserved,
2. validation semantics were corrected,
3. passing verifier decisions were required to contain evidence rather than artificial findings,
4. failed decisions were still required to provide actionable information,
5. a narrow fail-closed recovery path was added,
6. the original PP-10 run resumed after its existing verifier,
7. only the remaining Evidence Reporter stage executed,
8. hidden evaluation ran only after workflow completion.

Recovery command:

```powershell
python scripts\run_patchproof_final.py `
  --run-id PP-10-patchproof-final-fdf23080 `
  --resume-after-verifier
```

Relevant engineering commit:

```text
a7556e4 fix: recover verified runs after validation failure
```

Final PP-10 result:

```text
success = true
all final gates = true
```

---

# 16. PP-11: Investigator-Schema Shakedown

Official run:

```text
PP-11-patchproof-final-09973963
```

The Investigator successfully analyzed the bug but represented relevant files as structured objects:

```json
{
  "path": "app/main.py",
  "relevance": "Defines the update handler containing the mutation-before-validation defect."
}
```

The original harness expected plain strings and passed the dictionary directly to `pathlib.Path`.

The workflow failed before Repair Agent execution.

No repair had started.

No verifier had run.

No hidden evaluator had run.

## What PatchProof did

It did not rerun the Investigator.

Instead:

1. the raw Investigator artifact was preserved,
2. strict canonical normalization was added,
3. supported path strings and structured path objects were accepted,
4. absolute paths and traversal remained rejected,
5. unsupported structures still failed closed,
6. a narrow post-Investigator recovery path was added,
7. the original PP-11 run resumed without rerunning investigation.

Recovery command:

```powershell
python scripts\run_patchproof_final.py `
  --run-id PP-11-patchproof-final-09973963 `
  --resume-after-investigator
```

Relevant engineering commit:

```text
230663a fix: recover runs after investigator schema mismatch
```

Final PP-11 result:

```text
success = true
all final gates = true
```

---

# 17. Why Recovery Matters

These recovery mechanisms are not generic “try again until it passes” commands.

They enforce narrow prerequisite states.

For example:

```text
resume-after-verifier
```

cannot be used as a normal repair retry.

It requires an already-existing valid verifier artifact and refuses recovery from ambiguous or completed states.

Likewise:

```text
resume-after-investigator
```

requires that no repair attempt has started.

This protects the evaluation from silently replacing observed outcomes with cherry-picked reruns.

---

# 18. Improvement Changelog

Full changelog:

```text
docs/IMPROVEMENT_CHANGELOG.md
```

Key progression:

| Stage | What Happened | Decision / Learning |
|---|---|---|
| Benchmark freeze | Built 12 reproducible bug cases | Freeze before official evaluation |
| Simple Codex baseline | Reached 12/12 VTSR | Correctness was already saturated |
| Manual relay experiment | Malformed JSON, indentation and action-loop failures | Removed |
| Final v1 orchestration | Agents could verify but workflow state was not fully persisted | Build one-command persistent orchestration |
| Windows launcher shakedown | Python subprocess could not resolve bare `codex` | Resolve Windows `codex.cmd` explicitly |
| UTF-8 shakedown | Codex stdin failed under Windows encoding behavior | Force UTF-8 subprocess I/O |
| Review-schema shakedown | Model-added fields violated evaluator schema | Separate raw output from canonical review artifact |
| PP-10 shakedown | Passing verifier returned empty findings | Require evidence for a pass, not artificial findings |
| PP-11 shakedown | Investigator returned structured relevant-file objects | Strict normalization + safe resume |
| Final v2 | 12/12 VTSR and 12/12 VRRR | Freeze official results |

---

# 19. Removed Experiment

Before the official Codex baseline, an early manual-relay workflow attempted to move agent output between stages manually.

It was removed after exposing brittle behavior including:

```text
malformed JSON
indentation failures
action-loop failures
weak state persistence
```

The failed experiment was not rewritten as a success.

Its traces were retained locally as development evidence.

The central lesson was:

> Multi-agent reliability does not come from adding more roles. It comes from making state transitions explicit, machine-validated, and recoverable.

---

# 20. Main Failure Mode

The most important failure discovered during development was not an incorrect patch.

It was:

> **Verification could happen without the orchestration layer being able to reliably persist or prove that it happened.**

That changed the design.

PatchProof treats these as separate concepts:

```text
agent output
execution evidence
workflow state
canonical artifact
```

A robust agent workflow cannot assume that because a model produced a plausible statement, the system has valid evidence for that statement.

---

# 21. Hot Take

> **Patch generation is becoming the easy part. Verification debt is the new bottleneck.**

Coding agents are becoming good enough that producing a plausible patch is increasingly cheap.

That shifts the difficult engineering work toward:

```text
scope control
verification
evidence
auditability
recovery
human trust
```

The scarce resource is increasingly not code generation.

It is **justified trust**.

---

# 22. Repository Layout

```text
.
├── benchmark/
├── docs/
├── evidence/
├── prompts/
├── scripts/
├── src/
├── tests/
├── benchmark_manifest.jsonl
├── PROJECT_PLAN.md
├── pytest.ini
├── README.md
├── requirements.txt
└── SUBMISSION_DRAFT.md
```

Important paths:

```text
benchmark/BENCHMARK_SPEC.md
docs/VRRR_SPEC.md
docs/IMPROVEMENT_CHANGELOG.md
evidence/benchmark-sanity.json
evidence/patchproof-final-summary.json
evidence/final/
evidence/final-traces/
prompts/
scripts/
src/patchproof/
tests/
```

---

# 23. Reproduction Guide

The goal is for another engineer to start from a clean environment and reproduce the workflow and evaluation result.

## Recorded environment

```text
Operating system: Windows
Python:           3.12.10
Git:              2.54.0.windows.1
Codex CLI:        0.151.0
Model:            gpt-5.6-sol
```

Codex was authenticated through a ChatGPT account.

No OpenAI API key was required for the recorded runs.

Recorded direct API spend:

```text
$0
```

A token-based dollar cost is not claimed because Codex usage through ChatGPT authentication was not independently metered as API spend.

---

# 24. Clone the Frozen Final Version

```powershell
git clone https://github.com/NatthidaSirapongkulpoj/patchproof.git
cd patchproof
git checkout final-v2
```

Verify:

```powershell
git rev-parse --short HEAD
git tag --points-at HEAD
```

Expected:

```text
2c3fda4
final-v2
```

---

# 25. Create the Environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Expose the source package:

```powershell
$env:PYTHONPATH = "$PWD\src"
```

Verify the main tools:

```powershell
python --version
git --version
codex --version
```

---

# 26. Run the Repository Test Suite

Use an isolated temporary directory:

```powershell
$bt = ".patchproof\pytest-repro-$([guid]::NewGuid().ToString('N'))"
python -m pytest -q --basetemp=$bt
```

The implementation reached:

```text
95 passed
```

before the final evaluation evidence was frozen.

---

# 27. Inspect the Frozen Benchmark

Benchmark specification:

```powershell
Get-Content -Raw benchmark\BENCHMARK_SPEC.md
```

Sanity evidence:

```powershell
Get-Content -Raw evidence\benchmark-sanity.json
```

Frozen benchmark tag:

```powershell
git show benchmark-v1 --no-patch
```

The original buggy repositories are expected to fail hidden acceptance before repair.

---

# 28. Running One Final Case

Set:

```powershell
$env:PYTHONPATH = "$PWD\src"
```

Prepare an isolated case:

```powershell
python scripts\prepare_patchproof_final.py --case PP-12
```

The command returns a run ID similar to:

```text
PP-12-patchproof-final-<RUN_ID>
```

Run the workflow:

```powershell
python scripts\run_patchproof_final.py --run-id <RUN_ID>
```

Expected workflow-level shape:

```json
{
  "run_id": "<RUN_ID>",
  "verification_passed": true
}
```

Then evaluate:

```powershell
python scripts\evaluate_patchproof_final.py --run-id <RUN_ID>
```

A successful result has:

```json
{
  "success": true,
  "gates": {
    "correctness_pass": true,
    "regression_pass": true,
    "patch_policy_pass": true,
    "independent_verification_pass": true,
    "evidence_integrity_pass": true,
    "review_artifact_complete": true,
    "review_ready": true
  }
}
```

---

# 29. Running All Final Cases

Use the same process for:

```text
PP-01
PP-02
PP-03
PP-04
PP-05
PP-06
PP-07
PP-08
PP-09
PP-10
PP-11
PP-12
```

The intended evaluation protocol is:

```text
prepare
→ run workflow
→ evaluate
→ preserve result
```

Do not cherry-pick successful attempts.

Observed orchestration failures should be retained in the changelog or trajectories rather than silently replaced.

After all 12 cases have been evaluated:

```powershell
python scripts\summarize_patchproof_final.py
```

Expected aggregate:

```json
{
  "evaluated_case_count": 12,
  "successful_case_count": 12,
  "review_ready_case_count": 12,
  "vtsr_percentage": 100.0,
  "vrrr_percentage": 100.0,
  "missing_cases": []
}
```

---

# 30. Baseline Reproduction

The baseline uses the same frozen benchmark cases and the same model family but a simpler agent configuration.

Useful scripts:

```text
scripts/prepare_codex_baseline.py
scripts/evaluate_codex_run.py
scripts/summarize_codex_baseline.py
```

The frozen official baseline result is already recorded at:

```text
d82243e
```

with:

```text
12 / 12 successful
VTSR = 100%
```

The baseline intentionally uses fewer workflow resources:

```text
Baseline
--------
one general-purpose Codex repair agent
same frozen benchmark cases
same model
no independent verifier stage
no Evidence Reporter stage
no VRRR evidence requirements
no final-v2 human-review artifact protocol
```

Final workflow:

```text
PatchProof Final v2
-------------------
Investigator
Repair Agent
Independent Verifier
Evidence Reporter
evidence-integrity validation
bounded repair attempts
human-review checkpoint
fail-closed recovery
```

This difference in resource usage is intentional and is part of the intervention being evaluated.

---

# 31. Final Evidence

Official evaluator outputs:

```text
evidence/final/
```

Official complete trajectories:

```text
evidence/final-traces/
```

Aggregate:

```text
evidence/patchproof-final-summary.json
```

Every official final case has:

- evaluator outcome,
- gate outcomes,
- review artifact,
- complete trajectory.

---

# 32. Representative Agent Trajectories

Representative final trajectory:

```text
evidence/final-traces/PP-12-patchproof-final-618832b5.jsonl
```

PP-12 is useful because it demonstrates:

- Investigator reasoning,
- a multi-file repair,
- independent verification,
- contract checks,
- concurrency-sensitive behavior,
- evidence reporting,
- human-review checkpoint,
- hidden acceptance.

Recovery-focused trajectories:

```text
evidence/final-traces/PP-10-patchproof-final-fdf23080.jsonl
evidence/final-traces/PP-11-patchproof-final-09973963.jsonl
```

These show how the workflow preserves prior agent work rather than discarding it after harness failures.

---

# 33. Recovery Commands

Recovery commands are deliberately narrow and fail closed.

They are not ordinary retries.

## Resume after an existing Verifier result

```powershell
python scripts\run_patchproof_final.py `
  --run-id <RUN_ID> `
  --resume-after-verifier
```

The command requires the expected preconditions and refuses an already-completed or ambiguous run.

## Resume after an existing Investigator result

```powershell
python scripts\run_patchproof_final.py `
  --run-id <RUN_ID> `
  --resume-after-investigator
```

This recovery refuses a run if repair work has already begun.

Neither recovery path invokes hidden evaluation.

Hidden evaluation remains a separate explicit step.

---

# 34. Runtime and Resource Tradeoff

A normal successful final case generally requires several sequential agent calls and therefore takes longer than the single-agent baseline.

Observed ordinary successful final cases typically completed in the order of a few minutes, followed by evaluator tests taking only a few seconds.

The official evaluation also preserved non-ideal runtime behavior:

- PP-09 experienced a long-running Codex/session delay before eventually finishing successfully.
- PP-10 exposed a verifier-validation harness defect and was recovered from the original verifier result.
- PP-11 exposed an Investigator-schema harness defect and was recovered from the original Investigator result.

PatchProof intentionally accepts additional latency and agent calls in exchange for:

```text
independent verification
evidence integrity
review artifacts
recoverability
human-review readiness
```

That resource difference is disclosed rather than hidden.

---

# 35. Data, Safety, and Scope

The benchmark uses synthetic local repositories created for evaluation.

No production customer data is required.

The workflow:

- operates in isolated repair repositories,
- restricts repair writes,
- prevents normal agent access to hidden evaluator material,
- applies patch-policy checks,
- does not merge,
- does not deploy,
- ends at a human-review checkpoint.

Credentials and private information are not part of the submitted evaluation evidence.

---

# 36. Limitations

PatchProof does not claim that success on this benchmark proves production safety.

Current limitations include:

- benchmark repositories are intentionally small,
- evaluation covers FastAPI and Flask rather than all Python frameworks,
- the benchmark is synthetic,
- final-v2 uses more agent calls and latency than the baseline,
- PP-12 idempotency state remains process-local and in-memory,
- the benchmark does not evaluate multi-process or distributed persistence,
- generated Python bytecode may appear in isolated run directories even though evaluator patch policy identifies intentional source changes separately,
- VRRR was introduced after baseline saturation rather than before baseline execution,
- human review remains necessary.

These limitations are intentionally visible.

The goal is evidence-backed engineering, not inflated claims.

---

# 37. What Existed Before vs What Was Added

PatchProof's competition work is represented by the repository history and Improvement Changelog.

The submitted work includes the project-specific:

- benchmark design,
- benchmark repositories,
- evaluation harness,
- agent prompts,
- orchestration,
- evidence model,
- VRRR specification,
- strict artifact normalization,
- fail-closed recovery behavior,
- tests,
- final trajectories,
- baseline and final evaluation evidence.

The implementation uses existing external tooling and libraries including Python, Git, pytest, FastAPI, Flask, and Codex CLI.

The repository history provides the exact sequence of project changes.

---

# 38. Frozen Checkpoints

## Benchmark

```text
361870b
benchmark-v1
```

## Official baseline

```text
d82243e
```

Result:

```text
VTSR = 100% (12/12)
```

## Final workflow evidence

```text
2c3fda4
final-v2
```

Result:

```text
VTSR = 100% (12/12)
VRRR = 100% (12/12)
```

---

# 39. Quick Verification of the Frozen Submission

```powershell
git checkout final-v2
git rev-parse --short HEAD
git tag --points-at HEAD
Get-Content -Raw evidence\patchproof-final-summary.json
```

Expected:

```text
HEAD = 2c3fda4
tag  = final-v2

evaluated_case_count    = 12
successful_case_count   = 12
review_ready_case_count = 12
vtsr_percentage         = 100.0
vrrr_percentage         = 100.0
missing_cases           = []
```

---

# 40. Evidence Map

| Claim | Evidence |
|---|---|
| Benchmark is frozen | `benchmark-v1`, commit `361870b` |
| Baseline VTSR is 100% | baseline freeze commit `d82243e` |
| Final VTSR is 100% | `evidence/patchproof-final-summary.json` |
| Final VRRR is 100% | `evidence/patchproof-final-summary.json` |
| All 12 cases have evaluator results | `evidence/final/` |
| All 12 cases have trajectories | `evidence/final-traces/` |
| VRRR definition | `docs/VRRR_SPEC.md` |
| Improvement history | `docs/IMPROVEMENT_CHANGELOG.md` |
| PP-10 recovery behavior | PP-10 trajectory + commit `a7556e4` |
| PP-11 recovery behavior | PP-11 trajectory + commit `230663a` |
| Final evidence freeze | commit `2c3fda4`, tag `final-v2` |
| Challenging case | PP-12 final result and trajectory |

---

# 41. The Main Engineering Lesson

Agent reliability is not just model capability.

It is also:

```text
state machines
schemas
permissions
evidence
validation
failure handling
recovery boundaries
human approval
```

The official evaluation demonstrated this directly.

Two final cases exposed failures in the surrounding orchestration rather than failures in the repair itself.

Those failures became improvements to the product instead of being hidden through fresh reruns.

---

# 42. Conclusion

The baseline showed that a general-purpose coding agent could already reach:

```text
12/12 task success
```

on this frozen benchmark.

That made the real opportunity clearer.

The next useful layer is not simply asking another model to write another patch.

It is constructing a workflow that can answer:

```text
Why is this repair correct?

What exactly was checked?

Where is the evidence?

What could still be wrong?

Can the workflow recover without rewriting history?

Is this ready for a human engineer to review?
```

PatchProof's final result is therefore intentionally framed as:

> **100% correctness preserved, with 100% of evaluated repairs converted into independently verified, evidence-backed, human-review-ready artifacts.**

And the broader lesson is:

> **Patch generation is becoming the easy part. Verification debt is the new bottleneck.**
