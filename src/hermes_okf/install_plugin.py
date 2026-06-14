"""Install hermes-okf as a Hermes memory provider plugin.

Creates the plugin wrapper in ~/.hermes/plugins/hermes-okf/ so that
Hermes' directory-based discovery finds it automatically.
"""

from __future__ import annotations

from pathlib import Path

import hermes_okf


def install_plugin() -> None:
    """Create the Hermes plugin wrapper in ~/.hermes/plugins/hermes-okf/."""
    hermes_home = Path.home() / ".hermes"
    plugins_dir = hermes_home / "plugins"
    plugin_dir = plugins_dir / "hermes-okf"

    # Create directories
    plugin_dir.mkdir(parents=True, exist_ok=True)

    # Create plugin.yaml
    (plugin_dir / "plugin.yaml").write_text(
        "name: hermes-okf\n"
        f"version: {hermes_okf.__version__}\n"
        'description: "OKF-based memory provider for Hermes agent — '
        'structured, persistent, agent-readable knowledge storage."\n'
        "hooks:\n"
        "  - on_session_end\n"
    )

    # Create __init__.py wrapper
    (plugin_dir / "__init__.py").write_text(
        "from hermes_okf.memory_plugin import HermesOKFMemoryProvider\n"
        "__all__ = [\"HermesOKFMemoryProvider\"]\n"
    )

    print(f"✓ Installed hermes-okf plugin to {plugin_dir}")
    print("  Run 'hermes memory setup' to activate")


def uninstall_plugin() -> None:
    """Remove the Hermes plugin wrapper from ~/.hermes/plugins/hermes-okf/."""
    plugin_dir = Path.home() / ".hermes" / "plugins" / "hermes-okf"
    if plugin_dir.exists():
        import shutil

        shutil.rmtree(plugin_dir)
        print(f"✓ Removed hermes-okf plugin from {plugin_dir}")
    else:
        print("hermes-okf plugin not installed")


if __name__ == "__main__":
    install_plugin()
