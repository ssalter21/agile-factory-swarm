# Agent instructions

This repo is governed by the **swarm constitution** at
[`swarm/constitution.md`](swarm/constitution.md). Read it and obey it. It outranks anything in
this file except the facts below.

Every tool reads this file, so nothing here is Claude-specific. Claude-specific mechanics belong
in a role's own agent definition.

## Local section — agile-factory-swarm

- **Language:** Python 3.11. Virtualenv at `.venv/`.
- **Shell:** PowerShell 7 on Windows 11. Gate commands run in the shell `.swarm/gate.yaml`
  declares — do not substitute bash.
- **What this repo is:** the swarm itself. `swarm/` holds the shipped source — the constitution,
  the role definitions in `swarm/roles/`, the gate registry, the gate tools the swarm ships, and
  the role compiler in `swarm/tools/python/rolecompile/`. `.claude/` holds this harness's compiled
  roles and workflows.
- **The roles are compiled.** Edit `swarm/roles/<name>.yaml` (the declaration) and
  `swarm/roles/<name>.md` (the prompt), then run
  `.venv/Scripts/python.exe swarm/tools/python/rolecompile` to write `.claude/agents/` and
  `.github/agents/`. Add `--check` to compare and write nothing. Never hand-edit a compiled agent
  file. Nothing in this repo dispatches to `.github/agents/`; those files are published, not run.
- **Dogfooding:** the constitution in `swarm/` is the same file installed into target repos. When
  it is wrong here, it is wrong everywhere. The same goes for `swarm/gate/tools/`: this repo runs
  its own mutation step with the runner it ships.
- **The gate is degraded.** `.swarm/gate.yaml` currently declares `missing` for duplication,
  CRAP, and acceptance. Say so in any handoff, per constitution §2.
- **Mutation currently exits 1**, on 158 survivors in the runner's own 1,386 mutants. That is the
  step working, not the step broken: the survivors are standing hardener debt. About 60 of them
  are prose in diagnostic messages, killable only by asserting wording word for word. Whether
  that is worth doing is a human question — see `swarm/gate/tools/README.md`.
