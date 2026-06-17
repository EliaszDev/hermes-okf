# Troubleshooting

> **Common issues and how to fix them.**

---

## Installation Issues

### `hermes-okf install-plugin` is not found

**Cause:** The `hermes-okf` CLI is not installed or not in your PATH.

**Fixes:**

**Option 1 — Upgrade to the latest version:**
```bash
pip install --upgrade hermes-okf
hermes-okf --version
# Expected: 0.5.0+
```

**Option 2 — Use the module form:**
```bash
python -m hermes_okf.cli install-plugin
```

**Option 3 — Use the venv's Python directly:**
```bash
~/.hermes/hermes-agent/venv/bin/python -m hermes_okf.cli install-plugin
```

---

## Hermes Discovery Issues

### `hermes memory setup` doesn't show hermes-okf

**Cause:** Hermes doesn't see the plugin in `~/.hermes/plugins/`.

**Diagnosis:**
```bash
ls ~/.hermes/plugins/hermes-okf/
# Should show: __init__.py  plugin.yaml
```

**Fixes:**

1. **Run the install command:**
   ```bash
   hermes-okf install-plugin
   ```

2. **Check `plugins.enabled` in `~/.hermes/config.yaml`:**
   ```yaml
   plugins:
     enabled:
       - hermes-okf
   ```
   > Must be a YAML list, not a JSON string. This is wrong:
   > ```yaml
   > plugins:
   >   enabled: "[\"hermes-okf\"]"  # ❌ JSON string, Hermes ignores it
   > ```

3. **Restart Hermes:**
   ```bash
   hermes
   ```

---

## Config Issues

### `hermes okf show config/agent` shows wrong model

**Cause:** The OKF config concept was written before v0.3.7, or Hermes hasn't been restarted since the upgrade.

**Fix:** As of v0.3.7, `HermesOKFMemoryProvider.initialize()` reads the actual Hermes model from `config.yaml` (top-level `model` or `llm.model`) and syncs it into the OKF `config/agent` concept on every session start.

1. **Upgrade hermes-okf:**
   ```bash
   pip install --upgrade hermes-okf
   ```

2. **Restart Hermes:**
   ```bash
   hermes
   ```

3. **Verify:**
   ```bash
   hermes okf show config/agent
   ```
   The `model:` field should now match your actual Hermes model.

---

## OKF Bundle Issues

### "OKF bundle not found"

**Fix:** Initialize a new bundle:
```bash
hermes-okf init ~/.hermes/okf_memory
```

Or let the Hermes plugin create it automatically on first session start.

---

## CLI Issues

### `hermes okf show` throws `AttributeError: 'Concept' object has no attribute 'content'`

**Cause:** You're running hermes-okf v0.3.4 or earlier. The `show` command used `concept.content` instead of `concept.body`.

**Fix:** Upgrade to v0.3.5 or later:
```bash
pip install --upgrade hermes-okf
```

---

## Windows-Specific Issues

### Filename errors with colons

**Cause:** Older versions used `:` in filenames (e.g., `2026-06-15T10:30:00Z`), which is invalid on Windows.

**Fix:** Hermes-OKF v0.2.0+ uses Windows-safe filenames (`2026-06-15T10-30-00Z` instead of `2026-06-15T10:30:00Z`). Upgrade:

```bash
pip install --upgrade hermes-okf
```

---

## Performance Issues

### Slow memory writes

**Cause:** Hot memory buffer is flushing too frequently.

**Fix:** Increase `hot_memory_max` in your config:

```yaml
memory:
  provider: hermes-okf
  hot_memory_max: 200  # Default is 50
```

Or set via environment variable:
```bash
export HERMES_OKF_HOT_MEMORY_MAX=200
```

---

## Still Stuck?

- Open an issue: [github.com/EliaszDev/hermes-okf/issues](https://github.com/EliaszDev/hermes-okf/issues)
- Hermes Agent docs: [github.com/NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent)
- Check your version: `python -c "import hermes_okf; print(hermes_okf.__version__)"`
