# Improvement changelog

## Final-v2 verifier-validation shakedown

Stage: Final-v2 verifier-validation shakedown

What we tried:
The PP-10 workflow completed Investigator, Repair Agent, and Independent Verifier. The verifier passed with concrete verification evidence but returned an empty findings list.

Evidence:
`PP-10-patchproof-final-fdf23080` produced a passing verifier artifact with evidence IDs `visible-tests-attempt-1` and `contract-check-attempt-1`. The harness then failed because `VerificationDecision.validate()` incorrectly required non-empty findings for every decision. No hidden evaluator ran.

Decision / learning:
Changed verifier validation so passing decisions require concrete evidence, not artificial findings. Added a fail-closed recovery path that can continue an interrupted run from an already-observed verifier artifact without rerunning investigation, repair, or verification. PP-10 has not been evaluated yet.

## Final-v1 integration shakedown

Stage: Final-v1 integration shakedown

What we tried:
Four manually launched Codex stages with `FinalWorkflow` logic present but not wired into the execution path.

Evidence:
`PP-01-patchproof-final-e0d1d0a5` completed the agent roles, but `trajectory.jsonl` was absent and metadata remained `status=prepared`. The frozen evaluator correctly refused hidden evaluation. No hidden evaluator was run.

Decision / learning:
Removed the split manual execution path for official final runs and replaced it with a single orchestrated runner that owns stage execution, trace persistence, bounded retries, and workflow completion. Verification that is not persisted is still verification debt. This was an observed failed integration iteration, not an official final result, and final-v1 did not establish a VRRR pass.

The official final-v2 execution path is:

```powershell
python scripts/prepare_patchproof_final.py --case PP-01
python scripts/run_patchproof_final.py --run-id <RUN_ID>
python scripts/evaluate_patchproof_final.py --run-id <RUN_ID>
```

The runner uses the ChatGPT-authenticated Codex CLI with `gpt-5.6-sol`. It does not invoke the hidden evaluator; evaluation remains a separate, explicit command after workflow completion.

## Final-v2 Windows launcher shakedown

Stage: Final-v2 Windows launcher shakedown

What we tried:
The single orchestrated runner started correctly and persisted its first trajectory record, but Windows process creation failed before the Investigator could launch.

Evidence:
`PP-01-patchproof-final-fb1b903b` remained `status=prepared`. Its trajectory contains Investigator `stage_started` but no successful Codex command execution. Python subprocess creation raised WinError 2. PowerShell resolved Codex through npm shims, including `codex.ps1` and `codex.cmd`.

Decision / learning:
Changed the runner to resolve the platform-specific Codex executable explicitly, preferring `codex.cmd` on Windows while retaining `shell=False`. Process-creation failures are now persisted as `command_result` evidence before the workflow fails closed.

This run is not an official final result.

## Final-v2 UTF-8 stdin shakedown

Stage: Final-v2 UTF-8 stdin shakedown

What we tried:
The launcher-fixed orchestrated runner successfully resolved `codex.cmd` and launched Codex, but the Investigator prompt was rejected because stdin was not encoded as valid UTF-8.

Evidence:
`PP-01-patchproof-final-b067bc38` remained `status=prepared`. Its trajectory contains Investigator `stage_started` and `command_result`. Codex exited 1 with an explicit invalid UTF-8 stdin error.

Decision / learning:
Made subprocess text encoding explicit as UTF-8 so Unicode issue text and prompts are transmitted deterministically across Windows environments. The run remains an integration failure, not an official final result.

## Final-v2 review-schema shakedown

Stage: Final-v2 review-schema shakedown

What we tried:
The launcher- and UTF-8-fixed orchestrated workflow successfully executed Investigator, Repair Agent, Independent Verifier, and Evidence Reporter for PP-01.

Evidence:
`PP-01-patchproof-final-cc3c44c2` reached review-artifact parsing, then failed closed because the model added two non-schema top-level fields: `case` and `policy_result`. Metadata remained `status=prepared` and no hidden evaluator was run.

Decision / learning:
Kept strict validation for required review-readiness evidence while separating benign model-added metadata from the canonical ReviewArtifact. Unknown fields are now auditable in the trajectory rather than crashing an otherwise valid workflow. Model-generated policy claims are never substituted for the frozen evaluator's policy gate.

This run is an integration shakedown, not an official final result.
