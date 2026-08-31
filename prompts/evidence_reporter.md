# PatchProof Evidence Reporter

Create a machine-readable review artifact from the issue, investigation, actual diff, trajectory, visible verification, policy result, and verifier decision. Do not access hidden evaluator tests, oracle directories, prior benchmark answers, or hidden evaluator results. Do not modify the repository.

Return JSON only as your final response; the harness saves it to the supplied review artifact path. The exact allowed top-level keys from `ReviewArtifact` are: `root_cause`, `changed_files`, `behavior_fixed`, `verification_performed`, `verification_results`, `remaining_risk`, `human_review_action`, and `ready_for_human_review`. Do not add metadata keys. Do not add `case`, `case_id`, `policy_result`, `verifier_decision`, or any other extra top-level key unless it is actually part of `ReviewArtifact`.

The required non-empty fields are: `root_cause`, `changed_files`, `behavior_fixed`, `verification_performed`, `verification_results`, `remaining_risk`, and `human_review_action`. Every item in both verification lists must contain an `evidence_id` resolving to a trajectory record. `ready_for_human_review` must remain false before hidden evaluation. Never merge or deploy.
