# Rollout report: agent foundation v1.0.0 (2026-10-18)

## Summary

| Metric | Count |
|---|---|
| Target repositories discovered | 15 |
| Accessible (admin, via authenticated account `FebriCahyaa`) | 15 |
| Initialized | 15 |
| Validator: no errors, no warnings | 15 |
| Blocked | 0 |

## Key finding: every repository was empty
GitHub API and `git ls-remote` showed size 0, no branches, and no commits for all 15
repositories. There was no source code, CI, manifest, or existing agent configuration to
inspect or preserve. As a result:

- Every `PROJECT_CONTEXT.md` / `ARCHITECTURE.md` records the purpose as **Unverified**
  (taken from the GitHub description or a rollout hint) and the architecture as **Unknown**.
- No language-specific rules or subagents were created in project repositories: there is
  nothing for them to apply to. Only the `agent-docs` rule (scoped to the foundation files
  themselves) exists everywhere; `.github` also has `agent-foundation` and `foundation-auditor`.
- `release-process.md` is only in `Zairenkai-Release`, and it states it is **Not Configured**.

## Per-repository contents
Each repository received `CLAUDE.md`, `AGENTS.md`, `.gitignore`, `AGENT/` (README, context,
architecture, 10 prompts + index, 5 policies, 2 playbooks, 4 templates, manifest), and
`.claude/` (restrictive `settings.json`, `rules/agent-docs.md`, 6 skills). See
[inventory](../inventory/repositories.md) for per-repository descriptions and open questions.

## Verification evidence
```
$ python3 agent-foundation/scripts/validate_agent_setup.py --inventory agent-foundation/inventory/repositories.json --root <checkouts>
15/15 repositories without errors     (0 warnings)
$ python3 -m unittest discover -s agent-foundation/scripts/tests
Ran 8 tests ... OK
$ python3 agent-foundation/scripts/sync_agent_foundation.py --root <checkouts> --check
(all OK, exit 0)
```
The validator's first run failed on all 15 repositories because of two false-positive rules
in the validator itself (case-insensitive "verified" matching, and scanning the intentional
placeholders in `templates/`). Both rules were fixed and the run was repeated; the tests
cover the corrected behaviour.

Not verified: Claude Code loading behaviour in a live session for each repository (schema
followed: Claude Code 2.1.302 frontmatter conventions); GitHub "Verified" badge (only
observable after push).

## Git and signing
- Signing: `commit.gpgsign=true`, `gpg.format=ssh`. A test commit carried a valid ssh-ed25519
  SSHSIG (key `SHA256:32dP45eSMmVSt/G/CGvcxl/P+MO3Nwj9xeTh/GSA2wc`), checked with
  `scripts/verify_commit_signature.py`. The local `.pub` file is empty (the environment signs
  remotely), so `git verify-commit` could not be used.
- Commit identity is the environment's configured `Claude <noreply@anthropic.com>`; it was not
  changed. `Signed-By: FebriCahyaa` is a text trailer only.
- Branch: `ccr-63f8aa87-1b0paj` in every repository.

## Remaining issues and owners
| Issue | Owner / next action |
|---|---|
| Repositories had no commits, so the first pushed branch becomes GitHub's default branch. The configured default was `main`. | Maintainer: create `main` from this branch (or rename it) and set it as default, then open PRs normally. |
| No draft PRs: an empty repository has no base branch to target. | Maintainer: after `main` exists, open PRs for future changes. |
| `.github` is private, so organization-wide community health files and profile README in it do not take effect. | Maintainer: decide whether to make it public. |
| Every project profile is Unverified. | Each repository: run `/repo-audit` when code lands, then set `code_present: true`. |
| GitHub "Verified" status not yet observed. | Check commits on GitHub; compare key fingerprint above. |

## Update v1.1.0 (2026-10-18)
- After push, GitHub reported all 15 initial commits as `verified: true, reason: valid`
  (checked via the commits API). The "Verified status not yet observed" item is closed.
- Added `agent-foundation/allowed_signers` with the Claude Code cloud signing key, and
  `--allowed-signers` support in `verify_commit_signature.py`. Tested:
  `git verify-commit` → `Good "git" signature for noreply@anthropic.com`; a file listing the key
  for a different principal → exit 1 (untrusted).
- At the account owner's request, every commit now ends with
  `Signed-off-by: FebriCahyaa <febricahya12345@gmail.com>` (replacing `Signed-By:`). The v1.0.0
  commits keep their original trailer; published history was not rewritten.
- Not done, by design: no new SSH/GPG keys were generated and nothing was added to the GitHub
  account. This session can't reach account settings, and keys generated in an ephemeral
  container would be lost.
