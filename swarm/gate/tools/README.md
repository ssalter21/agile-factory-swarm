# Gate tools

Small tools the swarm ships so that a role does not have to build one before it can do its job.

One directory per language, named the same way as the recipes in `swarm/gate/`. A tool belongs
here only when it meets all of these:

- **No install step and no third-party dependency.** Standard library only. A role must be able
  to run it the moment the swarm is installed.
- **Self-contained.** One file, or one directory that can be copied whole. Nothing outside it.
- **Nothing to configure.** It reads `.swarm/gate.yaml` for the project's own facts and takes
  overrides on the command line.
- **Named by a recipe.** `swarm/gate/<language>.md` says which step it fills and how to run it.

This is the exception to "knowledge, not binaries" in `swarm/gate/README.md`, and it is narrow.
Where a good tool already exists for a language, the recipe names that tool and nothing lands
here. A tool ships only when a role would otherwise write one from scratch on every run.

## What ships today

| Language | Step | Tool |
|----------|------|------|
| Python | 4, mutation | [`python/mutate/`](python/mutate/) |

## The shared shape

A new language's mutation runner should look like the Python one from the outside, so that a
role that has used one has used them all:

- **Arguments** are the paths to mutate. `--all` ignores the manifest, `--verbose` gives one
  line per mutant, `--list` counts sites and runs nothing, `--max-sites` overrides the cap.
- **Output is survivors only.** Progress goes to stderr. The default output is read by an agent
  whose whole context is re-read on every turn, so anything it will not act on is a cost with no
  return.
- **A manifest** at `.swarm/mutation.json` carries verdicts between runs, keyed so that editing
  one function invalidates only that function. Re-running an untouched file must be free.
- **Exit codes:** `0` clean, `1` survivors, `2` a file is over the site cap, `3` the run could
  not be trusted.

## The unresolved part: prose

A mutant in a diagnostic message -- "results would be noise" losing a word -- can only be killed
by a test that asserts that sentence word for word. That is a worse test than no test: it breaks
on every rewording and proves nothing about behaviour. Documentation strings are already excluded
for exactly this reason (docstrings, and `help=`/`description=` arguments), but prose printed for
a human to read is not reliably distinguishable from output that is a real interface -- the
`SURVIVOR ...` lines an agent parses genuinely are behaviour, and are asserted exactly.

So a survivor count of zero is not currently reachable on a tool that talks. Three ways out, none
of them the tool's to choose: assert the wording anyway, widen the documentation rule to cover
printed prose, or let the gate carry a survivor budget instead of demanding zero. Constitution §2
says zero. The gap is real and it is a human question.

Mutation happens **in place**: while a run is going, the file being mutated is briefly wrong on
disk. Do not read, copy, commit or build from the tree during a run. The runner restores the
file in a `finally` and keeps the original under `.scratch/mutate-backup/` until it finishes, so
a crash is recoverable — but a concurrent reader is not something it can protect you from.

Inside, only the mutation operators are really about the language. The Python package keeps them
in `operators.py`, apart from the manifest, the config reader and the runner, so that the next
language reuses the shape rather than the syntax.
