"""Mutation testing for Python. Gate step 4 of swarm/constitution.md.

Ships with the swarm: standard library only, nothing to install, no third-party dependency.
Run the package directory.

    python swarm/gate/tools/python/mutate src/pkg
    python swarm/gate/tools/python/mutate src/pkg/gate.py --verbose
    python swarm/gate/tools/python/mutate src/pkg --list

It rewrites one source file with a single change, runs the project's test command, restores the
file, and reports the mutants that survived. A survivor is a hole in the tests, not a curiosity.

Every default is chosen to keep the run cheap, because the output is read by an agent whose
context is re-read on every turn:

- Survivors only. Per-mutant detail needs --verbose. Progress goes to stderr either way, so a
  long run is still distinguishable from a hang.
- Differential. Verdicts are cached in .swarm/mutation.json against a hash of the enclosing
  function and of the test suite, so an unchanged function is not run twice. --all ignores it.
- A file over `defaults.max_mutation_sites_per_file` is not mutated at all. Constitution
  section 2 says split it; mutating it first only spends the budget twice.

Exit codes: 0 clean, 1 survivors, 2 a file is over the site cap, 3 the run could not be trusted.

Mutation happens in place, so while a run is going the file under test is briefly wrong on disk.
Do not read, copy, commit or build from the tree during a run. The original is restored in a
`finally` and kept under .scratch/mutate-backup/ meanwhile, so a crash is recoverable.

The modules: `config` reads .swarm/gate.yaml, `units` gives every mutant a stable identity,
`mutants` holds the Python-specific operators, `manifest` remembers verdicts, `runner` does the
work. Only `mutants` is really about Python; a runner for another language reuses the rest.
"""
