# Gate registry

One file per language, naming how to fill the six gate steps in `swarm/constitution.md` §2.

A recipe is **knowledge first**. It says which tool to use, how to install it, and what command
fills the step. Where a good tool already exists, the recipe names it and the registry holds
nothing else.

Where none exists, the recipe says how to build one — and if a role would otherwise build the
same thing on every run, the built tool ships too, in [`tools/`](tools/README.md). That is a
narrow exception with its own rules: standard library only, nothing to install, self-contained.
Third-party tools are still named, never vendored.

Initiation reads `<language>.md` for the project it is setting up and writes `.swarm/gate.yaml`
from it. Where there is no file for that language, initiation builds what is missing and **writes
the recipe back here** — so the second project in a language costs less than the first.

Steps, in fixed order: `tests`, `coverage`, `duplication`, `mutation`, `crap`, `acceptance`.
