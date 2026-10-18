# Standard: Claude Code configuration

Canonical source for how Zairenkai repositories configure Claude Code. Repository files
under `.claude/` and `CLAUDE.md` must conform to this document.

## How Claude Code loads instructions

| Mechanism | Location | Loaded when |
|---|---|---|
| Project memory | `CLAUDE.md` at repo root | Every session started in the repo |
| Imports | `@path` lines inside `CLAUDE.md` | With the file that imports them |
| Rules | `.claude/rules/*.md` | Always, or only when matching `paths:` globs are touched |
| Skills | `.claude/skills/<name>/SKILL.md` | On `/name`, or when Claude judges the `description` relevant |
| Subagents | `.claude/agents/<name>.md` | When delegated to explicitly or by description |
| Shared settings | `.claude/settings.json` | Every session; committed |
| Personal settings | `.claude/settings.local.json` | Every session; **never committed** (gitignored) |

Verified against Claude Code 2.1.302 during the initial rollout.

## Rules for each mechanism

### CLAUDE.md
- Under 200 lines. It routes; it does not explain everything.
- Must import `@AGENTS.md` (portable rules) and `@AGENT/PROJECT_CONTEXT.md` (facts).
- Lists only commands that exist. Unknown commands are written as `Not Configured`.

### Skills
- One directory per skill, containing `SKILL.md` with YAML frontmatter `name` (matches the
  directory) and `description` (states *when* to use it).
- A skill holds the short, distinct procedure. The detailed prompt lives in
  `AGENT/prompts/` and the skill links to it rather than duplicating it.
- Standard set: `repo-audit`, `implement-feature`, `bug-fix`, `test-and-verify`,
  `security-review`, `release-readiness`.

### Rules
- Create a rule only for paths, languages, or toolchains that exist in the repository.
- Scope with `paths:` frontmatter whenever the rule is not universal.

### Subagents
- Only when a responsibility benefits from isolation (separate context, restricted tools).
- Frontmatter: `name`, `description`, `tools` (least privilege). Each must state its deliverable.

### settings.json
- Only **restrictive** shared settings belong here (e.g. `permissions.deny` for secret files
  and history-destroying git commands).
- Never commit `allow` rules for unrestricted shell, `defaultMode: bypassPermissions`,
  credentials, or machine-specific paths.

## Managed vs. seeded files

The sync script (`agent-foundation/scripts/sync_agent_foundation.py`) distinguishes:

- **Managed** files: rendered from `templates/repo/` and recorded with a SHA-256 in
  `AGENT/.foundation-manifest.json`. Change them centrally, then re-sync. Local edits are
  reported as drift by the validator.
- **Seeded** files (`CLAUDE.md`, `AGENT/PROJECT_CONTEXT.md`, `AGENT/ARCHITECTURE.md`,
  `.gitignore`): written only when absent. After that, the repository owns them.
