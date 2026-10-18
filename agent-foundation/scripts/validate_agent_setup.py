#!/usr/bin/env python3
"""Validate the Zairenkai agent foundation in one or more repositories.

Usage:
  validate_agent_setup.py REPO_PATH [REPO_PATH ...]
  validate_agent_setup.py --inventory inventory/repositories.json --root DIR

Errors make the exit code 1. Warnings do not, unless --strict is given.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

REQUIRED = [
    "CLAUDE.md", "AGENTS.md", "AGENT/README.md", "AGENT/PROJECT_CONTEXT.md", "AGENT/ARCHITECTURE.md",
    "AGENT/.foundation-manifest.json", ".claude/settings.json",
    *[f"AGENT/prompts/{p}.md" for p in (
        "README", "audit-repository", "implement-feature", "bug-fix", "refactor", "test-and-verify",
        "security-review", "documentation-update", "dependency-update", "release-readiness", "commit-and-pr")],
    *[f"AGENT/policies/{p}.md" for p in (
        "engineering", "testing", "security-and-secrets", "git-and-commit-signing", "documentation")],
    "AGENT/playbooks/feature-delivery.md", "AGENT/playbooks/debugging.md",
    *[f"AGENT/templates/{t}.md" for t in ("task-brief", "implementation-plan", "verification-report", "pull-request")],
]
SKILLS = ["repo-audit", "implement-feature", "bug-fix", "test-and-verify", "security-review", "release-readiness"]
PROMPT_SECTIONS = ["Role and objective", "Inputs", "Scope and constraints", "Procedure",
                   "Validation", "Security", "Deliverables", "Completion report"]
SKILL_KEYS = {"name", "description", "argument-hint", "allowed-tools", "disable-model-invocation",
              "user-invocable", "model", "context", "agent", "hooks", "license", "compatibility", "metadata"}
FACT_FILES = ["CLAUDE.md", "AGENT/PROJECT_CONTEXT.md", "AGENT/ARCHITECTURE.md"]
# Status words are case-sensitive ("Verified" asserts a fact; "verified" in prose does not).
CLAIM = re.compile(r"\bVerified\b|(?i:\b(all tests pass|tests passed|build succeed(s|ed)|production[- ]ready)\b)")
PLACEHOLDER = re.compile(r"\{\{[a-z_]+\}\}")
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
FOUNDATION_DIRS = ("AGENT/", ".claude/", "agent-foundation/")
FOUNDATION_FILES = {"CLAUDE.md", "AGENTS.md", ".gitignore"}


class Report:
    def __init__(self, repo):
        self.repo, self.errors, self.warnings = repo, [], []

    def error(self, msg):
        self.errors.append(msg)

    def warn(self, msg):
        self.warnings.append(msg)


def frontmatter(text):
    """Parse simple YAML frontmatter (scalars and '- item' lists). Returns dict or None."""
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end < 0:
        return None
    data, key = {}, None
    for line in text[4:end].splitlines():
        if not line.strip():
            continue
        if line.lstrip().startswith("- ") and key:
            data.setdefault(key, [])
            if isinstance(data[key], list):
                data[key].append(line.strip()[2:].strip().strip('"'))
            continue
        if ":" in line and not line.startswith(" "):
            key, _, val = line.partition(":")
            key, val = key.strip(), val.strip()
            data[key] = val.strip('"') if val else []
    return data


def strip_code(text):
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    return re.sub(r"`[^`\n]*`", "", text)


def meaningful(text):
    body = [l for l in text.splitlines() if l.strip() and not l.startswith(("#", "<!--", "---"))]
    return len(body) >= 3


def check_repo(path):
    r = Report(path.name)
    for rel in REQUIRED:
        f = path / rel
        if not f.is_file():
            r.error(f"missing required file {rel}")
        elif rel.endswith(".md") and not meaningful(f.read_text()):
            r.error(f"{rel} has no meaningful content")

    for name in SKILLS:
        f = path / ".claude/skills" / name / "SKILL.md"
        if not f.is_file():
            r.error(f"missing skill {name}")
            continue
        fm = frontmatter(f.read_text())
        if fm is None:
            r.error(f"skill {name}: missing YAML frontmatter")
            continue
        if fm.get("name") != name:
            r.error(f"skill {name}: frontmatter name {fm.get('name')!r} does not match directory")
        if len(str(fm.get("description", ""))) < 20:
            r.error(f"skill {name}: description missing or too short")
        for k in set(fm) - SKILL_KEYS:
            r.warn(f"skill {name}: unrecognised frontmatter key {k!r}")

    for f in sorted((path / ".claude/agents").glob("*.md")):
        fm = frontmatter(f.read_text())
        if not fm or not fm.get("name") or not fm.get("description"):
            r.error(f"agent {f.name}: frontmatter needs name and description")
        elif not fm.get("tools"):
            r.warn(f"agent {f.name}: no tools list; it inherits every tool")

    for f in sorted((path / ".claude/rules").glob("*.md")):
        fm = frontmatter(f.read_text())
        if fm is not None and "paths" in fm and not isinstance(fm["paths"], list):
            r.error(f"rule {f.name}: paths must be a list")

    settings = path / ".claude/settings.json"
    if settings.is_file():
        try:
            s = json.loads(settings.read_text())
            perms = s.get("permissions", {})
            if perms.get("defaultMode") == "bypassPermissions":
                r.error("settings.json: defaultMode bypassPermissions is forbidden")
            for rule in perms.get("allow", []):
                if rule in ("Bash", "Bash(*)", "*", "Bash(:*)"):
                    r.error(f"settings.json: unrestricted allow rule {rule!r}")
        except json.JSONDecodeError as e:
            r.error(f"settings.json: invalid JSON ({e})")
    if (path / ".claude/settings.local.json").exists():
        gi = (path / ".gitignore").read_text() if (path / ".gitignore").exists() else ""
        if "settings.local.json" not in gi:
            r.error(".claude/settings.local.json exists and is not gitignored")

    claude = path / "CLAUDE.md"
    if claude.is_file():
        text = claude.read_text()
        if len(text.splitlines()) > 200:
            r.warn(f"CLAUDE.md is {len(text.splitlines())} lines (target < 200)")
        for imp in re.findall(r"^@(\S+)", text, flags=re.M):
            if not (path / imp).is_file():
                r.error(f"CLAUDE.md imports missing file @{imp}")

    for f in sorted((path / "AGENT/prompts").glob("*.md")):
        if f.name == "README.md":
            continue
        heads = set(re.findall(r"^## (.+)$", f.read_text(), flags=re.M))
        for sec in PROMPT_SECTIONS:
            if sec not in heads:
                r.error(f"prompt {f.name}: missing section '{sec}'")

    # Central templates contain placeholders on purpose; only rendered files are checked.
    docs = [p for p in path.rglob("*.md") if ".git" not in p.parts
            and not p.relative_to(path).as_posix().startswith("agent-foundation/templates/")]
    for f in docs:
        rel = f.relative_to(path).as_posix()
        text = f.read_text()
        if PLACEHOLDER.search(text):
            r.error(f"{rel}: unresolved placeholder {PLACEHOLDER.search(text).group(0)}")
        for target in LINK.findall(strip_code(text)):
            if re.match(r"^[a-z]+:|^#", target):
                continue
            if not (f.parent / target.split("#")[0]).exists():
                r.error(f"{rel}: broken link {target}")

    for rel in FACT_FILES:
        f = path / rel
        if not f.is_file():
            continue
        for n, line in enumerate(strip_code(f.read_text()).splitlines(), 1):
            m = CLAIM.search(line)
            if m and "Evidence" not in line and not line.lstrip().startswith(">"):
                r.error(f"{rel}:{n}: claim '{m.group(0)}' without 'Evidence:'")

    mpath = path / "AGENT/.foundation-manifest.json"
    if mpath.is_file():
        manifest = json.loads(mpath.read_text())
        for rel, digest in manifest.get("managed", {}).items():
            f = path / rel
            if not f.is_file():
                r.error(f"managed file missing: {rel}")
            elif hashlib.sha256(f.read_bytes()).hexdigest() != digest:
                r.warn(f"managed file drifted from central template: {rel}")
    return r


def code_files(path, manifest):
    known = set(manifest.get("managed", {})) | set(manifest.get("seeded", [])) | {"AGENT/.foundation-manifest.json"}
    out = []
    for f in path.rglob("*"):
        if not f.is_file() or ".git" in f.relative_to(path).parts:
            continue
        rel = f.relative_to(path).as_posix()
        if rel in known or rel in FOUNDATION_FILES or rel.startswith(FOUNDATION_DIRS):
            continue
        out.append(rel)
    return out


def check_inventory(inv, root, reports):
    by_name = {r.repo: r for r in reports}
    for repo in inv["repositories"]:
        path = root / repo["name"]
        r = by_name.get(repo["name"])
        if r is None:
            continue
        mpath = path / "AGENT/.foundation-manifest.json"
        manifest = json.loads(mpath.read_text()) if mpath.is_file() else {}
        if manifest and manifest.get("foundation_version") != inv["foundation_version"]:
            r.warn(f"manifest version {manifest.get('foundation_version')} != inventory {inv['foundation_version']}")
        extra = code_files(path, manifest)
        if not repo["code_present"] and extra:
            r.error(f"inventory says code_present=false but repository has {len(extra)} other file(s), "
                    f"e.g. {extra[0]}; re-audit and update inventory and PROJECT_CONTEXT.md")
        if repo["code_present"] and "no source code" in (path / "CLAUDE.md").read_text():
            r.warn("code_present=true but CLAUDE.md still says there is no source code")
        if repo["foundation_status"] == "initialized" and r.errors:
            r.error("inventory says 'initialized' but required checks fail")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("repos", nargs="*", type=Path)
    ap.add_argument("--inventory", type=Path)
    ap.add_argument("--root", type=Path, help="directory with checkouts named as in the inventory")
    ap.add_argument("--format", choices=["text", "json"], default="text")
    ap.add_argument("--strict", action="store_true", help="treat warnings as errors")
    args = ap.parse_args(argv)
    inv = json.loads(args.inventory.read_text()) if args.inventory else None
    paths = list(args.repos)
    if inv:
        if not args.root:
            ap.error("--inventory requires --root")
        paths += [args.root / r["name"] for r in inv["repositories"]]
    if not paths:
        ap.error("give repository paths or --inventory with --root")

    reports = []
    for p in paths:
        if not p.is_dir():
            rep = Report(p.name)
            rep.error(f"repository not checked out at {p}")
            reports.append(rep)
        else:
            reports.append(check_repo(p.resolve()))
    if inv:
        check_inventory(inv, args.root, reports)

    failed = any(r.errors or (args.strict and r.warnings) for r in reports)
    if args.format == "json":
        print(json.dumps([vars(r) for r in reports], indent=2))
    else:
        for r in reports:
            status = "FAIL" if r.errors or (args.strict and r.warnings) else "PASS"
            print(f"{status} {r.repo}: {len(r.errors)} error(s), {len(r.warnings)} warning(s)")
            for m in r.errors:
                print(f"  ERROR   {m}")
            for m in r.warnings:
                print(f"  WARNING {m}")
        print(f"\n{sum(not r.errors for r in reports)}/{len(reports)} repositories without errors")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
