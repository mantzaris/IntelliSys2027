# Project conventions

- Keep all project code, configuration, documentation, and work inside `rep-sensitivity/`.
- Work directly on `main`. Do not create branches.
- Commit completed work on `main`; the user will push. Do not push automatically.
- Stage and commit all essential project changes, reviewing the staged files first.
- Keep the repository small: do not commit bulk datasets, model weights, checkpoints,
  logs, caches, virtual environments, or generated batch outputs.
- Store generated files in the ignored directories listed in `.gitignore`. Commit
  reproducible scripts, dependency declarations, and small curated results when
  needed to understand or reproduce the work.
- Do not commit credentials, private keys, or environment secrets.
