"""Tests for config_validator.py.

Covers all 15 checks and edge cases for ConfigValidator.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from hermes_okf.config_validator import ConfigValidator, format_report

# ------------------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------------------


@pytest.fixture
def fake_hermes_home(tmp_path: Path) -> Path:
    """Create a fresh fake ~/.hermes directory."""
    return tmp_path / "hermes"


# ------------------------------------------------------------------------------
# Happy path: all checks pass
# ------------------------------------------------------------------------------


class TestHappyPath:
    """Valid config — all 15 checks pass."""

    def test_all_checks_pass(self, fake_hermes_home: Path) -> None:
        hermes_home = fake_hermes_home
        plugins_dir = hermes_home / "plugins" / "hermes-okf"
        plugins_dir.mkdir(parents=True)

        # plugin.yaml
        (plugins_dir / "plugin.yaml").write_text(
            "name: hermes-okf\nversion: 0.5.0\n", encoding="utf-8"
        )

        # config.yaml with correct structure
        config = {
            "plugins": {"enabled": ["hermes-okf"]},
            "memory": {
                "provider": "hermes-okf",
                "bundle_path": str(hermes_home / "okf_memory"),
            },
            "model": "kimi/k2.6",
        }
        (hermes_home / "config.yaml").write_text(
            yaml.dump(config, default_flow_style=False), encoding="utf-8"
        )

        # okf_memory bundle
        bundle_path = hermes_home / "okf_memory"
        bundle_path.mkdir()
        (bundle_path / "index.md").write_text("# OKF Bundle\n", encoding="utf-8")

        validator = ConfigValidator(hermes_home=hermes_home)
        report = validator.validate()

        assert report.passed is True
        assert not report.has_critical_failures()
        assert not report.has_warnings()

        # Verify specific checks passed
        names = {r.name: r for r in report.results}
        assert names["hermes_okf importable"].passed is True
        assert names["version compatibility"].passed is True
        assert names["Hermes home directory"].passed is True
        assert names["Plugin directory"].passed is True
        assert names["plugin.yaml valid"].passed is True
        assert names["config.yaml exists"].passed is True
        assert names["config.yaml parseable"].passed is True
        assert names["plugins.enabled is list"].passed is True
        assert names["hermes-okf in plugins.enabled"].passed is True
        assert names["memory.provider set"].passed is True
        assert names["memory.provider is hermes-okf"].passed is True
        assert names["memory.bundle_path set"].passed is True
        assert names["Model detected"].passed is True
        assert names["Bundle writable"].passed is True

    def test_format_report_success(self, fake_hermes_home: Path) -> None:
        hermes_home = fake_hermes_home
        (hermes_home / "plugins" / "hermes-okf").mkdir(parents=True)
        (hermes_home / "plugins" / "hermes-okf" / "plugin.yaml").write_text(
            "name: hermes-okf\n", encoding="utf-8"
        )
        config = {"plugins": {"enabled": ["hermes-okf"]}, "memory": {"provider": "hermes-okf"}}
        (hermes_home / "config.yaml").write_text(yaml.dump(config), encoding="utf-8")
        (hermes_home / "okf_memory").mkdir()

        report = ConfigValidator(hermes_home=hermes_home).validate()
        text = format_report(report)

        assert "✅ hermes-okf" in text
        assert "all critical checks passed" in text
        assert "Hermes should discover" in text


# ------------------------------------------------------------------------------
# Critical failure cases
# ------------------------------------------------------------------------------


class TestCriticalFailures:
    """Config that fails critical checks."""

    def test_no_hermes_home(self, fake_hermes_home: Path) -> None:
        """Hermes home directory does not exist."""
        validator = ConfigValidator(hermes_home=fake_hermes_home)
        report = validator.validate()

        assert report.passed is False
        assert report.has_critical_failures()

        names = {r.name: r for r in report.results}
        assert names["Hermes home directory"].passed is False
        assert "Run Hermes once" in names["Hermes home directory"].fix

    def test_no_plugin_dir(self, fake_hermes_home: Path) -> None:
        """Plugin directory missing."""
        hermes_home = fake_hermes_home
        hermes_home.mkdir()

        validator = ConfigValidator(hermes_home=hermes_home)
        report = validator.validate()

        assert report.passed is False
        names = {r.name: r for r in report.results}
        assert names["Plugin directory"].passed is False
        assert "install-plugin" in names["Plugin directory"].fix

    def test_no_config_yaml(self, fake_hermes_home: Path) -> None:
        """config.yaml missing."""
        hermes_home = fake_hermes_home
        (hermes_home / "plugins" / "hermes-okf").mkdir(parents=True)
        (hermes_home / "plugins" / "hermes-okf" / "plugin.yaml").write_text(
            "name: hermes-okf\n", encoding="utf-8"
        )

        report = ConfigValidator(hermes_home=hermes_home).validate()
        assert report.passed is False
        names = {r.name: r for r in report.results}
        assert names["config.yaml exists"].passed is False

    def test_corrupt_yaml(self, fake_hermes_home: Path) -> None:
        """config.yaml is not valid YAML."""
        hermes_home = fake_hermes_home
        (hermes_home / "plugins" / "hermes-okf").mkdir(parents=True)
        (hermes_home / "plugins" / "hermes-okf" / "plugin.yaml").write_text(
            "name: hermes-okf\n", encoding="utf-8"
        )
        (hermes_home / "config.yaml").write_text(
            "plugins: { enabled: [hermes-okf\n", encoding="utf-8"  # unclosed bracket
        )

        report = ConfigValidator(hermes_home=hermes_home).validate()
        assert report.passed is False
        names = {r.name: r for r in report.results}
        assert names["config.yaml parseable"].passed is False
        assert "parse error" in names["config.yaml parseable"].message

    def test_plugins_enabled_json_string(self, fake_hermes_home: Path) -> None:
        """plugins.enabled is a JSON string, not a list."""
        hermes_home = fake_hermes_home
        (hermes_home / "plugins" / "hermes-okf").mkdir(parents=True)
        (hermes_home / "plugins" / "hermes-okf" / "plugin.yaml").write_text(
            "name: hermes-okf\n", encoding="utf-8"
        )
        config = {
            "plugins": {"enabled": '["hermes-okf"]'},  # JSON string, not list
            "memory": {"provider": "hermes-okf"},
        }
        (hermes_home / "config.yaml").write_text(yaml.dump(config), encoding="utf-8")

        report = ConfigValidator(hermes_home=hermes_home).validate()
        assert report.passed is False
        names = {r.name: r for r in report.results}
        assert names["plugins.enabled is list"].passed is False
        assert "str" in names["plugins.enabled is list"].message

    def test_plugins_enabled_missing_hermes_okf(self, fake_hermes_home: Path) -> None:
        """plugins.enabled is a list but does not contain hermes-okf."""
        hermes_home = fake_hermes_home
        (hermes_home / "plugins" / "hermes-okf").mkdir(parents=True)
        (hermes_home / "plugins" / "hermes-okf" / "plugin.yaml").write_text(
            "name: hermes-okf\n", encoding="utf-8"
        )
        config = {"plugins": {"enabled": ["other-plugin"]}, "memory": {"provider": "hermes-okf"}}
        (hermes_home / "config.yaml").write_text(yaml.dump(config), encoding="utf-8")

        report = ConfigValidator(hermes_home=hermes_home).validate()
        assert report.passed is False
        names = {r.name: r for r in report.results}
        assert names["hermes-okf in plugins.enabled"].passed is False
        assert "is NOT" in names["hermes-okf in plugins.enabled"].message


# ------------------------------------------------------------------------------
# Warning cases
# ------------------------------------------------------------------------------


class TestWarnings:
    """Config that passes critical but has warnings."""

    def test_memory_provider_missing(self, fake_hermes_home: Path) -> None:
        """memory.provider not set — warning, not critical."""
        hermes_home = fake_hermes_home
        (hermes_home / "plugins" / "hermes-okf").mkdir(parents=True)
        (hermes_home / "plugins" / "hermes-okf" / "plugin.yaml").write_text(
            "name: hermes-okf\n", encoding="utf-8"
        )
        config = {
            "plugins": {"enabled": ["hermes-okf"]},
            # no memory section at all
        }
        (hermes_home / "config.yaml").write_text(yaml.dump(config), encoding="utf-8")
        (hermes_home / "okf_memory").mkdir()

        report = ConfigValidator(hermes_home=hermes_home).validate()
        assert report.passed is True  # critical checks pass
        assert report.has_warnings() is True
        names = {r.name: r for r in report.results}
        assert names["memory.provider set"].passed is False
        assert names["memory.provider is hermes-okf"].passed is False

    def test_memory_provider_wrong(self, fake_hermes_home: Path) -> None:
        """memory.provider is set to something else."""
        hermes_home = fake_hermes_home
        (hermes_home / "plugins" / "hermes-okf").mkdir(parents=True)
        (hermes_home / "plugins" / "hermes-okf" / "plugin.yaml").write_text(
            "name: hermes-okf\n", encoding="utf-8"
        )
        config = {
            "plugins": {"enabled": ["hermes-okf"]},
            "memory": {"provider": "sqlite"},
        }
        (hermes_home / "config.yaml").write_text(yaml.dump(config), encoding="utf-8")
        (hermes_home / "okf_memory").mkdir()

        report = ConfigValidator(hermes_home=hermes_home).validate()
        assert report.passed is True
        names = {r.name: r for r in report.results}
        assert names["memory.provider is hermes-okf"].passed is False
        assert "sqlite" in names["memory.provider is hermes-okf"].message

    def test_bundle_path_missing(self, fake_hermes_home: Path) -> None:
        """memory.bundle_path not set."""
        hermes_home = fake_hermes_home
        (hermes_home / "plugins" / "hermes-okf").mkdir(parents=True)
        (hermes_home / "plugins" / "hermes-okf" / "plugin.yaml").write_text(
            "name: hermes-okf\n", encoding="utf-8"
        )
        config = {
            "plugins": {"enabled": ["hermes-okf"]},
            "memory": {"provider": "hermes-okf"},  # no bundle_path
        }
        (hermes_home / "config.yaml").write_text(yaml.dump(config), encoding="utf-8")

        report = ConfigValidator(hermes_home=hermes_home).validate()
        assert report.passed is True
        names = {r.name: r for r in report.results}
        assert names["memory.bundle_path set"].passed is False

    def test_model_not_detected(self, fake_hermes_home: Path) -> None:
        """No model in config — info severity."""
        hermes_home = fake_hermes_home
        (hermes_home / "plugins" / "hermes-okf").mkdir(parents=True)
        (hermes_home / "plugins" / "hermes-okf" / "plugin.yaml").write_text(
            "name: hermes-okf\n", encoding="utf-8"
        )
        config = {
            "plugins": {"enabled": ["hermes-okf"]},
            "memory": {"provider": "hermes-okf", "bundle_path": "~/.hermes/okf_memory"},
            # no model field
        }
        (hermes_home / "config.yaml").write_text(yaml.dump(config), encoding="utf-8")
        (hermes_home / "okf_memory").mkdir()

        report = ConfigValidator(hermes_home=hermes_home).validate()
        assert report.passed is True
        names = {r.name: r for r in report.results}
        assert names["Model detected"].passed is False
        assert names["Model detected"].severity == "info"

    def test_bundle_not_writable(self, fake_hermes_home: Path) -> None:
        """Bundle directory exists but is not writable."""
        import sys

        if sys.platform == "win32":
            pytest.skip("chmod-based read-only test not reliable on Windows")

        hermes_home = fake_hermes_home
        (hermes_home / "plugins" / "hermes-okf").mkdir(parents=True)
        (hermes_home / "plugins" / "hermes-okf" / "plugin.yaml").write_text(
            "name: hermes-okf\n", encoding="utf-8"
        )
        config = {
            "plugins": {"enabled": ["hermes-okf"]},
            "memory": {"provider": "hermes-okf", "bundle_path": str(hermes_home / "okf_memory")},
        }
        (hermes_home / "config.yaml").write_text(yaml.dump(config), encoding="utf-8")
        bundle = hermes_home / "okf_memory"
        bundle.mkdir()
        bundle.chmod(0o555)  # read-only

        try:
            report = ConfigValidator(hermes_home=hermes_home).validate()
            assert report.passed is True
            names = {r.name: r for r in report.results}
            assert names["Bundle writable"].passed is False
            assert names["Bundle writable"].severity == "warning"
        finally:
            bundle.chmod(0o755)  # restore


# ------------------------------------------------------------------------------
# Format report
# ------------------------------------------------------------------------------


class TestFormatReport:
    """Tests for format_report()."""

    def test_format_failure(self, fake_hermes_home: Path) -> None:
        """Failed report has the right shape."""
        hermes_home = fake_hermes_home
        hermes_home.mkdir()  # empty — many checks will fail
        report = ConfigValidator(hermes_home=hermes_home).validate()

        text = format_report(report)
        assert "❌ hermes-okf config validation failed" in text
        assert "[CRITICAL]" in text
        assert "Fix:" in text

    def test_format_success(self, fake_hermes_home: Path) -> None:
        """Success report has the right shape."""
        hermes_home = fake_hermes_home
        (hermes_home / "plugins" / "hermes-okf").mkdir(parents=True)
        (hermes_home / "plugins" / "hermes-okf" / "plugin.yaml").write_text(
            "name: hermes-okf\n", encoding="utf-8"
        )
        config = {
            "plugins": {"enabled": ["hermes-okf"]},
            "memory": {"provider": "hermes-okf", "bundle_path": str(hermes_home / "okf_memory")},
            "model": "kimi/k2.6",
        }
        (hermes_home / "config.yaml").write_text(yaml.dump(config), encoding="utf-8")
        (hermes_home / "okf_memory").mkdir()

        report = ConfigValidator(hermes_home=hermes_home).validate()
        text = format_report(report)
        assert "✅ hermes-okf" in text
        assert "all critical checks passed" in text


# ------------------------------------------------------------------------------
# Edge cases
# ------------------------------------------------------------------------------


class TestEdgeCases:
    """Unusual but valid configs."""

    def test_model_under_llm_key(self, fake_hermes_home: Path) -> None:
        """Model is under llm.model, not top-level."""
        hermes_home = fake_hermes_home
        (hermes_home / "plugins" / "hermes-okf").mkdir(parents=True)
        (hermes_home / "plugins" / "hermes-okf" / "plugin.yaml").write_text(
            "name: hermes-okf\n", encoding="utf-8"
        )
        config = {
            "plugins": {"enabled": ["hermes-okf"]},
            "memory": {"provider": "hermes-okf", "bundle_path": str(hermes_home / "okf_memory")},
            "llm": {"model": "openai/gpt-4o"},
        }
        (hermes_home / "config.yaml").write_text(yaml.dump(config), encoding="utf-8")
        (hermes_home / "okf_memory").mkdir()

        report = ConfigValidator(hermes_home=hermes_home).validate()
        assert report.passed is True
        names = {r.name: r for r in report.results}
        assert names["Model detected"].passed is True
        assert "openai/gpt-4o" in names["Model detected"].value

    def test_plugins_enabled_none(self, fake_hermes_home: Path) -> None:
        """plugins.enabled is None (not set)."""
        hermes_home = fake_hermes_home
        (hermes_home / "plugins" / "hermes-okf").mkdir(parents=True)
        (hermes_home / "plugins" / "hermes-okf" / "plugin.yaml").write_text(
            "name: hermes-okf\n", encoding="utf-8"
        )
        config = {"plugins": {}}  # no enabled key
        (hermes_home / "config.yaml").write_text(yaml.dump(config), encoding="utf-8")

        report = ConfigValidator(hermes_home=hermes_home).validate()
        assert report.passed is False
        names = {r.name: r for r in report.results}
        assert names["plugins.enabled is list"].passed is False

    def test_plugins_section_missing(self, fake_hermes_home: Path) -> None:
        """No plugins section at all."""
        hermes_home = fake_hermes_home
        (hermes_home / "plugins" / "hermes-okf").mkdir(parents=True)
        (hermes_home / "plugins" / "hermes-okf" / "plugin.yaml").write_text(
            "name: hermes-okf\n", encoding="utf-8"
        )
        config = {"memory": {"provider": "hermes-okf"}}  # no plugins key
        (hermes_home / "config.yaml").write_text(yaml.dump(config), encoding="utf-8")

        report = ConfigValidator(hermes_home=hermes_home).validate()
        assert report.passed is False
        names = {r.name: r for r in report.results}
        assert names["plugins.enabled is list"].passed is False

    def test_empty_plugin_yaml(self, fake_hermes_home: Path) -> None:
        """plugin.yaml is empty."""
        hermes_home = fake_hermes_home
        (hermes_home / "plugins" / "hermes-okf").mkdir(parents=True)
        (hermes_home / "plugins" / "hermes-okf" / "plugin.yaml").write_text("", encoding="utf-8")
        config = {"plugins": {"enabled": ["hermes-okf"]}, "memory": {"provider": "hermes-okf"}}
        (hermes_home / "config.yaml").write_text(yaml.dump(config), encoding="utf-8")

        report = ConfigValidator(hermes_home=hermes_home).validate()
        # plugin.yaml empty → parsed as None, missing name field → warning
        names = {r.name: r for r in report.results}
        assert names["plugin.yaml valid"].passed is False

    def test_no_plugins_section_no_memory(self, fake_hermes_home: Path) -> None:
        """Completely empty config.yaml."""
        hermes_home = fake_hermes_home
        (hermes_home / "plugins" / "hermes-okf").mkdir(parents=True)
        (hermes_home / "plugins" / "hermes-okf" / "plugin.yaml").write_text(
            "name: hermes-okf\n", encoding="utf-8"
        )
        (hermes_home / "config.yaml").write_text("", encoding="utf-8")

        report = ConfigValidator(hermes_home=hermes_home).validate()
        # config.yaml empty → parsed as None, then checks fail
        assert report.passed is False
        names = {r.name: r for r in report.results}
        assert names["plugins.enabled is list"].passed is False


# ------------------------------------------------------------------------------
# Version parsing
# ------------------------------------------------------------------------------


def test_parse_version() -> None:
    from hermes_okf.config_validator import _parse_version

    assert _parse_version("0.5.0") == (0, 5, 0)
    assert _parse_version("1.2.3") == (1, 2, 3)
    assert _parse_version("0.4.6") == (0, 4, 6)
    assert _parse_version("0.10.0") == (0, 10, 0)
