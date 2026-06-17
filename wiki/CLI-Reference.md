# CLI Reference

> **Complete reference for all hermes-okf commands.**

---

## Hermes Plugin Commands (`hermes okf`)

These commands are available when hermes-okf is installed as a Hermes plugin.

### `hermes okf search <query>`

Search the OKF memory bundle for relevant concepts.

```bash
hermes okf search "dark mode"
hermes okf search "deployment strategy" --top-k 10
```

| Option | Default | Description |
|--------|---------|-------------|
| `--top-k` | 5 | Number of results to return |

### `hermes okf list`

List all stored concepts in the OKF bundle.

```bash
hermes okf list
hermes okf list --type Decision
hermes okf list --type Session
```

| Option | Description |
|--------|-------------|
| `--type` | Filter by concept type (e.g., `Decision`, `Plan`, `Tool`) |

### `hermes okf show <path>`

Show the full content of a specific OKF concept, including YAML frontmatter and markdown body.

```bash
hermes okf show config/agent
hermes okf show sessions/2026-06-14T22-14-58Z
hermes okf show decisions/model_strategy
```

| Option | Description |
|--------|-------------|
| `--raw` | Print only the markdown body, without metadata |

**Example output:**
```
[AgentConfig] config/agent
Metadata:
  type: AgentConfig
  title: hermes Configuration
  model: kimi/k2.6
  system_prompt: You are a helpful, autonomous Hermes agent.
  version: 0.5.0
  timestamp: 2026-06-14T22:14:58Z
---
# Agent Configuration

System prompt and behaviour settings.
```

### `hermes okf snapshot`

Save a full memory snapshot to the OKF bundle.

```bash
hermes okf snapshot
hermes okf snapshot --note "Before deployment"
```

| Option | Description |
|--------|-------------|
| `--note` | Optional note to attach to the snapshot |

### `hermes okf restore`

Restore from the last saved snapshot.

```bash
hermes okf restore
```

---

## Standalone CLI Commands (`hermes-okf`)

These commands work independently of the Hermes plugin.

### `hermes-okf init <path>`

Initialize a new OKF bundle at the specified path.

```bash
hermes-okf init ./knowledge
hermes-okf init ~/.hermes/okf_memory
```

### `hermes-okf validate`

Validate an OKF bundle for conformance.

```bash
hermes-okf validate --path ./knowledge
hermes-okf validate --path ~/.hermes/okf_memory
```

### `hermes-okf list`

List concepts in a bundle.

```bash
hermes-okf list --path ./knowledge
hermes-okf list --path ./knowledge --subdir projects
```

| Option | Description |
|--------|-------------|
| `--path` | Path to the OKF bundle |
| `--subdir` | Only list concepts in this subdirectory |

### `hermes-okf show`

Show a specific concept.

```bash
hermes-okf show --path ./knowledge projects/my_project
hermes-okf show --path ./knowledge config/agent
```

### `hermes-okf search`

Search across all concepts.

```bash
hermes-okf search --path ./knowledge "ffmpeg GPU"
```

### `hermes-okf log`

View the bundle's chronological log.

```bash
hermes-okf log --path ./knowledge
```

### `hermes-okf log-append`

Append an entry to the log.

```bash
hermes-okf log-append --path ./knowledge "New decision made" --category Decision
```

| Option | Default | Description |
|--------|---------|-------------|
| `--category` | Update | Entry category (e.g., Decision, Observation, Tool-Call) |

### `hermes-okf graph-edges`

Show all graph edges (markdown links) in the bundle.

```bash
hermes-okf graph-edges --path ./knowledge
```

### `hermes-okf graph-neighbors <concept>`

Show neighbors of a specific concept in the knowledge graph.

```bash
hermes-okf graph-neighbors --path ./knowledge projects/my_project
```

### `hermes-okf snapshot`

Save a snapshot.

```bash
hermes-okf snapshot --path ./knowledge --note "Before deploy"
```

### `hermes-okf context`

Build LLM context from the bundle for a given query.

```bash
hermes-okf context --path ./knowledge "What should I prioritize?"
```

### `hermes-okf sessions`

List all sessions.

```bash
hermes-okf sessions --path ./knowledge
```

### `hermes-okf plans`

List all plans.

```bash
hermes-okf plans --path ./knowledge
```

### `hermes-okf tools`

List all registered tools.

```bash
hermes-okf tools --path ./knowledge
```

---

## Plugin Management Commands

### `hermes-okf install-plugin`

Register hermes-okf as a Hermes plugin.

```bash
hermes-okf install-plugin
```

Creates `~/.hermes/plugins/hermes-okf/` with the plugin wrapper.

### `hermes-okf uninstall-plugin`

Remove hermes-okf from Hermes.

```bash
hermes-okf uninstall-plugin
```

Removes `~/.hermes/plugins/hermes-okf/`. Does not delete your OKF bundle.

---

## Common Workflows

### Daily inspection

```bash
hermes okf show config/agent           # Check current config
hermes okf list --type Decision        # Review recent decisions
hermes okf search "Python"              # Find relevant concepts
```

### Before a big change

```bash
hermes okf snapshot --note "Before refactoring"
# ... make changes ...
hermes okf restore                      # If something breaks
```

### End of session

```bash
hermes okf snapshot --note "End of day checkpoint"
```

### Resume next day

```bash
hermes
hermes okf restore
```
