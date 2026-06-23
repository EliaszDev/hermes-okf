# Config Validator

> **Diagnose Hermes plugin setup issues in 5 seconds.**

The `hermes-okf` config validator catches 80% of setup issues before they become support tickets. Run it after installation and any time Hermes doesn't seem to discover the plugin.

## Usage

```bash
hermes-okf validate-config
```

No arguments needed — it checks `~/.hermes/` automatically.

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | All critical checks passed (warnings OK) |
| 1 | One or more critical checks failed |

## Checks performed

### Critical (🔴 fail = exit 1)

| # | Check | What it means | Fix |
|---|-------|---------------|-----|
| 1 | `hermes_okf` importable | The current Python can import the package | Check you're in the right virtual environment |
| 3 | `~/.hermes/` exists | Hermes home directory created | Run `hermes` once to auto-create it |
| 4 | Plugin directory exists | `~/.hermes/plugins/hermes-okf/` found | Run `hermes-okf install-plugin` |
| 6 | `config.yaml` exists | Hermes config file present | Create `~/.hermes/config.yaml` manually |
| 7 | `config.yaml` parseable | Valid YAML syntax | Fix YAML syntax errors |
| 8 | `plugins.enabled` is list | Must be a YAML list, not JSON string | Use `- hermes-okf` format |
| 9 | `hermes-okf` in enabled | Plugin name must be in the list | Run `hermes-okf install-plugin` |

### Warnings (🟡 fix recommended but not fatal)

| # | Check | What it means | Fix |
|---|-------|---------------|-----|
| 2 | Version compatibility | `hermes-okf` >= 0.5.0 | `pip install --upgrade hermes-okf` |
| 5 | `plugin.yaml` valid | Plugin descriptor readable | Re-run `install-plugin` |
| 10 | `memory.provider` set | Memory backend configured | `hermes-okf install-plugin` sets this |
| 11 | `memory.provider` is `hermes-okf` | Correct provider selected | `hermes-okf install-plugin` or edit config |
| 12 | `memory.bundle_path` set | OKF bundle location known | Default is `~/.hermes/okf_memory` |
| 14 | Bundle writable | Directory permissions OK | `chmod u+w ~/.hermes/okf_memory` |

### Info (ℹ️ FYI only)

| # | Check | What it means |
|---|-------|---------------|
| 13 | Model detected | Shows which LLM model is configured |
| 15 | Git available | Whether `gitpython` is installed for history tracking |

## Common failures and fixes

### ❌ Plugin directory not found

```
[CRITICAL] Plugin directory
  Not found: ~/.hermes/plugins/hermes-okf
  Fix: hermes-okf install-plugin
```

**Fix:** Run `hermes-okf install-plugin` to create the plugin wrapper.

### ❌ `plugins.enabled` is a JSON string

```
[CRITICAL] plugins.enabled is list
  plugins.enabled is a str
  Fix: Edit ~/.hermes/config.yaml:
plugins:
  enabled:
    - hermes-okf
```

**Fix:** The config was written with `"[\"hermes-okf\"]"` (a JSON-encoded string). Change to a YAML list:

```yaml
plugins:
  enabled:
    - hermes-okf
```

### ❌ `memory.provider` not set

```
[WARNING] memory.provider set
  memory.provider is NOT set
  Fix: hermes-okf install-plugin (sets default)
```

**Fix:** Run `hermes-okf install-plugin` or add to `config.yaml`:

```yaml
memory:
  provider: hermes-okf
  bundle_path: ~/.hermes/okf_memory
```

## Programmatic use

```python
from hermes_okf import ConfigValidator

validator = ConfigValidator()
report = validator.validate()

if report.passed:
    print("All critical checks passed!")
else:
    for r in report.results:
        if not r.passed and r.severity == "critical":
            print(f"FAIL: {r.name} — {r.message}")
            print(f"  Fix: {r.fix}")
```

## Related

- [`hermes-okf install-plugin`](CLI-Reference.md) — One-command setup
- [Troubleshooting](Troubleshooting.md) — If validate-config doesn't solve it
