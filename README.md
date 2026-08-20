# agile-factory-swarm
Personal helper for code quality and automation.

## Install

`swarm doctor` reads this repo's `.swarm/gate.yaml` and reports how much of the quality gate is
declared. Install it into the user's Python 3.11, whose `Scripts` directory is on the persistent
user `Path`, so a newly opened terminal resolves the command with no activation step:

```
cd C:\Users\salte\repos\agile-factory-swarm
py -3.11 -m pip install -e .
```

Not into `.venv/`: that directory is not on the user `Path`, so a console script installed there
would not resolve in a fresh terminal. `.venv/` stays as it is, and gate commands keep being
invoked by explicit `.venv/` path as `AGENTS.md` describes.

Then, from the repo root:

```
swarm doctor
```
