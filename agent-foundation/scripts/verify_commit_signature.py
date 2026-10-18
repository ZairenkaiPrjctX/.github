#!/usr/bin/env python3
"""Check the SSH signature on a git commit, using only the Python standard library.

Verifies the ed25519 SSHSIG against the public key embedded in the signature and prints
the key's SHA256 fingerprint. Compare that fingerprint with the signing key registered on
GitHub (or in your allowed-signers file): a valid signature only proves the commit was
signed by *that* key, not who owns it.

Usage: verify_commit_signature.py REPO [REV] [--allowed-signers FILE]
       (exit 0 = valid, 1 = invalid/unsigned/untrusted)

With --allowed-signers, the signing key must also be listed in FILE (OpenSSH allowed-signers
format, e.g. agent-foundation/allowed_signers) for the committer's email.
"""
import argparse
import base64
import hashlib
import re
import struct
import subprocess
import sys
from pathlib import Path

# Ed25519 verification (RFC 8032, section 5.1.7), pure Python.
P = 2 ** 255 - 19
L = 2 ** 252 + 27742317777372353535851937790883648493
D = -121665 * pow(121666, P - 2, P) % P
I = pow(2, (P - 1) // 4, P)


def _xrecover(y):
    xx = (y * y - 1) * pow(D * y * y + 1, P - 2, P)
    x = pow(xx, (P + 3) // 8, P)
    if (x * x - xx) % P:
        x = x * I % P
    return P - x if x % 2 else x


def _add(a, b):
    (x1, y1), (x2, y2) = a, b
    t = D * x1 * x2 * y1 * y2
    return ((x1 * y2 + x2 * y1) * pow(1 + t, P - 2, P) % P,
            (y1 * y2 + x1 * x2) * pow(1 - t, P - 2, P) % P)


def _mul(pt, e):
    q = (0, 1)
    while e:
        if e & 1:
            q = _add(q, pt)
        pt, e = _add(pt, pt), e >> 1
    return q


def _decode(s):
    y = int.from_bytes(s, "little") & ((1 << 255) - 1)
    x = _xrecover(y)
    if (x & 1) != (s[31] >> 7):
        x = P - x
    if (-x * x + y * y - 1 - D * x * x * y * y) % P:
        raise ValueError("point not on curve")
    return x, y


B = (_xrecover(4 * pow(5, P - 2, P) % P), 4 * pow(5, P - 2, P) % P)


def ed25519_verify(pub, sig, msg):
    if len(sig) != 64 or len(pub) != 32:
        return False
    try:
        a, r = _decode(pub), _decode(sig[:32])
    except ValueError:
        return False
    s = int.from_bytes(sig[32:], "little")
    if s >= L:
        return False
    h = int.from_bytes(hashlib.sha512(sig[:32] + pub + msg).digest(), "little")
    return _mul(B, s) == _add(r, _mul(a, h))


def _read(b, i):
    n = struct.unpack(">I", b[i:i + 4])[0]
    return b[i + 4:i + 4 + n], i + 4 + n


def split_commit(raw):
    payload, sig, in_sig = [], [], False
    for line in raw.split("\n"):
        if line.startswith("gpgsig "):
            in_sig = True
            sig.append(line[7:])
        elif in_sig and line.startswith(" "):
            sig.append(line[1:])
        else:
            in_sig = False
            payload.append(line)
    return "\n".join(payload).encode(), sig


def verify(raw):
    """Return (ok, message[, key_b64]) for a raw commit object."""
    payload, sig = split_commit(raw)
    if not sig:
        return False, "UNSIGNED: commit has no gpgsig header"
    if "SSH SIGNATURE" not in sig[0]:
        return False, "NOT SSH: use `git verify-commit` with GPG for this signature"
    blob = base64.b64decode("".join(l for l in sig if not l.startswith("-----")))
    if blob[:6] != b"SSHSIG":
        return False, "INVALID: malformed SSHSIG"
    i = 10
    pub, i = _read(blob, i)
    namespace, i = _read(blob, i)
    _, i = _read(blob, i)
    hash_alg, i = _read(blob, i)
    sigblob, _ = _read(blob, i)
    ktype, j = _read(pub, 0)
    if ktype != b"ssh-ed25519":
        return False, f"UNSUPPORTED key type {ktype.decode()}; use ssh-keygen -Y verify"
    key, _ = _read(pub, j)
    _, j = _read(sigblob, 0)
    raw_sig, _ = _read(sigblob, j)
    digest = hashlib.new(hash_alg.decode(), payload).digest()
    signed = b"SSHSIG" + b"".join(struct.pack(">I", len(x)) + x for x in (namespace, b"", hash_alg, digest))
    fp = base64.b64encode(hashlib.sha256(pub).digest()).decode().rstrip("=")
    if namespace != b"git" or not ed25519_verify(key, raw_sig, signed):
        return False, f"INVALID signature (key SHA256:{fp})"
    return True, f"VALID ssh-ed25519 signature, key SHA256:{fp}", base64.b64encode(pub).decode()


def committer_email(raw):
    for line in raw.split("\n"):
        if line.startswith("committer "):
            return line[line.index("<") + 1:line.index(">")]
        if not line:
            break
    return ""


def allowed_keys(path, email):
    """Return the base64 ed25519 keys FILE allows for EMAIL with the git namespace."""
    keys = set()
    for line in Path(path).read_text().splitlines():
        parts = line.split()
        if not parts or parts[0].startswith("#"):
            continue
        principals = parts[0].split(",")
        opts = parts[1] if len(parts) > 3 else ""
        m = re.search(r'namespaces="([^"]*)"', opts)
        if m and "git" not in m.group(1).split(","):
            continue
        if email in principals or "*" in principals:
            keys.add(parts[-1])
    return keys


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("repo")
    ap.add_argument("rev", nargs="?", default="HEAD")
    ap.add_argument("--allowed-signers", type=Path)
    args = ap.parse_args(argv)
    raw = subprocess.check_output(["git", "-C", args.repo, "cat-file", "commit", args.rev]).decode()
    ok, msg, *key = verify(raw)
    if ok and args.allowed_signers:
        email = committer_email(raw)
        if key[0] not in allowed_keys(args.allowed_signers, email):
            ok, msg = False, f"UNTRUSTED: {msg}, but not listed for <{email}> in {args.allowed_signers}"
        else:
            msg += f", trusted for <{email}>"
    print(f"{args.rev}: {msg}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
