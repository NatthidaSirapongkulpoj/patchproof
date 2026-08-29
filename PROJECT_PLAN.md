# PatchProof: Verification-First Agentic Repair for Python APIs

## Project lock

**Intended user:** Backend engineers maintaining small-to-medium Python API services, especially FastAPI and Flask, who need to turn a bug report or failing behavior into a safe, reviewable patch under time pressure.

**Exact bottleneck:** Generating a plausible code edit is easy; verifying that it is actually safe is not. The engineer must locate relevant code in an unfamiliar service, preserve API contracts and edge cases, run the right tests, detect regressions, use failures to revise the patch, and leave a concise evidence trail a reviewer can trust.

**User-valued result:** A minimal patch that fixes the requested behavior, passes acceptance and regression tests, respects patch boundaries, and includes a reviewer-ready verification report.

## Primary metric: Verified Task Success Rate (VTSR)

A case is successful only when all gates pass:
1. Acceptance behavior passes.
2. Regression suite passes.
3. Health/import/smoke check passes where defined.
4. Patch-policy checks pass (no evaluator/benchmark tampering; no forbidden files changed).
5. Evaluation finishes inside the case timeout.

`VTSR = 100 * successful_cases / total_cases`

Report secondary metrics separately: first-attempt success, regression-safe rate, repair rounds, wall time, tool calls, approximate model cost, changed production files, and human interventions.

## Fair single-agent baseline

One general-purpose coding/repair agent receives the issue, repository, and repository-visible tests. It can list/read/search files, apply patches, and run sandboxed shell commands. It receives no forced phase structure, mandatory verifier gate, structured failure summarizer, orchestrator-enforced retry, or generated context pack.

Fairness controls kept identical between baseline and final workflow: model/provider/version, repo snapshots, issue statements, visible tests, sandbox, final evaluator, and decoding settings where controllable. Resource use differences are reported transparently.

**Baseline prompt:**

> You are repairing a Python API repository. Read the issue, inspect the repository, make the smallest correct fix, run any tests you believe are useful, and return a concise summary of the changes and tests you ran. Do not modify benchmark or evaluator files.

Initial cap to freeze before the first official run: max 16 agent tool actions and max 8 minutes wall-clock per case.

## Advanced hypotheses (implement only after baseline failure analysis)

- **H1 Mandatory deterministic verification:** always run visible target/regression tests before accepting the patch.
- **H2 Structured failure feedback:** compact pytest failures into test/failure_type/expected/actual/trace_tail before retry.
- **H3 Repository context pack:** deterministic repo map + issue-linked symbol/file search to reduce wrong-file edits.
- **H4 Bounded retry:** one evidence-driven retry after verification failure.
- **H5 Reviewer-ready report:** root cause, files changed, behavior fixed, tests run, verification status, remaining risk, suggested reviewer action.
- **Optional negative-control:** separate planning agent only if baseline data suggests planning is the bottleneck. Remove it if it does not improve the same benchmark.

## Exact implementation layout

```text
patchproof/
├── README.md
├── pyproject.toml
├── .env.example
├── Makefile
├── Dockerfile
├── prompts/
│   ├── baseline_system.md
│   ├── repair_system.md
│   └── retry_feedback.md
├── src/patchproof/
│   ├── api.py
│   ├── cli.py
│   ├── config.py
│   ├── models.py
│   ├── sandbox.py
│   ├── workspace.py
│   ├── agents/
│   │   ├── base.py
│   │   ├── baseline.py
│   │   ├── repair.py
│   │   └── provider.py
│   ├── tools/
│   │   ├── files.py
│   │   ├── search.py
│   │   ├── patch.py
│   │   └── shell.py
│   ├── workflow/
│   │   ├── baseline_runner.py
│   │   ├── repair_runner.py
│   │   ├── context_builder.py
│   │   ├── verifier.py
│   │   └── feedback.py
│   └── reporting/
│       ├── result.py
│       └── reviewer_report.py
├── benchmark/
│   ├── manifest.jsonl
│   ├── cases/PP-01 ... PP-12/
│   ├── evaluator/
│   │   ├── run_case.py
│   │   ├── score.py
│   │   ├── policy.py
│   │   └── oracles/PP-01 ... PP-12/
│   └── results/
├── evidence/
│   ├── changelog.md
│   ├── result_table.csv
│   ├── traces/
│   └── clean_reproduction.txt
└── tests/
```

## Implementation order

1. Typed task/run/verification models.
2. Sandboxed file/search/patch/shell tools.
3. Final evaluator that can score a pre-made patch without any agent.
4. Build three pilot benchmark repos: PP-01, PP-06, PP-12.
5. Implement baseline runner.
6. Run pilot baseline to validate the evaluator itself.
7. Build the remaining nine cases.
8. Freeze benchmark definitions and evaluator.
9. Run the official 12-case baseline.
10. Classify failures by cause.
11. Implement the single highest-value advanced hypothesis.
12. Re-run exactly the same benchmark and keep/revert based on evidence.
