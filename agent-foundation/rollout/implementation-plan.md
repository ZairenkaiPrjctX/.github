# Implementation plan: agent foundation v1.0.0

1. **Preflight** (done 2026-10-18): verify access to all 15 repositories, branches, git status,
   signing configuration. Result: all accessible with admin rights; all empty.
2. **Central foundation** (done): standards, templates, inventory, sync, validator, signature
   verifier, tests in `ZairenkaiPrjctX/.github/agent-foundation/`.
3. **Per-repository initialization** (done): sync into all 15 checkouts; validate.
4. **Commit and push** (done): one signed commit per repository on branch
   `ccr-63f8aa87-1b0paj`.
5. **Next, owned by the maintainers:**
   - Decide each repository's default branch (see the rollout report: pushing to an empty
     repository makes the pushed branch the default).
   - As real code lands in a repository, run `/repo-audit` there, set `code_present: true`
     in the inventory, and fill in the commands in `CLAUDE.md`.
   - Add path-scoped rules and subagents only once a repository has the languages and
     toolchains to justify them.
