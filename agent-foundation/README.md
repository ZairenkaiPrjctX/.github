# Zairenkai agent foundation

Organization-level source of truth for how Claude Code and other coding agents work across
the 15 `ZairenkaiPrjctX` repositories.

| Path | Purpose |
|---|---|
| `standards/` | Canonical org-wide rules: [Claude Code](standards/claude-code.md), [agent instructions](standards/agent-instructions.md), [engineering](standards/engineering-principles.md), [security](standards/security-and-secrets.md), [testing](standards/testing-and-verification.md), [git and signing](standards/git-and-commit-signing.md) |
| `templates/repo/` | The tree rendered into every repository (`CLAUDE.md`, `AGENTS.md`, `AGENT/`, `.claude/`) |
| `templates/optional/` | Files rendered only into repositories that list them in the inventory |
| `templates/SKILL.md`, `templates/task-prompt.md` | Starting points for authoring a new skill or prompt |
| `inventory/repositories.json` | Machine-readable repository list, evidence, and status ([rendered table](inventory/repositories.md)) |
| `rollout/` | [Implementation plan](rollout/implementation-plan.md) and [rollout report](rollout/rollout-report.md) |
| `allowed_signers` | Trusted public signing keys for `git verify-commit` |
| `scripts/` | `sync_agent_foundation.py`, `validate_agent_setup.py`, `verify_commit_signature.py`, tests |

All scripts use only the Python 3 standard library.

## Managed vs. seeded files
- **Managed:** rendered from `templates/repo/`, hashed in each repo's
  `AGENT/.foundation-manifest.json`. Change centrally; local edits show as drift.
- **Seeded:** `CLAUDE.md`, `AGENT/PROJECT_CONTEXT.md`, `AGENT/ARCHITECTURE.md`, `.gitignore`.
  Written once; the repository owns them afterwards.

## Changing a standard or template
1. Edit `standards/` and/or `templates/repo/`. Keep repository policies consistent with standards.
2. Bump `foundation_version` in `inventory/repositories.json` for any managed-file change.
3. Check out the repositories side by side in one directory, then:
   ```
   python3 agent-foundation/scripts/sync_agent_foundation.py --root <dir>
   python3 agent-foundation/scripts/validate_agent_setup.py --inventory agent-foundation/inventory/repositories.json --root <dir>
   python3 -m unittest discover -s agent-foundation/scripts/tests
   ```
4. Commit the regenerated files in each repository (signed), on a topic branch, via draft PRs.

`sync_agent_foundation.py --check` writes nothing and exits 1 if any repository is out of date.

## Validating one repository
```
python3 <path-to-.github>/agent-foundation/scripts/validate_agent_setup.py <repo-path>
```
Exit code 1 means errors. Warnings (e.g. drift) do not fail unless `--strict` is given.

## Verifying a commit signature
```
git -c gpg.ssh.allowedSignersFile=agent-foundation/allowed_signers verify-commit <rev>
python3 agent-foundation/scripts/verify_commit_signature.py <repo> <rev> --allowed-signers agent-foundation/allowed_signers
```
The script needs no `ssh-keygen` and prints the signing key fingerprint. GitHub's "Verified" badge is confirmed only on GitHub.
