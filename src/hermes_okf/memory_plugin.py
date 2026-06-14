"""Hermes Agent plugin adapter for hermes-okf.

This module wraps HermesOKFProvider so it implements the Hermes Agent
MemoryProvider ABC interface, enabling discovery via pip entry points.

Usage (installed as a standalone plugin):

    pip install hermes-okf
    # hermes-okf is auto-discovered by Hermes' memory provider system

    # In ~/.hermes/config.yaml:
    memory:
      provider: hermes-okf
      bundle_path: ~/.hermes/okf_memory
      agent_id: hermes-alpha

    hermes memory setup  # runs post_setup() wizard if needed
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from hermes_okf.hermes_integration import HermesOKFConfig, HermesOKFProvider

# The Hermes MemoryProvider ABC interface (imported if available)
try:
    from agent.memory_provider import MemoryProvider  # type: ignore[import]
except ImportError:
    # Fallback ABC for when Hermes isn't installed (e.g., during testing)
    from abc import ABC, abstractmethod

    class MemoryProvider(ABC):  # type: ignore[no-redef]
        @abstractmethod
        def sync_turn(
            self, *, messages: list[dict], tools: list[dict] | None, **kwargs: Any
        ) -> dict:
            raise NotImplementedError

        @abstractmethod
        def prefetch(self, *, query: str, **kwargs: Any) -> list[dict]:
            raise NotImplementedError

        @abstractmethod
        def shutdown(self, **kwargs: Any) -> None:
            raise NotImplementedError


class HermesOKFMemoryProvider(MemoryProvider):
    """Hermes Agent memory provider backed by OKF (Open Knowledge Format).

    Implements the Hermes MemoryProvider ABC as a standalone plugin.
    Users install via `pip install hermes-okf` and select `provider: hermes-okf`
    in their Hermes config.
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize from Hermes config kwargs.

        Hermes passes config keys from `memory:` section as kwargs.
        """
        bundle_path = kwargs.get("bundle_path", "~/.hermes/okf_memory")
        agent_id = kwargs.get("agent_id", "hermes-agent")
        auto_snapshot = kwargs.get("auto_snapshot", True)
        log_tool_calls = kwargs.get("log_tool_calls", True)
        hot_buffer_max = kwargs.get("hot_buffer_max", 100)

        self.config = HermesOKFConfig(
            bundle_path=bundle_path,
            agent_id=agent_id,
            auto_snapshot=auto_snapshot,
            log_tool_calls=log_tool_calls,
            hot_buffer_max=hot_buffer_max,
        )
        self.provider = HermesOKFProvider(self.config)
        self._session_active = False

    # -- MemoryProvider ABC implementation ------------------------------------

    def sync_turn(
        self,
        *,
        messages: list[dict],
        tools: list[dict] | None = None,
        **kwargs: Any,
    ) -> dict:
        """Called on every Hermes turn. Stores messages and tool calls.

        Hermes calls this after each LLM interaction. We extract:
        - User/assistant messages → memory write
        - Tool calls → tool call record
        - Tool results → decision/observation
        """
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            if not content:
                continue

            # Store conversation messages as memory
            self.provider.on_memory_write(role, content)

        # Record tool calls if tools were used
        if tools:
            for tool in tools:
                name = tool.get("name", "unknown")
                args = tool.get("arguments", {})
                result = tool.get("result", "")
                self.provider.on_tool_call(name, args, result)

        return {"ok": True, "provider": "hermes-okf"}

    def prefetch(self, *, query: str, **kwargs: Any) -> list[dict]:
        """Retrieve relevant memory context for a query.

        Hermes calls this before a turn to fetch relevant past context.
        Returns top-k matching concepts from the OKF bundle.
        """
        top_k = kwargs.get("top_k", 5)
        results = self.provider.search(query, top_k=top_k)
        return [
            {
                "role": "system",
                "content": f"[{r.type}] {r.title or r.path}: {r.body[:500]}",
            }
            for r in results
        ]

    def shutdown(self, **kwargs: Any) -> None:
        """Graceful shutdown. Flushes hot buffer and ends session."""
        if self._session_active:
            session_id = kwargs.get("session_id", "default")
            self.provider.on_session_end(session_id)
            self._session_active = False

    def post_setup(self, hermes_home: Path, config: dict[str, Any]) -> None:
        """Interactive setup wizard. Called by `hermes memory setup`.

        Hermes calls this when the user runs `hermes memory setup`.
        We initialize the OKF bundle and guide the user through config.
        """
        default_bundle = hermes_home / "okf_memory"
        print("\n🧠 Hermes OKF Memory Provider Setup")
        print(f"   Default bundle path: {default_bundle}")
        print("   This will store all agent memory as markdown files.")
        print("\n   To customize, edit ~/.hermes/config.yaml:")
        print("\n   memory:")
        print("     provider: hermes-okf")
        print(f"     bundle_path: {default_bundle}")
        print(f"     agent_id: {config.get('agent_id', 'hermes-agent')}")
        print("\n   ✓ Setup complete. Run `hermes` to start.")

    # -- Session lifecycle (Hermes calls these via hooks) ----------------------

    def start_session(self, session_id: str) -> None:
        """Called when Hermes starts a new session."""
        self.provider.on_session_start(session_id)
        self._session_active = True

    def end_session(self, session_id: str) -> None:
        """Called when Hermes ends a session."""
        self.provider.on_session_end(session_id)
        self._session_active = False

    # -- CLI extension --------------------------------------------------------

    @staticmethod
    def register_cli(subparser: argparse._SubParsersAction) -> None:
        """Register hermes-okf CLI subcommands under `hermes okf ...`."""
        okf_parser = subparser.add_parser("okf", help="Hermes OKF memory commands")
        okf_sub = okf_parser.add_subparsers(dest="okf_command")

        # hermes okf search <query>
        search_parser = okf_sub.add_parser("search", help="Search OKF memory")
        search_parser.add_argument("query", help="Search query")
        search_parser.add_argument("--top-k", type=int, default=5)

        # hermes okf list
        list_parser = okf_sub.add_parser("list", help="List OKF concepts")
        list_parser.add_argument("--type", help="Filter by type")

        # hermes okf snapshot
        okf_sub.add_parser("snapshot", help="Save memory snapshot")

        # hermes okf restore
        okf_sub.add_parser("restore", help="Restore from last snapshot")


# -- Entry point for Hermes discovery ----------------------------------------

# Hermes discovers memory providers via:
# 1. `hermes_okf.memory_plugin` entry point (setuptools)
# 2. Files in ~/.hermes/plugins/ implementing MemoryProvider

# pip entry point registration (in pyproject.toml):
# [project.entry-points."hermes.memory_providers"]
# hermes-okf = "hermes_okf.memory_plugin:HermesOKFMemoryProvider"
