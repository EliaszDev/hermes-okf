"""Hermes Agent plugin adapter for hermes-okf.

Implements the full Hermes `MemoryProvider` ABC interface with exact
signature compatibility. Auto-discovered via pip entry point after
`pip install hermes-okf`.

Reference: https://github.com/NousResearch/hermes-agent/blob/main/agent/memory_provider.py
"""

from __future__ import annotations

import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import hermes_okf
from hermes_okf.hermes_integration import HermesOKFConfig, HermesOKFProvider

logger = logging.getLogger(__name__)

# The Hermes MemoryProvider ABC interface (imported if available)
try:
    from agent.memory_provider import (
        MemoryProvider as _HermesMemoryProvider,
    )
except ImportError:
    from abc import ABC, abstractmethod

    class _HermesMemoryProvider(ABC):  # type: ignore[no-redef]
        @property
        @abstractmethod
        def name(self) -> str:
            raise NotImplementedError

        @abstractmethod
        def is_available(self) -> bool:
            raise NotImplementedError

        @abstractmethod
        def initialize(self, session_id: str, **kwargs: Any) -> None:
            raise NotImplementedError

        @abstractmethod
        def get_tool_schemas(self) -> list[dict[str, Any]]:
            raise NotImplementedError


class HermesOKFMemoryProvider(_HermesMemoryProvider):  # type: ignore[misc]
    """Hermes Agent memory provider backed by OKF (Open Knowledge Format).

    Implements the full Hermes MemoryProvider ABC with exact signature
    compatibility. Auto-discovered after `pip install hermes-okf`.
    """

    def __init__(self) -> None:
        self._provider: HermesOKFProvider | None = None
        self._session_id: str = ""
        self._hermes_home: str = ""

    # -- Required ABC properties -----------------------------------------------

    @property
    def name(self) -> str:
        return "hermes-okf"

    # -- Required ABC methods ------------------------------------------------

    def is_available(self) -> bool:
        """Check if pyyaml is installed and config is accessible."""
        try:
            import yaml  # noqa: F401
        except ImportError:
            return False
        return True

    def initialize(self, session_id: str, **kwargs: Any) -> None:
        """Initialize the OKF provider for a session.

        kwargs include:
        - hermes_home (str): ~/.hermes directory
        - platform (str): "cli", "telegram", "discord", etc.
        - agent_identity (str): Profile name (e.g. "coder")
        """
        self._hermes_home = kwargs.get("hermes_home", str(Path.home() / ".hermes"))
        self._session_id = session_id

        hermes_home_path = Path(self._hermes_home)
        config_path = hermes_home_path / "config.yaml"

        # Load config from Hermes config.yaml if it exists
        config_kwargs: dict[str, Any] = {}
        hermes_model = ""
        if config_path.exists():
            import yaml

            with open(config_path, encoding="utf-8") as f:
                hermes_config = yaml.safe_load(f) or {}
            memory_cfg = hermes_config.get("memory", {})
            config_kwargs["bundle_path"] = memory_cfg.get(
                "bundle_path", str(hermes_home_path / "okf_memory")
            )
            config_kwargs["agent_id"] = memory_cfg.get("agent_id", "hermes-agent")
            config_kwargs["auto_snapshot"] = memory_cfg.get("auto_snapshot", True)
            config_kwargs["log_tool_calls"] = memory_cfg.get("log_tool_calls", True)
            config_kwargs["hot_memory_max"] = memory_cfg.get("hot_memory_max", 50)
            # Read the actual Hermes model (top-level or under llm)
            hermes_model = hermes_config.get(
                "model",
                hermes_config.get("llm", {}).get("model", ""),
            )
        else:
            config_kwargs["bundle_path"] = str(hermes_home_path / "okf_memory")
            config_kwargs["agent_id"] = "hermes-agent"

        config = HermesOKFConfig(**config_kwargs)
        if hermes_model:
            config.model = hermes_model
        self._provider = HermesOKFProvider(config)
        self._provider.on_session_start(session_id)

        # Sync the OKF config concept with the actual Hermes model
        if hermes_model:
            self._provider.agent.memory.bundle.write_concept(
                "config/agent",
                body="# Agent Configuration\n\nSystem prompt and behaviour settings.",
                type="AgentConfig",
                title=f"{config.agent_id} Configuration",
                model=hermes_model,
                system_prompt="You are a helpful, autonomous Hermes agent.",
                version=hermes_okf.__version__,
                timestamp=datetime.now(timezone.utc).isoformat() + "Z",
            )

    def get_tool_schemas(self) -> list[dict[str, Any]]:
        """Return tool schemas for memory operations.

        Exposes: search_memory, snapshot_memory
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_memory",
                    "description": (
                        "Search the agent's persistent OKF memory for relevant "
                        "concepts, decisions, observations, and prior context. "
                        "Use this when you need to recall past sessions, "
                        "decisions, or stored knowledge."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query — keywords or natural language",
                            },
                            "top_k": {
                                "type": "integer",
                                "description": "Number of results to return",
                                "default": 5,
                            },
                        },
                        "required": ["query"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "snapshot_memory",
                    "description": (
                        "Save a point-in-time snapshot of the agent's OKF "
                        "memory bundle. Use before risky operations or at "
                        "natural breakpoints."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "note": {
                                "type": "string",
                                "description": "Human-readable note about why this snapshot was taken",
                                "default": "",
                            },
                        },
                    },
                },
            },
        ]

    def handle_tool_call(self, tool_name: str, args: dict[str, Any], **kwargs: Any) -> str:
        """Dispatch tool calls from the agent to the OKF provider."""
        if self._provider is None:
            return json.dumps({"error": "OKF provider not initialized"})

        if tool_name == "search_memory":
            query = args.get("query", "")
            top_k = args.get("top_k", 5)
            if not query:
                return json.dumps({"error": "query is required"})
            try:
                results = self._provider.search(query, top_k=top_k)
                items = []
                for path, score in results:
                    concept = self._provider.agent.memory.bundle.read_concept(path)
                    if concept is None:
                        continue
                    items.append(
                        {
                            "id": concept.id,
                            "type": concept.type or "unknown",
                            "title": concept.title or concept.id,
                            "body": (concept.body or "")[:500],
                            "score": round(score, 3),
                        }
                    )
                return json.dumps({"results": items, "count": len(items)})
            except Exception as e:
                logger.warning("search_memory failed: %s", e)
                return json.dumps({"error": str(e)})

        elif tool_name == "snapshot_memory":
            note = args.get("note", "")
            try:
                assert self._provider is not None
                self._provider.snapshot(note=note)
                return json.dumps({"status": "ok", "note": note})
            except Exception as e:
                logger.warning("snapshot_memory failed: %s", e)
                return json.dumps({"error": str(e)})

        return json.dumps({"error": f"Unknown tool: {tool_name}"})

    # -- Core lifecycle (optional ABC, but we implement) -----------------------

    def sync_turn(
        self,
        user_content: str,
        assistant_content: str,
        *,
        session_id: str = "",
        messages: list[dict[str, Any]] | None = None,
    ) -> None:
        """Persist a completed turn to the OKF bundle."""
        if self._provider is None:
            return

        # Store user message
        if user_content:
            self._provider.on_memory_write("user", user_content)

        # Store assistant response
        if assistant_content:
            self._provider.on_memory_write("assistant", assistant_content)

        # Extract tool calls from messages if present
        if messages:
            for msg in messages:
                if msg.get("role") == "assistant" and "tool_calls" in msg:
                    for tc in msg["tool_calls"]:
                        func = tc.get("function", {})
                        tool_name = func.get("name", "unknown")
                        tool_args = func.get("arguments", "")
                        self._provider.on_tool_call(tool_name, {"args": tool_args}, "")

                if msg.get("role") == "tool" and "content" in msg:
                    tool_name = msg.get("name", "unknown")
                    result = msg.get("content", "")
                    self._provider.on_tool_call(tool_name, {}, result)

    def prefetch(self, query: str, *, session_id: str = "") -> str:
        """Recall relevant memory context as a formatted string."""
        if self._provider is None or not query:
            return ""

        try:
            results = self._provider.search(query, top_k=5)
        except Exception as e:
            logger.debug("prefetch search failed: %s", e)
            return ""
        if not results:
            return ""

        lines = ["## Relevant Memory (from OKF bundle)", ""]
        for path, score in results:
            try:
                concept = self._provider.agent.memory.bundle.read_concept(path)
            except Exception:
                continue
            if concept is None:
                continue
            title = concept.title or concept.id
            body_preview = (concept.body or "")[:300].replace("\n", " ")
            lines.append(f"- [{concept.type}] {title} (score: {score:.2f})")
            if body_preview:
                lines.append(f"  {body_preview}")
            lines.append("")

        return "\n".join(lines)

    def queue_prefetch(self, query: str, *, session_id: str = "") -> None:
        """Pre-warm the search cache for the next turn in a background thread."""
        if self._provider is None or not query:
            return

        provider = self._provider  # capture for mypy narrowing

        def _warm() -> None:
            try:
                provider.search(query, top_k=5)
            except Exception as e:
                logger.debug("queue_prefetch warm-up failed: %s", e)

        t = threading.Thread(target=_warm, daemon=True, name="okf-prefetch")
        t.start()

    def shutdown(self) -> None:
        """Clean shutdown — flush buffer and end session."""
        if self._provider is None:
            return
        self._provider.on_session_end(self._session_id)

    # -- Optional hooks (we implement the useful ones) ------------------------

    def on_session_start(self, session_id: str) -> None:
        """Called when Hermes starts a new session (after initialize)."""
        if self._provider is not None:
            self._provider.on_session_start(session_id)

    def on_session_end(self, messages: list[dict[str, Any]]) -> None:
        """End-of-session extraction."""
        if self._provider is None:
            return
        self._provider.on_session_end(self._session_id)

    def on_memory_write(
        self,
        action: str,
        target: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Mirror built-in memory writes to the OKF bundle."""
        if self._provider is None:
            return
        if action == "add" and target in ("memory", "user"):
            self._provider.on_memory_write(target, content)

    def system_prompt_block(self) -> str:
        """Static info injected into the system prompt."""
        return (
            "Memory is persisted via OKF (Open Knowledge Format) — "
            "a directory of markdown files with YAML frontmatter.\n"
            "Relevant memories are automatically injected into context "
            "before each turn. Use search_memory to query your OKF bundle "
            "explicitly when you need to recall past decisions, "
            "observations, or stored knowledge.\n"
            "Use snapshot_memory to save a point-in-time snapshot.\n"
            f"Bundle location: {self._hermes_home or '~/.hermes'}/okf_memory/"
        )

    # -- Config for `hermes memory setup` ------------------------------------

    def get_config_schema(self) -> list[dict[str, Any]]:
        """Fields needed for `hermes memory setup`."""
        return [
            {
                "key": "bundle_path",
                "description": "Directory where OKF memory bundle is stored",
                "required": False,
                "default": "~/.hermes/okf_memory",
            },
            {
                "key": "agent_id",
                "description": "Identifier for this agent's memory",
                "required": False,
                "default": "hermes-agent",
            },
            {
                "key": "auto_snapshot",
                "description": "Auto-save snapshots on session end",
                "required": False,
                "default": True,
                "choices": [True, False],
            },
        ]

    def save_config(self, values: dict[str, Any], hermes_home: str) -> None:
        """Write non-secret config to the Hermes config.yaml."""
        import yaml

        config_path = Path(hermes_home) / "config.yaml"
        config: dict[str, Any] = {}
        if config_path.exists():
            with open(config_path, encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}

        if "memory" not in config:
            config["memory"] = {}
        config["memory"]["provider"] = "hermes-okf"
        for key in ("bundle_path", "agent_id", "auto_snapshot"):
            if key in values:
                config["memory"][key] = values[key]

        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)


# -- Entry point for Hermes discovery ----------------------------------------

# Hermes discovers memory providers via:
# 1. `hermes_okf.memory_plugin` entry point (setuptools)
# 2. Files in ~/.hermes/plugins/ implementing MemoryProvider

# pip entry point registration (in pyproject.toml):
# [project.entry-points."hermes.memory_providers"]
# hermes-okf = "hermes_okf.memory_plugin:HermesOKFMemoryProvider"
