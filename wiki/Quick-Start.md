# Quick Start

> **Get hermes-okf running in 2 commands.**

---

## Step 1 — Install

```bash
pip install hermes-okf
```

## Step 2 — Register

```bash
hermes-okf-install
```

This does two things automatically:
1. Creates `~/.hermes/plugins/hermes-okf/` so Hermes discovers the plugin
2. Updates `~/.hermes/config.yaml` to add `hermes-okf` to `plugins.enabled` and set `memory.provider`

---

## Done. Start Hermes.

```bash
hermes
```

The plugin activates on first session start. Your OKF bundle is created at `~/.hermes/okf_memory/` automatically.

---

## Verify it's working

```bash
hermes okf show config/agent
```

You should see your agent config with the correct model from `config.yaml`.

---

## Full Walkthrough

```bash
# Install
pip install hermes-okf

# Register (auto-configures everything)
hermes-okf-install
# Output:
#   Installed hermes-okf plugin to /home/you/.hermes/plugins/hermes-okf
#   Updated ~/.hermes/config.yaml
#   Run 'hermes memory setup' to finish activation

# Optional: run setup wizard for bundle path / agent ID
hermes memory setup

# Start Hermes
hermes

# Inside Hermes, inspect your memory
hermes okf show config/agent
hermes okf list --type Decision
hermes okf search "Python"
```

---

## What if `hermes-okf-install` is not found?

Use the Python module form:

```bash
python -m hermes_okf.install_plugin
```

Or with a virtual environment:
```bash
~/.hermes/hermes-agent/venv/bin/python -m hermes_okf.install_plugin
```

---

## Uninstall

```bash
hermes-okf-uninstall
```

Removes the plugin from Hermes but keeps your OKF bundle.

---

## Next Steps

- [CLI Reference](CLI-Reference) — All commands explained
- [Installation Guide](Installation-Guide) — Detailed setup with virtual environments
- [Troubleshooting](Troubleshooting) — Common issues and fixes
