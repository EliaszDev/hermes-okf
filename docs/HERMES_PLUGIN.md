# Hermes Plugin: hermes-okf Memory Provider

> **Plug structured, persistent, graph-based memory into Hermes Agent.**

This guide shows how to wire `hermes-okf` into Hermes' memory provider system so your agent gets typed concepts, knowledge graphs, plan tracking, and cross-session state persistence alongside Hermes' native curated memory.

---

## What This Plugin Does

Hermes' default memory is **small, hot, and curated** — two flat text files (`MEMORY.md`, `USER.md`) injected into every system prompt. It works like a brain's working memory.

`hermes-okf` adds a **structured knowledge layer** — like a long-term memory archive with:

- **Typed concepts** (`Decision`, `Plan`, `Tool`, `Session`, `AgentConfig`)
- **Knowledge graph** — relationships via markdown links
- **Plan execution** — checkable steps, progress tracking, archiving
- **State snapshots** — save and resume full agent state
- **Tool registry** — JSON schemas stored as readable concepts
- **Cross-session recall** — searchable, traversable session history

**The two systems coexist.** Hermes keeps its fast, bounded working memory. OKF handles structured, long-term knowledge.

---

## Installation

### 1. Install hermes-okf

```bash
pip install hermes-okf
```

Or install from source:

```bash
git clone https://github.com/EliaszDev/hermes-okf.git
cd hermes-okf
pip install -e .
```

### 2. Create the Hermes-OKF configuration

Create `~/.hermes/hermes-okf.json`:

```json
{
  "bundle_path": "~/.hermes/okf_memory",
  "agent_id": "hermes",
  "auto_snapshot": true,
  "snapshot_on_plan_complete": true,
  "log_decisions": true,
  "log_tool_calls": true
}
```

| Option | Description |
|--------|-------------|
| `bundle_path` | Where the OKF knowledge bundle lives |
| `agent_id` | Identifier for this agent instance |
| `auto_snapshot` | Save state snapshot after every session |
| `snapshot_on_plan_complete` | Snapshot when a plan finishes |
| `log_decisions` | Record model/strategy decisions to OKF |
| `log_tool_calls` | Record tool usage to OKF |

### 3. Register the plugin in Hermes config

Edit `~/.hermes/config.yaml`:

```yaml
memory:
  memory_enabled: true
  user_profile_enabled: true

plugins:
  hermes_okf:
    enabled: true
    config_path: ~/.hermes/hermes-okf.json

hooks:
  on_session_start:
    - hermes_okf.session_start
  on_session_end:
    - hermes_okf.session_end
  on_memory_write:
    - hermes_okf.memory_write
  on_tool_call:
    - hermes_okf.tool_call
  on_plan_complete:
    - hermes_okf.plan_complete
```

> **Note:** Hermes' hook system is event-based. If your Hermes version doesn't support custom hooks yet, use the Python integration below.

---

## Python Integration (Recommended)

If Hermes' native hook system isn't available in your version, use this Python bridge to connect Hermes events to OKF.

### Create `~/.hermes/skills/hermes-okf-bridge.py`

```python
"""Hermes-OKF bridge skill — wires Hermes events into OKF memory."""

import os
import json
from pathlib import Path
from hermes_okf.hermes import HermesAgent

# Load config
CONFIG_PATH = Path(os.environ.get("HERMES_HOME", "~/.hermes")).expanduser() / "hermes-okf.json"

if CONFIG_PATH.exists():
    config = json.loads(CONFIG_PATH.read_text())
else:
    config = {
        "bundle_path": str(Path("~/.hermes/okf_memory").expanduser()),
        "agent_id": "hermes",
    }

# Initialize the OKF-backed agent
agent = HermesAgent(
    bundle_path=config["bundle_path"],
    agent_id=config["agent_id"],
)

# --- Hermes hook handlers ---

def on_session_start(session_id: str, **kwargs) -> None:
    """Called when Hermes starts a new session."""
    agent.start_session(session_id)
    if config.get("auto_snapshot"):
        agent.snapshot(note=f"Session {session_id} started")


def on_session_end(session_id: str, **kwargs) -> None:
    """Called when Hermes ends a session."""
    agent.end_session()
    if config.get("auto_snapshot"):
        agent.snapshot(note=f"Session {session_id} ended")


def on_memory_write(target: str, content: str, **kwargs) -> None:
    """Called when Hermes writes to MEMORY.md or USER.md.

    Maps flat Hermes memory entries into typed OKF concepts.
    """
    if target == "memory":
        # Agent's personal notes → Observation concept
        agent.memory.record_observation(content, category="Memory")
    elif target == "user":
        # User profile → UserProfile concept
        agent.memory.bundle.write_concept(
            f"context/user_profile_{agent._now_date()}",
            body=f"# User Profile\n\n{content}",
            type="UserProfile",
            title="User Profile",
            tags=["user", "profile"],
        )


def on_tool_call(tool_name: str, args: dict, result: str, **kwargs) -> None:
    """Called when Hermes invokes a tool."""
    if not config.get("log_tool_calls"):
        return
    agent.memory.record_tool_call(
        tool_name,
        f"args={args} -> {result[:200]}",
    )
    # Also ensure tool is registered in OKF
    if not agent.get_tool(tool_name):
        agent.register_tool(
            name=tool_name,
            description=f"Tool used by Hermes agent",
        )


def on_plan_complete(plan: str, steps: list, **kwargs) -> None:
    """Called when Hermes completes a multi-step plan."""
    plan_id = agent.create_plan(plan, steps)
    for i, _ in enumerate(steps):
        agent.complete_step(i, result="Completed via Hermes")
    if config.get("snapshot_on_plan_complete"):
        agent.snapshot(note=f"Plan completed: {plan}")


def on_decision(decision: str, rationale: str, **kwargs) -> None:
    """Called when Hermes makes a strategic decision."""
    if not config.get("log_decisions"):
        return
    agent.memory.record_decision(decision, rationale=rationale)


# --- Hermes skill interface ---
# Hermes can call these via /skill hermes-okf-bridge or RPC

SKILL_NAME = "hermes-okf-bridge"
SKILL_VERSION = "0.2.0"


def skill_status():
    """Return OKF bundle status."""
    return {
        "bundle_path": config["bundle_path"],
        "sessions": len(agent.list_sessions()),
        "tools": len(agent.list_tools()),
        "plans": len(agent.memory.bundle.list_concepts("plans")),
    }


def skill_context(query: str, top_k: int = 5):
    """Build LLM context from OKF for a given query."""
    return agent.build_context(query, top_k=top_k)


def skill_recall(tag: str):
    """Recall all OKF concepts with a given tag."""
    return [c.id for c in agent.memory.recall_by_tag(tag)]


def skill_snapshot(note: str = ""):
    """Save a manual snapshot."""
    agent.snapshot(note=note)
    return {"snapshot": "saved"}


def skill_restore():
    """Restore agent from last snapshot."""
    meta = agent.restore()
    return {"restored": meta}
```

### Register the skill in Hermes

Create `~/.hermes/skills/hermes-okf-bridge/skill.yaml`:

```yaml
name: hermes-okf-bridge
version: 0.2.0
description: Bridge Hermes events to OKF structured memory
author: EliaszDev
entry: hermes-okf-bridge.py
commands:
  - name: status
    description: Show OKF bundle status
    handler: skill_status
  - name: context
    description: Build LLM context from OKF
    handler: skill_context
    args:
      - query
      - top_k
  - name: recall
    description: Recall concepts by tag
    handler: skill_recall
    args:
      - tag
  - name: snapshot
    description: Save state snapshot
    handler: skill_snapshot
    args:
      - note
  - name: restore
    description: Restore from last snapshot
    handler: skill_restore
```

Now use it from Hermes CLI or messaging:

```bash
/hermes-okf-bridge status
/hermes-okf-bridge context "What did we decide about GPU?"
/hermes-okf-bridge recall decision
/hermes-okf-bridge snapshot "Before big refactor"
/hermes-okf-bridge restore
```

---

## How Hermes Memory Maps to OKF

| Hermes Action | OKF Concept | Where It Goes |
|---------------|-------------|---------------|
| `memory(action="add", target="memory")` | `Observation` | `log.md` + `context/observations/` |
| `memory(action="add", target="user")` | `UserProfile` | `context/user_profile_*.md` |
| `session_search` result | `Session` | `sessions/*.md` |
| Tool invocation | `Tool` | `tools/*.md` + `log.md` |
| Strategic choice | `Decision` | `decisions/*.md` |
| Multi-step task | `Plan` | `plans/*.md` |
| Agent config | `AgentConfig` | `config/agent.md` |

---

## Daily Usage Workflow

### 1. Start Hermes — OKF auto-initializes

```bash
hermes
# OKF bundle is created at ~/.hermes/okf_memory on first run
```

### 2. Hermes learns something — OKF records it

```
You: Remember that I prefer Python over Go
Hermes: memory(action="add", target="user", content="User prefers Python over Go")
OKF: Writes UserProfile concept
```

### 3. Hermes uses a tool — OKF logs it

```
Hermes: search_web(query="Python 3.14 features")
OKF: Records Tool-Call in log.md + registers search_web schema in tools/
```

### 4. Hermes makes a plan — OKF tracks it

```
You: Research and summarize AI trends
Hermes: Creates Plan concept in OKF with 3 steps
# As Hermes completes each step, OKF updates progress
```

### 5. End session — OKF snapshots state

```bash
/hermes-okf-bridge snapshot "End of day checkpoint"
# Full agent state saved to snapshots/YYYY-MM-DDTHH-MM-SSZ.md
```

### 6. Resume tomorrow — restore from OKF

```bash
hermes
/hermes-okf-bridge restore
# Agent resumes with config, last session, active plan, and all tools
```

---

## CLI Commands (from `hermes-okf` package)

Even without the Hermes bridge, you can inspect the OKF bundle:

```bash
# View the agent's structured knowledge
hermes-okf list --path ~/.hermes/okf_memory
hermes-okf show --path ~/.hermes/okf_memory decisions/model_strategy

# Search across all memories
hermes-okf search --path ~/.hermes/okf_memory "Python GPU"

# Inspect the knowledge graph
hermes-okf graph-edges --path ~/.hermes/okf_memory
hermes-okf graph-neighbors --path ~/.hermes/okf_memory tools/search_web

# View sessions
hermes-okf sessions --path ~/.hermes/okf_memory
hermes-okf plans --path ~/.hermes/okf_memory
hermes-okf tools --path ~/.hermes/okf_memory

# Save and restore snapshots
hermes-okf snapshot --path ~/.hermes/okf_memory --note "Before deploy"
hermes-okf context --path ~/.hermes/okf_memory "What should I prioritize?"
```

---

## Troubleshooting

### "OKF bundle not found"

```bash
hermes-okf init ~/.hermes/okf_memory
```

### "Hermes doesn't see my skill"

Make sure the skill YAML is at `~/.hermes/skills/hermes-okf-bridge/skill.yaml` and the Python file is in the same directory. Run `hermes skills reload`.

### "OKF concepts are not showing up in Hermes context"

Hermes' default memory injection is separate from OKF. Use `/hermes-okf-bridge context "query"` to pull OKF knowledge into the conversation explicitly. Or configure the bridge to inject a condensed OKF summary into Hermes' working memory on session start.

### "Windows: filename errors"

Hermes-OKF uses Windows-safe filenames (`2026-06-15T10-30-00Z` instead of `2026-06-15T10:30:00Z`). If you see errors with older versions, upgrade:

```bash
pip install --upgrade hermes-okf
```

---

## Community

- Open issues: [github.com/EliaszDev/hermes-okf/issues](https://github.com/EliaszDev/hermes-okf/issues)
- Hermes Agent: [github.com/NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent)
- OKF Spec: [cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing](https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing)

---

## License

MIT — same as Hermes Agent.
