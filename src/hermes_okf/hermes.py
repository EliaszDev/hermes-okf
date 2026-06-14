"""Hermes-OKF Bridge — Deep integration layer.

Makes OKF the native memory and state backbone of a Hermes agent.
Every agent configuration, session, tool definition, plan, and decision
lives in the OKF bundle. The agent can be stopped, restarted, and resumed
from its bundle alone.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Callable

from hermes_okf.agent import HermesMemoryMixin, memorize_decision, memorize_tool, memorize_observation
from hermes_okf.bundle import OKFBundle
from hermes_okf.memory import HermesMemory


class HermesAgent(HermesMemoryMixin):
    """A Hermes agent whose entire state lives in an OKF bundle.

    The bundle is the single source of truth. You can stop the agent,
    restart it later, and it resumes from the last OKF snapshot.

    Args:
        bundle_path: Path to the agent's OKF bundle root.
        agent_id: Unique identifier for this agent instance.
        model: Default LLM model identifier.
    """

    def __init__(
        self,
        bundle_path: str,
        agent_id: str,
        model: str = "gpt-4o",
    ) -> None:
        super().__init__(bundle_path, agent_id=agent_id)
        self.model = model
        self.current_session_id: str | None = None
        self.current_plan_id: str | None = None
        self._ensure_structure()
        self._load_config()
        self.start_session()

    # ------------------------------------------------------------------
    # Structure
    # ------------------------------------------------------------------
    def _ensure_structure(self) -> None:
        """Ensure the OKF bundle has the Hermes-native directory layout."""
        dirs = ("config", "tools", "sessions", "plans", "plans/archive")
        for d in dirs:
            (self.memory.bundle.root / d).mkdir(parents=True, exist_ok=True)
        if not self.memory.bundle.read_concept("config/agent"):
            self._create_default_config()

    def _create_default_config(self) -> None:
        self.memory.bundle.write_concept(
            "config/agent",
            body="# Agent Configuration\n\nSystem prompt and behaviour settings.",
            type="AgentConfig",
            title=f"{self.memory.agent_id} Configuration",
            model=self.model,
            system_prompt="You are a helpful, autonomous Hermes agent.",
            version="0.1.0",
        )

    def _load_config(self) -> None:
        config = self.memory.bundle.read_concept("config/agent")
        if config and isinstance(config.metadata, dict):
            self.model = config.metadata.get("model", self.model)
            self.system_prompt = config.metadata.get(
                "system_prompt", "You are a helpful, autonomous Hermes agent."
            )

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------
    def start_session(self, session_id: str | None = None) -> str:
        """Begin a new session and record it in OKF."""
        self.current_session_id = session_id or self._now_filename_safe()
        self.memory.start_session(self.current_session_id)
        self.memory.bundle.write_concept(
            f"sessions/{self.current_session_id}",
            body=f"# Session {self.current_session_id}\n\nAgent: {self.memory.agent_id}\nModel: {self.model}",
            type="Session",
            title=f"Session {self.current_session_id}",
            agent_id=self.memory.agent_id,
            model=self.model,
            status="active",
            started_at=self._now_iso(),
        )
        return self.current_session_id

    def end_session(self) -> None:
        """Close the current session and archive its state."""
        if self.current_session_id:
            self.memory.end_session(self.current_session_id)
            session = self.memory.bundle.read_concept(f"sessions/{self.current_session_id}")
            if session:
                self.memory.bundle.write_concept(
                    f"sessions/{self.current_session_id}",
                    body=session.body,
                    type="Session",
                    title=session.title,
                    agent_id=self.memory.agent_id,
                    model=self.model,
                    status="completed",
                    ended_at=self._now_iso(),
                )
        self.current_session_id = None

    def list_sessions(self) -> list[str]:
        """Return all session IDs ordered chronologically."""
        return sorted(self.memory.bundle.list_concepts("sessions"))

    def recall_session(self, session_id: str | None = None) -> Any:
        """Retrieve a previous session. Defaults to the most recent."""
        if session_id:
            return self.memory.bundle.read_concept(f"sessions/{session_id}")
        sessions = self.list_sessions()
        if sessions:
            return self.memory.bundle.read_concept(sessions[-1])
        return None

    # ------------------------------------------------------------------
    # Tool registry
    # ------------------------------------------------------------------
    def register_tool(
        self,
        name: str,
        description: str,
        schema: dict[str, Any] | None = None,
        example: str = "",
    ) -> None:
        """Register a tool definition in OKF so the agent can self-document."""
        body = f"# Tool: {name}\n\n{description}\n"
        if example:
            body += f"\n## Example\n\n```\n{example}\n```\n"
        self.memory.bundle.write_concept(
            f"tools/{name}",
            body=body,
            type="Tool",
            title=name,
            description=description,
            schema=json.dumps(schema) if schema else "",
            tags=["tool"],
        )

    def list_tools(self) -> list[str]:
        """Return IDs of all registered tools."""
        return self.memory.bundle.list_concepts("tools")

    def get_tool(self, name: str) -> Any:
        """Read a tool definition from OKF."""
        return self.memory.bundle.read_concept(f"tools/{name}")

    # ------------------------------------------------------------------
    # Plan execution
    # ------------------------------------------------------------------
    def create_plan(self, task: str, steps: list[str]) -> str:
        """Create a tracked plan and store it in OKF. Returns plan ID."""
        plan_id = f"plans/{self._slugify(task[:40])}_{self._now_date()}"
        body_lines = [f"# Plan: {task}\n", f"Created: {self._now_iso()}\n", "## Steps\n"]
        for i, step in enumerate(steps, 1):
            body_lines.append(f"{i}. [ ] {step}\n")
        self.memory.bundle.write_concept(
            plan_id,
            body="".join(body_lines),
            type="Plan",
            title=task,
            status="active",
            steps=steps,
            progress=0,
        )
        self.current_plan_id = plan_id
        self.memory.record_observation(f"Plan created: {task} ({len(steps)} steps)", category="Plan")
        return plan_id

    def complete_step(self, step_index: int, result: str = "") -> None:
        """Mark a plan step as complete."""
        if not self.current_plan_id:
            return
        plan = self.memory.bundle.read_concept(self.current_plan_id)
        if not plan:
            return
        steps = plan.metadata.get("steps", [])
        if not steps or step_index >= len(steps):
            return

        # Rebuild body with the step checked off
        body_lines = plan.body.splitlines()
        for i, line in enumerate(body_lines):
            if line.startswith(f"{step_index + 1}. [ ] {steps[step_index]}"):
                body_lines[i] = line.replace("[ ]", "[x]")
                if result:
                    body_lines.insert(i + 1, f"    → {result}")
                break

        progress = int(((step_index + 1) / len(steps)) * 100)
        self.memory.bundle.write_concept(
            self.current_plan_id,
            body="\n".join(body_lines),
            type="Plan",
            title=plan.title,
            status="active" if progress < 100 else "completed",
            steps=steps,
            progress=progress,
        )
        self.memory.record_observation(
            f"Plan step {step_index + 1}/{len(steps)} completed: {steps[step_index]}",
            category="Plan",
        )

    def archive_plan(self, plan_id: str | None = None) -> None:
        """Move a completed plan to the archive folder."""
        pid = plan_id or self.current_plan_id
        if not pid:
            return
        plan = self.memory.bundle.read_concept(pid)
        if not plan:
            return
        archive_id = f"plans/archive/{self._slugify(plan.title[:40])}_{self._now_date()}"
        self.memory.bundle.write_concept(
            archive_id,
            body=plan.body,
            type="Plan",
            title=plan.title,
            status="archived",
            steps=plan.metadata.get("steps", []),
            progress=plan.metadata.get("progress", 100),
            archived_at=self._now_iso(),
        )
        self.memory.bundle.delete_concept(pid)
        if self.current_plan_id == pid:
            self.current_plan_id = None

    # ------------------------------------------------------------------
    # State snapshots
    # ------------------------------------------------------------------
    def snapshot(self, note: str = "") -> None:
        """Save a full snapshot of current agent state to OKF."""
        snapshot_id = f"snapshots/{self._now_filename_safe()}"
        state = {
            "agent_id": self.memory.agent_id,
            "model": self.model,
            "current_session": self.current_session_id,
            "current_plan": self.current_plan_id,
            "system_prompt": getattr(self, "system_prompt", ""),
            "note": note,
        }
        self.memory.bundle.write_concept(
            snapshot_id,
            body=f"# State Snapshot\n\n```json\n{json.dumps(state, indent=2)}\n```",
            type="Snapshot",
            title="State Snapshot",
            **state,
        )

    def restore(self, snapshot_id: str | None = None) -> dict[str, Any]:
        """Restore agent state from a snapshot."""
        if snapshot_id:
            snap = self.memory.bundle.read_concept(snapshot_id)
        else:
            snaps = sorted(self.memory.bundle.list_concepts("snapshots"))
            snap = self.memory.bundle.read_concept(snaps[-1]) if snaps else None
        if not snap:
            return {}
        meta = snap.metadata
        self.model = meta.get("model", self.model)
        self.current_session_id = meta.get("current_session")
        self.current_plan_id = meta.get("current_plan")
        self.system_prompt = meta.get("system_prompt", "")
        return meta

    # ------------------------------------------------------------------
    # Context for LLM calls
    # ------------------------------------------------------------------
    def build_context(self, query: str, top_k: int = 5) -> str:
        """Build a context string for an LLM call from the OKF bundle.

        Returns markdown text combining relevant concepts, recent log,
        active plan, and agent configuration.
        """
        lines: list[str] = [f"# Agent Context: {self.memory.agent_id}\n"]

        # System prompt
        lines.append(f"## System Prompt\n\n{getattr(self, 'system_prompt', '')}\n")

        # Active plan
        if self.current_plan_id:
            plan = self.memory.bundle.read_concept(self.current_plan_id)
            if plan:
                lines.append(f"## Active Plan\n\n{plan.title}\n\n{plan.body}\n")

        # Relevant memory
        relevant = self.memory.recall(query, top_k=top_k)
        if relevant:
            lines.append("## Relevant Memory\n")
            for c in relevant:
                lines.append(f"- **{c.title}** ({c.type}): {c.description or c.body[:200]}\n")

        # Recent log
        log = self.memory.get_recent_log(n_lines=20)
        if log:
            lines.append(f"## Recent Activity\n\n```\n{log}\n```\n")

        # Tool registry
        tools = self.list_tools()
        if tools:
            lines.append("## Available Tools\n")
            for t in tools:
                tool = self.memory.bundle.read_concept(t)
                if tool:
                    lines.append(f"- `{tool.title}` — {tool.description}\n")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    @staticmethod
    def _now_filename_safe() -> str:
        """Return a timestamp safe for use in filenames (no colons)."""
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")

    @staticmethod
    def _now_date() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    @staticmethod
    def _slugify(text: str) -> str:
        return "".join(c if c.isalnum() else "_" for c in text.lower()).strip("_")
