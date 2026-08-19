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
- **What this repo is:** the swarm itself. `swarm/` holds the shipped, language-neutral source —
  the constitution and the gate registry. `.claude/` holds this harness's compiled roles and
  workflows.
- **Dogfooding:** the constitution in `swarm/` is the same file installed into target repos. When
  it is wrong here, it is wrong everywhere.
- **The gate is degraded.** `.swarm/gate.yaml` currently declares `missing` for duplication,
  mutation, and CRAP. Say so in any handoff, per constitution §2.
