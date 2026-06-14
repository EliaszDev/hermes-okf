# Hermes OKF — Universal Memory for AI Agents

[![CI](https://github.com/EliaszDev/hermes-okf/actions/workflows/ci.yml/badge.svg)](https://github.com/EliaszDev/hermes-okf/actions)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OKF](https://img.shields.io/badge/OKF-v0.1-green.svg)](https://cloud.google.com/knowledge-catalog)

> **The first open-source memory system built on Google's Open Knowledge Format (OKF) for the Hermes agent ecosystem.**

Hermes OKF gives your AI agent a **persistent, structured, version-controlled memory** — no database, no lock-in, just markdown + YAML on your filesystem. Every decision, observation, and project context lives in a human-readable knowledge graph that your agent can read, write, and traverse programmatically.

---

## Why Hermes OKF?

| Feature | What You Get |
|---------|-------------|
| 🧠 **Agent Memory** | Persistent decisions, observations, and tool-call history across sessions |
| 🔗 **Knowledge Graph** | Implicit graph from markdown links — no RDF, no Cypher |
| 📁 **Filesystem-First** | Plain `.md` + YAML. `cat` it, `grep` it, Git it. |
| ⚡ **Zero-DB Core** | Single dependency: `pyyaml`. Optional RAG via LangChain/ChromaDB. |
| 🎁 **Hermes-Ready** | Drop-in decorators: `@memorize_decision`, `@memorize_tool` |
| 📦 **Portable** | Clone a bundle to another machine — the agent resumes instantly. |

---

## Quick Start

```bash
pip install hermes-okf
```

```python
from hermes_okf.bundle import OKFBundle

# Create a knowledge bundle
bundle = OKFBundle("./my_knowledge")

# Store a project concept
bundle.write_concept(
    "projects/my_project",
    body="# My Project\n\nDescribe your project here.",
    type="Project",
    title="My Project",
    tags=["ml", "data", "gpu"],
    resource="https://github.com/YOUR_USERNAME/my-project",
)

# Log a decision
bundle.append_log("Switched from TensorFlow to PyTorch for better ecosystem support", category="Decision")

# Search by tag
for concept in bundle.search_by_tag("gpu"):
    print(concept.title)

# Inspect the graph
for edge in bundle.get_graph_edges():
    print(f"{edge['source']} -> {edge['target']}")
```

---

## Agent Integration (Memory Mixin)

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

## CLI

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
│  HermesMemory / MemoryMixin         │  ← Agent integration
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
