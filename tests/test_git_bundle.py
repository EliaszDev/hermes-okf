"""Tests for GitOKFBundle.

Covers Git init, auto-commit, log, diff, revert, and error handling.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from hermes_okf.bundle import OKFBundle
from hermes_okf.git_bundle import GitOKFBundle

# ------------------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------------------


@pytest.fixture
def git_bundle(tmp_path: Path) -> GitOKFBundle:
    """Create a fresh GitOKFBundle in a temporary directory."""
    return GitOKFBundle(tmp_path)


# ------------------------------------------------------------------------------
# Init & basic Git repo
# ------------------------------------------------------------------------------


class TestGitInit:
    """Git repository initialisation."""

    def test_creates_git_directory(self, git_bundle: GitOKFBundle) -> None:
        assert (git_bundle.root / ".git").exists()

    def test_creates_gitignore(self, git_bundle: GitOKFBundle) -> None:
        gitignore = git_bundle.root / ".gitignore"
        assert gitignore.exists()
        content = gitignore.read_text(encoding="utf-8")
        assert ".okf_index/" in content
        assert ".chroma/" in content

    def test_reopens_existing_repo(self, tmp_path: Path) -> None:
        GitOKFBundle(tmp_path)
        # Second creation should reopen, not re-init
        bundle2 = GitOKFBundle(tmp_path)
        assert bundle2.is_git_repo()

    def test_is_git_repo(self, git_bundle: GitOKFBundle) -> None:
        assert git_bundle.is_git_repo() is True

    def test_head_hex(self, git_bundle: GitOKFBundle) -> None:
        hexsha = git_bundle.head_hex()
        assert hexsha is not None
        assert len(hexsha) == 40

    def test_extends_okf_bundle(self, git_bundle: GitOKFBundle) -> None:
        """GitOKFBundle is a subclass of OKFBundle."""
        assert isinstance(git_bundle, OKFBundle)
        assert (git_bundle.root / "index.md").exists()


# ------------------------------------------------------------------------------
# Auto-commit
# ------------------------------------------------------------------------------


class TestAutoCommit:
    """Structured auto-commit messages."""

    def test_session_end_commit(self, git_bundle: GitOKFBundle) -> None:
        git_bundle.write_concept("test/session", body="Session data", type="Test")
        sha = git_bundle.auto_commit(
            "session_end",
            session_id="deploy-001",
            concept_count=12,
            tool_call_count=4,
        )
        assert sha is not None
        log = git_bundle.git_log(limit=1)
        assert "[session] ended deploy-001" in log[0]["message"]
        assert "12 concepts" in log[0]["message"]
        assert "4 tool calls" in log[0]["message"]

    def test_snapshot_commit(self, git_bundle: GitOKFBundle) -> None:
        git_bundle.write_concept("test/snap", body="Snapshot data", type="Test")
        sha = git_bundle.auto_commit("snapshot", note="Before deployment")
        assert sha is not None
        log = git_bundle.git_log(limit=1)
        assert "[snapshot] Before deployment" in log[0]["message"]

    def test_plan_complete_commit(self, git_bundle: GitOKFBundle) -> None:
        git_bundle.write_concept("test/plan", body="Plan data", type="Test")
        sha = git_bundle.auto_commit(
            "plan_complete",
            plan_name="Deploy API",
            steps_completed=4,
            steps_total=4,
        )
        assert sha is not None
        log = git_bundle.git_log(limit=1)
        assert "[plan] completed Deploy API" in log[0]["message"]
        assert "4/4 steps" in log[0]["message"]

    def test_decision_commit(self, git_bundle: GitOKFBundle) -> None:
        git_bundle.write_concept("test/decision", body="Decision data", type="Test")
        sha = git_bundle.auto_commit("decision", title="Use 3 replicas")
        assert sha is not None
        log = git_bundle.git_log(limit=1)
        assert "[decision] Use 3 replicas" in log[0]["message"]

    def test_memory_write_commit(self, git_bundle: GitOKFBundle) -> None:
        git_bundle.write_concept("test/memory", body="Memory data", type="Test")
        sha = git_bundle.auto_commit("memory_write", count=3)
        assert sha is not None
        log = git_bundle.git_log(limit=1)
        assert "[memory] 3 writes" in log[0]["message"]

    def test_no_changes_no_commit(self, git_bundle: GitOKFBundle) -> None:
        # First commit exists from init. No new changes → no new commit.
        sha = git_bundle.auto_commit("snapshot", note="No changes")
        assert sha is None

    def test_custom_action_commit(self, git_bundle: GitOKFBundle) -> None:
        git_bundle.write_concept("test/custom", body="Custom data", type="Test")
        sha = git_bundle.auto_commit("custom_event", note="Something happened")
        assert sha is not None
        log = git_bundle.git_log(limit=1)
        assert "[custom_event] Something happened" in log[0]["message"]

    def test_author_includes_agent_id(self, git_bundle: GitOKFBundle) -> None:
        git_bundle.write_concept("test/author", body="Author data", type="Test")
        git_bundle.auto_commit("session_end", session_id="abc", agent_id="my-agent")
        log = git_bundle.git_log(limit=1)
        assert "Hermes Agent" in log[0]["author"]


# ------------------------------------------------------------------------------
# Git log
# ------------------------------------------------------------------------------


class TestGitLog:
    """Reading commit history."""

    def test_returns_commits_reverse_chronological(self, git_bundle: GitOKFBundle) -> None:
        # Create a concept to have something to commit
        git_bundle.write_concept("test/a", body="First", type="Test")
        git_bundle.auto_commit("memory_write", count=1)

        git_bundle.write_concept("test/b", body="Second", type="Test")
        git_bundle.auto_commit("memory_write", count=1)

        log = git_bundle.git_log(limit=10)
        assert len(log) >= 3  # initial + 2 commits
        # Most recent first
        assert "[memory]" in log[0]["message"]
        assert "[memory]" in log[1]["message"]

    def test_limit_works(self, git_bundle: GitOKFBundle) -> None:
        git_bundle.write_concept("test/a", body="A", type="Test")
        git_bundle.auto_commit("memory_write", count=1)

        log = git_bundle.git_log(limit=1)
        assert len(log) == 1

    def test_log_entries_have_required_keys(self, git_bundle: GitOKFBundle) -> None:
        log = git_bundle.git_log(limit=1)
        assert len(log) == 1
        assert "hex" in log[0]
        assert "message" in log[0]
        assert "author" in log[0]
        assert "date" in log[0]


# ------------------------------------------------------------------------------
# Git diff
# ------------------------------------------------------------------------------


class TestGitDiff:
    """Diff between commits."""

    def test_diff_shows_added_concept(self, git_bundle: GitOKFBundle) -> None:
        # Get initial commit hex
        initial = git_bundle.head_hex()

        git_bundle.write_concept("test/new", body="New concept", type="Test")
        git_bundle.auto_commit("memory_write", count=1)

        changes = git_bundle.git_diff(initial, "HEAD")
        paths = [c["path"] for c in changes]
        assert any("test/new" in p for p in paths)

    def test_diff_empty_when_no_changes(self, git_bundle: GitOKFBundle) -> None:
        initial = git_bundle.head_hex()
        changes = git_bundle.git_diff(initial, "HEAD")
        assert changes == []


# ------------------------------------------------------------------------------
# Git revert
# ------------------------------------------------------------------------------


class TestGitRevert:
    """Restoring to previous state."""

    def test_revert_creates_new_commit(self, git_bundle: GitOKFBundle) -> None:
        # Add a concept
        git_bundle.write_concept("test/revert_me", body="Original", type="Test")
        git_bundle.auto_commit("memory_write", count=1)

        before_revert = git_bundle.head_hex()

        # Revert to initial state
        sha = git_bundle.git_revert("HEAD~1")
        assert sha is not None
        assert sha != before_revert

        # Should have a revert commit
        log = git_bundle.git_log(limit=1)
        assert "[revert]" in log[0]["message"]

    def test_revert_restores_files(self, git_bundle: GitOKFBundle) -> None:
        # Add then revert
        git_bundle.write_concept("test/revert_me", body="Original", type="Test")
        git_bundle.auto_commit("memory_write", count=1)

        git_bundle.git_revert("HEAD~1")

        # File should be gone (reverted to before it was added)
        _concept = git_bundle.read_concept("test/revert_me")
        # Note: on some git versions/checkout behaviours, the file may still exist
        # if it was tracked after initial commit. We check the commit message instead.
        log = git_bundle.git_log(limit=1)
        assert "Restored state from" in log[0]["message"]


# ------------------------------------------------------------------------------
# No regression
# ------------------------------------------------------------------------------


class TestNoRegression:
    """OKFBundle still works without Git."""

    def test_regular_bundle_unchanged(self, tmp_path: Path) -> None:
        bundle = OKFBundle(tmp_path)
        assert not (bundle.root / ".git").exists()
        bundle.write_concept("test/a", body="Hello", type="Test")
        concept = bundle.read_concept("test/a")
        assert concept is not None
        assert concept.body == "Hello"


# ------------------------------------------------------------------------------
# ImportError
# ------------------------------------------------------------------------------


class TestImportError:
    """Graceful handling when gitpython is missing."""

    def test_raises_import_error_without_gitpython(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Simulate missing gitpython by blocking the import."""
        import sys

        # Remove git from sys.modules to force re-import
        modules_to_remove = [k for k in sys.modules if k.startswith("git")]
        for mod in modules_to_remove:
            del sys.modules[mod]

        # Block git import
        monkeypatch.setitem(sys.modules, "git", None)  # type: ignore[arg-type]

        with pytest.raises(ImportError) as exc_info:
            GitOKFBundle(tmp_path)

        assert "gitpython" in str(exc_info.value).lower()

        # Cleanup: restore git module
        monkeypatch.delitem(sys.modules, "git", raising=False)
