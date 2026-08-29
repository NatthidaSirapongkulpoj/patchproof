# Submission draft

## Title
PatchProof: Verification-First Agentic Repair for Python APIs

## Description
PatchProof is an agentic repair workflow for backend engineers maintaining Python API services.

The bottleneck is not producing a plausible code edit. Engineers still need to find the relevant context in an unfamiliar repository, preserve API contracts, run the right tests, catch regressions, retry from concrete failures, and leave evidence another reviewer can trust.

PatchProof turns a bug report plus a FastAPI/Flask repository into a minimal patch and reviewer-ready verification report. We compare it against a fair single-agent baseline on the same 12 reproducible repair cases.

Our primary metric is **Verified Task Success Rate (VTSR)**: a case counts as successful only when the requested behavior passes, the regression suite still passes, repository health checks pass, patch-policy constraints are respected, and evaluation finishes within the case timeout.

Final submission will report:
- baseline VTSR: [MEASURED VALUE]
- PatchProof VTSR: [MEASURED VALUE]
- change: [MEASURED VALUE]
- runtime/cost trade-off: [MEASURED VALUE]

The improvement changelog records every meaningful experiment, including changes we removed. Representative agent trajectories show instructions, tool calls, test feedback, retries, and human checkpoints. The repository includes exact clean-environment commands for the baseline, final workflow, and evaluator.

Main remaining failure mode: [FILL AFTER FINAL EVALUATION]

Hot take: [DERIVE FROM OBSERVED FAILURE; DO NOT INVENT IN ADVANCE]
