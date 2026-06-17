# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] - 2026-06-15

### Changed
- **Unified CLI**: `hermes-okf install-plugin` and `hermes-okf uninstall-plugin` are now the only documented installation method. The standalone `hermes-okf-install` and `hermes-okf-uninstall` entry points have been removed from `pyproject.toml` to eliminate PATH confusion and provide a single, consistent CLI interface.
- All documentation (README, wiki, docs) updated to use the subcommand form exclusively.

### Fixed
- CLI `--path` argument now works after subcommands (`hermes-okf validate --path /tmp/test`). Previously `--path` was on the parent parser only, so argparse rejected it after subcommand names. Now each subparser shares a `path_parent` parser that includes `--path`, making placement natural.
- Added `--version` flag (`hermes-okf --version` now prints `hermes-okf 0.5.0`).

## [0.4.5] - 2026-06-15

### Fixed
- `hermes-okf init --path <dir>` now correctly uses the `--path` argument instead of checking the current working directory. The `init` subparser's positional `path` argument was renamed to `init_path` to avoid argparse shadowing the parent parser's `--path`.
- `hermes-okf snapshot` now accepts `--agent-id` (was missing, causing `AttributeError` on the `agent_id` attribute).
- Moved all CLI handler functions (`_snapshot`, `_context`, `_sessions`, `_plans`, `_tools`) before `main()` for cleaner code structure and to avoid any potential import-order issues.

## [0.4.4] - 2026-06-15

### Fixed
- CI black formatting failure — added missing blank lines after inline imports in `cli.py` (`_install_plugin` / `_uninstall_plugin`)

## [0.4.3] - 2026-06-14

### Added
- `hermes-okf install-plugin` CLI command — standalone CLI now supports plugin installation
- `hermes-okf uninstall-plugin` CLI command — standalone CLI now supports plugin removal
- `HermesOKFMemoryProvider.on_session_start()` — standalone method for Hermes session lifecycle

### Fixed
- Removed false "auto-discovered" claims from documentation — Hermes uses filesystem discovery, not entry points
- `recall()`/`prefetch()` — SearchIndex rebuilds correctly after invalidate()

## [0.4.2] - 2026-06-14

### Changed
- `hermes-okf-install` now **auto-configures `~/.hermes/config.yaml`** — adds `hermes-okf` to `plugins.enabled`, sets `memory.provider`, and adds `bundle_path`. No manual YAML editing needed.
- Install flow reduced from 4 steps to **2 steps**: `pip install hermes-okf && hermes-okf-install`, then `hermes`.

## [0.4.1] - 2026-06-14

### Changed
- Complete README rewrite — clear 2-step install flow, removed false claims, added architecture diagram
- Wiki docs rewritten (`Home`, `Architecture`, `CLI`, `Changelog`, `Troubleshooting`) to align with v0.4.1
- `hermes-okf-install` script now creates `~/.hermes/plugins/hermes-okf/` wrapper directory
- `hermes okf show` command added — inspect single concepts with `--json` option
- `hermes-okf.wiki` embedded repo removed from main repo

### Fixed
- `hermes okf list` now works via `cli_extension.py` registration (not standalone `list` command)
- README badge and version numbers bumped to v0.4.1

## [0.4.0] - 2026-06-14

### Added
- `hermes-okf-install` CLI — one-command plugin registration (`~/.hermes/plugins/`)
- `hermes-okf-uninstall` CLI — removes plugin wrapper from `~/.hermes/plugins/`

### Fixed
- `register_cli` receives `ArgumentParser` directly (not `_SubParsersAction`)
- Entry point fix: `hermes_agent.plugins` points to module `hermes_okf.plugin` (no `:register`)
- README now correctly explains filesystem discovery (not entry points)

## [0.3.9] - 2026-06-14

### Fixed
- Import order in `memory_plugin.py` — `import hermes_okf` moved after stdlib imports (ruff isort I001)
- README badge and version bumped to v0.3.9

## [0.3.8] - 2026-06-14

### Fixed
- `register_cli` in `cli_extension.py` returns `None` (no premature `return parser`)
- `add_parser` calls placed on single lines for Black line-length compliance
- README badge and version bumped to v0.3.8

## [0.3.7] - 2026-06-14

### Fixed
- `hermes_integration.py` reads `model` from Hermes `config.yaml` (top-level or `llm.model`) and writes to OKF `config/agent` on session start
- `on_session_end` snapshot logic restored
- README updated to v0.3.7

## [0.3.6] - 2026-06-14

### Fixed
- `install_plugin.py` `register_hermes_cli` reformat for Black (wrap long lines, add trailing comma)
- `cli_extension.py` return type reformat for Black
- `README.md` updated to v0.3.6

## [0.3.5] - 2026-06-14

### Fixed
- `hermes-okf` entry point now points to `hermes_okf.cli:main` (standalone CLI restored)
- `hermes-okf-install` points to `hermes_okf.install_plugin:install_plugin`
- README updated to v0.3.5

## [0.3.4] - 2026-06-14

### Fixed
- `register_cli` in `cli_extension.py` takes `parser` directly and does not call `add_parser` on `_SubParsersAction`
- `cli_extension.py` properly registers `okf` subcommand via `parser.add_parser` with parent parser
- README updated to v0.3.4

## [0.3.3] - 2026-06-14

### Fixed
- `register_cli` in `cli_extension.py` receives `subparsers` (`_SubParsersAction`) and calls `add_parser` on it, then registers commands under that subparser
- `add_parser` chain in `cli_extension.py` formatted for Black (100-col line length)
- README updated to v0.3.3

## [0.3.2] - 2026-06-14

### Fixed
- `cli_extension.py` uses `parser.add_parser("okf", ...)` instead of `subparsers.add_parser("okf", ...)` to match Hermes CLI registration
- `hermes okf search|list|show|snapshot|restore` now work via `hermes okf <sub>` command
- README updated to v0.3.2

## [0.3.1] - 2026-06-14

### Fixed
- `add_parser` calls placed on single lines for Black compliance (100-char limit)
- `README.md` badge and version bumped to v0.3.1
- `hermes okf show` CLI subcommand added
- `register_cli` returns `None` (no `return parser`)

## [0.3.0] - 2026-06-14

### Added
- `HermesOKFMemoryProvider` — full `MemoryProvider` ABC implementation
- `cli_extension.py` — Hermes CLI extension (`hermes okf search|list|snapshot|restore`)
- `plugin.py` — general Hermes plugin registration (`register(ctx)`)
- `hermes_integration.py` — universal `HermesOKFProvider` with session lifecycle, search, memory write, tool call tracking, and snapshots
- `install_plugin.py` — one-command `hermes-okf-install` script to create `~/.hermes/plugins/hermes-okf/`
- `register_hermes_cli` — Hermes CLI registration helper
- `register_memory_provider` — memory provider registration helper
- `on_memory_write` — writes user/assistant messages to `conversations/{id}/user|assistant`
- `on_tool_call` — writes tool calls to `tool_calls/{tool_name}`
- `prefetch` / `recall` — returns top-5 relevant memory as formatted context string
- `search_memory` / `snapshot_memory` / `restore_memory` tool schemas for Hermes agent
- `get_config_schema` / `save_config` — for `hermes memory setup` integration
- `system_prompt_block` — static info about OKF memory provider
- Entry points: `hermes.memory_providers` and `hermes_agent.plugins`
- `README.md` updated with full MemoryProvider API reference and install instructions
- `CHANGELOG.md` created
- `docs/` directory with architecture, API, and install guides
- `wiki/` directory with GitHub wiki content (Home, Architecture, CLI, Changelog, Troubleshooting)

### Fixed
- `README.md` badge and version bumped to v0.3.0
- `hermes okf list` command fixed via `list` subcommand registration
- `show` command added to `cli_extension.py`
- `pyproject.toml` entry points updated to `hermes.memory_providers` and `hermes_agent.plugins`

## [0.2.1] - 2026-06-14

### Fixed
- `README.md` badge and version bumped to v0.2.1
- `CHANGELOG.md` updated
- `pyproject.toml` entry points updated to `hermes.memory_providers` and `hermes_agent.plugins`
- `register_cli` receives `ArgumentParser` directly (not `_SubParsersAction`)

## [0.2.0] - 2026-06-14

### Added
- `HermesOKFMemoryProvider` — full `MemoryProvider` ABC implementation
- `cli_extension.py` — Hermes CLI extension (`hermes okf search|list|snapshot|restore`)
- `plugin.py` — general Hermes plugin registration (`register(ctx)`)
- `hermes_integration.py` — universal `HermesOKFProvider` with session lifecycle, search, memory write, tool call tracking, and snapshots
- `install_plugin.py` — one-command `hermes-okf-install` script to create `~/.hermes/plugins/hermes-okf/`
- `register_hermes_cli` — Hermes CLI registration helper
- `register_memory_provider` — memory provider registration helper
- `on_memory_write` — writes user/assistant messages to `conversations/{id}/user|assistant`
- `on_tool_call` — writes tool calls to `tool_calls/{tool_name}`
- `prefetch` / `recall` — returns top-5 relevant memory as formatted context string
- `search_memory` / `snapshot_memory` / `restore_memory` tool schemas for Hermes agent
- `get_config_schema` / `save_config` — for `hermes memory setup` integration
- `system_prompt_block` — static info about OKF memory provider
- Entry points: `hermes.memory_providers` and `hermes_agent.plugins`
- `README.md` updated with full MemoryProvider API reference and install instructions
- `CHANGELOG.md` created
- `docs/` directory with architecture, API, and install guides
- `wiki/` directory with GitHub wiki content (Home, Architecture, CLI, Changelog, Troubleshooting)

### Fixed
- `README.md` badge and version bumped to v0.2.0
- `hermes okf list` command fixed via `list` subcommand registration
- `show` command added to `cli_extension.py`
- `pyproject.toml` entry points updated to `hermes.memory_providers` and `hermes_agent.plugins`

## [0.1.1] - 2026-06-14

### Fixed
- `README.md` badge and version bumped to v0.1.1
- `CHANGELOG.md` updated
- `pyproject.toml` entry points updated to `hermes.memory_providers` and `hermes_agent.plugins`
- `register_cli` receives `ArgumentParser` directly (not `_SubParsersAction`)

## [0.1.0] - 2026-06-14

### Added
- `HermesOKFMemoryProvider` — full `MemoryProvider` ABC implementation
- `cli_extension.py` — Hermes CLI extension (`hermes okf search|list|snapshot|restore`)
- `plugin.py` — general Hermes plugin registration (`register(ctx)`)
- `hermes_integration.py` — universal `HermesOKFProvider` with session lifecycle, search, memory write, tool call tracking, and snapshots
- `install_plugin.py` — one-command `hermes-okf-install` script to create `~/.hermes/plugins/hermes-okf/`
- `register_hermes_cli` — Hermes CLI registration helper
- `register_memory_provider` — memory provider registration helper
- `on_memory_write` — writes user/assistant messages to `conversations/{id}/user|assistant`
- `on_tool_call` — writes tool calls to `tool_calls/{tool_name}`
- `prefetch` / `recall` — returns top-5 relevant memory as formatted context string
- `search_memory` / `snapshot_memory` / `restore_memory` tool schemas for Hermes agent
- `get_config_schema` / `save_config` — for `hermes memory setup` integration
- `system_prompt_block` — static info about OKF memory provider
- Entry points: `hermes.memory_providers` and `hermes_agent.plugins`
- `README.md` updated with full MemoryProvider API reference and install instructions
- `CHANGELOG.md` created
- `docs/` directory with architecture, API, and install guides
- `wiki/` directory with GitHub wiki content (Home, Architecture, CLI, Changelog, Troubleshooting)

### Fixed
- `README.md` badge and version bumped to v0.1.0
- `hermes okf list` command fixed via `list` subcommand registration
- `show` command added to `cli_extension.py`
- `pyproject.toml` entry points updated to `hermes.memory_providers` and `hermes_agent.plugins`

## [0.0.1] - 2026-06-14

### Added
- Initial release of `hermes-okf`
- `OKFBundle` — create, read, write, and validate OKF bundles
- `Concept` — structured knowledge units with YAML frontmatter + markdown body
- `SearchIndex` — TF-IDF based search over concepts
- `GraphExtractor` — relationship extraction from concept tags and references
- `OKFValidator` — conformance checking against OKF schema
- `HermesAgent` — agent wrapper for OKF memory (sessions, plans, tools, context building)
- `HermesMemory` — high-level memory interface (read, write, search, snapshot, restore)
- `HermesOKFProvider` — universal provider for Hermes integration
- `hermes-okf` CLI — standalone commands: `init`, `validate`, `search`, `list`, `show`, `log`, `log-append`, `graph-edges`, `graph-neighbors`, `snapshot`, `context`, `sessions`, `plans`, `tools`
- `README.md` with quick start and architecture overview
- `CHANGELOG.md` created
- `docs/` directory with architecture and API guides
- `pyproject.toml` with hatchling build backend and entry points
- `tests/` with pytest suite for bundle, search, graph, and validator modules
- `examples/` with example OKF bundle for validation
- `wiki/` directory with GitHub wiki content (Home, Architecture, CLI, Changelog, Troubleshooting)
