"""Hermes-native memory provider for Hermes Agent (Nous Research).

This module makes hermes-okf a **first-class memory provider** for any Hermes
agent. It works with Hermes' native config system, session lifecycle, and
tool-calling interface.

No pipeline-specific code. No FIFA references. Just a clean, generic
integration that any Hermes user can drop in.

Usage for any Hermes user::

    # In ~/.hermes/config.yaml or hermes-okf.yaml
    memory:
      provider: hermes-okf
      bundle_path: ~/.hermes/okf_memory

    # Or from Python:
    from hermes_okf.hermes_integration import HermesOKFProvider
    provider = HermesOKFProvider()
    provider.on_session_start("session-123")
    provider.on_memory_write("user", "User prefers dark mode")
    provider.on_tool_call("search_web", {"query": "Python"}, "Found 5 results")
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from hermes_okf import HermesAgent
from hermes_okf.search import SearchIndex

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_BUNDLE_PATH = Path("~/.hermes/okf_memory").expanduser()
DEFAULT_CONFIG_PATH = Path("~/.hermes/hermes-okf.yaml").expanduser()


@dataclass
class HermesOKFConfig:
    """Configuration for the Hermes-OKF memory provider.

    Reads from environment variables first, then from Hermes' config
    directory, then falls back to defaults.
    """

    bundle_path: str = str(DEFAULT_BUNDLE_PATH)
    agent_id: str = "hermes"
    model: str = ""
    auto_snapshot: bool = True
    snapshot_on_tool_call: bool = False
    log_tool_calls: bool = True
    log_decisions: bool = True
    use_hot_memory: bool = True
    hot_memory_max: int = 50  # Max items in hot buffer before flush
    enable_rag: bool = False
    rag_model: str = "openai/text-embedding-3-small"

    @classmethod
    def from_hermes_config(cls, path: str | None = None) -> HermesOKFConfig:
        """Load config from Hermes' config directory or env vars.

        Looks for:
        1. Environment variables (HERMES_OKF_*)
        2. ~/.hermes/hermes-okf.yaml
        3. ~/.hermes/config.yaml → plugins.hermes_okf
        4. Defaults
        """
        # Environment overrides
        kwargs: dict[str, Any] = {}
        if os.environ.get("HERMES_OKF_BUNDLE_PATH"):
            kwargs["bundle_path"] = os.environ["HERMES_OKF_BUNDLE_PATH"]
        if os.environ.get("HERMES_OKF_AGENT_ID"):
            kwargs["agent_id"] = os.environ["HERMES_OKF_AGENT_ID"]
        if os.environ.get("HERMES_OKF_AUTO_SNAPSHOT"):
            kwargs["auto_snapshot"] = os.environ["HERMES_OKF_AUTO_SNAPSHOT"].lower() in (
                "1",
                "true",
                "yes",
            )
        if os.environ.get("HERMES_OKF_ENABLE_RAG"):
            kwargs["enable_rag"] = os.environ["HERMES_OKF_ENABLE_RAG"].lower() in (
                "1",
                "true",
                "yes",
            )

        # Config file
        config_file = Path(path) if path else DEFAULT_CONFIG_PATH
        if config_file.exists():
            try:
                import yaml

                raw = yaml.safe_load(config_file.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    kwargs.update({k: raw[k] for k in raw if k in cls.__dataclass_fields__})
            except Exception:
                pass  # Fallback to defaults

        # Hermes main config
        hermes_config = Path("~/.hermes/config.yaml").expanduser()
        if hermes_config.exists() and not kwargs.get("bundle_path"):
            try:
                import yaml

                raw = yaml.safe_load(hermes_config.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    plugin = raw.get("plugins", {}).get("hermes_okf", {})
                    kwargs.update({k: plugin[k] for k in plugin if k in cls.__dataclass_fields__})
            except Exception:
                pass

        return cls(**kwargs)


# ---------------------------------------------------------------------------
# Hot Memory Buffer
# ---------------------------------------------------------------------------


@dataclass
class HotMemoryBuffer:
    """In-process hot memory layer for fast writes.

    Flushes to the OKF cold archive on:
    - Session end
    - Buffer reaching max size
    - Explicit flush()
    """

    max_items: int = 50
    items: list[dict[str, Any]] = field(default_factory=list)

    def push(self, **item: Any) -> None:
        """Add an item to the hot buffer."""
        self.items.append(
            {
                **item,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    def flush(self, agent: HermesAgent) -> list[dict[str, Any]]:
        """Write all buffered items to the OKF cold archive."""
        if not self.items:
            return []
        for item in self.items:
            kind = item.pop("_kind", "observation")
            if kind == "decision":
                agent.memory.record_decision(
                    decision=item.get("decision", ""),
                    rationale=item.get("rationale", ""),
                    tags=item.get("tags", []),
                )
            elif kind == "tool_call":
                agent.memory.record_tool_call(
                    tool_name=item.get("tool_name", ""),
                    result_summary=item.get("result", "")[:500],
                )
            elif kind == "observation":
                agent.memory.record_observation(
                    observation=item.get("content", ""),
                    category=item.get("category", "Observation"),
                )
        flushed = self.items[:]
        self.items.clear()
        return flushed


# ---------------------------------------------------------------------------
# Hermes Native Memory Provider
# ---------------------------------------------------------------------------


class HermesOKFProvider:
    """Hermes-native memory provider backed by OKF.

    This is the **main entry point** for any Hermes user who wants to use
    hermes-okf as their memory backend. It implements the memory provider
    interface that Hermes expects:

    - `on_session_start(session_id)`
    - `on_session_end(session_id)`
    - `on_memory_write(target, content)`
    - `on_tool_call(tool_name, args, result)`
    - `on_decision(decision, rationale)`
    - `on_plan_complete(plan, steps)`

    The provider auto-initializes from Hermes config, creates the OKF
    bundle if it doesn't exist, and manages hot/cold memory automatically.

    Args:
        config: Optional :class:`HermesOKFConfig`. If not provided, reads
            from Hermes config files automatically.

    Example::

        provider = HermesOKFProvider()
        provider.on_session_start("my-session")
        provider.on_memory_write("memory", "User prefers Python")
        provider.on_tool_call("search", {"query": "Python"}, "Found 5")
        provider.on_decision("Use Claude", "Better reasoning")
        provider.on_session_end("my-session")
    """

    def __init__(self, config: HermesOKFConfig | None = None) -> None:
        self.config = config or HermesOKFConfig.from_hermes_config()
        self.agent = HermesAgent(
            bundle_path=self.config.bundle_path,
            agent_id=self.config.agent_id,
            model=self.config.model or "openai/gpt-4o",
        )
        self.hot = HotMemoryBuffer(max_items=self.config.hot_memory_max)
        self._search_index = SearchIndex(self.agent.memory.bundle)

        # Ensure the bundle has the Hermes-native structure
        self._ensure_directories()

    # -- Bundle structure -------------------------------------------------

    def _ensure_directories(self) -> None:
        """Create the Hermes-native directory layout."""
        dirs = (
            "hermes/sessions",
            "hermes/tools",
            "hermes/plans",
            "hermes/plans/archive",
            "hermes/decisions",
            "hermes/observations",
            "hermes/snapshots",
        )
        for d in dirs:
            Path(self.agent.memory.bundle.root, d).mkdir(parents=True, exist_ok=True)

    # -- Session hooks ----------------------------------------------------

    def on_session_start(self, session_id: str) -> None:
        """Called when Hermes starts a new session."""
        self.agent.start_session(session_id)
        self.agent.memory.record_observation(f"Session {session_id} started", category="Session")
        if self.config.auto_snapshot:
            self.agent.snapshot(note=f"Session {session_id} start")

    def on_session_end(self, session_id: str) -> None:
        """Called when Hermes ends a session."""
        # Flush hot buffer before ending
        self._flush_hot()
        self.agent.memory.record_observation(f"Session {session_id} ended", category="Session")
        self.agent.end_session()
        if self.config.auto_snapshot:
            self.agent.snapshot(note=f"Session {session_id} end")

    # -- Memory hooks -----------------------------------------------------

    def on_memory_write(self, target: str, content: str) -> None:
        """Called when Hermes writes to MEMORY.md or USER.md.

        Maps Hermes' flat memory to typed OKF concepts:
        - target="memory" → Observation in hermes/observations/
        - target="user" → UserProfile in hermes/observations/
        """
        if target == "memory":
            self.hot.push(
                _kind="observation",
                content=content,
                category="HermesMemory",
            )
        elif target == "user":
            self.agent.memory.bundle.write_concept(
                f"hermes/observations/user_profile_{self._now_date()}",
                body=f"# User Profile\n\n{content}",
                type="UserProfile",
                title="User Profile",
                tags=["user", "profile"],
            )
        self._maybe_flush()

    # -- Tool hooks -------------------------------------------------------

    def on_tool_call(self, tool_name: str, args: dict[str, Any], result: str) -> None:
        """Called when Hermes invokes a tool."""
        if self.config.log_tool_calls:
            self.hot.push(
                _kind="tool_call",
                tool_name=tool_name,
                args=args,
                result=result,
            )
            # Ensure tool is registered in OKF
            self._ensure_tool_registered(tool_name)
        if self.config.snapshot_on_tool_call:
            self.agent.snapshot(note=f"Tool: {tool_name}")
        self._maybe_flush()

    # -- Decision hooks ---------------------------------------------------

    def on_decision(
        self, decision: str, rationale: str = "", tags: list[str] | None = None
    ) -> None:
        """Called when the agent makes a strategic decision."""
        if self.config.log_decisions:
            self.hot.push(
                _kind="decision",
                decision=decision,
                rationale=rationale,
                tags=tags or ["decision"],
            )
        self._maybe_flush()

    # -- Plan hooks -------------------------------------------------------

    def on_plan_create(self, plan_name: str, steps: list[str]) -> str:
        """Called when the agent creates a multi-step plan."""
        plan_id = self.agent.create_plan(plan_name, steps)
        return plan_id

    def on_plan_step_complete(self, plan_id: str, step_index: int, result: str = "") -> None:
        """Called when a plan step completes."""
        self.agent.complete_step(step_index, result=result)

    def on_plan_complete(self, plan_id: str) -> None:
        """Called when all plan steps are done."""
        self.agent.memory.record_observation(f"Plan completed: {plan_id}", category="Plan")
        self.agent.archive_plan(plan_id)
        self._flush_hot()
        if self.config.auto_snapshot:
            self.agent.snapshot(note=f"Plan complete: {plan_id}")

    # -- Tool registry ----------------------------------------------------

    def register_tool(
        self, name: str, description: str, schema: dict[str, Any] | None = None
    ) -> None:
        """Register a tool definition in OKF."""
        self.agent.register_tool(name, description, schema=schema)

    def _ensure_tool_registered(self, name: str) -> None:
        """Lazy-register a tool if not already in the registry."""
        if not self.agent.get_tool(name):
            self.agent.register_tool(name, description="Tool used by Hermes agent")

    # -- State management -------------------------------------------------

    def snapshot(self, note: str = "") -> None:
        """Save a full agent state snapshot."""
        self._flush_hot()
        self.agent.snapshot(note=note)

    def restore(self) -> dict[str, Any]:
        """Restore agent from last snapshot."""
        self._flush_hot()
        return self.agent.restore()

    def resume(self) -> None:
        """Resume the agent from last snapshot."""
        self.restore()
        self.agent.memory.record_observation("Resumed from snapshot", category="Resume")

    # -- Hot/cold memory --------------------------------------------------

    def _maybe_flush(self) -> None:
        """Flush hot buffer if it exceeds max size."""
        if len(self.hot.items) >= self.hot.max_items:
            self._flush_hot()

    def _flush_hot(self) -> None:
        """Write all hot buffer items to the OKF cold archive."""
        self.hot.flush(self.agent)

    # -- Search & recall --------------------------------------------------

    def search(self, query: str, top_k: int = 10) -> list[tuple[str, float]]:
        """Search the OKF bundle for relevant concepts."""
        self._search_index.invalidate()
        return self._search_index.search(query, top_k=top_k)

    def recall_by_tag(self, tag: str) -> list[Any]:
        """Return all concepts with a given tag."""
        return self.agent.memory.recall_by_tag(tag)

    def build_context(self, query: str, top_k: int = 5) -> str:
        """Build a context string for an LLM call from the OKF bundle."""
        return self.agent.build_context(query, top_k=top_k)

    # -- RAG (optional) ---------------------------------------------------

    def rag_search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Semantic search over the OKF bundle using ChromaDB.

        Requires: pip install hermes-okf[rag]
        """
        try:
            from langchain_chroma import Chroma
            from langchain_openai import OpenAIEmbeddings
        except ImportError as exc:
            raise ImportError(
                "RAG requires hermes-okf[rag]. Install: pip install hermes-okf[rag]"
            ) from exc

        # Lazy index
        persist_dir = Path(self.config.bundle_path) / ".chroma"
        if not persist_dir.exists():
            self._build_rag_index()

        vectorstore = Chroma(
            persist_directory=str(persist_dir),
            embedding_function=OpenAIEmbeddings(model=self.config.rag_model),
        )
        retriever = vectorstore.as_retriever(search_kwargs={"k": top_k})
        results = retriever.invoke(query)
        return [
            {"source": r.metadata.get("source", ""), "content": r.page_content[:500]}
            for r in results
        ]

    def _build_rag_index(self) -> None:
        """Build the ChromaDB vector index from the OKF bundle."""
        from langchain.text_splitter import MarkdownHeaderTextSplitter
        from langchain_chroma import Chroma
        from langchain_community.document_loaders import DirectoryLoader, TextLoader
        from langchain_openai import OpenAIEmbeddings

        loader = DirectoryLoader(
            self.config.bundle_path,
            glob="**/*.md",
            loader_cls=TextLoader,
            loader_kwargs={"encoding": "utf-8"},
        )
        docs = loader.load()
        splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[("#", "Header 1"), ("##", "Header 2")]
        )
        splits = [chunk for doc in docs for chunk in splitter.split_text(doc.page_content)]
        Chroma.from_documents(
            documents=splits,
            embedding=OpenAIEmbeddings(model=self.config.rag_model),
            persist_directory=str(Path(self.config.bundle_path) / ".chroma"),
        )

    # -- Helpers ----------------------------------------------------------

    @staticmethod
    def _now_date() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # -- Direct access to underlying agent --------------------------------

    def __getattr__(self, name: str) -> Any:
        return getattr(self.agent, name)


# ---------------------------------------------------------------------------
# Singleton helper
# ---------------------------------------------------------------------------

_provider: HermesOKFProvider | None = None


def get_provider() -> HermesOKFProvider:
    """Return the singleton HermesOKFProvider."""
    global _provider
    if _provider is None:
        _provider = HermesOKFProvider()
    return _provider
