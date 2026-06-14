# Hermes OKF (Open Knowledge Format) — Universal Memory for AI Agents

[![PyPI](https://img.shields.io/pypi/v/hermes-okf.svg)](https://pypi.org/project/hermes-okf/)
[![CI](https://github.com/EliaszDev/hermes-okf/actions/workflows/ci.yml/badge.svg)](https://github.com/EliaszDev/hermes-okf/actions)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OKF](https://img.shields.io/badge/OKF-v0.3.6-green.svg)](https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing)

> **The first open-source memory system built on Google's Open Knowledge Format (OKF) for the Hermes agent ecosystem. v0.3.6 fixes CI black formatting and publishes a clean wheel. `HermesOKFMemoryProvider` — a native Hermes Agent plugin with `MemoryProvider` ABC integration. `pip install hermes-okf` and Hermes auto-discovers it. `hermes okf search|list|show|snapshot|restore` CLI commands work out of the box.**

Hermes OKF gives your AI agent a **persistent, structured, version-controlled memory** — no database, no lock-in, just markdown + YAML on your filesystem. Every decision, observation, and project context lives in a human-readable knowledge graph that your agent can read, write, and traverse programmatically.

---

## Why Hermes OKF?

| Feature | What You Get |
|---------|-------------|
| 🧠 **Agent Memory** | Persistent decisions, observations, and tool-call history across sessions |
| 🔗 **Knowledge Graph** | Implicit graph from markdown links — no RDF, no Cypher |
| 📁 **Filesystem-First** | Plain `.md` + YAML. `cat` it, `grep` it, Git it. |
| ⚡ **Zero-DB Core** | Single dependency: `pyyaml`. Optional RAG via LangChain/ChromaDB. |
| 🔌 **Hermes Plugin** | `HermesOKFMemoryProvider` — native `MemoryProvider` ABC, auto-discovered after `pip install` |
| 🎁 **Hermes-Ready** | Drop-in decorators: `@memorize_decision`, `@memorize_tool` |
| 🔄 **Resume** | Stop and restart — the agent restores from its OKF bundle |
| 📦 **Portable** | Clone a bundle to another machine — the agent resumes instantly. |

---

## Why OKF?

[OKF (Open Knowledge Format)](https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing) is a **vendor-neutral, open specification** published by Google Cloud on June 12, 2026. It formalizes the "LLM wiki" pattern into a portable standard: every concept is a `.md` file with YAML frontmatter, and markdown links create a knowledge graph.

> *"OKF is a vendor-neutral, agent- and human-friendly standard for representing the metadata, context, and curated knowledge that modern AI systems need."* — [Sam McVeety & Amir Hormati, Google Cloud](https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing)

**Why hermes-okf chose OKF:**

| OKF Principle | What it means for agents |
|---------------|--------------------------|
| **Minimally opinionated** | Only one required field: `type`. Everything else is up to the producer. |
| **Producer/consumer independence** | A human can write a bundle; an AI agent can read it. No lock-in. |
| **Format, not platform** | No proprietary runtime, no SDK, no cloud required. Just markdown files. |
| **Human-readable** | `cat` any file and understand it. Git diffs work out of the box. |

**References:**
- [Google Cloud Blog: Introducing the Open Knowledge Format](https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing)
- [OKF Specification (GitHub)](https://github.com/GoogleCloudPlatform/knowledge-catalog)
- [Google Cloud Knowledge Catalog](https://cloud.google.com/knowledge-catalog)

---

## Quick Start

### As a Hermes Agent Plugin (Recommended)

```bash
pip install hermes-okf
```

Add to `~/.hermes/config.yaml`:

```yaml
plugins:
  enabled:
    - hermes-okf

memory:
  provider: hermes-okf
  bundle_path: ~/.hermes/okf_memory
  agent_id: hermes-alpha
```

> **Important:** `plugins.enabled` must be a YAML list, not a string. If you use `hermes config set plugins.enabled '["hermes-okf"]'`, it stores a JSON string which Hermes ignores. Edit `~/.hermes/config.yaml` directly to ensure it's a proper list.

Run the setup wizard:

```bash
hermes memory setup
```

Hermes auto-discovers the plugin via pip entry points. No code changes needed.

### As a Standalone Library

```python
from hermes_okf import HermesOKFProvider

provider = HermesOKFProvider()
provider.on_session_start("session-1")
provider.on_memory_write("user", "User prefers dark mode")
provider.on_tool_call("search_web", {"query": "Python"}, "Found 5 results")
provider.on_decision("Use Claude", "Better reasoning", tags=["model"])
provider.on_session_end("session-1")
```

---

## Hermes Plugin CLI

When installed as a Hermes plugin, these subcommands are available:

```bash
# Search your OKF memory
hermes okf search "dark mode"

# List stored concepts
hermes okf list --type Decision

# Save a snapshot
hermes okf snapshot --note "Before deployment"

# Restore from last snapshot
hermes okf restore
```

---

## Agent Integration (Memory Mixin)

> **For most Hermes users, the plugin approach above is recommended.** The decorators below are for advanced use cases or custom agent classes.

```python
from hermes_okf.agent import HermesMemoryMixin

class MyAgent(HermesMemoryMixin):
    def __init__(self):
        super().__init__("./agent_knowledge", agent_id="my-agent-v1")
        self.start_session()

    @HermesMemoryMixin.memorize_decision
    def choose_model(self, task: str) -> str:
        if "code" in task.lower():
            return "anthropic/claude-3.5-sonnet"
        return "openai/gpt-4o"

    @HermesMemoryMixin.memorize_tool
    def scrape_data(self, url: str) -> dict:
        return {"url": url, "items": 42}

# Run it
agent = MyAgent()
agent.choose_model("Write a Python script")
agent.scrape_data("https://example.com")

# Recall relevant context
context = agent.with_context("python script", top_k=3)
```

---

## Full Hermes Agent (State as OKF Bundle)

For deeper integration, use `HermesAgent` — the entire agent state lives in the OKF bundle. The agent can be stopped, restarted, and resumed from its bundle alone.

```python
from hermes_okf import HermesAgent

# Create or resume an agent
agent = HermesAgent(
    bundle_path="./hermes_agent_brain",
    agent_id="hermes-alpha",
    model="anthropic/claude-3.5-sonnet",
)

# Register tools with JSON schemas
agent.register_tool("search_web", "Search the web", schema={"type": "object", ...})

# Create and execute plans
agent.create_plan("Research AI trends", ["Search", "Summarize", "Report"])
agent.complete_step(0, result="Found 5 major trends")

# Build LLM context automatically
context = agent.build_context("What should I do next?")

# Save snapshot — resume later from this exact state
agent.snapshot()

agent.end_session()
```

The agent bundle structure:
```
hermes_agent_brain/
├── config/agent.md        # Identity, model, system prompt
├── tools/*.md             # Tool definitions with schemas
├── sessions/*.md          # Session records
├── plans/*.md             # Active plans with checkable steps
├── plans/archive/*.md     # Completed plans
├── decisions/*.md         # Strategic decisions
├── snapshots/*.md         # Full state snapshots
└── index.md / log.md      # Bundle overview and activity log
```

Read the full integration guide: [`docs/HERMES_INTEGRATION.md`](docs/HERMES_INTEGRATION.md)

For the universal provider usage, see: [`docs/HERMES_USERS.md`](docs/HERMES_USERS.md)

---

## Standalone CLI

```bash
# Initialise a new OKF bundle
hermes-okf init ./knowledge

# Validate conformance
hermes-okf validate --path ./knowledge

# List concepts
hermes-okf list --path ./knowledge

# Show a concept
hermes-okf show --path ./knowledge projects/my_project

# Search
hermes-okf search --path ./knowledge "ffmpeg GPU"

# View log
hermes-okf log --path ./knowledge

# Append to log
hermes-okf log-append --path ./knowledge "New decision made" --category Decision

# Graph inspection
hermes-okf graph-edges --path ./knowledge
hermes-okf graph-neighbors --path ./knowledge projects/my_project
```

---

## RAG Integration (Optional)

```bash
pip install hermes-okf[rag]
```

Feed your OKF bundle into LangChain + ChromaDB for vector retrieval:

```python
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import MarkdownHeaderTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

from hermes_okf.bundle import OKFBundle

bundle = OKFBundle("./my_knowledge")
loader = DirectoryLoader(
    str(bundle.root),
    glob="**/*.md",
    loader_cls=TextLoader,
    loader_kwargs={"encoding": "utf-8"},
)
docs = loader.load()

splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=[("#", "Header 1"), ("##", "Header 2")]
)
splits = [chunk for doc in docs for chunk in splitter.split_text(doc.page_content)]

vectorstore = Chroma.from_documents(
    documents=splits,
    embedding=OpenAIEmbeddings(),
    persist_directory="./chroma_okf_db",
)

# Query
retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
results = retriever.invoke("What GPU decisions did we make?")
```

See `examples/rag_integration.py` for a complete example.

---

## Architecture

```
┌─────────────────────────────────────┐
│  CLI (hermes-okf)                   │
├─────────────────────────────────────┤
│  HermesOKFMemoryProvider            │  ← Hermes plugin (v0.3.1)
│  HermesOKFProvider                  │  ← Universal provider (v0.3.0)
│  HermesAgent / MemoryMixin          │  ← Agent integration
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

Read the full architecture in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

---

## OKF Format

This library implements the **Google Open Knowledge Format (OKF) v0.1** spec:

- Every concept is a `.md` file with YAML frontmatter
- Frontmatter **must** include a `type` field
- Reserved files: `index.md` (directory), `log.md` (chronology)
- Markdown links create implicit directed edges
- Directory structure provides containment hierarchy
- Tags create cross-cutting clusters

> *"If you can `cat` a file, you can read OKF."*

---

## Project Structure

```
hermes-okf/
├── src/hermes_okf/          # Core library
│   ├── bundle.py             # OKFBundle read/write
│   ├── concept.py            # Concept dataclass
│   ├── graph.py              # Graph extraction & traversal
│   ├── search.py             # Full-text search & indexing
│   ├── validators.py         # OKF conformance checking
│   ├── memory.py             # Agent memory layer
│   ├── agent.py              # Drop-in decorators
│   ├── hermes.py             # HermesAgent full-state bundle
│   ├── hermes_integration.py # Universal HermesOKFProvider (v0.3.0)
│   ├── memory_plugin.py      # HermesOKFMemoryProvider plugin (v0.3.1)
│   └── cli.py                # CLI entry point
├── tests/                    # pytest suite
├── examples/                 # Usage examples
├── docs/                     # Architecture docs
└── .github/workflows/        # CI/CD
```

---

## Development

```bash
git clone https://github.com/EliaszDev/hermes-okf.git
cd hermes-okf
pip install -e ".[dev]"
pytest
```

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for full guidelines.

---

## Roadmap

- [x] **Hermes plugin** (`HermesOKFMemoryProvider`) — MemoryProvider ABC, auto-discovered, `hermes memory setup` integration
- [x] **Universal Hermes memory provider** (`HermesOKFProvider`) — any Hermes agent can use it
- [x] Two-memory model (hot buffer + cold OKF archive) with automatic flushing
- [x] Hermes config system integration (`~/.hermes/hermes-okf.yaml`)
- [ ] Async I/O support for high-throughput agents
- [ ] Multi-agent bundle merging and conflict resolution
- [ ] Git-backed history with automatic diff summaries
- [ ] Web viewer for knowledge graph exploration
- [ ] Plugin system for custom concept types and validators
- [ ] Integration with Hermes agent orchestration layer

---

## License

MIT — see [`LICENSE`](LICENSE).

---

## Acknowledgements

Built for the **Hermes agent ecosystem** and inspired by the Google Cloud Knowledge Catalog team's OKF draft specification. If you use Hermes or OKF, this library is designed to be your memory backbone.

**⭐ Star this repo if you're building agent memory systems — let's make Hermes the best agent framework out there.**
