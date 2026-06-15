# Installation Guide

> **Install hermes-okf as a Hermes Agent plugin in 2 steps.**

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
# Expected: 0.4.4 or higher
```

---

## Step 2 — Register the Plugin

```bash
hermes-okf-install
```

Expected output:
```
Installed hermes-okf plugin to /home/username/.hermes/plugins/hermes-okf
  Updated ~/.hermes/config.yaml
  Run 'hermes memory setup' to finish activation
```

### What this does (automatically)

**1. Creates plugin wrapper:**

`~/.hermes/plugins/hermes-okf/plugin.yaml` — Manifest that Hermes reads:
```yaml
name: hermes-okf
version: 0.4.4
description: "OKF-based memory provider for Hermes agent..."
hooks:
  - on_session_end
```

`~/.hermes/plugins/hermes-okf/__init__.py` — Wrapper that imports the provider:
```python
from hermes_okf.memory_plugin import HermesOKFMemoryProvider
__all__ = ["HermesOKFMemoryProvider"]
```

**2. Auto-configures Hermes:**

Reads `~/.hermes/config.yaml` and adds:
- `hermes-okf` to `plugins.enabled`
- `memory.provider: hermes-okf`
- `memory.bundle_path: ~/.hermes/okf_memory`

### Why this is needed

Hermes uses **filesystem-based discovery** (`~/.hermes/plugins/`), not `importlib.metadata` entry points. The `hermes.memory_providers` entry point in `pyproject.toml` exists but is never read by Hermes core.

The `hermes-okf-install` command creates the wrapper directory and configures Hermes so it finds the plugin immediately.

---

## Activate

Start Hermes:

```bash
hermes
```

The plugin activates on first session start. On first run, it creates the OKF bundle structure:
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

## Optional: Customize with Setup Wizard

If you want to customize the bundle path or agent ID:

```bash
hermes memory setup
```

The wizard will prompt you for:
- Directory where OKF memory bundle is stored (default: `~/.hermes/okf_memory`)
- Identifier for this agent's memory (default: `hermes-agent`)

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
