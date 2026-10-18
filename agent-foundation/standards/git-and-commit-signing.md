# Standard: Git workflow and commit signing

## Branches and pull requests
- Never commit directly to the default branch. Work on a topic branch and open a pull request.
- Agents may open **draft** pull requests. Agents never merge, approve, or enable auto-merge.
- Never rewrite published history (`rebase`, `--amend`, `push --force`) on a branch other people
  use. Prefer merge commits when bringing in the base branch.
- Do not change default branches, repository visibility, or ownership.

## Commit messages
Imperative subject line, at most 72 characters, then a body explaining *why*. Agent-created
commits end with these trailers:

```
Signed-By: <GitHub username of the human who directed the work, as resolved from the authenticated account>
Co-Authored-By: <model name actually used, if known> <noreply@anthropic.com>
Claude-Session: <URL of the current session, if one exists>
```

- Resolve the username from the authenticated GitHub account; do not assume the organization
  name is a user name.
- Name the model only if the runtime states it. Do not copy a model name from an old commit.
- Omit `Claude-Session` when no current session URL exists. Never reuse a stale one.

## `Signed-By` is not a signature
`Signed-By:` is plain text. Anyone can type it. It does **not** make a commit cryptographically
signed and does **not** produce GitHub's "Verified" badge.

## Cryptographic signing (required)
- Commits must be signed with SSH or GPG (`commit.gpgsign=true`, `gpg.format`, `user.signingkey`).
- Before committing, confirm signing works by making a commit and checking it carries a signature
  (`git cat-file commit HEAD` shows a `gpgsig` header), or with `git verify-commit` when an
  allowed-signers file or GPG keyring is available.
- If signing fails, **stop and report the error**. Do not pass `--no-gpg-sign`, do not set
  `commit.gpgsign=false`, and never describe an unsigned commit as signed.
- Never generate signing keys or tokens as part of repository work, and never commit them.

## Verifying a signature independently
1. Locally: `git log --show-signature -1` (needs `gpg.ssh.allowedSignersFile` for SSH keys),
   or run `agent-foundation/scripts/verify_commit_signature.py <repo> <rev>`, which checks the
   SSH signature against the public key embedded in it and prints the key fingerprint.
2. On GitHub: open the commit; "Verified" appears only if the signing key is registered to a
   GitHub account whose verified email matches the committer email. Compare the fingerprint from
   step 1 with the key listed in that account's settings.
