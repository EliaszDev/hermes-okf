"""General Hermes plugin registration for hermes-okf.

This module registers the ``hermes okf`` CLI subcommand via the
general Hermes plugin system (``hermes_agent.plugins`` entry point).

Memory-provider plugins installed via pip cannot rely on the
convention-based ``cli.py`` discovery used for in-tree or
user-directory providers (``plugins/memory/<name>/cli.py``).
Instead, they register CLI commands through the general plugin
``register(ctx)`` hook using ``ctx.register_cli_command()``.

Reference:
    https://github.com/NousResearch/hermes-agent/blob/main/
    website/docs/guides/build-a-hermes-plugin.md
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from hermes_cli.plugins import PluginContext


def register(ctx: PluginContext) -> None:
    """Register the ``hermes okf`` CLI command tree.

    Called by Hermes' ``PluginManager`` when the plugin is discovered
    via the ``hermes_agent.plugins`` entry point.
    """
    from hermes_okf.cli_extension import register_cli

    ctx.register_cli_command(
        name="okf",
        help="Hermes OKF memory commands",
        setup_fn=register_cli,
        handler_fn=None,  # subparsers set their own ``func`` defaults
    )
