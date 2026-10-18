---
paths:
  - "agent-foundation/**"
---
<!-- Managed by ZairenkaiPrjctX/.github agent-foundation v1.1.0. Edit the central template, then re-sync. -->
# Rule: editing the central agent foundation

- `agent-foundation/standards/` is canonical. Repository policies and templates restate it
  briefly and link back; never let them contradict it.
- After changing `templates/repo/` or `inventory/repositories.json`, re-run
  `scripts/sync_agent_foundation.py` against all repositories, then the validator, and
  commit the regenerated files in each repository.
- Scripts stay standard-library Python with no machine-specific paths. Run
  `python3 -m unittest discover -s agent-foundation/scripts/tests` after changing them.
- The inventory records evidence. Do not mark a repository `code_present: true` or a status
  as validated without the evidence and validator output.
