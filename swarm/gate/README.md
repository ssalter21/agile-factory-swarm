# Gate registry

One file per language, naming how to fill the six gate steps in `swarm/constitution.md` §2.

A recipe is **knowledge, not binaries**. It says which tool to use, how to install it, and what
command fills the step. Where no tool exists for a language, the recipe says how to build one.

Initiation reads `<language>.md` for the project it is setting up and writes `.swarm/gate.yaml`
from it. Where there is no file for that language, initiation builds what is missing and **writes
the recipe back here** — so the second project in a language costs less than the first.

Steps, in fixed order: `tests`, `coverage`, `duplication`, `mutation`, `crap`, `acceptance`.
