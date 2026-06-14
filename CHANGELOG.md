# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-06-15

### Added
- `HermesAgent` — full agent whose entire state lives in an OKF bundle (config, tools, sessions, plans, snapshots, resume)
- `HermesAgent.register_tool()` — tool definitions stored as OKF concepts with JSON schemas
- `HermesAgent.create_plan()` / `complete_step()` / `archive_plan()` — structured plan execution tracked in OKF
- `HermesAgent.snapshot()` / `restore()` — full state snapshots for crash recovery and resume
- `HermesAgent.build_context()` — auto-assembles LLM context from system prompt, active plan, memory, log, and tools
- `HermesAgent.list_sessions()` / `recall_session()` — cross-session memory
- New CLI commands: `snapshot`, `context`, `sessions`, `plans`, `tools`
- `docs/HERMES_INTEGRATION.md` — architecture guide for deep integration
- `examples/full_agent.py` — complete Hermes agent example with tool registry, plans, and resume
- `tests/test_hermes.py` — full test coverage for `HermesAgent`

## [0.1.0] - 2026-06-15

### Added
- Initial release of `hermes-okf`
- `OKFBundle` — core bundle manager with read/write, logging, graph edge extraction
- `Concept` — dataclass for OKF concepts
- `GraphExtractor` — link traversal, directory hierarchy, tag clustering, BFS traversal, NetworkX export
- `SearchIndex` — inverted-index full-text search, fuzzy search, custom predicate filtering
- `OKFValidator` — OKF v0.1 conformance validation
- `HermesMemory` — agent memory layer: sessions, decisions, observations, tool calls, context recall
- `HermesMemoryMixin` — drop-in decorators for agent classes
- CLI (`hermes-okf`) — init, validate, show, search, log, graph commands
- RAG integration example (LangChain + ChromaDB)
- Full test suite with pytest
- GitHub Actions CI for Python 3.10–3.13
