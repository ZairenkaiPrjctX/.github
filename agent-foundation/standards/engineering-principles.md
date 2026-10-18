# Standard: Engineering principles

1. **Smallest correct change.** Solve the stated problem; do not refactor surrounding code
   unless the task requires it.
2. **Read before writing.** Inspect the code, tests and callers you are about to change.
3. **Match the codebase.** Follow existing naming, structure, error handling and comment density.
4. **Preserve behaviour.** Changes to public interfaces, file formats, or on-device behaviour need
   explicit approval and a migration note.
5. **No speculative architecture.** Do not add layers, abstractions, or dependencies for
   hypothetical future needs.
6. **Dependencies are a cost.** Prefer the standard library and existing dependencies. A new
   dependency needs a reason, a pinned version, and a licence check.
7. **Generated files are outputs.** Edit the generator or source, then regenerate. Never
   hand-edit generated artifacts.
8. **Leave evidence.** A change is finished when it is tested (or the reason it cannot be is
   stated) and documented where behaviour changed.
9. **Destructive operations require a human.** Deleting data, rewriting history, force-pushing,
   publishing releases, flashing devices, or deploying need explicit, per-instance approval.
