# Standard: Testing and verification

## Required evidence
A completion claim needs one of the following:
- The exact command run and its relevant output (pass/fail counts, exit code).
- For a change that cannot be tested automatically: what was checked manually, and how.
- For a change that was not verified: the statement "Not verified" and the reason.

## Rules
- Run the repository's own checks (as listed in `CLAUDE.md`). If none exist, say so;
  do not invent a command.
- Reproduce a bug before fixing it whenever possible, and show the reproduction passing after.
- Never disable, skip, or weaken a test, linter, or security check to get a green result.
- Distinguish **configured** (a check exists), **executed** (it ran in this task) and
  **passing** (it ran and passed). Report each separately.
- Hardware-, device-, or root-dependent behaviour that was not exercised on a real device
  must be reported as unverified on hardware.

## Foundation validation
After changing any agent foundation file, run:

```
python3 <path-to-.github>/agent-foundation/scripts/validate_agent_setup.py <repo-path>
```

Errors must be fixed. Warnings must be fixed or explained in the pull request.
