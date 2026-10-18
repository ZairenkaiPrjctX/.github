# Standard: Security and secrets

## Never commit or print
- Private keys (`*.pem`, `*.key`, `id_*`, `*.p12`, `*.jks`, `*.keystore`), signing keys,
  API tokens, passwords, license-signing material, `.env` files and their values.
- Contents of environment variables that hold credentials.

Agents may refer to a secret by **name** (e.g. "the `RELEASE_SIGNING_KEY` repository secret"),
never by value.

## Enforcement
- `.claude/settings.json` denies agent reads of common secret file patterns. This is a
  safeguard, not a substitute for keeping secrets out of the repository.
- `.gitignore` excludes `.env*`, key material and `.claude/settings.local.json`.
- If a secret is found committed: stop, do not copy it anywhere, report the path to a
  maintainer, and treat it as compromised (rotate, then purge history with maintainer approval).

## Trust boundaries to review in every change
- Input crossing a process, network, device, or privilege boundary.
- Code that runs as root or in kernel space (modules, tweaks, init scripts). A mistake here
  can brick devices, so such changes need a human reviewer and a rollback path.
- Licensing and authentication logic: no hardcoded keys, no client-side-only trust checks.
- CI workflows: pin third-party actions to a commit SHA, use least-privilege `permissions:`,
  never echo secrets, treat `pull_request_target` as dangerous.

## Reporting
Security findings go to repository maintainers privately, not in public issues.
