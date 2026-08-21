# Gate recipe: Python

Assumes a virtualenv at `.venv/`. Commands are written for PowerShell on Windows; on POSIX use
`.venv/bin/` instead of `.venv/Scripts/`.

| Step | Tool | Command |
|------|------|---------|
| tests | pytest | `.venv/Scripts/pytest.exe -q` |
| coverage | coverage.py | `.venv/Scripts/coverage.exe run -m pytest -q` then `coverage report --fail-under=<n>` |
| duplication | pylint's duplicate-code checker | `pylint --disable=all --enable=duplicate-code <pkg>` |
| mutation | shipped — `swarm/gate/tools/python/mutate/` | `.venv/Scripts/python.exe swarm/gate/tools/python/mutate <pkg>` |
| crap | build it — see below | — |
| acceptance | pytest-bdd | `.venv/Scripts/pytest.exe -q <feature-dir>` |

## Mutation

The runner ships with the swarm: standard library only, nothing to install, no `pip` step. Point
it at the package under change and it does the rest.

    .venv/Scripts/python.exe swarm/gate/tools/python/mutate src/pkg

- It reports **survivors only**. Add `--verbose` for one line per mutant, and expect that to be
  a few hundred lines a file.
- It is **differential by default**, against `.swarm/mutation.json`. An untouched function is
  not re-run; adding tests re-runs only the mutants that previously survived. Commit the
  manifest — that is what makes the second run cheap. Never hand-edit it.
- A file over `defaults.max_mutation_sites_per_file` is **not mutated**, reported, and the run
  exits 2. Split the file; do not raise the cap to get past it.
- `--list` counts sites without running anything. Use it before a long run.
- Set `defaults.mutation_test_command` in `.swarm/gate.yaml` to a faster equivalent of the tests
  step — `-x` and `-p no:cacheprovider` are worth having when a command runs several hundred
  times.

Exit codes: `0` clean, `1` survivors, `2` a file is over the site cap, `3` the run could not be
trusted — most often a baseline failure, which means the suite fails before any mutant is
applied and no result would mean anything.

Property tests must stay out of the command it runs, per constitution §2.

It mutates **in place**. While a run is going the file under test is briefly wrong on disk, so
do not read, copy, commit or build from the tree until it finishes.

## CRAP has no off-the-shelf Python tool

Build one. It is a small script, not a project:

1. `radon cc -j <pkg>` gives cyclomatic complexity per function as JSON.
2. `coverage json` gives per-line execution, which reduces to per-function coverage.
3. Join on function, then compute `complexity² × (1 − coverage)³ + complexity`.
4. Exit non-zero on any function above the project's `crap_max` (default 6).

If it turns out to be worth keeping, it belongs in `swarm/gate/tools/python/` next to the
mutation runner, under the rules in [`tools/README.md`](tools/README.md). Otherwise keep
it in the target project under `tools/`. Either way, replace this section with the command that
runs it.

## Notes

- `mutmut` is the usual third-party answer for mutation. The shipped runner exists because it
  needs no install and because it can be taught the swarm's own rules — the site cap, the
  manifest, survivors-only output. Reach for `mutmut` only if you need something the shipped
  runner does not do, and write down what that was.
- Keep property tests (Hypothesis) tagged and excluded from the coverage, mutation, and CRAP
  runs — constitution §2.
