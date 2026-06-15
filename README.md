# Hermes OKF (Open Knowledge Format) — Universal Memory for AI Agents

[![PyPI](https://img.shields.io/pypi/v/hermes-okf.svg)](https://pypi.org/project/hermes-okf/)
[![CI](https://github.com/EliaszDev/hermes-okf/actions/workflows/ci.yml/badge.svg)](https://github.com/EliaszDev/hermes-okf/actions)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OKF](https://img.shields.io/badge/OKF-v0.4.4-green.svg)](https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing)

> **The first open-source memory system built on Google's Open Knowledge Format (OKF) for the Hermes agent ecosystem. `pip install hermes-okf && hermes-okf-install` — two commands and you're live. The install command auto-configures `~/.hermes/config.yaml` so `hermes memory setup` finds the plugin immediately. `hermes okf search|list|show|snapshot|restore` work out of the box.**

Hermes OKF gives your AI agent a **persistent, structured, version-controlled memory** — no database, no lock-in, just markdown + YAML on your filesystem. Every decision, observation, and project context lives in a human-readable knowledge graph that your agent can read, write, and traverse programmatically.

---

## Table of Contents

- [Quick Start: Install as Hermes Plugin](#quick-start-install-as-hermes-plugin)
- [Hermes Plugin CLI Commands](#hermes-plugin-cli-commands)
- [Standalone CLI](#standalone-cli)
- [Why OKF?](#why-okf)
- [Architecture](#architecture)
- [Agent Integration](#agent-integration)
- [RAG Integration (Optional)](#rag-integration-optional)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [Roadmap](#roadmap)

---

## Quick Start: Install as Hermes Plugin

### Step 1 — Install from PyPI

```bash
pip install hermes-okf
```

### Step 2 — Register the plugin in Hermes

Hermes discovers plugins from the `~/.hermes/plugins/` directory. Run the install command to create the plugin wrapper:

```bash
hermes-okf-install
```

Expected output:
```
Installed hermes-okf plugin to /home/username/.hermes/plugins/hermes-okf
  Run 'hermes memory setup' to activate
```

> **What this does:** Creates `~/.hermes/plugins/hermes-okf/` and auto-updates `~/.hermes/config.yaml` to add `hermes-okf` to `plugins.enabled` and set `memory.provider`. Hermes finds the plugin on next startup.

### Step 3 — Start Hermes

```bash
hermes
```

The plugin activates on first session start. Your OKF bundle is created at `~/.hermes/okf_memory/` automatically.

**Optional:** Run the setup wizard to customize bundle path and agent ID:

```bash
hermes memory setup
```

### Uninstall

To remove the plugin wrapper from Hermes:

```bash
hermes-okf-uninstall
```

This removes `~/.hermes/plugins/hermes-okf/` but does not delete your OKF bundle.

---

## Hermes Plugin CLI Commands

When installed as a Hermes plugin, these subcommands are available under `hermes okf`:

```bash
# Search your OKF memory
hermes okf search "dark mode"

# List stored concepts (optionally filter by type)
hermes okf list --type Decision

# Show full content of a specific concept
hermes okf show config/agent
hermes okf show sessions/2026-06-14T22-14-58Z
hermes okf show sessions/2026-06-14T22-14-58Z --raw  # metadata stripped

# Save a snapshot
hermes okf snapshot --note "Before deployment"

# Restore from last snapshot
hermes okf restore
```

The `show` command displays the full concept with YAML frontmatter and markdown body, making it easy to inspect any piece of your agent's memory.

---

## Standalone CLI

Even without the Hermes plugin, you can use `hermes-okf` as a standalone knowledge management tool:

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

# Save snapshot
hermes-okf snapshot --path ./knowledge --note "Before deploy"

# Build LLM context
hermes-okf context --path ./knowledge "What should I prioritize?"

# List sessions, plans, tools
hermes-okf sessions --path ./knowledge
hermes-okf plans --path ./knowledge
hermes-okf tools --path ./knowledge
```

---

## Why Hermes OKF?

| Feature | What You Get |
|---------|-------------|
| 🧠 **Agent Memory** | Persistent decisions, observations, and tool-call history across sessions |
| 🔗 **Knowledge Graph** | Implicit graph from markdown links — no RDF, no Cypher |
| 📁 **Filesystem-First** | Plain `.md` + YAML. `cat` it, `grep` it, Git it. |
| ⚡ **Zero-DB Core** | Single dependency: `pyyaml`. Optional RAG via LangChain/ChromaDB. |
| 🔌 **Hermes Plugin** | `HermesOKFMemoryProvider` — native `MemoryProvider` ABC, discovered via `hermes-okf-install` |
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

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  HUMAN INTERFACE                                              │
│  ├─ hermes okf search|list|show|snapshot|restore  (Hermes CLI) │
│  ├─ hermes-okf init|validate|search|show...     (Standalone)  │
│  ├─ hermes-okf-install / hermes-okf-uninstall  (Plugin mgmt) │
├─────────────────────────────────────────────────────────────┤
│  HERMES PLUGIN LAYER                                          │
│  ├─ HermesOKFMemoryProvider  ← MemoryProvider ABC implementation│
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

Read the full architecture in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

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

For the full HermesAgent (state-as-bundle), see [`docs/HERMES_INTEGRATION.md`](docs/HERMES_INTEGRATION.md).
For the universal provider usage, see [`docs/HERMES_USERS.md`](docs/HERMES_USERS.md).

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

## Development

```bash
git clone https://github.com/EliaszDev/hermes-okf.git
cd hermes-okf
pip install -e ".[dev]"
pytest
```

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for full guidelines.

---

## Troubleshooting

### `hermes-okf-install: command not found`

The script is installed in your Python environment's `bin/` directory, which may not be in PATH. Use the full path:

```bash
# Find your Python environment
which python
# Then run:
/path/to/python -m hermes_okf.install_plugin
```

Or if using a virtual environment:
```bash
source /path/to/venv/bin/activate
hermes-okf-install
```

### `hermes memory setup` doesn't show hermes-okf

1. Make sure you ran `hermes-okf-install` (creates `~/.hermes/plugins/hermes-okf/`)
2. Check the plugin directory exists:
   ```bash
   ls ~/.hermes/plugins/hermes-okf/
   # Should show: __init__.py  plugin.yaml
   ```
3. Ensure `plugins.enabled` in `~/.hermes/config.yaml` is a YAML list:
   ```yaml
   plugins:
     enabled:
       - hermes-okf
   ```

### `hermes okf show` shows wrong model

As of v0.3.7, `HermesOKFMemoryProvider.initialize()` reads the actual Hermes model from `config.yaml` (top-level `model` or `llm.model`) and syncs it into the OKF `config/agent` concept. If you see an old model, restart your Hermes session to trigger re-initialization.

### OKF bundle not found

```bash
hermes-okf init ~/.hermes/okf_memory
```

### Windows: filename errors

Hermes-OKF uses Windows-safe filenames (`2026-06-15T10-30-00Z` instead of `2026-06-15T10:30:00Z`). If you see errors with older versions, upgrade:

```bash
pip install --upgrade hermes-okf
```

---

## Roadmap

- [x] **Hermes plugin** (`HermesOKFMemoryProvider`) — MemoryProvider ABC, `hermes memory setup` integration
- [x] **Plugin installer** (`hermes-okf-install`) — one-command registration in `~/.hermes/plugins/`
- [x] **Universal Hermes memory provider** (`HermesOKFProvider`) — any Hermes agent can use it
- [x] Two-memory model (hot buffer + cold OKF archive) with automatic flushing
- [x] Hermes config system integration (`~/.hermes/hermes-okf.yaml`)
- [x] Model sync — OKF config concept auto-updates from Hermes `config.yaml`
- [x] `show` command — inspect any concept with metadata
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
