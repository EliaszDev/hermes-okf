"""Hermes agent memory integration.

High-level memory layer that lets a Hermes agent persist decisions,
observations, and context across sessions using an OKF bundle.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from hermes_okf.bundle import OKFBundle
from hermes_okf.concept import Concept
from hermes_okf.search import SearchIndex


class HermesMemory:
    """Persistent memory layer for a Hermes agent.

    Wraps an ``OKFBundle`` with agent-specific semantics: sessions, decisions,
    observations, and context retrieval.

    Args:
        bundle_path: Path to the OKF bundle root.
        agent_id: Identifier for this agent instance (used in log entries).
    """

    def __init__(self, bundle_path: str, agent_id: str = "hermes") -> None:
        self.bundle = OKFBundle(bundle_path)
        self.agent_id = agent_id
        self.search = SearchIndex(self.bundle)

    # ------------------------------------------------------------------
    # Session management
    # ------------------------------------------------------------------
    def start_session(self, session_id: str | None = None) -> str:
        """Record the start of a new agent session.

        Returns the session ID.
        """
        sid = session_id or self._now()
        self.bundle.append_log(f"Session started: {sid}", category="Session")
        return sid

    def end_session(self, session_id: str) -> None:
        """Record the end of an agent session."""
        self.bundle.append_log(f"Session ended: {session_id}", category="Session")

    # ------------------------------------------------------------------
    # Decision logging
    # ------------------------------------------------------------------
    def record_decision(
        self,
        decision: str,
        rationale: str | None = None,
        tags: list[str] | None = None,
    ) -> Concept:
        """Persist an architectural or strategic decision.

        Decisions are stored as concepts under ``decisions/`` with auto-generated IDs.
        """
        concept_id = f"decisions/{self._slugify(decision[:40])}_{self._now()[:10]}"
        body = f"# Decision\n\n{decision}\n"
        if rationale:
            body += f"\n## Rationale\n\n{rationale}\n"

        return self.bundle.write_concept(
            concept_id=concept_id,
            body=body,
            type="Decision",
            title=decision[:80],
            description=decision[:200],
            tags=tags or ["decision"],
        )

    # ------------------------------------------------------------------
    # Observation / event logging
    # ------------------------------------------------------------------
    def record_observation(
        self,
        observation: str,
        category: str = "Observation",
        tags: list[str] | None = None,
    ) -> None:
        """Append a lightweight observation to the log."""
        self.bundle.append_log(observation, category=category)

    def record_tool_call(
        self,
        tool_name: str,
        result_summary: str,
    ) -> None:
        """Log a tool call and its outcome."""
        self.bundle.append_log(
            f"Tool '{tool_name}': {result_summary}", category="Tool-Call"
        )

    # ------------------------------------------------------------------
    # Context retrieval
    # ------------------------------------------------------------------
    def recall(self, query: str, top_k: int = 5) -> list[Concept]:
        """Search the memory for relevant concepts."""
        self.search.invalidate()
        return self.search.search_concepts(query, top_k=top_k)

    def recall_by_tag(self, tag: str) -> list[Concept]:
        """Return all concepts tagged with a given tag."""
        return self.bundle.search_by_tag(tag)

    def recall_project(self, project_name: str) -> Concept | None:
        """Retrieve a project concept by name (exact match on title or ID)."""
        for concept_id in self.bundle.list_concepts("projects"):
            concept = self.bundle.read_concept(concept_id)
            if concept and (
                concept.title.lower() == project_name.lower()
                or concept_id.endswith(project_name.lower().replace(" ", "_"))
            ):
                return concept
        return None

    def get_recent_log(self, n_lines: int = 50) -> str:
        """Return the last *n* lines of the agent log."""
        log = self.bundle.read_log()
        lines = log.splitlines()
        return "\n".join(lines[-n_lines:]) if lines else ""

    def get_decisions(self) -> list[Concept]:
        """Return all recorded decisions."""
        return self.bundle.search_by_tag("decision")

    # ------------------------------------------------------------------
    # Project memory
    # ------------------------------------------------------------------
    def register_project(
        self,
        project_id: str,
        title: str,
        description: str = "",
        tags: list[str] | None = None,
        resource: str | None = None,
    ) -> Concept:
        """Register a project in the knowledge bundle."""
        return self.bundle.write_concept(
            concept_id=f"projects/{project_id}",
            body=f"# {title}\n\n{description}\n",
            type="Project",
            title=title,
            description=description,
            tags=tags or ["project"],
            resource=resource,
        )

    def update_project(self, project_id: str, body: str, **metadata: Any) -> Concept:
        """Overwrite a project concept with new content."""
        existing = self.bundle.read_concept(f"projects/{project_id}")
        if existing:
            metadata = {**existing.metadata, **metadata}
        return self.bundle.write_concept(
            concept_id=f"projects/{project_id}",
            body=body,
            **metadata,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    @staticmethod
    def _slugify(text: str) -> str:
        """Simple slug for use in filenames."""
        return "".join(c if c.isalnum() else "_" for c in text.lower()).strip("_")
