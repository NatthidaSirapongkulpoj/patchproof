# Improvement changelog

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
