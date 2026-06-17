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
- **Model sync** — OKF config auto-updates from Hermes `config.yaml` (v0.3.7+)

**The two systems coexist.** Hermes keeps its fast, bounded working memory. OKF handles structured, long-term knowledge.

---

## Installation (v0.5.0+)

### 1. Install hermes-okf

```bash
pip install hermes-okf
```

### 2. Register the plugin

```bash
hermes-okf install-plugin
```

This does **everything automatically**:

1. **Creates** `~/.hermes/plugins/hermes-okf/` with `plugin.yaml` + `__init__.py`
2. **Updates** `~/.hermes/config.yaml` to add `hermes-okf` to `plugins.enabled` and set `memory.provider`

> **Why this is needed:** Hermes uses filesystem-based discovery (`~/.hermes/plugins/`), not `importlib.metadata` entry points. The `hermes.memory_providers` entry point exists but is never read by Hermes. The `hermes-okf install-plugin` command creates the wrapper directory and configures Hermes so it finds the plugin immediately.

### 3. Start Hermes

```bash
hermes
```

The plugin activates on first session start. Your OKF bundle is created at `~/.hermes/okf_memory/` automatically.

**Optional:** Run `hermes memory setup` to customize bundle path or agent ID.

```bash
hermes memory setup
```

Then start a new Hermes session:

```bash
hermes
```

### Uninstall

```bash
hermes-okf uninstall-plugin
```

Removes the plugin wrapper from `~/.hermes/plugins/` but does not delete your OKF bundle.

---

## Hermes Plugin CLI Commands

When installed as a Hermes plugin, these subcommands are available:

```bash
# Search your OKF memory
hermes okf search "dark mode"

# List stored concepts
hermes okf list --type Decision

# Show full content of a concept (v0.3.4+)
hermes okf show config/agent
hermes okf show sessions/2026-06-14T22-14-58Z
hermes okf show sessions/2026-06-14T22-14-58Z --raw  # no metadata

# Save a snapshot
hermes okf snapshot --note "Before deployment"

# Restore from last snapshot
hermes okf restore
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

### 5. Inspect memory

```bash
hermes okf show config/agent        # See your config (model, system prompt)
hermes okf list --type Decision     # See all decisions
hermes okf search "Python"           # Full-text search
```

### 6. End session — OKF snapshots state

```bash
hermes okf snapshot "End of day checkpoint"
# Full agent state saved to snapshots/YYYY-MM-DDTHH-MM-SSZ.md
```

### 7. Resume tomorrow

```bash
hermes
hermes okf restore
# Agent resumes with config, last session, active plan, and all tools
```

---

## Standalone CLI Commands

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

### "hermes-okf install-plugin" is not found

If the `hermes-okf` CLI is not in PATH, use the module form:

```bash
python -m hermes_okf.cli install-plugin
```

### "Hermes doesn't see my plugin"

1. Check the plugin directory exists:
   ```bash
   ls ~/.hermes/plugins/hermes-okf/
   # Should show: __init__.py  plugin.yaml
   ```
2. Ensure `plugins.enabled` in `~/.hermes/config.yaml` is a YAML list (not a JSON string)
3. Restart Hermes

### "OKF bundle not found"

```bash
hermes-okf init ~/.hermes/okf_memory
```

### "Config shows wrong model"

As of v0.3.7, the model is synced from Hermes `config.yaml` on every session start. Restart Hermes to refresh.

### "Windows: filename errors"

Hermes-OKF uses Windows-safe filenames. If you see errors with older versions, upgrade:

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
