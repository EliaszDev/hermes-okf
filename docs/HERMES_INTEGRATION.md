# Hermes-OKF Integration

This document explains how Hermes OKF becomes the native memory and state system for a Hermes agent.

## Philosophy: The Bundle IS the Agent

In a traditional agent architecture, state is scattered across:
- In-memory variables (lost on restart)
- Databases (require schema migrations, lock-in)
- Log files (unstructured, hard to query)
- Configuration files (static, not versioned)

Hermes-OKF unifies all of this into **one OKF bundle** that IS the agent's brain:

```
hermes_agent_brain/
├── index.md              # Bundle overview
├── log.md                # Chronological agent activity
├── config/
│   └── agent.md          # Identity, model, system prompt
├── tools/
│   ├── search_web.md     # Tool definitions with schemas
│   └── run_python.md
├── sessions/
│   ├── 2026-06-15T10:00:00Z.md
│   └── 2026-06-15T14:30:00Z.md
├── plans/
│   ├── research_ai_trends.md
│   └── archive/
│       └── completed_plan.md
├── decisions/
│   └── model_strategy.md
├── projects/
│   └── viral_clip_pipeline.md
├── context/
│   └── openrouter_models.md
└── snapshots/
    └── 2026-06-15T14-30-00Z.md
```

## Key Integration Points

### 1. Agent Configuration

The agent's identity is stored in `config/agent.md`:

```yaml
---
type: AgentConfig
title: hermes-alpha Configuration
model: anthropic/claude-3.5-sonnet
system_prompt: You are a helpful, autonomous Hermes agent.
version: "0.1.0"
---
```

When the agent restarts, it reads this file and resumes with the same identity.

### 2. Tool Registry

Tools are not just Python functions — they are OKF concepts with JSON schemas:

```yaml
---
type: Tool
title: search_web
description: Search the web for current information.
schema: '{"type": "object", "properties": {"query": {"type": "string"}}}'
tags: [tool]
---
```

This means:
- The agent can self-document its capabilities
- Other agents can read the bundle and understand the tool surface
- Tool schemas are versioned alongside the agent

### 3. Session Lifecycle

Every session is a concept under `sessions/`:

```yaml
---
type: Session
title: Session 2026-06-15T10:00:00Z
agent_id: hermes-alpha
model: anthropic/claude-3.5-sonnet
status: completed
---
```

Sessions are linked to decisions, observations, and plans via the OKF graph. The agent can recall any previous session and its context.

### 4. Plan Execution

Plans are structured tasks with checkable steps:

```markdown
# Plan: Research AI trends

Created: 2026-06-15T10:00:00Z

## Steps

1. [x] Search for latest AI news
2. [x] Summarize key findings
3. [ ] Write a concise report
```

As the agent completes steps, the OKF file is updated. Progress is tracked in frontmatter. Completed plans are archived to `plans/archive/`.

### 5. State Snapshots

At any point, the agent can save a full state snapshot:

```json
{
  "agent_id": "hermes-alpha",
  "model": "anthropic/claude-3.5-sonnet",
  "current_session": "2026-06-15T10:00:00Z",
  "current_plan": "plans/research_ai_trends",
  "system_prompt": "..."
}
```

This enables:
- **Resume after crash**: restart the agent, it restores from last snapshot
- **Fork an agent**: copy the bundle, change the agent_id, resume
- **Audit trails**: every snapshot is a point-in-time record

### 6. LLM Context Building

Before every LLM call, the agent builds a context string from the bundle:

```python
context = agent.build_context(
    query="What should I do next?",
    top_k=5,
)
```

This includes:
- System prompt
- Active plan
- Relevant memory (via search)
- Recent activity log
- Available tools with schemas

## Resume Pattern

```python
# Agent dies here

# Later, restart
agent = HermesAgent("./hermes_agent_brain", "hermes-alpha")
# Automatically restores:
# - config (model, system prompt)
# - last session ID
# - current plan
# - all tool definitions
```

## Multi-Agent Coordination

Multiple agents can share a bundle or have linked bundles:

```python
# Agent A creates a plan
agent_a = HermesAgent("./shared_brain", "agent-a")
agent_a.create_plan("Shared task", ["Step 1", "Step 2"])

# Agent B reads the plan and continues
agent_b = HermesAgent("./shared_brain", "agent-b")
agent_b.complete_step(0, result="Done by agent-b")
```

## Why This Matters

| Without OKF | With Hermes-OKF |
|-------------|-------------------|
| State lives in RAM | State lives in versioned markdown |
| Restart = blank slate | Restart = resume from last snapshot |
| Tool schemas in code | Tool schemas in the knowledge graph |
| Logs are opaque | Logs are structured, linkable, searchable |
| One agent per process | Multiple agents share one brain |
| Hard to audit | Every decision is a git-trackable concept |

## Next Steps

- See `examples/full_agent.py` for a complete working example
- See `examples/hermes_integration.py` for the decorator-based approach
- Use `hermes-okf context --path ./brain "query"` to preview LLM context from CLI
