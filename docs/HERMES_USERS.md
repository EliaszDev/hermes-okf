# Using hermes-okf with Hermes Agent (Nous Research)

> **The official memory provider integration for Hermes Agent.**

This guide shows how to use `hermes-okf` as a **first-class memory provider** for any Hermes Agent setup. It works with your existing `~/.hermes/config.yaml` and requires no pipeline-specific code.

---

## Quick Start (Any Hermes User)

### 1. Install

```bash
pip install hermes-okf
```

### 2. Register the plugin

```bash
hermes-okf-install
```

Creates `~/.hermes/plugins/hermes-okf/` so Hermes discovers the plugin.

### 3. Configure Hermes

Edit `~/.hermes/config.yaml`:

```yaml
plugins:
  enabled:
    - hermes-okf

memory:
  provider: hermes-okf
  bundle_path: ~/.hermes/okf_memory
  agent_id: hermes-alpha
```

> **Important:** `plugins.enabled` must be a YAML list, not a string.

### 4. Run the setup wizard

```bash
hermes memory setup
```

Then start a new Hermes session to activate.

---

## Optional: Install with RAG support

```bash
pip install hermes-okf[rag]
```

For semantic search (ChromaDB vector search) over your OKF bundle.

---

## What You Get

| Feature | What It Does |
|---------|-------------|
| **Sessions** | Every Hermes session recorded as a typed concept |
| **Observations** | Hermes `memory` writes become searchable `Observation` concepts |
| **User Profiles** | Hermes `user` writes become `UserProfile` concepts |
| **Tool Registry** | Every tool auto-registered with JSON schema in OKF |
| **Decisions** | Strategic choices logged with rationale and tags |
| **Plans** | Multi-step tasks tracked with checkable progress |
| **Snapshots** | Full state save/resume for crash recovery |
| **Hot Memory** | Fast in-process buffer, flushed to cold archive automatically |
| **Search** | Full-text search over all concepts |
| **RAG** | Semantic vector search (optional, requires `[rag]` extra) |
| **Git-friendly** | `git diff` your agent's memory |
| **Model sync** | OKF config auto-updates from Hermes `config.yaml` (v0.3.7+) |

---

## The Two-Memory Model

Hermes' native memory is **hot** — small, fast, always in the system prompt. `hermes-okf` adds a **cold** archive for structured, long-term knowledge.

```
┌─────────────────────────────────────────┐
│  HERMES AGENT                           │
│                                         │
│  ┌──────────────┐    ┌────────────────┐ │
│  │  HOT MEMORY  │    │  COLD ARCHIVE  │ │
│  │              │    │                │ │
│  │ MEMORY.md    │◄──►│ hermes/        │ │
│  │ ├ 2,200 chars│    │ ├ sessions/    │ │
│  │ ├ Always hot │    │ ├ decisions/     │ │
│  │              │    │ ├ observations/  │ │
│  │ USER.md      │    │ ├ tools/         │ │
│  │ ├ 1,375 chars│    │ ├ plans/         │ │
│  │ ├ Frozen     │    │ ├ snapshots/     │ │
│  │              │    │                │ │
│  └──────────────┘    └────────────────┘ │
│                                         │
│  Hot: fast, bounded, in-prompt         │
│  Cold: structured, searchable, permanent │
└─────────────────────────────────────────┘
```

**Rule:** Hot = critical facts always in context. Cold = structured knowledge queried when needed.

---

## Hook Events

The provider fires on standard Hermes lifecycle events:

| Event | Method | OKF Action |
|-------|--------|------------|
| Session start | `on_session_start(sid)` | Creates `Session` concept, optional snapshot |
| Session end | `on_session_end(sid)` | Flushes hot buffer, ends session, snapshot |
| Memory write | `on_memory_write(target, content)` | `target="memory"` → `Observation`; `target="user"` → `UserProfile` |
| Tool call | `on_tool_call(name, args, result)` | Records `Tool-Call`, lazy-registers tool schema |
| Decision | `on_decision(text, rationale, tags)` | Creates `Decision` concept with rationale |
| Plan create | `on_plan_create(name, steps)` | Creates `Plan` concept with checkable steps |
| Plan step | `on_plan_step_complete(id, idx, result)` | Marks step complete, updates progress % |
| Plan complete | `on_plan_complete(id)` | Archives plan, flushes hot buffer, snapshot |

---

## Example: Full Session with Plans and Tools

```python
from hermes_okf import HermesOKFProvider

provider = HermesOKFProvider()

# 1. Start session
provider.on_session_start("deploy-session-001")

# 2. Create a plan
plan_id = provider.on_plan_create(
    "Deploy microservice",
    [
        "Build Docker image",
        "Push to registry",
        "Deploy to k8s",
        "Run health check",
    ]
)

# 3. Execute steps, record tool calls
provider.on_tool_call("docker_build", {"tag": "v1.2.3"}, "Built in 45s")
provider.on_plan_step_complete(plan_id, 0, "Built in 45s")

provider.on_tool_call("docker_push", {"registry": "ghcr.io"}, "Pushed 45MB")
provider.on_plan_step_complete(plan_id, 1, "Pushed 45MB")

provider.on_tool_call("k8s_deploy", {"namespace": "prod"}, "3 replicas ready")
provider.on_plan_step_complete(plan_id, 2, "3 replicas ready")

provider.on_tool_call("health_check", {"endpoint": "/health"}, "200 OK")
provider.on_plan_step_complete(plan_id, 3, "200 OK")

# 4. Record a decision
provider.on_decision(
    "Use 3 replicas for initial deploy",
    "Traffic expected to be moderate; can scale up",
    tags=["deployment", "strategy"],
)

# 5. Complete plan
provider.on_plan_complete(plan_id)

# 6. End session
provider.on_session_end("deploy-session-001")
```

Your OKF bundle now contains:
- `hermes/sessions/deploy-session-001.md` — full session record
- `hermes/plans/deploy_microservice.md` — plan with all 4 steps checked
- `hermes/decisions/3_replicas.md` — decision with rationale
- `hermes/tools/docker_build.md` — tool schema auto-registered
- `hermes/snapshots/...` — state snapshot for resume

---

## Crash Recovery

If the agent crashes mid-session, resume from the last snapshot:

```python
from hermes_okf import HermesOKFProvider

provider = HermesOKFProvider()
provider.resume()

# The agent is now restored to the exact state before the crash
# - Last session ID
# - Active plan (if any)
# - All configuration
```

---

## Search Your Memory

```python
from hermes_okf import HermesOKFProvider

provider = HermesOKFProvider()

# Full-text search
results = provider.search("Docker deployment", top_k=5)
for concept_id, score in results:
    print(f"{score:.2f}  {concept_id}")

# Tag search
for concept in provider.recall_by_tag("deployment"):
    print(concept.title)

# Build LLM context
context = provider.build_context("What did we decide about replicas?")
print(context)  # Returns system prompt + relevant memory + recent log

# Semantic search (requires RAG)
results = provider.rag_search("deployment strategies for Python services")
for r in results:
    print(f"{r['source']}: {r['content'][:100]}")
```

---

## CLI Commands

### Hermes Plugin Commands (hermes okf)

```bash
# Search
hermes okf search "deployment strategy"

# List concepts
hermes okf list --type Decision

# Show a concept (v0.3.4+)
hermes okf show config/agent
hermes okf show sessions/2026-06-14T22-14-58Z
hermes okf show sessions/2026-06-14T22-14-58Z --raw

# Snapshot
hermes okf snapshot --note "Before big deploy"

# Restore
hermes okf restore
```

### Standalone Commands (hermes-okf)

```bash
# Initialise bundle
hermes-okf init ~/.hermes/okf_memory

# Validate
hermes-okf --path ~/.hermes/okf_memory validate

# List sessions
hermes-okf --path ~/.hermes/okf_memory sessions

# List decisions
hermes-okf --path ~/.hermes/okf_memory list --subdir hermes/decisions

# Search
hermes-okf --path ~/.hermes/okf_memory search "deployment strategy"

# Graph
hermes-okf --path ~/.hermes/okf_memory graph-edges
hermes-okf --path ~/.hermes/okf_memory graph-neighbors hermes/decisions/3_replicas

# Save snapshot
hermes-okf --path ~/.hermes/okf_memory snapshot --note "Before big deploy"

# Build LLM context
hermes-okf --path ~/.hermes/okf_memory context "What did we decide?"
```

---

## Configuration Reference

| Key | Default | Description |
|-----|---------|-------------|
| `bundle_path` | `~/.hermes/okf_memory` | Where the OKF bundle lives |
| `agent_id` | `hermes` | Identifier for this agent |
| `model` | (from Hermes config) | Auto-synced from `config.yaml` (v0.3.7+) |
| `auto_snapshot` | `true` | Snapshot on session start/end |
| `snapshot_on_tool_call` | `false` | Snapshot on every tool call |
| `log_tool_calls` | `true` | Record tool calls to OKF |
| `log_decisions` | `true` | Record decisions to OKF |
| `use_hot_memory` | `true` | Use in-process buffer for fast writes |
| `hot_memory_max` | `50` | Buffer items before flush |
| `enable_rag` | `false` | Enable ChromaDB vector search |
| `rag_model` | `openai/text-embedding-3-small` | Embedding model |

---

## Comparison: Hermes Native vs. hermes-okf

| | Hermes Native | hermes-okf |
|---|---|---|
| **Format** | Flat text (`MEMORY.md`, `USER.md`) | Markdown + YAML with types |
| **Types** | ❌ None | ✅ `Decision`, `Plan`, `Tool`, `Session` |
| **Graph** | ❌ No links | ✅ Markdown links = directed edges |
| **Search** | FTS5 keyword only | ✅ Full-text + semantic (optional) |
| **Tool schemas** | ❌ In code only | ✅ Stored as readable concepts |
| **Plan tracking** | ❌ No native plans | ✅ Checkable steps with progress |
| **Resume** | ❌ No snapshots | ✅ Full state save/restore |
| **Version control** | ❌ Not git-friendly | ✅ `git diff` every decision |
| **Cross-agent** | ❌ Isolated per agent | ✅ Copy bundle, resume elsewhere |
| **Model tracking** | ❌ Static | ✅ Auto-sync from Hermes config (v0.3.7+) |

---

## Community

- **hermes-okf**: [github.com/EliaszDev/hermes-okf](https://github.com/EliaszDev/hermes-okf)
- **Hermes Agent**: [github.com/NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent)
- **Open Knowledge Format**: [cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing](https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing)

---

## License

MIT — same as Hermes Agent.
