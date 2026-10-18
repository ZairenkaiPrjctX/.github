#!/usr/bin/env python3
"""Render the Zairenkai agent foundation into repository checkouts.

Managed files (everything under templates/repo except the seeded set) are overwritten and
recorded with their SHA-256 in AGENT/.foundation-manifest.json. Seeded files are written only
when absent; after that the repository owns them.

Usage:
  sync_agent_foundation.py --root DIR [--only NAME ...] [--check]

DIR holds one checkout per repository, named exactly as in the inventory.
--check writes nothing and exits 1 if any repository is out of date.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

FOUNDATION = Path(__file__).resolve().parent.parent
TEMPLATES = FOUNDATION / "templates" / "repo"
OPTIONAL = FOUNDATION / "templates" / "optional"
INVENTORY = FOUNDATION / "inventory" / "repositories.json"
MANIFEST = "AGENT/.foundation-manifest.json"
SEEDED = {"CLAUDE.md", "AGENT/PROJECT_CONTEXT.md", "AGENT/ARCHITECTURE.md", ".gitignore"}
PLACEHOLDER = re.compile(r"\{\{([a-z_]+)\}\}")


def sha256(text):
    return hashlib.sha256(text.encode()).hexdigest()


def bullets(items, empty):
    return "\n".join(f"- {i}" for i in items) if items else empty


def variables(repo, version, surveyed):
    playbooks = ["- [Feature delivery](playbooks/feature-delivery.md)",
                 "- [Debugging](playbooks/debugging.md)"]
    if "AGENT/playbooks/release-process.md" in repo["optional_templates"]:
        playbooks.append("- [Release process](playbooks/release-process.md)")
    return {
        "repo": repo["name"],
        "description": repo["github_description"] or "(none set)",
        "role_hint": repo["role_hint_unverified"],
        "evidence": repo["evidence"],
        "surveyed": surveyed,
        "related": bullets(repo["related_repositories"],
                           "None verified. Record relationships here, with evidence, once code shows them."),
        "questions": bullets(repo["open_questions"], "None recorded."),
        "playbook_list": "\n".join(playbooks),
        "foundation_version": version,
        "managed_notice": f"<!-- Managed by ZairenkaiPrjctX/.github agent-foundation v{version}. "
                          "Edit the central template, then re-sync. -->",
    }


def render(text, values, source):
    def sub(m):
        if m.group(1) not in values:
            raise KeyError(f"{source}: unknown placeholder {m.group(0)}")
        return values[m.group(1)]
    return PLACEHOLDER.sub(sub, text)


def plan(repo, version, surveyed):
    """Return {relative path: rendered text} for one repository."""
    values = variables(repo, version, surveyed)
    sources = {p.relative_to(TEMPLATES).as_posix(): p for p in TEMPLATES.rglob("*") if p.is_file()}
    for rel in repo["optional_templates"]:
        sources[rel] = OPTIONAL / rel
    return {rel: render(src.read_text(), values, rel) for rel, src in sorted(sources.items())}


def sync_repo(path, repo, version, surveyed, check):
    files = plan(repo, version, surveyed)
    changed = []
    managed = {}
    for rel, text in files.items():
        dest = path / rel
        if rel in SEEDED:
            if dest.exists():
                continue
        else:
            managed[rel] = sha256(text)
            if dest.exists() and dest.read_text() == text:
                continue
        changed.append(rel)
        if not check:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(text)
    manifest = json.dumps({
        "foundation_version": version,
        "source": "ZairenkaiPrjctX/.github:agent-foundation/templates/repo",
        "managed": managed,
        "seeded": sorted(SEEDED & files.keys()),
    }, indent=2) + "\n"
    mpath = path / MANIFEST
    if not mpath.exists() or mpath.read_text() != manifest:
        changed.append(MANIFEST)
        if not check:
            mpath.parent.mkdir(parents=True, exist_ok=True)
            mpath.write_text(manifest)
    return changed


def render_inventory_md(inv):
    rows = ["| Repository | GitHub description | Code present | Foundation status | Role (unverified hint) |",
            "|---|---|---|---|---|"]
    for r in inv["repositories"]:
        rows.append(f"| `{r['name']}` | {r['github_description'] or '(none)'} | "
                    f"{'yes' if r['code_present'] else 'no'} | {r['foundation_status']} | "
                    f"{r['role_hint_unverified']} |")
    return ("# Repository inventory\n\n"
            "<!-- Generated from repositories.json by scripts/sync_agent_foundation.py. Do not edit. -->\n\n"
            f"Organization: `{inv['organization']}`. Foundation version: {inv['foundation_version']}. "
            f"Surveyed: {inv['surveyed']}.\n\n" + "\n".join(rows) + "\n\n"
            "Evidence for every row: " + inv["repositories"][0]["evidence"] + "\n\n"
            "\"Role\" is a rollout hint, not a verified fact. Replace it with the verified purpose "
            "from the repository's `AGENT/PROJECT_CONTEXT.md` once code exists.\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", required=True, type=Path, help="directory containing repository checkouts")
    ap.add_argument("--inventory", type=Path, default=INVENTORY)
    ap.add_argument("--only", nargs="*", help="limit to these repository names")
    ap.add_argument("--check", action="store_true", help="report out-of-date files; write nothing")
    args = ap.parse_args(argv)

    inv = json.loads(args.inventory.read_text())
    stale = False
    for repo in inv["repositories"]:
        if args.only and repo["name"] not in args.only:
            continue
        path = args.root / repo["name"]
        if not path.is_dir():
            print(f"SKIP  {repo['name']}: no checkout at {path}")
            continue
        changed = sync_repo(path, repo, inv["foundation_version"], inv["surveyed"], args.check)
        stale |= bool(changed)
        verb = "STALE" if args.check else "WROTE"
        print(f"{verb if changed else 'OK   '} {repo['name']}: {len(changed)} file(s)")
        for rel in changed:
            print(f"        {rel}")

    md_path = args.inventory.parent / "repositories.md"
    md = render_inventory_md(inv)
    if not md_path.exists() or md_path.read_text() != md:
        stale = True
        if not args.check:
            md_path.write_text(md)
        print(f"{'STALE' if args.check else 'WROTE'} {md_path.name}")
    return 1 if (args.check and stale) else 0


if __name__ == "__main__":
    sys.exit(main())
