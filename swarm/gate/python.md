# Gate recipe: Python

Assumes a virtualenv at `.venv/`. Commands are written for PowerShell on Windows; on POSIX use
`.venv/bin/` instead of `.venv/Scripts/`.

| Step | Tool | Command |
|------|------|---------|
| tests | pytest | `.venv/Scripts/pytest.exe -q` |
| coverage | coverage.py | `.venv/Scripts/coverage.exe run -m pytest -q` then `coverage report --fail-under=<n>` |
| duplication | pylint's duplicate-code checker | `pylint --disable=all --enable=duplicate-code <pkg>` |
| mutation | mutmut | `mutmut run` then `mutmut results` |
| crap | build it — see below | — |
| acceptance | pytest-bdd | `.venv/Scripts/pytest.exe -q <feature-dir>` |

## CRAP has no off-the-shelf Python tool

Build one. It is a small script, not a project:

1. `radon cc -j <pkg>` gives cyclomatic complexity per function as JSON.
2. `coverage json` gives per-line execution, which reduces to per-function coverage.
3. Join on function, then compute `complexity² × (1 − coverage)³ + complexity`.
4. Exit non-zero on any function above the project's `crap_max` (default 6).

Keep it in the target project under `tools/`, not vendored into the swarm repo. When you build
it, replace this section with the command that runs it.

## Notes

- `mutmut` is slow on large packages. Scope it to the package under change rather than the repo.
- Keep property tests (Hypothesis) tagged and excluded from the coverage, mutation, and CRAP
  runs — constitution §2.
