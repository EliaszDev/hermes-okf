# Config Validator

> **Diagnose Hermes plugin setup issues in 5 seconds.**

Run this after installation or any time Hermes doesn't discover `hermes-okf`.

## Usage

```bash
hermes-okf validate-config
```

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | All critical checks passed |
| 1 | One or more critical checks failed |

## Common failures

### Plugin directory not found
```
[CRITICAL] Plugin directory
  Not found: ~/.hermes/plugins/hermes-okf
  Fix: hermes-okf install-plugin
```
**Fix:** Run `hermes-okf install-plugin`.

### plugins.enabled is a JSON string
```
[CRITICAL] plugins.enabled is list
  plugins.enabled is a str
  Fix: Use YAML list format
```
**Fix:** Change `"[\"hermes-okf\"]"` to:
```yaml
plugins:
  enabled:
    - hermes-okf
```

### memory.provider not set
```
[WARNING] memory.provider set
  memory.provider is NOT set
  Fix: hermes-okf install-plugin (sets default)
```
**Fix:** Run `hermes-okf install-plugin` or add `memory.provider: hermes-okf` to config.

## Programmatic use

```python
from hermes_okf import ConfigValidator

report = ConfigValidator().validate()
if not report.passed:
    for r in report.results:
        if not r.passed:
            print(f"{r.severity}: {r.name} — {r.message}")
```
