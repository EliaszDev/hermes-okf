"""Config validator for hermes-okf Hermes plugin setup.

Validates that Hermes can discover and load the hermes-okf plugin.
Runs 15 checks covering the most common setup issues.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import hermes_okf


@dataclass
class CheckResult:
    """Result of a single validation check."""

    name: str
    passed: bool
    severity: str  # "critical", "warning", "info"
    message: str
    fix: str = ""
    value: str = ""


@dataclass
class ValidationReport:
    """Aggregate report from all validation checks."""

    passed: bool
    results: list[CheckResult] = field(default_factory=list)

    def has_critical_failures(self) -> bool:
        return any(not r.passed and r.severity == "critical" for r in self.results)

    def has_warnings(self) -> bool:
        return any(not r.passed and r.severity == "warning" for r in self.results)


class ConfigValidator:
    """Validate Hermes plugin configuration for hermes-okf."""

    def __init__(self, hermes_home: str | Path = "~/.hermes") -> None:
        self.hermes_home = Path(hermes_home).expanduser()
        self.results: list[CheckResult] = []
        self._config: dict[str, Any] | None = None

    def validate(self) -> ValidationReport:
        """Run all checks and return a report."""
        self.results = []

        self._check_importable()
        self._check_version()
        self._check_hermes_home()
        self._check_plugin_dir()
        self._check_plugin_yaml()
        self._check_config_yaml_exists()
        self._check_config_yaml_parseable()
        self._check_plugins_enabled_type()
        self._check_plugins_enabled_value()
        self._check_memory_provider_set()
        self._check_memory_provider_value()
        self._check_bundle_path()
        self._check_model()
        self._check_writable()
        self._check_git_available()

        passed = not self.has_critical_failures()
        return ValidationReport(passed=passed, results=self.results)

    def has_critical_failures(self) -> bool:
        return any(not r.passed and r.severity == "critical" for r in self.results)

    # ------------------------------------------------------------------
    # Individual checks
    # ------------------------------------------------------------------

    def _add(self, result: CheckResult) -> None:
        self.results.append(result)

    def _check_importable(self) -> None:
        """Check 1: hermes_okf is importable in the current Python."""
        # We already imported it at the top of this module, so if we got here
        # it's importable. However, we want to verify the *current* Python
        # which might be different from Hermes's Python. This is best-effort.
        self._add(
            CheckResult(
                name="hermes_okf importable",
                passed=True,
                severity="critical",
                message="hermes_okf is importable in the current Python",
                value=f"v{hermes_okf.__version__}",
            )
        )

    def _check_version(self) -> None:
        """Check 2: Version is at least 0.5.0."""
        try:
            current = _parse_version(hermes_okf.__version__)
            minimum = (0, 5, 0)
            passed = current >= minimum
            self._add(
                CheckResult(
                    name="version compatibility",
                    passed=passed,
                    severity="warning",
                    message=f"hermes-okf version is {hermes_okf.__version__}",
                    fix="pip install --upgrade hermes-okf" if not passed else "",
                    value=hermes_okf.__version__,
                )
            )
        except Exception:
            self._add(
                CheckResult(
                    name="version compatibility",
                    passed=False,
                    severity="warning",
                    message="Could not parse hermes-okf version",
                    fix="pip install --upgrade hermes-okf",
                )
            )

    def _check_hermes_home(self) -> None:
        """Check 3: ~/.hermes/ directory exists."""
        passed = self.hermes_home.exists()
        self._add(
            CheckResult(
                name="Hermes home directory",
                passed=passed,
                severity="critical",
                message=f"{'Found' if passed else 'Not found'}: {self.hermes_home}",
                fix="Run Hermes once to create ~/.hermes/" if not passed else "",
            )
        )

    def _check_plugin_dir(self) -> None:
        """Check 4: Plugin directory exists."""
        plugin_dir = self.hermes_home / "plugins" / "hermes-okf"
        passed = plugin_dir.exists()
        self._add(
            CheckResult(
                name="Plugin directory",
                passed=passed,
                severity="critical",
                message=f"{'Found' if passed else 'Not found'}: {plugin_dir}",
                fix="hermes-okf install-plugin" if not passed else "",
            )
        )

    def _check_plugin_yaml(self) -> None:
        """Check 5: plugin.yaml is valid YAML with a name field."""
        plugin_yaml = self.hermes_home / "plugins" / "hermes-okf" / "plugin.yaml"
        if not plugin_yaml.exists():
            self._add(
                CheckResult(
                    name="plugin.yaml valid",
                    passed=False,
                    severity="warning",
                    message="plugin.yaml not found",
                    fix="hermes-okf install-plugin",
                )
            )
            return

        try:
            import yaml

            data = yaml.safe_load(plugin_yaml.read_text(encoding="utf-8")) or {}
            passed = isinstance(data, dict) and "name" in data
            self._add(
                CheckResult(
                    name="plugin.yaml valid",
                    passed=passed,
                    severity="warning",
                    message=f"{'Valid' if passed else 'Invalid'} plugin.yaml"
                    f" (name={data.get('name', 'missing')})",
                    fix="hermes-okf install-plugin" if not passed else "",
                    value=data.get("name", ""),
                )
            )
        except Exception as exc:
            self._add(
                CheckResult(
                    name="plugin.yaml valid",
                    passed=False,
                    severity="warning",
                    message=f"Could not read plugin.yaml: {exc}",
                    fix="hermes-okf install-plugin",
                )
            )

    def _check_config_yaml_exists(self) -> None:
        """Check 6: config.yaml exists."""
        config_path = self.hermes_home / "config.yaml"
        passed = config_path.exists()
        self._add(
            CheckResult(
                name="config.yaml exists",
                passed=passed,
                severity="critical",
                message=f"{'Found' if passed else 'Not found'}: {config_path}",
                fix="Create default Hermes config or run 'hermes' once" if not passed else "",
            )
        )

    def _check_config_yaml_parseable(self) -> None:
        """Check 7: config.yaml is parseable YAML."""
        config_path = self.hermes_home / "config.yaml"
        if not config_path.exists():
            self._add(
                CheckResult(
                    name="config.yaml parseable",
                    passed=False,
                    severity="critical",
                    message="config.yaml not found — cannot parse",
                    fix="Create default Hermes config",
                )
            )
            return

        try:
            import yaml

            text = config_path.read_text(encoding="utf-8")
            self._config = yaml.safe_load(text) or {}
            self._add(
                CheckResult(
                    name="config.yaml parseable",
                    passed=True,
                    severity="critical",
                    message="config.yaml is valid YAML",
                )
            )
        except Exception as exc:
            self._config = None
            self._add(
                CheckResult(
                    name="config.yaml parseable",
                    passed=False,
                    severity="critical",
                    message=f"config.yaml YAML parse error: {exc}",
                    fix="Fix YAML syntax errors in ~/.hermes/config.yaml",
                )
            )

    def _check_plugins_enabled_type(self) -> None:
        """Check 8: plugins.enabled is a YAML list."""
        if self._config is None:
            self._add(
                CheckResult(
                    name="plugins.enabled is list",
                    passed=False,
                    severity="critical",
                    message="Cannot check plugins.enabled — config.yaml not parseable",
                    fix="Fix config.yaml first",
                )
            )
            return

        plugins = self._config.get("plugins", {})
        enabled = plugins.get("enabled")

        if enabled is None:
            self._add(
                CheckResult(
                    name="plugins.enabled is list",
                    passed=False,
                    severity="critical",
                    message="plugins.enabled not found in config.yaml",
                    fix="Add plugins.enabled as a YAML list to ~/.hermes/config.yaml",
                )
            )
            return

        passed = isinstance(enabled, list)
        self._add(
            CheckResult(
                name="plugins.enabled is list",
                passed=passed,
                severity="critical",
                message=f"plugins.enabled is a {'list' if passed else type(enabled).__name__}",
                fix=(
                    """Edit ~/.hermes/config.yaml:
plugins:
  enabled:
    - hermes-okf"""
                    if not passed
                    else ""
                ),
                value=str(enabled)[:60],
            )
        )

    def _check_plugins_enabled_value(self) -> None:
        """Check 9: hermes-okf is in plugins.enabled."""
        if self._config is None:
            self._add(
                CheckResult(
                    name="hermes-okf in plugins.enabled",
                    passed=False,
                    severity="critical",
                    message="Cannot check plugins.enabled — config.yaml not parseable",
                    fix="Fix config.yaml first",
                )
            )
            return

        plugins = self._config.get("plugins", {})
        enabled = plugins.get("enabled", [])

        if not isinstance(enabled, list):
            self._add(
                CheckResult(
                    name="hermes-okf in plugins.enabled",
                    passed=False,
                    severity="critical",
                    message="plugins.enabled is not a list — cannot check membership",
                    fix="Fix plugins.enabled to be a YAML list first",
                )
            )
            return

        passed = "hermes-okf" in enabled
        self._add(
            CheckResult(
                name="hermes-okf in plugins.enabled",
                passed=passed,
                severity="critical",
                message=f"hermes-okf {'is' if passed else 'is NOT'} in plugins.enabled",
                fix="hermes-okf install-plugin" if not passed else "",
                value=str(enabled),
            )
        )

    def _check_memory_provider_set(self) -> None:
        """Check 10: memory.provider is set."""
        if self._config is None:
            self._add(
                CheckResult(
                    name="memory.provider set",
                    passed=False,
                    severity="warning",
                    message="Cannot check memory.provider — config.yaml not parseable",
                    fix="Fix config.yaml first",
                )
            )
            return

        memory = self._config.get("memory", {})
        provider = memory.get("provider")
        passed = provider is not None
        self._add(
            CheckResult(
                name="memory.provider set",
                passed=passed,
                severity="warning",
                message=f"memory.provider is {'set' if passed else 'NOT set'}",
                fix="hermes-okf install-plugin (sets default)" if not passed else "",
                value=provider or "",
            )
        )

    def _check_memory_provider_value(self) -> None:
        """Check 11: memory.provider is hermes-okf."""
        if self._config is None:
            self._add(
                CheckResult(
                    name="memory.provider is hermes-okf",
                    passed=False,
                    severity="warning",
                    message="Cannot check memory.provider — config.yaml not parseable",
                    fix="Fix config.yaml first",
                )
            )
            return

        memory = self._config.get("memory", {})
        provider = memory.get("provider")
        passed = provider == "hermes-okf"
        self._add(
            CheckResult(
                name="memory.provider is hermes-okf",
                passed=passed,
                severity="warning",
                message=f"memory.provider is '{provider or 'not set'}'",
                fix="hermes-okf install-plugin or edit ~/.hermes/config.yaml" if not passed else "",
                value=provider or "",
            )
        )

    def _check_bundle_path(self) -> None:
        """Check 12: memory.bundle_path is set."""
        if self._config is None:
            self._add(
                CheckResult(
                    name="memory.bundle_path set",
                    passed=False,
                    severity="warning",
                    message="Cannot check bundle_path — config.yaml not parseable",
                    fix="Fix config.yaml first",
                )
            )
            return

        memory = self._config.get("memory", {})
        bundle_path = memory.get("bundle_path")
        passed = bundle_path is not None
        self._add(
            CheckResult(
                name="memory.bundle_path set",
                passed=passed,
                severity="warning",
                message=f"memory.bundle_path is {'set' if passed else 'NOT set'}",
                fix=(
                    "hermes-okf install-plugin (sets default ~/.hermes/okf_memory)"
                    if not passed
                    else ""
                ),
                value=bundle_path or "",
            )
        )

    def _check_model(self) -> None:
        """Check 13: Model is detected from config.yaml."""
        if self._config is None:
            self._add(
                CheckResult(
                    name="Model detected",
                    passed=False,
                    severity="info",
                    message="Cannot check model — config.yaml not parseable",
                    fix="Fix config.yaml first",
                )
            )
            return

        model = self._config.get("model") or self._config.get("llm", {}).get("model")
        passed = model is not None and model != ""
        self._add(
            CheckResult(
                name="Model detected",
                passed=passed,
                severity="info",
                message=f"Model: {model or 'not detected'}",
                fix=(
                    "Add 'model: <provider>/<model>' to ~/.hermes/config.yaml" if not passed else ""
                ),
                value=model or "",
            )
        )

    def _check_writable(self) -> None:
        """Check 14: OKF bundle directory is writable."""
        if self._config is None:
            # Try default bundle path
            bundle_path = self.hermes_home / "okf_memory"
        else:
            memory = self._config.get("memory", {})
            bp = memory.get("bundle_path", "~/.hermes/okf_memory")
            bundle_path = Path(bp).expanduser()

        passed = os.access(bundle_path, os.W_OK) if bundle_path.exists() else False
        self._add(
            CheckResult(
                name="Bundle writable",
                passed=passed,
                severity="warning",
                message=f"Bundle directory {'is' if passed else 'is NOT'} writable: {bundle_path}",
                fix=f"Check permissions: chmod u+w {bundle_path}" if not passed else "",
                value=str(bundle_path),
            )
        )

    def _check_git_available(self) -> None:
        """Check 15: Git is available (optional)."""
        try:
            import git  # noqa: F401

            self._add(
                CheckResult(
                    name="Git available",
                    passed=True,
                    severity="info",
                    message="gitpython is installed — Git history available",
                    fix="",
                    value="gitpython installed",
                )
            )
        except ImportError:
            self._add(
                CheckResult(
                    name="Git available",
                    passed=False,
                    severity="info",
                    message="gitpython not installed — Git history disabled",
                    fix="pip install hermes-okf[git]",
                    value="not installed",
                )
            )


# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------


def _parse_version(version_str: str) -> tuple[int, int, int]:
    """Parse a semver string into a tuple of ints."""
    parts = version_str.split(".")
    if len(parts) < 3:
        parts += ["0"] * (3 - len(parts))
    return (int(parts[0]), int(parts[1]), int(parts[2]))


# ------------------------------------------------------------------------------
# CLI formatting helpers
# ------------------------------------------------------------------------------


def format_report(report: ValidationReport) -> str:
    """Format a ValidationReport into a human-readable string."""
    lines: list[str] = []

    if report.passed:
        lines.append(f"✅ hermes-okf v{hermes_okf.__version__} — all critical checks passed")
    else:
        lines.append("❌ hermes-okf config validation failed")

    lines.append("")

    critical_failures = [r for r in report.results if not r.passed and r.severity == "critical"]
    warnings = [r for r in report.results if not r.passed and r.severity == "warning"]
    info = [r for r in report.results if not r.passed and r.severity == "info"]

    for r in critical_failures:
        lines.append(f"[CRITICAL] {r.name}")
        lines.append(f"  {r.message}")
        if r.fix:
            lines.append(f"  Fix: {r.fix}")
        lines.append("")

    for r in warnings:
        lines.append(f"[WARNING] {r.name}")
        lines.append(f"  {r.message}")
        if r.fix:
            lines.append(f"  Fix: {r.fix}")
        lines.append("")

    for r in info:
        lines.append(f"[INFO] {r.name}")
        lines.append(f"  {r.message}")
        if r.fix:
            lines.append(f"  Fix: {r.fix}")
        lines.append("")

    # Summary of passing checks
    passed_critical = [r for r in report.results if r.passed and r.severity == "critical"]
    passed_warning = [r for r in report.results if r.passed and r.severity == "warning"]

    if report.passed:
        for r in passed_critical:
            lines.append(f"✅ {r.name}: {r.message}")
        for r in passed_warning:
            lines.append(f"✅ {r.name}: {r.message}")
        lines.append("")
        lines.append("Hermes should discover hermes-okf on next startup.")
        lines.append("Run 'hermes' to start.")

    return "\n".join(lines)
