# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
