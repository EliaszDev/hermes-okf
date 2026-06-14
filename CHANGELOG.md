# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.9] - 2026-06-14

### Fixed
- `memory_plugin.py` — fix import order (ruff isort I001): stdlib imports must come before first-party `import hermes_okf`

## [0.3.8] - 2026-06-14

### Fixed
- `memory_plugin.py` — add missing `import hermes_okf` (was used for `hermes_okf.__version__` but only `from hermes_okf.hermes_integration import ...` was present, causing ruff F821 undefined name)

## [0.3.7] - 2026-06-14

### Fixed
- `HermesOKFMemoryProvider.initialize()` now reads the actual Hermes model from `config.yaml` (top-level `model` or `llm.model`) and syncs it into the OKF `config/agent` concept. Previously the config concept was hardcoded with `openai/gpt-4o` regardless of the actual model.

## [0.3.6] - 2026-06-14

### Fixed
- CI black formatting — `cli_extension.py` had `add_parser` call split across 3 lines when it fit on 1 line (88 chars), causing `black --check` to fail
- `hermes.py` and `plugin.py` — split lines that were 110 and 103 chars respectively

## [0.3.5] - 2026-06-14

### Fixed
- `hermes okf show` — `_cli_show` used `concept.content` instead of `concept.body`, causing `AttributeError` on any concept read
- The published 0.3.4 wheel had the broken `show` command; 0.3.5 is a clean rebuild

## [0.3.4] - 2026-06-14

### Added
- `hermes okf show <path> [--raw]` — display full content of an OKF concept with metadata and markdown body
- README now documents `plugins.enabled` as a YAML list (critical for Hermes plugin discovery)

## [0.3.3] - 2026-06-14

### Fixed
- Entry point format corrected — `hermes_agent.plugins` must be **module-only** (`hermes_okf.plugin`), not `hermes_okf.plugin:register`. The `:register` suffix caused `ep.load()` to return the function object instead of the module, so Hermes couldn't find `register()` and skipped the plugin with "no register() function"
- The published 0.3.2 wheel had the broken entry point; 0.3.3 is a clean rebuild

## [0.3.2] - 2026-06-14

### Fixed
- CLI plugin registration — pip-installed packages cannot use convention-based `cli.py` discovery; now registers via general `hermes_agent.plugins` entry point with `ctx.register_cli_command("okf", ...)`
- `register_cli()` signature corrected — receives `argparse.ArgumentParser` directly (the `okf` parser), not a `_SubParsersAction` that would double-nest the command
- Removed dead `register_cli` and `_cli_*` handlers from `memory_plugin.py` (they were never called by Hermes)
- New `plugin.py` — general Hermes plugin registration bridge; new `cli_extension.py` — clean CLI tree builder
- Users should run `pip install --upgrade hermes-okf` to get the working CLI

## [0.3.1] - 2026-06-14

### Added
- `HermesOKFMemoryProvider` — Hermes Agent `MemoryProvider` ABC plugin adapter
- Implements `sync_turn()`, `prefetch()`, `shutdown()`, `post_setup()` for native Hermes integration
- `register_cli()` — adds `hermes okf search/list/snapshot/restore` CLI extension
- Pip entry point: `hermes.memory_providers` for auto-discovery by Hermes Agent
- Aligns with Hermes CONTRIBUTING.md policy: standalone memory plugins, no core changes needed

### Fixed
- `memory_plugin.py` type annotations — `dict[str, Any]`, `hot_memory_max`, `Concept.id`
- All 46 tests pass, ruff/black/mypy clean

## [0.3.0] - 2026-06-14

### Added
- `HermesOKFProvider` — generic Hermes-native memory provider for **any** Nous Research Hermes agent
- Two-memory model: Hot buffer (in-process) + Cold archive (OKF bundle) with automatic flushing
- Hermes config system integration — reads from `~/.hermes/hermes-okf.yaml` or env vars (`HERMES_OKF_*`)
- Lifecycle hooks: `on_session_start`, `on_memory_write`, `on_tool_call`, `on_decision`, `on_plan_complete`, `on_session_end`
- Tool registry — auto-registers Hermes tool schemas as typed OKF concepts
- Plan tracking — Hermes plan steps automatically persisted to OKF
- RAG layer — optional ChromaDB vector search over the OKF bundle (LangChain)
- Crash recovery — `snapshot()` and `restore()` from the provider level
- `docs/HERMES_USERS.md` — user guide for any Hermes agent owner
- `tests/test_hermes_integration.py` — 7 test cases covering all provider features

### Changed
- `HermesAgent` constructor now creates `hermes/` directory structure automatically
- All pipeline-specific references removed — integration is now generic
- Hermes tool decorators (`@memorize_tool`, `@memorize_decision`) now store in `tool_schema.md` + `tool_call_*.md`

## [0.2.0] - 2026-06-15

### Added
- `HermesAgent` — full agent whose entire state lives in an OKF bundle (config, tools, sessions, plans, snapshots, resume)
- `HermesAgent.register_tool()` — tool definitions stored as OKF concepts with JSON schemas
- `HermesAgent.create_plan()` / `complete_step()` / `archive_plan()` — structured plan execution tracked in OKF
- `HermesAgent.snapshot()` / `restore()` — full state snapshots for crash recovery and resume
- `HermesAgent.build_context()` — auto-assembles LLM context from system prompt, active plan, memory, log, and tools
- `HermesAgent.list_sessions()` / `recall_session()` — cross-session memory
- New CLI commands: `snapshot`, `context`, `sessions`, `plans`, `tools`
- `docs/HERMES_INTEGRATION.md` — architecture guide for deep integration
- `examples/full_agent.py` — complete Hermes agent example with tool registry, plans, and resume
- `tests/test_hermes.py` — full test coverage for `HermesAgent`

## [0.1.0] - 2026-06-15

### Added
- Initial release of `hermes-okf`
- `OKFBundle` — core bundle manager with read/write, logging, graph edge extraction
- `Concept` — dataclass for OKF concepts
- `GraphExtractor` — link traversal, directory hierarchy, tag clustering, BFS traversal, NetworkX export
- `SearchIndex` — inverted-index full-text search, fuzzy search, custom predicate filtering
- `OKFValidator` — OKF v0.1 conformance validation
- `HermesMemory` — agent memory layer: sessions, decisions, observations, tool calls, context recall
- `HermesMemoryMixin` — drop-in decorators for agent classes
- CLI (`hermes-okf`) — init, validate, show, search, log, graph commands
- RAG integration example (LangChain + ChromaDB)
- Full test suite with pytest
- GitHub Actions CI for Python 3.10–3.13
