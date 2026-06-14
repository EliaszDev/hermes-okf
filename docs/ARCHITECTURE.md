# Architecture

## Design Philosophy

Hermes OKF is built on a few simple principles:

1. **No database required** — If you can `cat` a file, you can read the memory.
2. **Agent-first** — Every API is designed for programmatic read/write by an AI agent.
3. **Human-readable** — The knowledge store is plain markdown + YAML, viewable in any editor.
4. **Standard-library lean** — Core runtime has only one dependency (`pyyaml`).
5. **Extensible** — Optional RAG, graph export, and fuzzy search via extras.

## Layered Architecture

```
┌─────────────────────────────────────┐
│  CLI (hermes-okf)                   │  ← Human operator interface
├─────────────────────────────────────┤
│  HermesMemory / MemoryMixin         │  ← Agent integration layer
├─────────────────────────────────────┤
│  OKFBundle                          │  ← Core read/write API
│  ├── Concept (dataclass)            │
│  ├── GraphExtractor                 │
│  ├── SearchIndex                    │
│  └── OKFValidator                   │
├─────────────────────────────────────┤
│  Filesystem (markdown + YAML)       │  ← Persistent storage
└─────────────────────────────────────┘
```

## Module Responsibilities

| Module | Role |
|--------|------|
| `bundle.py` | File I/O, concept CRUD, logging, graph edge extraction |
| `concept.py` | Dataclass representing a single OKF concept |
| `graph.py` | Link traversal, directory hierarchy, tag clustering, BFS traversal, networkx export |
| `search.py` | Inverted index full-text search, fuzzy search, custom predicate filtering |
| `validators.py` | OKF conformance checking (required frontmatter, `type` field) |
| `memory.py` | Agent-level semantics: sessions, decisions, observations, tool calls, context recall |
| `agent.py` | Drop-in decorators (`@memorize_decision`, `@memorize_tool`, `@memorize_observation`) |
| `cli.py` | `argparse` CLI for init, validate, show, search, log, graph inspection |

## OKF Conformance

Hermes OKF follows the **Google Open Knowledge Format v0.1** draft spec:

- Every concept file is a `.md` with YAML frontmatter
- Frontmatter **must** contain a `type` field
- Reserved files: `index.md` (directory listing), `log.md` (agent chronology)
- Directory tree provides structural hierarchy
- Markdown links (`[label](path.md)`) are implicit directed edges
- No fixed taxonomy — types are user-defined

## Extension Points

- **RAG**: `examples/rag_integration.py` shows LangChain + ChromaDB loading
- **Fuzzy search**: Install `rapidfuzz` for Levenshtein distance
- **Graph export**: `GraphExtractor.to_networkx()` exports to NetworkX for analysis
- **Custom validators**: Subclass `OKFValidator` and add rules
