"""Git-backed OKF bundle for audit history and rollback.

Wraps ``gitpython`` around ``OKFBundle`` to provide automatic commit
history on significant agent events, plus CLI-friendly history queries.

Usage::

    from hermes_okf.git_bundle import GitOKFBundle
    bundle = GitOKFBundle("~/.hermes/okf_memory")
    bundle.auto_commit(action="session_end", session_id="abc-123")
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from hermes_okf.bundle import OKFBundle


class GitOKFBundle(OKFBundle):
    """OKF bundle with optional Git history tracking.

    Extends ``OKFBundle`` with automatic Git commits on significant
    agent events. ``gitpython`` is an optional dependency — install with
    ``pip install hermes-okf[git]``.
    """

    def __init__(self, root_path: str | Path, auto_init: bool = True) -> None:
        super().__init__(root_path)
        try:
            import git

            self._git_module = git
        except ImportError as exc:
            raise ImportError(
                "Install gitpython to use Git-backed bundles: " "pip install hermes-okf[git]"
            ) from exc

        self._repo: Any = None
        if auto_init:
            self._ensure_git()

    # ------------------------------------------------------------------
    # Git lifecycle
    # ------------------------------------------------------------------

    def _ensure_git(self) -> None:
        """Initialise Git repository if not already present."""
        git_dir = self.root / ".git"
        if not git_dir.exists():
            self._repo = self._git_module.Repo.init(self.root)
            self._create_gitignore()
            self._commit("Initial commit", "GitOKFBundle <system@okf>")
        else:
            self._repo = self._git_module.Repo(self.root)

    def _create_gitignore(self) -> None:
        """Create ``.gitignore`` in the bundle root."""
        content = (
            "# OKF index\n"
            ".okf_index/\n"
            "# ChromaDB vector store\n"
            ".chroma/\n"
            "# Python cache\n"
            "__pycache__/\n"
            "*.pyc\n"
        )
        (self.root / ".gitignore").write_text(content, encoding="utf-8")

    def _commit(self, message: str, author: str, force: bool = False) -> str | None:
        """Stage all changes and create a commit."""
        if not force and not self._repo.is_dirty() and not self._repo.untracked_files:
            return None
        self._repo.git.add(A=True)
        actor = self._git_module.Actor._from_string(author)
        commit = self._repo.index.commit(message, author=actor, committer=actor)
        return str(commit.hexsha)

    # ------------------------------------------------------------------
    # Auto-commit triggers
    # ------------------------------------------------------------------

    def auto_commit(self, action: str, **kwargs: Any) -> str | None:
        """Create a commit with a structured message based on action type.

        Args:
            action: One of ``session_end``, ``snapshot``, ``plan_complete``,
                ``decision``, ``memory_write``.
            **kwargs: Additional context for the commit message.

        Returns:
            Hex SHA of the new commit, or ``None`` if nothing changed.
        """
        agent_id = kwargs.get("agent_id", "hermes")
        author = f"Hermes Agent <agent@{agent_id}>"

        msg = self._format_message(action, **kwargs)
        return self._commit(msg, author)

    def _format_message(self, action: str, **kwargs: Any) -> str:
        """Build a commit message from action type and kwargs."""
        if action == "session_end":
            return (
                f"[session] ended {kwargs.get('session_id', '?')}"
                f" — {kwargs.get('concept_count', 0)} concepts,"
                f" {kwargs.get('tool_call_count', 0)} tool calls"
            )
        if action == "snapshot":
            return f"[snapshot] {kwargs.get('note', '')}"
        if action == "plan_complete":
            return (
                f"[plan] completed {kwargs.get('plan_name', '?')}"
                f" — {kwargs.get('steps_completed', 0)}/"
                f"{kwargs.get('steps_total', 0)} steps"
            )
        if action == "decision":
            return f"[decision] {kwargs.get('title', '')}"
        if action == "memory_write":
            return f"[memory] {kwargs.get('count', 1)} writes"
        return f"[{action}] {kwargs.get('note', 'auto-commit')}"

    # ------------------------------------------------------------------
    # History queries
    # ------------------------------------------------------------------

    def git_log(self, limit: int = 10) -> list[dict[str, Any]]:
        """Return commits in reverse chronological order.

        Args:
            limit: Maximum number of commits to return.

        Returns:
            List of commit dicts with ``hex``, ``message``, ``author``,
            ``date`` keys.
        """
        if self._repo is None:
            return []
        commits: list[dict[str, Any]] = []
        for commit in self._repo.iter_commits("HEAD", max_count=limit):
            commits.append(
                {
                    "hex": commit.hexsha,
                    "message": commit.message.strip(),
                    "author": str(commit.author),
                    "date": commit.committed_datetime.isoformat(),
                }
            )
        return commits

    def git_diff(self, from_ref: str, to_ref: str) -> list[dict[str, Any]]:
        """Show file-level diff between two refs.

        Args:
            from_ref: Starting Git reference (e.g. ``HEAD~1``).
            to_ref: Ending Git reference (e.g. ``HEAD``).

        Returns:
            List of change dicts with ``path``, ``additions``, ``deletions``.
        """
        if self._repo is None:
            return []
        changes: list[dict[str, Any]] = []
        diffs = self._repo.commit(from_ref).diff(to_ref)
        for d in diffs:
            path = d.b_path or d.a_path or "unknown"
            changes.append(
                {
                    "path": path,
                    "additions": d.diff.count("\n+") - d.diff.count("\n++"),
                    "deletions": d.diff.count("\n-") - d.diff.count("\n--"),
                }
            )
        return changes

    def git_revert(self, ref: str) -> str | None:
        """Restore OKF files to state at ``ref`` and create a new commit.

        This is **not** ``git revert`` — it checks out the tracked files
        from the given ref and commits the restored state.

        Args:
            ref: Git reference to restore (e.g. ``HEAD~1``).

        Returns:
            Hex SHA of the new commit, or ``None`` if nothing changed.
        """
        if self._repo is None:
            return None
        self._repo.git.checkout(ref, "--", ".")
        author = "Hermes Agent <agent@hermes>"
        return self._commit(f"[revert] Restored state from {ref}", author, force=True)

    # ------------------------------------------------------------------
    # Status helpers
    # ------------------------------------------------------------------

    def is_git_repo(self) -> bool:
        """Return whether the bundle is a Git repository."""
        return (self.root / ".git").exists()

    def head_hex(self) -> str | None:
        """Return hex SHA of the current HEAD commit."""
        if self._repo is None:
            return None
        try:
            return str(self._repo.head.commit.hexsha)
        except Exception:
            return None
