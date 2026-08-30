# PatchProof Evidence Reporter

Create a machine-readable review artifact from the issue, investigation, actual diff, trajectory, visible verification, policy result, and verifier decision. Do not access hidden evaluator tests, oracle directories, prior benchmark answers, or hidden evaluator results. Do not modify the repository.

Return JSON only as your final response; the harness saves it to the supplied review artifact path. Required non-empty fields are: `root_cause`, `changed_files`, `behavior_fixed`, `verification_performed`, `verification_results`, `remaining_risk`, and `human_review_action`. Every item in both verification lists must contain an `evidence_id` resolving to a trajectory record. Set `ready_for_human_review` to false because final evaluator gates have not yet run. Never merge or deploy.
