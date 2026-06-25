# Hermes OKF (Open Knowledge Format) — Universal Memory for AI Agents

[![PyPI](https://img.shields.io/pypi/v/hermes-okf.svg?cacheSeconds=1)](https://pypi.org/project/hermes-okf/)
[![CI](https://github.com/EliaszDev/hermes-okf/actions/workflows/ci.yml/badge.svg)](https://github.com/EliaszDev/hermes-okf/actions)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OKF](https://img.shields.io/badge/OKF-v0.5.9-green.svg)](https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing)

> **The first open-source memory system built on Google's Open Knowledge Format (OKF) for the Hermes agent ecosystem.** Persistent, structured, version-controlled memory — no database, no lock-in, just markdown + YAML on your filesystem. Every decision, observation, and project context lives in a human-readable knowledge graph that your agent can read, write, and traverse programmatically.

---

## Table of Contents

- [Why Hermes OKF?](#why-hermes-okf)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Hermes Plugin CLI](#hermes-plugin-cli)
- [Standalone CLI](#standalone-cli)
- [Why OKF?](#why-okf)
- [Agent Integration](#agent-integration)
- [RAG Integration (Optional)](#rag-integration-optional)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [Roadmap](#roadmap)

---

## Why Hermes OKF?

| Feature | What You Get |
|---------|-------------|
| **Agent Memory** | Persistent decisions, observations, and tool-call history across sessions |
| **Knowledge Graph** | Implicit graph from markdown links — no RDF, no Cypher |
| **Filesystem-First** | Plain `.md` + YAML. `cat` it, `grep` it, Git it. |
| **Zero-DB Core** | Single dependency: `pyyaml`. Optional RAG via LangChain/ChromaDB. |
| **Hermes Plugin** | Native `MemoryProvider` ABC, discovered via `hermes-okf install-plugin` |
| **Hermes-Ready** | Drop-in decorators: `@memorize_decision`, `@memorize_tool` |
| **Resume** | Stop and restart — the agent restores from its OKF bundle |
| **Portable** | Clone a bundle to another machine — the agent resumes instantly |
| **Config Validator** | `hermes-okf validate-config` — 15 checks, catches 80% of setup issues |
| **Git History** | Opt-in `GitOKFBundle` — auto-commit on every session, diff, revert |

---

## Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│  HUMAN INTERFACE                                                     │
│  ├─ hermes okf search|list|show|snapshot|restore    (Hermes CLI)   │
│  ├─ hermes-okf init|validate|search|show...         (Standalone)   │
│  ├─ hermes-okf install-plugin|uninstall-plugin      (Plugin mgmt)  │
│  └─ hermes-okf validate-config                      (Diagnostics)  │
├────────────────────────────────────────────────────────────────────┤
│  HERMES PLUGIN LAYER                                                 │
│  ├─ HermesOKFMemoryProvider  ← MemoryProvider ABC implementation    │
│  ├─ plugin.py / cli_extension.py  ← CLI registration bridge         │
│  └─ install_plugin.py  ← Creates ~/.hermes/plugins/hermes-okf/     │
├────────────────────────────────────────────────────────────────────┤
│  UNIVERSAL PROVIDER                                                  │
│  ├─ HermesOKFProvider  ← Any Hermes agent can use it               │
│  ├─ HermesAgent / MemoryMixin  ← Drop-in decorators               │
│  ├─ HotMemoryBuffer  ← In-process fast write buffer               │
│  └─ ConfigValidator  ← 15-check Hermes plugin diagnostics          │
├────────────────────────────────────────────────────────────────────┤
│  CORE OKF LAYER                                                      │
│  ├─ OKFBundle  ← File I/O, concept CRUD, logging                 │
│  ├─ GitOKFBundle  ← Optional Git-backed history (auto-commit)      │
│  ├─ Concept  ← Dataclass: type, title, body, metadata              │
│  ├─ GraphExtractor  ← Link traversal, tag clustering               │
│  ├─ SearchIndex  ← Full-text + fuzzy search                      │
│  └─ OKFValidator  ← Conformance checking                           │
├────────────────────────────────────────────────────────────────────┤
│  PERSISTENCE                                                         │
│  └─ Filesystem (markdown + YAML frontmatter)                       │
└────────────────────────────────────────────────────────────────────┘
```

- Full architecture: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- Config validator: [`docs/CONFIG_VALIDATOR.md`](docs/CONFIG_VALIDATOR.md)
- Git history: [`docs/GIT_HISTORY.md`](docs/GIT_HISTORY.md)

---

## Quick Start

### Step 1 — Install from PyPI

```bash
pip install hermes-okf
```

### Step 2 — Register the plugin

```bash
hermes-okf install-plugin
```

Expected output:
```
Installed hermes-okf plugin to /home/username/.hermes/plugins/hermes-okf
  Updated ~/.hermes/config.yaml
```

> This creates `~/.hermes/plugins/hermes-okf/` and auto-updates `~/.hermes/config.yaml` to add `hermes-okf` to `plugins.enabled` and set `memory.provider`.

### Step 3 — Validate the setup

```bash
hermes-okf validate-config
```

Runs 15 checks in 5 seconds. If everything passes, you'll see:

```
✅ hermes-okf v0.5.9 — all critical checks passed
Hermes should discover hermes-okf on next startup.
Run 'hermes' to start.
```

### Step 4 — Activate the memory provider

```bash
hermes memory setup
# Select hermes-okf from the list
```

### Uninstall

```bash
hermes-okf uninstall-plugin
```

Removes the plugin from Hermes but keeps your OKF bundle.

---

## Hermes Plugin CLI

When installed as a Hermes plugin, these subcommands are available under `hermes okf`:

```bash
# Search your OKF memory
hermes okf search "dark mode"

# List stored concepts
hermes okf list --type Decision

# Show full content of a concept
hermes okf show config/agent
hermes okf show sessions/2026-06-14T22-14-58Z
hermes okf show sessions/2026-06-14T22-14-58Z --raw

# Save a snapshot
hermes okf snapshot --note "Before deployment"

# Restore from last snapshot
hermes okf restore
```

---

## Standalone CLI

Use `hermes-okf` as a standalone knowledge management tool:

```bash
# Validate Hermes plugin configuration
hermes-okf validate-config

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
hermes-okf log --path ./knowledge --git          # Git history
hermes-okf log --path ./knowledge --git --oneline # Compact view

# Show diff between commits
hermes-okf diff --path ./knowledge HEAD~1
hermes-okf diff --path ./knowledge HEAD~5..HEAD

# Revert to previous state
hermes-okf revert --path ./knowledge HEAD~1

# Append to log
hermes-okf log-append --path ./knowledge "New decision" --category Decision

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

## Why OKF?

[OKF (Open Knowledge Format)](https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing) is a **vendor-neutral, open specification** published by Google Cloud on June 12, 2026. It formalizes the "LLM wiki" pattern into a portable standard: every concept is a `.md` file with YAML frontmatter, and markdown links create a knowledge graph.

> *"OKF is a vendor-neutral, agent- and human-friendly standard for representing the metadata, context, and curated knowledge that modern AI systems need."* — [Sam McVeety & Amir Hormati, Google Cloud](https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing)

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

## Agent Integration

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

agent = MyAgent()
agent.choose_model("Write a Python script")
agent.scrape_data("https://example.com")

# Recall relevant context
context = agent.with_context("python script", top_k=3)
```

- Full integration: [`docs/HERMES_INTEGRATION.md`](docs/HERMES_INTEGRATION.md)
- Universal provider: [`docs/HERMES_USERS.md`](docs/HERMES_USERS.md)

---

## RAG Integration (Optional)

```bash
pip install hermes-okf[rag]
```

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

```bash
pip install --upgrade hermes-okf
hermes-okf --version
# Expected: 0.5.9+
```

Or use the module form:
```bash
python -m hermes_okf.cli install-plugin
```

### `hermes memory setup` doesn't show hermes-okf

1. Run `hermes-okf validate-config` first — it catches 80% of setup issues in 5 seconds
2. Check `~/.hermes/plugins/hermes-okf/` exists:
   ```bash
   ls ~/.hermes/plugins/hermes-okf/
   # Should show: __init__.py  plugin.yaml
   ```
3. Ensure `plugins.enabled` is a YAML list:
   ```yaml
   plugins:
     enabled:
       - hermes-okf
   ```

### `hermes okf show` shows wrong model

As of v0.3.7, `HermesOKFMemoryProvider.initialize()` reads the Hermes model from `config.yaml` and syncs it into the OKF `config/agent` concept on every session start. Restart Hermes to trigger re-initialization.

### OKF bundle not found

```bash
hermes-okf init ~/.hermes/okf_memory
```

### Windows: filename errors

Hermes-OKF uses Windows-safe filenames (`2026-06-15T10-30-00Z`). Upgrade:

```bash
pip install --upgrade hermes-okf
```

---

## Roadmap

| # | Feature | Status | Priority | Notes |
|---|---------|--------|----------|-------|
| 1 | **Hermes plugin** (`HermesOKFMemoryProvider`) | ✅ Shipped | P0 | Full `MemoryProvider` ABC; `hermes memory setup` |
| 2 | **Plugin installer** (`hermes-okf install-plugin`) | ✅ Shipped | P0 | One-command registration |
| 3 | **Unified CLI** (single entry point) | ✅ Shipped | P0 | Subcommands replace standalone scripts |
| 4 | **Universal provider** (`HermesOKFProvider`) | ✅ Shipped | P0 | Any Hermes agent can use it |
| 5 | **Two-memory model** (hot + cold archive) | ✅ Shipped | P0 | Automatic flushing from hot buffer to OKF bundle |
| 6 | **Model sync** | ✅ Shipped | P0 | OKF config auto-updates from Hermes `config.yaml` |
| 7 | **Concept inspector** (`show` command) | ✅ Shipped | P0 | Inspect any concept with metadata + body |
| 8 | **CI/CD gating** | ✅ Shipped | P0 | Tests must pass before PyPI publish |
| 9 | **Config Validator** (`validate-config`) | ✅ Shipped | P0 | 15 checks, 5 seconds, exit 0/1 |
| 10 | **Git-backed history** | ✅ Shipped | P1 | `GitOKFBundle` — auto-commit, diff, revert |
| 11 | **Async I/O** | 🚧 Not started | P2 | All file ops are sync today |
| 12 | **Web viewer** | 🚧 Not started | P1 | CLI-only today. A small FastAPI/HTML viewer |
| 13 | **Plugin system** (custom types) | 🚧 Not started | P2 | `OKFValidator` is hardcoded |
| 14 | **Multi-agent merge** | 🚧 Not started | P2 | Each agent is isolated |
| 15 | **Hermes orchestration** | 🚧 Not started | P3 | Single agent per bundle |

**Legend:**
- ✅ Shipped — in `hermes-okf` v0.5.9
- 🚧 Not started — on the backlog for a 1.0 release

**Current focus:** v0.5.9 completes the "Git + Diagnostics" milestone. v0.5.8+ performance (search index, bundle compression) is next.

---

## License

MIT — see [`LICENSE`](LICENSE).

---

## Acknowledgements

Built for the **Hermes agent ecosystem** and inspired by the Google Cloud Knowledge Catalog team's OKF draft specification. If you use Hermes or OKF, this library is designed to be your memory backbone.

**⭐ Star this repo if you're building agent memory systems.**
