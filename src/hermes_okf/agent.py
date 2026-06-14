"""Hermes agent hooks and decorators.

Provides drop-in decorators and mixins to wire OKF memory into a Hermes agent
without changing the agent's core logic.
"""

from __future__ import annotations

import functools
import inspect
from typing import Any, Callable, Optional

from hermes_okf.memory import HermesMemory


def _get_memory(args: tuple[Any, ...]) -> Optional[HermesMemory]:
    """Try to extract a memory object from the first positional arg (self)."""
    if not args:
        return None
    maybe_self = args[0]
    if isinstance(maybe_self, HermesMemoryMixin):
        return maybe_self.memory
    return None


def memorize_decision(
    fn: Optional[Callable[..., Any]] = None,
    *,
    memory: Optional[HermesMemory] = None,
) -> Callable[..., Any]:
    """Decorator: persist the function's return value as a Decision.

    Can be used in two ways:

    1. With an explicit memory object::

        @memorize_decision(memory=mem)
        def choose_model(task):
            ...

    2. On a method of a ``HermesMemoryMixin`` subclass — the decorator
       auto-detects ``self.memory`` at call time::

        class MyAgent(HermesMemoryMixin):
            def __init__(self):
                super().__init__("./knowledge")
                self.choose_model = self.wrap_decision(self.choose_model)

            def choose_model(self, task):
                ...
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)
            mem = memory or _get_memory(args)
            if mem is not None:
                sig = inspect.signature(func)
                bound = sig.bind(*args, **kwargs)
                bound.apply_defaults()
                args_repr = ", ".join(
                    f"{k}={v!r}" for k, v in bound.arguments.items() if k != "self"
                )
                mem.record_decision(
                    decision=f"{func.__qualname__}({args_repr}) -> {result!r}",
                    rationale=f"Called by {mem.agent_id}",
                    tags=["decision", "auto-decision", func.__name__],
                )
            return result

        return wrapper

    if fn is not None:
        return decorator(fn)
    return decorator


def memorize_observation(
    fn: Optional[Callable[..., Any]] = None,
    *,
    memory: Optional[HermesMemory] = None,
) -> Callable[..., Any]:
    """Decorator: log each call as an Observation."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)
            mem = memory or _get_memory(args)
            if mem is not None:
                sig = inspect.signature(func)
                bound = sig.bind(*args, **kwargs)
                bound.apply_defaults()
                args_repr = ", ".join(
                    f"{k}={v!r}" for k, v in bound.arguments.items() if k != "self"
                )
                mem.record_observation(
                    observation=f"{func.__qualname__}({args_repr}) -> {result!r}",
                    category="Observation",
                )
            return result

        return wrapper

    if fn is not None:
        return decorator(fn)
    return decorator


def memorize_tool(
    fn: Optional[Callable[..., Any]] = None,
    *,
    memory: Optional[HermesMemory] = None,
) -> Callable[..., Any]:
    """Decorator: log each call as a Tool-Call."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)
            mem = memory or _get_memory(args)
            if mem is not None:
                sig = inspect.signature(func)
                bound = sig.bind(*args, **kwargs)
                bound.apply_defaults()
                args_repr = ", ".join(
                    f"{k}={v!r}" for k, v in bound.arguments.items() if k != "self"
                )
                summary = f"{args_repr} -> {result!r}"
                mem.record_tool_call(func.__name__, summary[:500])
            return result

        return wrapper

    if fn is not None:
        return decorator(fn)
    return decorator


class HermesMemoryMixin:
    """Mixin class for Hermes agents that want built-in OKF memory.

    Usage::

        class MyAgent(HermesMemoryMixin):
            def __init__(self):
                super().__init__("./knowledge", agent_id="my-agent")
                # Apply decorators after super().__init__
                self.choose_model = self.wrap_decision(self.choose_model)
                self.run_scraper = self.wrap_tool(self.run_scraper)

            def choose_model(self, task: str) -> str:
                ...

            def run_scraper(self, url: str) -> dict:
                ...
    """

    def __init__(self, bundle_path: str, agent_id: str = "hermes") -> None:
        self.memory = HermesMemory(bundle_path, agent_id=agent_id)

    # ------------------------------------------------------------------
    # Convenience wrappers for use inside __init__
    # ------------------------------------------------------------------
    def wrap_decision(self, fn: Callable[..., Any]) -> Callable[..., Any]:
        return memorize_decision(fn, memory=self.memory)

    def wrap_observation(self, fn: Callable[..., Any]) -> Callable[..., Any]:
        return memorize_observation(fn, memory=self.memory)

    def wrap_tool(self, fn: Callable[..., Any]) -> Callable[..., Any]:
        return memorize_tool(fn, memory=self.memory)

    def with_context(self, query: str, top_k: int = 3) -> list[Any]:
        """Retrieve relevant context from memory for a given query."""
        return self.memory.recall(query, top_k=top_k)
