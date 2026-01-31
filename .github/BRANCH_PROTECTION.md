# Branch protection (manual setup)

Require the **Workflow Verify** status check to pass before merging into `main`. Configure in GitHub (not stored in the repo).

## Steps

1. Open the repo on GitHub.
2. Go to **Settings → Branches** (or **Rules → Branch protection rules**).
3. Under **Branch protection rules**, edit the existing rule for `main` or add a rule with **Branch name pattern** `main`.
4. Enable **Require status checks to pass before merging**.
5. In **Status checks that are required**, search for and select **Workflow Verify** (from [workflows/ci.yml](workflows/ci.yml)).  
   The check appears after the workflow has run at least once (e.g. push to main or open a PR).
6. Save the rule.

**Result:** PRs targeting `main` cannot be merged until the Workflow Verify job (and any other required checks) has succeeded.

**Optional:** Enable **Require branches to be up to date before merging** so the latest push must pass CI.
