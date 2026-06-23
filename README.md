# Hermes OKF (Open Knowledge Format) — Universal Memory for AI Agents

[![PyPI](https://img.shields.io/pypi/v/hermes-okf.svg?cacheSeconds=1)](https://pypi.org/project/hermes-okf/)
[![CI](https://github.com/EliaszDev/hermes-okf/actions/workflows/ci.yml/badge.svg)](https://github.com/EliaszDev/hermes-okf/actions)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OKF](https://img.shields.io/badge/OKF-v0.5.9-green.svg)](https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing)

> **The first open-source memory system built on Google's Open Knowledge Format (OKF) for the Hermes agent ecosystem. `pip install hermes-okf && hermes-okf install-plugin` — two commands and you're live. The install command auto-configures `~/.hermes/config.yaml` so `hermes memory setup` finds the plugin immediately. `hermes okf search|list|show|snapshot|restore` work out of the box.**

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
hermes-okf install-plugin
```

Expected output:
```
Installed hermes-okf plugin to /home/username/.hermes/plugins/hermes-okf
  Updated ~/.hermes/config.yaml
```

> **What this does:** Creates `~/.hermes/plugins/hermes-okf/` and auto-updates `~/.hermes/config.yaml` to add `hermes-okf` to `plugins.enabled` and set `memory.provider`. Hermes finds the plugin on next startup.

### Step 3 — Activate the memory provider

Start Hermes and select `hermes-okf` from the interactive setup:

```bash
hermes memory setup
```
# Select hermes-okf from the list

### Uninstall

To remove the plugin wrapper from Hermes:

```bash
hermes-okf uninstall-plugin
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
| 🔌 **Hermes Plugin** | `HermesOKFMemoryProvider` — native `MemoryProvider` ABC, discovered via `hermes-okf install-plugin` |
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
│  ├─ hermes-okf install-plugin / uninstall-plugin  (Plugin mgmt) │
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

### `hermes-okf install-plugin` fails

If the command is not found, make sure `hermes-okf` is installed:

```bash
pip install --upgrade hermes-okf
hermes-okf --version
# Expected: 0.5.0+
```

If `hermes-okf` itself is not in PATH, use the module form:

```bash
python -m hermes_okf.cli install-plugin
```

### `hermes memory setup` doesn't show hermes-okf

1. Make sure you ran `hermes-okf install-plugin` (creates `~/.hermes/plugins/hermes-okf/`)
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

## What's New in v0.5.0

**Critical memory provider integration fix.** Previous versions shipped the OKF CLI and plugin skeleton, but the agent-side integration was broken — `handle_tool_call()` raised `NotImplementedError`, `queue_prefetch()` was a no-op, and `system_prompt_block()` didn't instruct the agent to use memory tools. Users had to manually edit their system prompt ("soul md") to get data retrieval working.

### Fixed in v0.5.0

| Component | Before (v0.4.x) | After (v0.5.0) |
|-----------|------------------|-----------------|
| `handle_tool_call()` | ❌ Not implemented → `NotImplementedError` | ✅ Dispatches `search_memory` + `snapshot_memory` with JSON results |
| `queue_prefetch()` | ❌ No-op → no background warming | ✅ Background thread prefetch warming |
| `system_prompt_block()` | Passive ("inspect memory at...") | Active ("memories are auto-injected, use search_memory to...") |
| `prefetch()` | No error handling → crashes on broken bundles | ✅ try/except with graceful fallback |
| Tool descriptions | Generic | Descriptive ("Use when you need to recall past decisions...") |

**What this means:** A fresh `pip install hermes-okf && hermes-okf-install` now works out of the box. The agent gets told about auto-injected memories, can call `search_memory`/`snapshot_memory` tools without crashing, and prefetch is warmed in the background.

### Upgrading

```bash
pip install --upgrade hermes-okf
```

No configuration changes needed — the plugin automatically uses the new integration.

---

## Roadmap

| # | Feature | Status | Priority | Notes |
|---|---------|--------|----------|-------|
| 1 | **Hermes plugin** (`HermesOKFMemoryProvider`) | ✅ Shipped | P0 | Full `MemoryProvider` ABC; `hermes memory setup` integration |
| 2 | **Plugin installer** (`hermes-okf install-plugin`) | ✅ Shipped | P0 | One-command registration in `~/.hermes/plugins/` |
| 3 | **Unified CLI** (`hermes-okf` single entry point) | ✅ Shipped | P0 | `install-plugin`/`uninstall-plugin` subcommands replace standalone scripts |
| 3 | **Universal provider** (`HermesOKFProvider`) | ✅ Shipped | P0 | Any Hermes agent can use it out of the box |
| 4 | **Two-memory model** (hot + cold archive) | ✅ Shipped | P0 | Automatic flushing from hot buffer to OKF bundle |
| 5 | **Model sync** | ✅ Shipped | P0 | OKF config auto-updates from Hermes `config.yaml` |
| 6 | **Concept inspector** (`show` command) | ✅ Shipped | P0 | Inspect any concept with metadata + body |
| 7 | **CI/CD gating** | ✅ Shipped | P0 | Tests must pass before PyPI publish; skip duplicates |
| 8 | **Async I/O** | 🚧 Not started | P2 | All file ops are sync today. Needed for high-throughput agents. |
| 9 | **Git-backed history** | 🚧 Not started | P1 | Bundle is markdown files — `git init` works manually. No programmatic diff/rollback yet. |
| 10 | **Web viewer** | 🚧 Not started | P1 | CLI-only today. A small FastAPI/HTML viewer would unlock graph exploration. |
| 11 | **Plugin system** (custom types/validators) | 🚧 Not started | P2 | `OKFValidator` is hardcoded. No custom concept types or validator hooks. |
| 12 | **Multi-agent merge** | 🚧 Not started | P2 | Each agent is isolated. No `merge_bundles()` or conflict resolution API. |
| 13 | **Hermes orchestration** | 🚧 Not started | P3 | Single agent per bundle. No multi-agent coordinator. |

**Legend:**
- ✅ Shipped — in `hermes-okf` v0.5.0
- 🚧 Not started — on the backlog; not planned for 0.5.x

**Current focus:** v0.5.0 unifies the CLI (`install-plugin`/`uninstall-plugin` subcommands) and fixes the critical memory provider integration. Roadmap items 8–13 are for a 1.0 release.

---

## License

MIT — see [`LICENSE`](LICENSE).

---

## Acknowledgements

Built for the **Hermes agent ecosystem** and inspired by the Google Cloud Knowledge Catalog team's OKF draft specification. If you use Hermes or OKF, this library is designed to be your memory backbone.

**⭐ Star this repo if you're building agent memory systems — let's make Hermes the best agent framework out there.**
