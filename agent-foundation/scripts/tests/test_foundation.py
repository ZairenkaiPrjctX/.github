"""Tests for sync, validation, and signature verification. Run:
python3 -m unittest discover -s agent-foundation/scripts/tests"""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import sync_agent_foundation as sync  # noqa: E402
import validate_agent_setup as val  # noqa: E402
import verify_commit_signature as sig  # noqa: E402

REPO = {"name": "Demo", "github_description": "Demo repo", "evidence": "test fixture",
        "role_hint_unverified": "demo", "related_repositories": [], "open_questions": ["Q?"],
        "optional_templates": [], "code_present": False, "foundation_status": "initialized"}


class FoundationTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.repo = self.root / "Demo"
        self.repo.mkdir()
        sync.sync_repo(self.repo, REPO, "1.0.0", "2026-01-01", check=False)

    def tearDown(self):
        shutil.rmtree(self.root)

    def errors(self):
        return val.check_repo(self.repo).errors

    def test_fresh_sync_is_valid_and_idempotent(self):
        self.assertEqual(self.errors(), [])
        self.assertEqual(sync.sync_repo(self.repo, REPO, "1.0.0", "2026-01-01", check=True), [])

    def test_seeded_files_are_not_overwritten(self):
        (self.repo / "CLAUDE.md").write_text((self.repo / "CLAUDE.md").read_text() + "\nlocal note\n")
        sync.sync_repo(self.repo, REPO, "1.0.0", "2026-01-01", check=False)
        self.assertIn("local note", (self.repo / "CLAUDE.md").read_text())

    def test_missing_skill_and_bad_frontmatter(self):
        shutil.rmtree(self.repo / ".claude/skills/bug-fix")
        f = self.repo / ".claude/skills/repo-audit/SKILL.md"
        f.write_text(f.read_text().replace("name: repo-audit", "name: wrong"))
        errs = " ".join(self.errors())
        self.assertIn("missing skill bug-fix", errs)
        self.assertIn("does not match directory", errs)

    def test_broken_link_import_and_placeholder(self):
        (self.repo / "AGENT/README.md").write_text("# x\n[a](nope.md)\n{{repo}}\nline\nline\n")
        (self.repo / "CLAUDE.md").write_text((self.repo / "CLAUDE.md").read_text() + "\n@missing.md\n")
        errs = " ".join(self.errors())
        for needle in ("broken link nope.md", "unresolved placeholder", "@missing.md"):
            self.assertIn(needle, errs)

    def test_unsupported_claim_and_dangerous_settings(self):
        ctx = self.repo / "AGENT/PROJECT_CONTEXT.md"
        ctx.write_text(ctx.read_text() + "\nAll tests pass on device.\n")
        (self.repo / ".claude/settings.json").write_text(json.dumps(
            {"permissions": {"defaultMode": "bypassPermissions", "allow": ["Bash(*)"]}}))
        errs = " ".join(self.errors())
        self.assertIn("without 'Evidence:'", errs)
        self.assertIn("bypassPermissions", errs)
        self.assertIn("unrestricted allow", errs)

    def test_drift_is_warning_and_inventory_staleness_is_error(self):
        f = self.repo / "AGENT/policies/testing.md"
        f.write_text(f.read_text() + "\n- local edit\n")
        (self.repo / "main.c").write_text("int main(){}\n")
        reports = [val.check_repo(self.repo)]
        val.check_inventory({"foundation_version": "1.0.0", "repositories": [REPO]}, self.root, reports)
        self.assertTrue(any("drifted" in w for w in reports[0].warnings))
        self.assertTrue(any("code_present=false" in e for e in reports[0].errors))


class SignatureTest(unittest.TestCase):
    def test_rfc8032_vector_1(self):
        pub = bytes.fromhex("d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a")
        s = bytes.fromhex("e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e06522490155"
                          "5fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b")
        self.assertTrue(sig.ed25519_verify(pub, s, b""))
        self.assertFalse(sig.ed25519_verify(pub, s, b"x"))

    def test_allowed_signers_parsing(self):
        f = Path(tempfile.mkdtemp()) / "allowed"
        f.write_text('# c\n'
                     'a@x namespaces="git" ssh-ed25519 KEYA\n'
                     'a@x namespaces="file" ssh-ed25519 KEYB\n'
                     'b@x,a@x ssh-ed25519 KEYC\n')
        self.assertEqual(sig.allowed_keys(f, "a@x"), {"KEYA", "KEYC"})
        self.assertEqual(sig.allowed_keys(f, "z@x"), set())
        shutil.rmtree(f.parent)

    def test_repo_allowed_signers_file_is_well_formed(self):
        f = Path(__file__).resolve().parents[2] / "allowed_signers"
        self.assertTrue(sig.allowed_keys(f, "noreply@anthropic.com"))

    def test_unsigned_commit(self):
        ok, msg = sig.verify("tree abc\nauthor a <a> 0 +0000\n\nmsg\n")
        self.assertFalse(ok)
        self.assertIn("UNSIGNED", msg)


if __name__ == "__main__":
    unittest.main()
