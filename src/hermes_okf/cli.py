"""Command-line interface for Hermes OKF.

Provides ``hermes-okf`` CLI commands to initialise, validate, inspect,
and search OKF bundles from the terminal.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from hermes_okf.bundle import OKFBundle
from hermes_okf.graph import GraphExtractor
from hermes_okf.search import SearchIndex
from hermes_okf.validators import OKFValidator


def _init_bundle(args: argparse.Namespace) -> int:
    path = Path(args.path).expanduser().resolve()
    if path.exists() and any(path.iterdir()) and not args.force:
        print(f"Error: Directory '{path}' is not empty. Use --force to overwrite.")
        return 1
    OKFBundle(str(path))
    print(f"Initialised OKF bundle at {path}")
    return 0


def _validate(args: argparse.Namespace) -> int:
    bundle = OKFBundle(args.path)
    validator = OKFValidator(bundle)
    errors = validator.validate()
    if errors:
        print(f"Found {len(errors)} validation error(s):")
        for err in errors:
            print(f"  - {err}")
        return 1
    print("Bundle is valid.")
    return 0


def _list_concepts(args: argparse.Namespace) -> int:
    bundle = OKFBundle(args.path)
    concepts = bundle.list_concepts(args.subdir)
    if not concepts:
        print("No concepts found.")
        return 0
    for cid in concepts:
        print(cid)
    return 0


def _show_concept(args: argparse.Namespace) -> int:
    bundle = OKFBundle(args.path)
    concept = bundle.read_concept(args.concept_id)
    if concept is None:
        print(f"Concept '{args.concept_id}' not found.")
        return 1
    if args.json:
        import json as _json
        from dataclasses import asdict

        print(_json.dumps(asdict(concept), indent=2, default=str))
    else:
        print(f"ID:         {concept.id}")
        print(f"Type:       {concept.type}")
        print(f"Title:      {concept.title}")
        print(f"Tags:       {', '.join(concept.tags)}")
        print(f"Timestamp:  {concept.timestamp}")
        if concept.resource:
            print(f"Resource:   {concept.resource}")
        print()
        print(concept.body)
    return 0


def _search(args: argparse.Namespace) -> int:
    bundle = OKFBundle(args.path)
    index = SearchIndex(bundle)
    results = index.search(args.query, top_k=args.top_k)
    if not results:
        print("No results.")
        return 0
    for cid, score in results:
        print(f"{score:.2f}  {cid}")
    return 0


def _log(args: argparse.Namespace) -> int:
    bundle = OKFBundle(args.path)
    log = bundle.read_log()
    if not log:
        print("Log is empty.")
        return 0
    print(log)
    return 0


def _append_log(args: argparse.Namespace) -> int:
    bundle = OKFBundle(args.path)
    bundle.append_log(args.entry, category=args.category)
    print("Log entry added.")
    return 0


def _graph_edges(args: argparse.Namespace) -> int:
    bundle = OKFBundle(args.path)
    extractor = GraphExtractor(bundle)
    edges = extractor.get_edges()
    if not edges:
        print("No edges found.")
        return 0
    for edge in edges:
        print(f"{edge['source']} -> {edge['target']}  ({edge['context']})")
    return 0


def _graph_neighbors(args: argparse.Namespace) -> int:
    bundle = OKFBundle(args.path)
    extractor = GraphExtractor(bundle)
    neighbors = extractor.get_neighbors(args.concept_id)
    if not neighbors:
        print("No neighbors found.")
        return 0
    for n in neighbors:
        print(n)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="hermes-okf",
        description="Universal OKF-based memory system for Hermes agent",
    )
    parser.add_argument("--path", default=".", help="Path to OKF bundle (default: .)")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # init
    init_parser = subparsers.add_parser("init", help="Initialise a new OKF bundle")
    init_parser.add_argument("path", nargs="?", default=".", help="Bundle path")
    init_parser.add_argument("--force", action="store_true", help="Overwrite non-empty dir")
    init_parser.set_defaults(func=_init_bundle)

    # validate
    validate_parser = subparsers.add_parser("validate", help="Validate OKF conformance")
    validate_parser.set_defaults(func=_validate)

    # list
    list_parser = subparsers.add_parser("list", help="List concepts")
    list_parser.add_argument("--subdir", help="Filter by subdirectory")
    list_parser.set_defaults(func=_list_concepts)

    # show
    show_parser = subparsers.add_parser("show", help="Show a concept")
    show_parser.add_argument("concept_id", help="Concept ID (e.g. projects/my_project)")
    show_parser.add_argument("--json", action="store_true", help="Output as JSON")
    show_parser.set_defaults(func=_show_concept)

    # search
    search_parser = subparsers.add_parser("search", help="Search concepts")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--top-k", type=int, default=10, help="Max results")
    search_parser.set_defaults(func=_search)

    # log
    log_parser = subparsers.add_parser("log", help="Show agent log")
    log_parser.set_defaults(func=_log)

    # log-append
    log_append_parser = subparsers.add_parser("log-append", help="Append to agent log")
    log_append_parser.add_argument("entry", help="Log entry text")
    log_append_parser.add_argument("--category", default="Update", help="Entry category")
    log_append_parser.set_defaults(func=_append_log)

    # graph edges
    edges_parser = subparsers.add_parser("graph-edges", help="Show all graph edges")
    edges_parser.set_defaults(func=_graph_edges)

    # graph neighbors
    neighbors_parser = subparsers.add_parser("graph-neighbors", help="Show neighbors of a concept")
    neighbors_parser.add_argument("concept_id", help="Concept ID")
    neighbors_parser.set_defaults(func=_graph_neighbors)

    # agent snapshot
    snap_parser = subparsers.add_parser("snapshot", help="Save agent state snapshot")
    snap_parser.add_argument("--note", default="", help="Snapshot note")
    snap_parser.set_defaults(func=_snapshot)

    # agent context
    ctx_parser = subparsers.add_parser("context", help="Build LLM context from bundle")
    ctx_parser.add_argument("query", help="Query to build context around")
    ctx_parser.add_argument("--top-k", type=int, default=5, help="Relevant concepts to include")
    ctx_parser.add_argument("--agent-id", default="hermes", help="Agent ID")
    ctx_parser.set_defaults(func=_context)

    # sessions
    sess_parser = subparsers.add_parser("sessions", help="List agent sessions")
    sess_parser.set_defaults(func=_sessions)

    # plans
    plan_parser = subparsers.add_parser("plans", help="List agent plans")
    plan_parser.set_defaults(func=_plans)

    # tools
    tools_parser = subparsers.add_parser("tools", help="List registered tools")
    tools_parser.set_defaults(func=_tools)

    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0

    return int(args.func(args))


def _snapshot(args: argparse.Namespace) -> int:
    from hermes_okf.hermes import HermesAgent

    agent = HermesAgent(args.path, args.agent_id)
    agent.snapshot(note=args.note)
    print("Snapshot saved.")
    return 0


def _context(args: argparse.Namespace) -> int:
    from hermes_okf.hermes import HermesAgent

    agent = HermesAgent(args.path, args.agent_id)
    ctx = agent.build_context(args.query, top_k=args.top_k)
    print(ctx)
    return 0


def _sessions(args: argparse.Namespace) -> int:
    from hermes_okf.hermes import HermesAgent

    agent = HermesAgent(args.path, "hermes")
    for sid in agent.list_sessions():
        print(sid)
    return 0


def _plans(args: argparse.Namespace) -> int:
    bundle = OKFBundle(args.path)
    plans = bundle.list_concepts("plans")
    if not plans:
        print("No active plans.")
        return 0
    for p in plans:
        print(p)
    return 0


def _tools(args: argparse.Namespace) -> int:
    from hermes_okf.hermes import HermesAgent

    agent = HermesAgent(args.path, "hermes")
    for t in agent.list_tools():
        print(t)
    return 0


if __name__ == "__main__":
    sys.exit(main())
