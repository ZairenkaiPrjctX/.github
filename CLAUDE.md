# CLAUDE.md: .github

Instructions for Claude Code in `ZairenkaiPrjctX/.github`. Keep this file under 200 lines;
put detail in `AGENT/`.

@AGENTS.md
@AGENT/PROJECT_CONTEXT.md

## Current state (read first)

As of 2026-10-18 this repository contained **no source code** other than the agent foundation in `agent-foundation/` (GitHub API 2026-10-18: repository size 0, no branches, no commits; ls-remote returned no refs.).
Until that changes:

- Do not describe an architecture, language, or toolchain as fact. Record discoveries in
  `AGENT/PROJECT_CONTEXT.md` with evidence (file paths, manifests, command output).
- When the first real code lands, update this file's **Commands** table and
  `AGENT/ARCHITECTURE.md` in the same pull request.

## Commands

| Purpose | Command | Status |
|---|---|---|
| Build | — | Not Configured |
| Test (foundation scripts) | `python3 -m unittest discover -s agent-foundation/scripts/tests` | Verified. Evidence: 8 tests OK, 2026-10-18 |
| Lint / format | — | Not Configured |
| Validate agent foundation | `python3 <path-to-.github>/agent-foundation/scripts/validate_agent_setup.py .` | Configured |
| Sync foundation into checkouts | `python3 agent-foundation/scripts/sync_agent_foundation.py --root <dir>` | Configured |

Only list commands that exist in this repository. Never invent one.

## Working rules

- Inspect the relevant code before editing it. Preserve unrelated and uncommitted changes.
- Generated files are edited at their source, then regenerated. Managed foundation files
  (listed in `AGENT/.foundation-manifest.json`) are edited in `ZairenkaiPrjctX/.github`, not here.
- Destructive or outward-facing actions (deleting data, force-push, history rewrites,
  publishing releases, deploying, flashing devices) need explicit human approval each time.
- Do not claim a build, test, or signature succeeded without showing the output.

## Git

- Work on a topic branch; open **draft** pull requests; never merge or approve.
- Commits must be cryptographically signed. If signing fails, stop and report the error.
  Trailer format and verification: `AGENT/policies/git-and-commit-signing.md`.

## Where things are

- `AGENT/README.md`: index of the agent library (prompts, policies, playbooks, templates).
- `.claude/skills/`: run `/repo-audit`, `/implement-feature`, `/bug-fix`, `/test-and-verify`,
  `/security-review`, `/release-readiness`.
- `.claude/rules/`: path-scoped rules, loaded automatically.
