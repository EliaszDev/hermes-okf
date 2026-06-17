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
┌─────────────────────────────────────────────────────────────┐
│  HUMAN INTERFACE                                              │
│  ├─ hermes okf search|list|show|snapshot|restore  (Hermes CLI) │
│  ├─ hermes-okf init|validate|search|show...     (Standalone)  │
│  ├─ hermes-okf install-plugin / uninstall-plugin  (Plugin mgmt) │
├─────────────────────────────────────────────────────────────┤
│  HERMES PLUGIN LAYER                                          │
│  ├─ HermesOKFMemoryProvider  ← MemoryProvider ABC            │
│  ├─ plugin.py / cli_extension.py  ← CLI registration bridge    │
│  ├─ install_plugin.py  ← Creates ~/.hermes/plugins/hermes-okf/│
├─────────────────────────────────────────────────────────────┤
│  UNIVERSAL PROVIDER                                           │
│  ├─ HermesOKFProvider  ← Any Hermes agent can use it          │
│  ├─ HermesAgent / MemoryMixin  ← Drop-in decorators           │
│  ├─ HotMemoryBuffer  ← In-process fast write buffer           │
├─────────────────────────────────────────────────────────────┤
│  CORE OKF LAYER                                               │
│  ├─ OKFBundle  ← File I/O, concept CRUD, logging            │
│  ├─ Concept  ← Dataclass: type, title, body, metadata         │
│  ├─ GraphExtractor  ← Link traversal, tag clustering          │
│  ├─ SearchIndex  ← Full-text + fuzzy search                 │
│  └─ OKFValidator  ← Conformance checking                      │
├─────────────────────────────────────────────────────────────┤
│  PERSISTENCE                                                  │
│  └─ Filesystem (markdown + YAML frontmatter)                  │
└─────────────────────────────────────────────────────────────┘
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
| `cli_extension.py` | Builds `hermes okf <sub>` argparse tree for Hermes plugin integration |
| `plugin.py` | Hermes general plugin registration bridge (`register(ctx)`) |
| `install_plugin.py` | Creates `~/.hermes/plugins/hermes-okf/` wrapper for Hermes discovery |
| `memory_plugin.py` | `HermesOKFMemoryProvider` — full MemoryProvider ABC implementation |
| `hermes_integration.py` | `HermesOKFProvider` — universal Hermes memory provider |
| `hermes.py` | `HermesAgent` — full-state agent whose entire state lives in an OKF bundle |

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
- **Plugin installer**: `hermes-okf install-plugin` creates the Hermes plugin wrapper; extend `install_plugin.py` for custom plugin metadata
