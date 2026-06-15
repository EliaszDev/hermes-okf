# Hermes OKF Wiki

Welcome to the **hermes-okf** wiki. This is the knowledge base for installing, configuring, and using the OKF-based memory system for Hermes Agent.

## Quick Links

- [Installation Guide](Installation-Guide) — Step-by-step setup for Hermes plugin
- [CLI Reference](CLI-Reference) — All commands explained
- [Troubleshooting](Troubleshooting) — Common issues and fixes
- [Architecture](Architecture) — How it works under the hood
- [Changelog](Changelog) — Version history

## What is hermes-okf?

The first open-source memory system built on Google's **Open Knowledge Format (OKF)** for the Hermes agent ecosystem. It gives your AI agent a **persistent, structured, version-controlled memory** — no database, no lock-in, just markdown + YAML on your filesystem.

**Key feature (v0.4.1):** `hermes-okf-install` — a one-command plugin registration that makes `hermes memory setup` discover hermes-okf automatically.

```bash
pip install hermes-okf
hermes-okf-install
hermes memory setup
```

## Features

- 🧠 **Agent Memory** — Persistent decisions, observations, tool-call history
- 🔗 **Knowledge Graph** — Implicit graph from markdown links
- 📁 **Filesystem-First** — Plain `.md` + YAML, git-friendly
- ⚡ **Zero-DB Core** — Single dependency: `pyyaml`
- 🔌 **Hermes Plugin** — Native `MemoryProvider` ABC integration
- 🔄 **Resume** — Stop and restart, agent restores from OKF bundle
- 📦 **Portable** — Clone bundle to another machine, resume instantly

## Latest Version

**v0.4.1** — [View on PyPI](https://pypi.org/project/hermes-okf/)

**Latest fixes:**
- v0.4.1 — `hermes-okf-install` / `hermes-okf-uninstall` commands for plugin registration
- v0.3.9 — Import order fixes for CI compliance
- v0.3.7 — Hermes model auto-sync from `config.yaml` to OKF config
- v0.3.6 — Black formatting fixes
- v0.3.5 — `show` command uses `concept.body` instead of broken `.content`
- v0.3.4 — `hermes okf show <path>` command added
- v0.3.3 — Entry point format corrected for Hermes plugin discovery
