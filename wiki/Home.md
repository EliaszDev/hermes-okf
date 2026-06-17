# Hermes OKF Wiki

Welcome to the **hermes-okf** wiki. This is the knowledge base for installing, configuring, and using the OKF-based memory system for Hermes Agent.

## Quick Links

- [Quick Start](Quick-Start) — **2-step setup: pip install + hermes-okf install-plugin**
- [Installation Guide](Installation-Guide) — Detailed setup with virtual environments
- [CLI Reference](CLI-Reference) — All commands explained
- [Troubleshooting](Troubleshooting) — Common issues and fixes
- [Architecture](Architecture) — How it works under the hood
- [Changelog](Changelog) — Version history

## What is hermes-okf?

The first open-source memory system built on Google's **Open Knowledge Format (OKF)** for the Hermes agent ecosystem. It gives your AI agent a **persistent, structured, version-controlled memory** — no database, no lock-in, just markdown + YAML on your filesystem.

**Key feature (v0.5.0):** `hermes-okf install-plugin` now **auto-configures `~/.hermes/config.yaml`**. The install flow is just **2 steps**:

```bash
pip install hermes-okf
hermes-okf install-plugin
```

Then `hermes` and the plugin is live. No manual YAML editing needed.

## Features

- 🧠 **Agent Memory** — Persistent decisions, observations, tool-call history
- 🔗 **Knowledge Graph** — Implicit graph from markdown links
- 📁 **Filesystem-First** — Plain `.md` + YAML, git-friendly
- ⚡ **Zero-DB Core** — Single dependency: `pyyaml`
- 🔌 **Hermes Plugin** — Native `MemoryProvider` ABC integration, discovered via `hermes-okf install-plugin`
- 🔄 **Resume** — Stop and restart, agent restores from OKF bundle
- 📦 **Portable** — Clone bundle to another machine, resume instantly

## Latest Version

**v0.5.0** — [View on PyPI](https://pypi.org/project/hermes-okf/)

**Latest fixes:**
- v0.5.0 — Unified CLI: `install-plugin`/`uninstall-plugin` subcommands replace standalone scripts
- v0.4.6 — CLI `--path` works after subcommands; `--version` flag added
- v0.4.5 — `init --path` fixed; `snapshot` accepts `--agent-id`; cleaner CLI code structure
- v0.4.4 — CI publish pipeline gating + black formatting fix; `install-plugin`/`uninstall-plugin` in standalone CLI
- v0.4.3 — `hermes-okf install-plugin` / `uninstall-plugin` in standalone CLI; `on_session_start()` hook
- v0.4.2 — `hermes-okf-install` auto-configures `~/.hermes/config.yaml` (no manual YAML editing)
- v0.4.1 — `hermes-okf-install` / `hermes-okf-uninstall` commands for plugin registration
- v0.3.9 — Import order fixes for CI compliance
- v0.3.7 — Hermes model auto-sync from `config.yaml` to OKF config
- v0.3.6 — Black formatting fixes
- v0.3.5 — `show` command uses `concept.body` instead of broken `.content`
- v0.3.4 — `hermes okf show <path>` command added
- v0.3.3 — Entry point format corrected for Hermes plugin discovery
