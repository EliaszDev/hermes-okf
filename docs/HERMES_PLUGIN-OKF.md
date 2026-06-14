# Hermes-OKF Architecture: Why Structured Memory Matters

> **How the Open Knowledge Format extends Hermes Agent's memory into a typed, traversable, long-term knowledge system.**

Hermes Agent's core memory is intentionally **bounded and curated** — two small text files (`MEMORY.md`, `USER.md`) that act like a brain's working memory. This is a feature, not a bug. It keeps the agent focused, fast, and cheap.

But working memory has limits. It can't express:
- *"This decision was caused by that observation"*
- *"This tool depends on that configuration"*
- *"This plan has 3 steps, and I'm 67% done"*
- *"What did I decide about model selection last Tuesday?"*

Hermes-OKF solves this by adding a **structured knowledge archive** that lives alongside Hermes' native memory. It doesn't replace the hot, fast working memory — it complements it.

---

## The Two-Memory Model

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
│  │  Session Search     │    │  sessions/*.md              ││
│  │  ├─ FTS5 over SQLite│    │  ├─ Full session records    ││
│  │  └─ Keyword search  │    │  ├─ Status, model, duration ││
│  │                     │    │  └─ Linked to decisions     ││
│  │                     │    │                             ││
│  │                     │    │  decisions/*.md             ││
│  │                     │    │  ├─ Strategic choices         ││
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

## Why OKF Specifically?

Hermes could use any structured format. Why Google's Open Knowledge Format?

| OKF Property | Benefit for Hermes |
|--------------|-------------------|
| **Markdown + YAML** | Hermes already reads markdown. No new parser needed. |
| **`type` field** | Maps naturally to Hermes' concept types (Decision, Plan, Tool). |
| **Markdown links** | Creates implicit graphs from Hermes' own references. |
| **Directory structure** | Mirrors Hermes' file-based architecture. |
| **No runtime required** | `"If you can cat a file, you can read OKF"` — fits Hermes' philosophy. |
| **Agent-readable** | Hermes can read and write OKF without a custom SDK. |
| **Human-editable** | Users can open any `.md` file and edit the agent's knowledge. |
| **Git-friendly** | `git diff` shows exactly what the agent learned. |
| **Standard** | Google's spec — interoperability with other OKF consumers. |

OKF is the closest thing to a *native* format for an agent that already lives in a filesystem-heavy environment.

---

## Typed Concepts: What Hermes Can't Express Today

Hermes' flat memory stores everything as text. OKF adds types:

### Before (Hermes default)
```
§
I decided to use Claude for reasoning and GPT-4o for coding
§
```

### After (OKF)
```yaml
---
type: Decision
title: Model Selection Strategy
description: Use Claude for reasoning, GPT-4o for coding
tags: [model-selection, architecture]
timestamp: 2026-06-15T10:00:00Z
---

# Decision

Use Claude for reasoning tasks and GPT-4o for coding tasks.

## Rationale

Claude shows better long-context reasoning; GPT-4o is faster for code generation.
```

The difference:
- **Type** tells Hermes this is a strategic decision, not a random observation
- **Tags** cluster it with other architecture decisions
- **Timestamp** enables temporal queries
- **Rationale** preserves *why*, not just *what*
- **Links** can connect to related tools or configurations

---

## The Knowledge Graph: From Flat to Connected

Hermes' memory entries are isolated. There's no way to express *"this tool depends on that API key, which is stored in that config, which was decided in that meeting."*

OKF builds a graph through markdown links:

```markdown
---
type: Tool
title: search_web
---

# search_web

Search the web using [Firecrawl](context/firecrawl_config.md).
Requires [OpenRouter key](config/agent.md) for rate limits.
```

```markdown
---
type: Decision
title: API Provider Choice
---

# API Provider Choice

Selected OpenRouter for [tool access](tools/search_web.md).
```

Now the graph has edges:
```
Decision(api_provider) → Tool(search_web) → Config(firecrawl)
                      → Config(agent) → Config(openrouter_key)
```

Hermes can traverse this graph programmatically to answer questions like:
- *"What tools depend on OpenRouter?"*
- *"Which decisions led to this configuration?"*
- *"What did I change that broke this tool?"*

---

## Plan Execution: Structured Task Tracking

Hermes doesn't have native plan concepts. When it does multi-step work, it's just a stream of tool calls and reasoning. There's no way to ask:
- *"What was the original plan?"*
- *"Which steps are done vs. pending?"*
- *"How far along is this task?"*

OKF adds `Plan` concepts with checkable steps:

```markdown
---
type: Plan
title: Deploy Microservice
status: active
progress: 67
steps: ["Build Docker image", "Push to registry", "Deploy to k8s"]
---

# Plan: Deploy Microservice

Created: 2026-06-15T10:00:00Z

## Steps

1. [x] Build Docker image
   → Built eliasz/myservice:v1.2.3
2. [x] Push to registry
   → Pushed to ghcr.io, 45MB
3. [ ] Deploy to k8s
   → Waiting for cluster credentials
```

Progress is tracked in frontmatter. Completed plans are archived. The agent can resume an interrupted plan by reading the `plans/` directory.

---

## State Snapshots: Resume as a Feature

Hermes' sessions are stored in SQLite (`~/.hermes/state.db`) with FTS5 search. But there's no concept of a **snapshot** — a full capture of agent state at a moment in time.

OKF snapshots save:
- Current model and system prompt
- Active session ID
- Active plan ID
- All configuration values

```json
{
  "agent_id": "hermes-alpha",
  "model": "anthropic/claude-3.5-sonnet",
  "current_session": "2026-06-15T10-00-00Z",
  "current_plan": "plans/deploy_microservice",
  "system_prompt": "You are a helpful DevOps assistant..."
}
```

Use cases:
- **Crash recovery**: restart the agent, restore from last snapshot
- **Fork an agent**: copy the bundle, change agent_id, resume with different settings
- **A/B testing**: snapshot before a change, compare outcomes
- **Audit**: every snapshot is a point-in-time record of agent state

---

## Tool Registry: Self-Documenting Agent Surface

Hermes has 60+ built-in tools, but their schemas are defined in code. There's no way for the agent to introspect its own capabilities without reading source files.

OKF stores tool definitions as concepts:

```markdown
---
type: Tool
title: run_python
description: Execute Python code and return the result.
schema: |
  {"type": "object", "properties": {"code": {"type": "string"}}, "required": ["code"]}
tags: [tool, code, execution]
---

# run_python

Execute Python code in a sandboxed environment.

## Example

```python
run_python(code="print([x**2 for x in range(10)])")
```
```

Benefits:
- **Self-documenting**: the agent can read its own tool schemas
- **Versioned**: tool changes are tracked in git
- **Shareable**: another agent can read the bundle and use the same tools
- **Auditable**: users can inspect exactly what tools the agent has access to

---

## How the Bridge Works

The Hermes-OKF bridge is a thin event mapper:

```
Hermes Event              →  OKF Action
─────────────────────────────────────────────────────────
Session starts            →  Create Session concept
                          →  Optionally save Snapshot

Memory.write(target=memory) →  Append Observation to log
                          →  Optionally create Decision concept

Memory.write(target=user)   →  Create UserProfile concept

Tool.call(name, args)     →  Record Tool-Call in log
                          →  Register tool schema if new

Plan completes            →  Create Plan concept
                          →  Mark steps complete
                          →  Archive plan

User asks: "What did      →  Search OKF by tag/title
we decide about X?"     →  Return matching Decision concepts

User asks: "Resume        →  Read last Snapshot
my work from yesterday"  →  Restore session + plan + config
```

The bridge doesn't modify Hermes' core. It listens to events and writes to OKF. Hermes remains unchanged.

---

## Known Gap: Semantic Search

Hermes-OKF uses inverted-index text search, not vector embeddings. For pure semantic similarity ("find me things *like* this idea"), you still need a vector DB.

The recommended hybrid:
- **OKF** for structured, typed, graph-linked knowledge
- **ChromaDB / Qdrant** for raw semantic search over session transcripts
- **Hermes' default memory** for hot, always-in-prompt facts

See `examples/rag_integration.py` for loading OKF into ChromaDB.

---

## Community Request: Structured Memory

Hermes GitHub issue [#346](https://github.com/NousResearch/hermes-agent/issues/346) (March 2026) explicitly requests:

> *"Hermes Agent's current memory system uses flat text files... While functional and simple, it cannot express relationships between memories, distinguish between types of knowledge, decay stale information, or perform semantic search."*

The proposed solution in the issue: **8 typed memory nodes, 6 graph edge types, hybrid vector+FTS+graph search**.

Hermes-OKF delivers the typed nodes and graph edges today. It can be extended with vector search via the optional RAG integration.

---

## Summary

| What Hermes Has | What OKF Adds | Result |
|-----------------|---------------|--------|
| Small, hot working memory | Large, structured archive | Agent remembers *and* reasons |
| Flat text entries | Typed concepts with schemas | Knowledge is searchable by type |
| Isolated memories | Markdown-linked graph | Agent follows chains of reasoning |
| Session transcripts | Session records with metadata | Cross-session recall by model, status, date |
| Tool code in repo | Tool schemas as concepts | Agent introspects its own capabilities |
| No plan tracking | Checkable steps with progress | Structured task execution |
| No state snapshots | Full state snapshots | Resume from crash, fork agents |
| SQLite session DB | Git-trackable markdown | Human-readable, auditable, versioned |

Hermes-OKF doesn't replace Hermes' memory. It **architects the knowledge** that Hermes accumulates.

---

## Further Reading

- [`HERMES_PLUGIN.md`](HERMES_PLUGIN.md) — Installation and configuration guide
- [`docs/ARCHITECTURE.md`](ARCHITECTURE.md) — OKF bundle architecture
- [`examples/full_agent.py`](../examples/full_agent.py) — Complete working example
- [Hermes Agent Memory Docs](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory)
- [Hermes Issue #346 — Structured Memory](https://github.com/NousResearch/hermes-agent/issues/346)
- [Google OKF Spec](https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing)
