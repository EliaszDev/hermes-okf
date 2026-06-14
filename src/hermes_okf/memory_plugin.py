"""Hermes Agent plugin adapter for hermes-okf.

Implements the full Hermes `MemoryProvider` ABC interface with exact
signature compatibility. Auto-discovered via pip entry point after
`pip install hermes-okf`.

Reference: https://github.com/NousResearch/hermes-agent/blob/main/agent/memory_provider.py
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from hermes_okf.hermes_integration import HermesOKFConfig, HermesOKFProvider

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
        else:
            config_kwargs["bundle_path"] = str(hermes_home_path / "okf_memory")
            config_kwargs["agent_id"] = "hermes-agent"

        config = HermesOKFConfig(**config_kwargs)
        self._provider = HermesOKFProvider(config)
        self._provider.on_session_start(session_id)

    def get_tool_schemas(self) -> list[dict[str, Any]]:
        """Return tool schemas for memory operations.

        Exposes: search_memory, snapshot_memory, restore_memory
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_memory",
                    "description": "Search the agent's OKF memory bundle for relevant concepts.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query",
                            },
                            "top_k": {
                                "type": "integer",
                                "description": "Number of results",
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
                    "description": "Save a full memory snapshot to the OKF bundle.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "note": {
                                "type": "string",
                                "description": "Snapshot note",
                                "default": "",
                            },
                        },
                    },
                },
            },
        ]

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

        results = self._provider.search(query, top_k=5)
        if not results:
            return ""

        lines = ["## Relevant Memory (from OKF bundle)", ""]
        for path, score in results:
            concept = self._provider.agent.memory.bundle.read_concept(path)
            if concept is None:
                continue
            title = concept.title or concept.id
            body_preview = (concept.body or "")[:300].replace("\n", " ")
            lines.append(f"- [{concept.type}] {title} (score: {score:.2f})")
            if body_preview:
                lines.append(f"  {body_preview}")
            lines.append("")

        return "\n".join(lines)

    def shutdown(self) -> None:
        """Clean shutdown — flush buffer and end session."""
        if self._provider is None:
            return
        self._provider.on_session_end(self._session_id)

    # -- Optional hooks (we implement the useful ones) ------------------------

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
        """Static info about the OKF memory provider."""
        return (
            "Memory is persisted via OKF (Open Knowledge Format) — "
            "a directory of markdown files with YAML frontmatter. "
            "You can inspect memory at ~/.hermes/okf_memory/"
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


# -- CLI extension (not part of ABC, but Hermes picks it up) -----------------


def register_cli(subparser: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register hermes-okf CLI subcommands under `hermes okf ...`."""
    okf_parser = subparser.add_parser("okf", help="Hermes OKF memory commands")
    okf_sub = okf_parser.add_subparsers(dest="okf_command")

    # hermes okf search <query>
    search_parser = okf_sub.add_parser("search", help="Search OKF memory")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--top-k", type=int, default=5)
    search_parser.set_defaults(func=_cli_search)

    # hermes okf list
    list_parser = okf_sub.add_parser("list", help="List OKF concepts")
    list_parser.add_argument("--type", help="Filter by type")
    list_parser.set_defaults(func=_cli_list)

    # hermes okf snapshot
    snapshot_parser = okf_sub.add_parser("snapshot", help="Save memory snapshot")
    snapshot_parser.add_argument("--note", default="", help="Snapshot note")
    snapshot_parser.set_defaults(func=_cli_snapshot)

    # hermes okf restore
    restore_parser = okf_sub.add_parser("restore", help="Restore from last snapshot")
    restore_parser.set_defaults(func=_cli_restore)


# -- CLI handlers ------------------------------------------------------------


def _cli_search(args: argparse.Namespace) -> None:
    """Handle `hermes okf search <query>`."""
    from hermes_okf import HermesOKFProvider

    provider = HermesOKFProvider()
    results = provider.search(args.query, top_k=args.top_k)
    if not results:
        print("No results found.")
        return
    for path, score in results:
        print(f"  [{score:.2f}] {path}")


def _cli_list(args: argparse.Namespace) -> None:
    """Handle `hermes okf list`."""
    from hermes_okf import HermesOKFProvider

    provider = HermesOKFProvider()
    paths = provider.agent.memory.bundle.list_concepts(subdir=None)
    if not paths:
        print("No concepts found.")
        return
    for path in paths:
        concept = provider.agent.memory.bundle.read_concept(path)
        if concept is None:
            continue
        if args.type and concept.type != args.type:
            continue
        print(f"  [{concept.type}] {concept.id}")


def _cli_snapshot(args: argparse.Namespace) -> None:
    """Handle `hermes okf snapshot`."""
    from hermes_okf import HermesOKFProvider

    provider = HermesOKFProvider()
    provider.snapshot(note=args.note)
    print("✓ Snapshot saved.")


def _cli_restore(args: argparse.Namespace) -> None:
    """Handle `hermes okf restore`."""
    from hermes_okf import HermesOKFProvider

    provider = HermesOKFProvider()
    state = provider.restore()
    if state:
        print(f"✓ Restored from: {state.get('timestamp', 'unknown')}")
    else:
        print("No snapshots found.")


# -- Entry point for Hermes discovery ----------------------------------------

# Hermes discovers memory providers via:
# 1. `hermes_okf.memory_plugin` entry point (setuptools)
# 2. Files in ~/.hermes/plugins/ implementing MemoryProvider

# pip entry point registration (in pyproject.toml):
# [project.entry-points."hermes.memory_providers"]
# hermes-okf = "hermes_okf.memory_plugin:HermesOKFMemoryProvider"
