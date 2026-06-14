"""Hermes CLI extension for hermes-okf.

This module provides ``register_cli(subparser)`` which builds the
``hermes okf <subcommand>`` argparse tree.

When used via the general Hermes plugin system (``hermes_agent.plugins``
entry point), ``register_cli`` is passed the ``okf`` parser directly and
adds subparsers to it. When used via the memory-provider convention-based
discovery (``plugins/memory/<name>/cli.py``), it receives the same
``plugin_parser`` shape.

Usage::

    hermes okf search <query>
    hermes okf list [--type TYPE]
    hermes okf snapshot [--note NOTE]
    hermes okf restore
"""

from __future__ import annotations

import argparse


def register_cli(subparser: argparse.ArgumentParser) -> None:
    """Build the ``hermes okf`` argparse subcommand tree.

    Called by the plugin CLI registration system during argparse setup.
    The *subparser* is already the parser for ``hermes okf``.
    """
    okf_sub = subparser.add_subparsers(dest="okf_command")

    # hermes okf search <query>
    search_parser = okf_sub.add_parser("search", help="Search OKF memory")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--top-k", type=int, default=5)
    search_parser.set_defaults(func=_cli_search)

    # hermes okf list
    list_parser = okf_sub.add_parser("list", help="List OKF concepts")
    list_parser.add_argument("--type", help="Filter by type")
    list_parser.set_defaults(func=_cli_list)

    # hermes okf show <path> [--raw]
    show_parser = okf_sub.add_parser("show", help="Show full content of an OKF concept")
    show_parser.add_argument("path", help="Concept path (e.g. config/agent, sessions/2026-06-14T22-14-58Z)")
    show_parser.add_argument("--raw", action="store_true", help="Print raw markdown without metadata")
    show_parser.set_defaults(func=_cli_show)

    # hermes okf snapshot
    snapshot_parser = okf_sub.add_parser("snapshot", help="Save memory snapshot")
    snapshot_parser.add_argument("--note", default="", help="Snapshot note")
    snapshot_parser.set_defaults(func=_cli_snapshot)

    # hermes okf restore
    restore_parser = okf_sub.add_parser("restore", help="Restore from last snapshot")
    restore_parser.set_defaults(func=_cli_restore)

    # Default when no subcommand is given — argparse will print its own error
    # (no func set on the parent parser; subparsers handle their own dispatch)


def _cli_search(args: argparse.Namespace) -> None:
    """Handle ``hermes okf search <query>``."""
    from hermes_okf import HermesOKFProvider

    provider = HermesOKFProvider()
    results = provider.search(args.query, top_k=args.top_k)
    if not results:
        print("No results found.")
        return
    for path, score in results:
        print(f"  [{score:.2f}] {path}")


def _cli_list(args: argparse.Namespace) -> None:
    """Handle ``hermes okf list``."""
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


def _cli_show(args: argparse.Namespace) -> None:
    """Handle ``hermes okf show <path>``."""
    from hermes_okf import HermesOKFProvider

    provider = HermesOKFProvider()
    concept = provider.agent.memory.bundle.read_concept(args.path)
    if concept is None:
        print(f"Concept not found: {args.path}")
        return

    if args.raw:
        print(concept.body)
    else:
        print(f"\n[{concept.type}] {concept.id}")
        if concept.metadata:
            print("Metadata:")
            for k, v in concept.metadata.items():
                print(f"  {k}: {v}")
        print("---")
        print(concept.body)


def _cli_snapshot(args: argparse.Namespace) -> None:
    """Handle ``hermes okf snapshot``."""
    from hermes_okf import HermesOKFProvider

    provider = HermesOKFProvider()
    provider.snapshot(note=args.note)
    print("✓ Snapshot saved.")


def _cli_restore(args: argparse.Namespace) -> None:
    """Handle ``hermes okf restore``."""
    from hermes_okf import HermesOKFProvider

    provider = HermesOKFProvider()
    state = provider.restore()
    if state:
        print(f"✓ Restored from: {state.get('timestamp', 'unknown')}")
    else:
        print("No snapshots found.")
