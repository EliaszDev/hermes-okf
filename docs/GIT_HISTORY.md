# Git History

> **Track every agent action with automatic Git commits.**

Git-backed bundles give you an audit trail of everything your agent does. See what changed, when, and why. Roll back bad decisions without losing the rest of the session.

## Quick start

### Install

```bash
pip install hermes-okf[git]
```

### Enable

Add to `~/.hermes/config.yaml`:

```yaml
memory:
  provider: hermes-okf
  bundle_path: ~/.hermes/okf_memory
  enable_git: true
```

Or via environment variable:

```bash
export HERMES_OKF_ENABLE_GIT=1
```

### Verify

```bash
hermes-okf log --git --oneline
```

## What gets committed

| Event | Commit message prefix | Example |
|-------|----------------------|---------|
| Session end | `[session]` | `[session] ended deploy-001 — 12 concepts, 4 tool calls` |
| Snapshot | `[snapshot]` | `[snapshot] Before deployment` |
| Plan complete | `[plan]` | `[plan] completed Deploy API — 4/4 steps` |
| Decision | `[decision]` | `[decision] Use 3 replicas` |
| Memory write (batch) | `[memory]` | `[memory] 3 writes` |

Commits are authored as `Hermes Agent <agent@{agent_id}>`.

## CLI commands

### View history

```bash
# Full log with author, date, message
hermes-okf log --path ~/.hermes/okf_memory --git

# Compact one-line view
hermes-okf log --path ~/.hermes/okf_memory --git --oneline

# Limit commits
hermes-okf log --path ~/.hermes/okf_memory --git --limit 5
```

### Show what changed

```bash
# What changed in the last commit
hermes-okf diff --path ~/.hermes/okf_memory HEAD~1

# Changes across last 5 commits
hermes-okf diff --path ~/.hermes/okf_memory HEAD~5..HEAD
```

### Revert to previous state

```bash
# Restore bundle to previous commit (creates new commit, preserves history)
hermes-okf revert --path ~/.hermes/okf_memory HEAD~1
```

## Programmatic use

```python
from hermes_okf import GitOKFBundle

bundle = GitOKFBundle("~/.hermes/okf_memory")

# Manual commit
bundle.auto_commit(
    action="session_end",
    session_id="deploy-001",
    concept_count=12,
    tool_call_count=4,
)

# Read history
for commit in bundle.git_log(limit=10):
    print(f"{commit['hex'][:8]}  {commit['message']}")

# Diff between commits
changes = bundle.git_diff("HEAD~1", "HEAD")
for ch in changes:
    print(f"{ch['path']}: +{ch['additions']} -{ch['deletions']}")

# Revert to previous state
bundle.git_revert("HEAD~1")
```

## `.gitignore`

GitOKFBundle automatically creates a `.gitignore` in the bundle root:

```gitignore
# OKF index
.okf_index/

# ChromaDB vector store
.chroma/

# Python cache
__pycache__/
*.pyc
```

## Design

- **Opt-in**: `enable_git: false` (default) means zero behaviour change
- **Lightweight**: Commits only on significant events (session end, not every write)
- **Non-destructive**: `revert` creates a new commit rather than erasing history
- **Backward compatible**: `OKFBundle` remains the base class; `GitOKFBundle` extends it

## Error handling

| Scenario | Behaviour |
|----------|-----------|
| `gitpython` not installed | `ImportError` with install instructions |
| `git` binary missing | Runtime error with OS-specific instructions |
| Bundle not a git repo | Auto-initialised on first `GitOKFBundle` creation |
| No changes to commit | `auto_commit()` returns `None` (no empty commits) |

## Related

- [Config Validator](CONFIG_VALIDATOR.md) — Verify setup before enabling Git
- [CLI Reference](CLI-Reference.md) — Full command list
- [Troubleshooting](Troubleshooting.md) — Common issues
