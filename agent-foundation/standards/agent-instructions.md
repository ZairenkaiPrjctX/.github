# Standard: Agent instructions

Applies to `AGENTS.md`, `AGENT/`, prompts, skills and subagents in every Zairenkai repository.

## Layering (no duplicated authority)

1. **Organization standards**: `ZairenkaiPrjctX/.github/agent-foundation/standards/` (this directory).
2. **Repository policies**: `AGENT/policies/`, operational checklists that point back to a standard.
3. **Repository facts**: `AGENT/PROJECT_CONTEXT.md` and `AGENT/ARCHITECTURE.md`, owned by the repository.
4. **Task procedures**: `AGENT/prompts/` (detailed) and `.claude/skills/` (short entry points).

When two layers disagree, the higher layer wins and the conflict is a bug to fix.

## Evidence rule

Every technical statement in repository facts must be one of:

- **Verified**: followed by `Evidence:` and a file path, manifest, workflow, or command output.
- **Unverified**: stated as an assumption or hint, explicitly labelled.
- **Unknown / Not Configured**: nothing exists yet.

Never state that a build, test, deployment, or signature succeeded without the output that shows it.

## Writing prompts

A prompt in `AGENT/prompts/` contains, in this order: role and objective; inputs (parameters
in `<angle-brackets>`); context to read; scope and constraints; discovery and planning;
procedure; validation; security; deliverables; completion report. Use
`agent-foundation/templates/task-prompt.md` as the starting point.

Prompts must require inspecting real code before editing, preserving unrelated changes, and
proving completion claims. They must not request total rewrites by default.

## Cross-repository boundaries

A fact about another repository is recorded in that repository's `PROJECT_CONTEXT.md` and
only *referenced* elsewhere. The inventory (`inventory/repositories.json`) is the single list
of repositories and their declared relationships.
