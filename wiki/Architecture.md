# Architecture

> **How hermes-okf works under the hood.**

---

## Design Philosophy

1. **No database required** — If you can `cat` a file, you can read the memory.
2. **Agent-first** — Every API is designed for programmatic read/write by an AI agent.
3. **Human-readable** — The knowledge store is plain markdown + YAML, viewable in any editor.
4. **Standard-library lean** — Core runtime has only one dependency (`pyyaml`).
5. **Extensible** — Optional RAG, graph export, and fuzzy search via extras.

---

## Layered Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  HUMAN INTERFACE                                              │
│  ├─ hermes okf search|list|show|snapshot|restore  (Hermes CLI) │
│  ├─ hermes-okf init|validate|search|show...     (Standalone)  │
│  ├─ hermes-okf-install / hermes-okf-uninstall  (Plugin mgmt) │
├─────────────────────────────────────────────────────────────┤
│  HERMES PLUGIN LAYER (v0.3.1+)                              │
│  ├─ HermesOKFMemoryProvider  ← MemoryProvider ABC            │
│  ├─ plugin.py / cli_extension.py  ← CLI registration bridge    │
│  ├─ install_plugin.py  ← Creates ~/.hermes/plugins/hermes-okf/│
├─────────────────────────────────────────────────────────────┤
│  UNIVERSAL PROVIDER (v0.3.0+)                               │
│  ├─ HermesOKFProvider  ← Any Hermes agent can use it          │
│  ├─ HermesAgent / MemoryMixin  ← Drop-in decorators           │
│  ├─ HotMemoryBuffer  ← In-process fast write buffer           │
├─────────────────────────────────────────────────────────────┤
│  CORE OKF LAYER                                             │
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

---

## Module Responsibilities

| Module | Role | Added In |
|--------|------|----------|
| `bundle.py` | File I/O, concept CRUD, logging, graph edge extraction | v0.1.0 |
| `concept.py` | Dataclass representing a single OKF concept | v0.1.0 |
| `graph.py` | Link traversal, directory hierarchy, tag clustering, BFS traversal | v0.1.0 |
| `search.py` | Inverted index full-text search, fuzzy search | v0.1.0 |
| `validators.py` | OKF conformance checking | v0.1.0 |
| `memory.py` | Agent-level semantics: sessions, decisions, observations, tool calls | v0.1.0 |
| `agent.py` | Drop-in decorators (`@memorize_decision`, `@memorize_tool`) | v0.1.0 |
| `cli.py` | Standalone CLI entry point | v0.1.0 |
| `cli_extension.py` | Builds `hermes okf <sub>` argparse tree | v0.3.2 |
| `plugin.py` | Hermes general plugin registration bridge | v0.3.2 |
| `install_plugin.py` | Creates `~/.hermes/plugins/hermes-okf/` wrapper | **v0.4.0** |
| `memory_plugin.py` | `HermesOKFMemoryProvider` — full MemoryProvider ABC | v0.3.1 |
| `hermes_integration.py` | `HermesOKFProvider` — universal Hermes memory provider | v0.3.0 |
| `hermes.py` | `HermesAgent` — full-state agent in OKF bundle | v0.2.0 |

---

## The Two-Memory Model

Hermes' native memory is **hot** — small, fast, always in the system prompt. `hermes-okf` adds a **cold** archive for structured, long-term knowledge.

```
┌─────────────────────────────────────────────────────────────┐
│  HERMES AGENT                                               │
│                                                             │
│  ┌─────────────────────┐    ┌─────────────────────────────┐│
│  │  HOT MEMORY         │    │  LONG-TERM ARCHIVE          ││
│  │  (working memory)     │    │  (OKF bundle)               ││
│  │                     │    │                             ││
│  │  MEMORY.md          │◄──►│  config/agent.md            ││
│  │  ├─ 2,200 chars     │    │  ├─ Agent identity          ││
│  │  ├─ §-delimited     │    │  ├─ Model, system prompt    ││
│  │  ├─ Always in prompt│    │  └─ Versioned               ││
│  │                     │    │                             ││
│  │  USER.md            │◄──►│  tools/*.md                 ││
│  │  ├─ 1,375 chars     │    │  ├─ JSON schemas            ││
│  │  ├─ User profile    │    │  ├─ Descriptions            ││
│  │  └─ Frozen snapshot │    │  └─ Self-documenting        ││
│  │                     │    │                             ││
│  │                     │    │  sessions/*.md              ││
│  │                     │    │  ├─ Full session records    ││
│  │                     │    │  └─ Linked to decisions     ││
│  │                     │    │                             ││
│  │                     │    │  decisions/*.md             ││
│  │                     │    │  ├─ Strategic choices       ││
│  │                     │    │  ├─ Rationale               ││
│  │                     │    │  └─ Tagged, searchable      ││
│  │                     │    │                             ││
│  │                     │    │  plans/*.md                 ││
│  │                     │    │  ├─ Checkable steps          ││
│  │                     │    │  ├─ Progress %              ││
│  │                     │    │  └─ Archive on completion     ││
│  │                     │    │                             ││
│  │                     │    │  snapshots/*.md             ││
│  │                     │    │  └─ Full state at a point   ││
│  │                     │    │                             ││
│  │                     │    │  log.md                     ││
│  │                     │    │  └─ Chronological history     ││
│  └─────────────────────┘    └─────────────────────────────┘│
│                                                             │
│  Bridge: Hooks fire on Hermes events → write to OKF         │
│  Bridge: `build_context()` pulls OKF into Hermes prompt     │
└─────────────────────────────────────────────────────────────┘
```

**Rule of thumb:**
- **Hot memory** = critical facts that must always be in context
- **OKF archive** = structured knowledge that the agent can query when needed

---

## OKF Conformance

Hermes OKF follows the **Google Open Knowledge Format v0.1** draft spec:

- Every concept file is a `.md` with YAML frontmatter
- Frontmatter **must** contain a `type` field
- Reserved files: `index.md` (directory listing), `log.md` (agent chronology)
- Directory tree provides structural hierarchy
- Markdown links (`[label](path.md)`) are implicit directed edges
- No fixed taxonomy — types are user-defined

---

## Extension Points

- **RAG**: `examples/rag_integration.py` shows LangChain + ChromaDB loading
- **Fuzzy search**: Install `rapidfuzz` for Levenshtein distance
- **Graph export**: `GraphExtractor.to_networkx()` exports to NetworkX for analysis
- **Custom validators**: Subclass `OKFValidator` and add rules
- **Plugin installer**: `hermes-okf-install` creates the Hermes plugin wrapper; extend `install_plugin.py` for custom plugin metadata
