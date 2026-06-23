# Git History

> **Track every agent action with automatic Git commits.**

## Quick start

```bash
pip install hermes-okf[git]
```

Add to `~/.hermes/config.yaml`:
```yaml
memory:
  provider: hermes-okf
  bundle_path: ~/.hermes/okf_memory
  enable_git: true
```

## What gets committed

| Event | Commit prefix | Example |
|-------|--------------|---------|
| Session end | `[session]` | `[session] ended deploy-001 — 12 concepts, 4 tool calls` |
| Snapshot | `[snapshot]` | `[snapshot] Before deployment` |
| Plan complete | `[plan]` | `[plan] completed Deploy API — 4/4 steps` |
| Decision | `[decision]` | `[decision] Use 3 replicas` |
| Memory write | `[memory]` | `[memory] 3 writes` |

## CLI

```bash
# View history
hermes-okf log --git --oneline

# Show diff
hermes-okf diff HEAD~1

# Revert to previous state
hermes-okf revert HEAD~1
```

## Programmatic use

```python
from hermes_okf import GitOKFBundle

bundle = GitOKFBundle("~/.hermes/okf_memory")

# Read history
for c in bundle.git_log(limit=10):
    print(f"{c['hex'][:8]}  {c['message']}")

# Diff
changes = bundle.git_diff("HEAD~1", "HEAD")

# Revert
bundle.git_revert("HEAD~1")
```

## Design notes

- **Opt-in**: `enable_git: false` by default
- **Lightweight**: Commits only on significant events, not every write
- **Non-destructive**: `revert` creates a new commit rather than erasing history
