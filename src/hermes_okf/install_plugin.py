"""Install hermes-okf as a Hermes memory provider plugin.

Creates the plugin wrapper in ~/.hermes/plugins/hermes-okf/ and
auto-configures ~/.hermes/config.yaml so `hermes memory setup` finds
it immediately.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import hermes_okf


def _configure_hermes_config(hermes_home: Path) -> bool:
    """Add hermes-okf to ~/.hermes/config.yaml if it exists.

    Returns True if the config was modified.
    """
    config_path = hermes_home / "config.yaml"
    if not config_path.exists():
        return False

    try:
        import yaml
    except ImportError:
        return False

    text = config_path.read_text(encoding="utf-8")
    config = yaml.safe_load(text) or {}

    modified = False

    # Ensure plugins.enabled is a list with hermes-okf
    if "plugins" not in config:
        config["plugins"] = {}
    if "enabled" not in config["plugins"]:
        config["plugins"]["enabled"] = []
    if not isinstance(config["plugins"]["enabled"], list):
        config["plugins"]["enabled"] = []
    if "hermes-okf" not in config["plugins"]["enabled"]:
        config["plugins"]["enabled"].append("hermes-okf")
        modified = True

    # Ensure memory provider config
    if "memory" not in config:
        config["memory"] = {}
    if config["memory"].get("provider") != "hermes-okf":
        config["memory"]["provider"] = "hermes-okf"
        modified = True
    if "bundle_path" not in config["memory"]:
        config["memory"]["bundle_path"] = "~/.hermes/okf_memory"
        modified = True

    if modified:
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    return modified


def install_plugin() -> None:
    """Create the Hermes plugin wrapper and configure Hermes."""
    hermes_home = Path.home() / ".hermes"
    plugins_dir = hermes_home / "plugins"
    plugin_dir = plugins_dir / "hermes-okf"

    plugin_dir.mkdir(parents=True, exist_ok=True)

    yaml_text = (
        "name: hermes-okf\n"
        f"version: {hermes_okf.__version__}\n"
        'description: "OKF-based memory provider for Hermes agent — '
        'structured, persistent, agent-readable knowledge storage."\n'
        "hooks:\n"
        "  - on_session_end\n"
    )
    (plugin_dir / "plugin.yaml").write_text(yaml_text)

    init_text = (
        "from hermes_okf.memory_plugin import HermesOKFMemoryProvider\n"
        '__all__ = ["HermesOKFMemoryProvider"]\n'
    )
    (plugin_dir / "__init__.py").write_text(init_text)

    print(f"Installed hermes-okf plugin to {plugin_dir}")

    # Auto-configure Hermes config.yaml
    config_modified = _configure_hermes_config(hermes_home)
    if config_modified:
        print("  Updated ~/.hermes/config.yaml")
        print("  Run 'hermes memory setup' to finish activation")
    else:
        print("  Run 'hermes memory setup' to activate")


def uninstall_plugin() -> None:
    """Remove the Hermes plugin wrapper from ~/.hermes/plugins/hermes-okf/."""
    plugin_dir = Path.home() / ".hermes" / "plugins" / "hermes-okf"
    if plugin_dir.exists():
        shutil.rmtree(plugin_dir)
        print(f"Removed hermes-okf plugin from {plugin_dir}")
    else:
        print("hermes-okf plugin not installed")


if __name__ == "__main__":
    install_plugin()
