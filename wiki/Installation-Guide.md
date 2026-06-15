# Installation Guide

> **Install hermes-okf as a Hermes Agent plugin in 4 steps.**

---

## Prerequisites

- Python 3.10+ installed
- Hermes Agent installed and configured (`~/.hermes/` exists)
- `pip` or `uv` for package management

---

## Step 1 — Install from PyPI

```bash
pip install hermes-okf
```

Or with `uv`:

```bash
uv pip install hermes-okf
```

To verify the installation:

```bash
python -c "import hermes_okf; print(hermes_okf.__version__)"
# Expected: 0.4.1 or higher
```

---

## Step 2 — Register the Plugin in Hermes

Hermes discovers plugins from the `~/.hermes/plugins/` directory. Run the install command to create the plugin wrapper:

```bash
hermes-okf-install
```

Expected output:
```
Installed hermes-okf plugin to /home/username/.hermes/plugins/hermes-okf
  Run 'hermes memory setup' to activate
```

### What this does

Creates `~/.hermes/plugins/hermes-okf/` with two files:

**`plugin.yaml`** — Manifest that Hermes reads:
```yaml
name: hermes-okf
version: 0.4.1
description: "OKF-based memory provider for Hermes agent..."
hooks:
  - on_session_end
```

**`__init__.py`** — Wrapper that imports the provider:
```python
from hermes_okf.memory_plugin import HermesOKFMemoryProvider
__all__ = ["HermesOKFMemoryProvider"]
```

### Why this is needed

Hermes uses **filesystem-based discovery** (`~/.hermes/plugins/`), not `importlib.metadata` entry points. The `hermes.memory_providers` entry point in `pyproject.toml` exists but is never read by Hermes core.

The `hermes-okf-install` command creates the wrapper directory so Hermes finds the plugin at startup.

---

## Step 3 — Add to Hermes Config

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

### Important notes

- **`plugins.enabled` must be a YAML list**, not a string. If you use `hermes config set plugins.enabled '["hermes-okf"]'`, it stores a JSON string which Hermes ignores. Edit `~/.hermes/config.yaml` directly.
- The `bundle_path` is where your OKF memory files will be stored. Default is `~/.hermes/okf_memory/`.
- The `agent_id` identifies this agent's memory. Use something unique if you run multiple agents.

---

## Step 4 — Run the Setup Wizard

```bash
hermes memory setup
```

The wizard will prompt you for:

1. **Directory where OKF memory bundle is stored** — Press Enter to accept `~/.hermes/okf_memory`
2. **Identifier for this agent's memory** — Press Enter to accept `hermes-agent`

After setup completes, you'll see:
```
Memory provider: hermes-okf
Activation saved to config.yaml
Provider config saved
Start a new session to activate.
```

---

## Activate the Plugin

Start a new Hermes session:

```bash
hermes
```

The plugin will initialize automatically. On first run, it creates the OKF bundle structure:
```
~/.hermes/okf_memory/
├── config/
│   └── agent.md          # Agent config (auto-synced from Hermes config.yaml)
├── tools/
├── sessions/
├── plans/
├── plans/archive/
├── index.md
└── log.md
```

Verify the plugin is working:

```bash
hermes okf show config/agent
```

You should see your agent's configuration with the correct model from `config.yaml`.

---

## Uninstall

To remove the plugin from Hermes (but keep your OKF bundle):

```bash
hermes-okf-uninstall
```

This removes `~/.hermes/plugins/hermes-okf/`. Hermes will no longer discover the plugin on startup. Your OKF bundle at `~/.hermes/okf_memory/` remains intact.

---

## Install with RAG Support (Optional)

For semantic vector search over your memory:

```bash
pip install hermes-okf[rag]
```

This adds LangChain + ChromaDB dependencies. See [RAG Integration](../README.md#rag-integration-optional) for usage.

---

## Install in a Virtual Environment

If Hermes runs in a specific virtual environment (e.g., `~/.hermes/hermes-agent/venv/`):

```bash
# Activate the venv first, or use the venv's Python directly
~/.hermes/hermes-agent/venv/bin/python -m pip install hermes-okf

# Then run the install command through that Python
~/.hermes/hermes-agent/venv/bin/python -m hermes_okf.install_plugin
```

Or activate the venv:

```bash
source ~/.hermes/hermes-agent/venv/bin/activate
pip install hermes-okf
hermes-okf-install
```

---

## Next Steps

- [CLI Reference](CLI-Reference) — Learn all available commands
- [Troubleshooting](Troubleshooting) — Fix common issues
- [Architecture](Architecture) — Understand how it works
