# Agile Factory Swarm

A configurable swarm of agents that turns a loose brief into a specified, built, and reviewed
change. This glossary is the shared language for the swarm and the documents it produces.

## Language

### The swarm

**Constitution**:
The law binding every role, in every repo the swarm runs in. Outranks a role's own prompt.
_Avoid_: articles, rules file, guidelines

**Section**:
A numbered part of the constitution, carrying a scope line naming which roles it binds.
_Avoid_: article, chapter

**Role**:
A named builder agent with a remit, a tool allowlist, and one step of the quality gate to own.
_Avoid_: worker, agent (too general)

**Personality**:
A named spec-swarm agent with a point of view it argues from. Distinct from a Role — a
personality argues about what to build, a role builds it.
_Avoid_: persona, character

**Spec swarm**:
The personalities that turn a brief into a spec. Runs before the seam.

**Builder swarm**:
The roles that turn an approved spec into a merged change. Runs after the seam.

**Brief**:
The human's loose starting statement of what they want. Input to the spec swarm.
_Avoid_: request, ticket, prompt

### The seam

**Seam**:
The human approval boundary between the spec swarm and the builder swarm. Structural, not
optional — a workflow cannot take input mid-run, so the two swarms are separately invoked.
_Avoid_: gate (that word is taken), checkpoint, approval step

**Spec**:
The artifact the spec swarm produces and the human approves. After approval it is the builder
swarm's only authority on what to build.

**Blackboard**:
The files under `.swarm/` and `specs/` that roles read and write instead of passing messages
through a queue. File state *is* the queue.
_Avoid_: shared context, workspace, scratch

**Escalation ladder**:
The three-rung rule for an open question: research it, else assume defensibly and record it,
else make it a human question. Human questions accumulate and are asked as a batch.

### Quality

**Quality gate**:
The six fixed steps every builder runs before handing work on — tests, coverage, duplication,
mutation, CRAP, acceptance. The order is constitutional; the commands are per-project.
_Avoid_: pipeline, checks, CI

**Missing**:
A gate step with no tool yet for this language. A debt for initiation to clear, not an opt-out.
A run with any missing step is a **degraded run** and says so at the seam.
_Avoid_: none, skipped, n/a

**CRAP**:
Change Risk Anti-Patterns — one number per function combining complexity and coverage:
`complexity² × (1 − coverage)³ + complexity`. Either keep it simple or test it properly.

**Mutation site**:
A place in the code where a mutation tool could inject a small change. Used as a size measure:
over 100 in one file means the file does too much.

**Testability boundary**:
The line between modules that can be tested automatically and those that cannot — GUI, device,
engine runtime. Only the testable side participates in the gate.
_Avoid_: seam (that word is taken), interface

### Setup

**Initiation**:
The one-time act of making the generic swarm concrete for a repo: writing `AGENTS.md` and
`.swarm/gate.yaml`, procuring or building the gate tooling, and configuring the personalities.
_Avoid_: setup, install, onboarding, bootstrap

**Gate registry**:
`swarm/gate/<language>.md` — the accumulated knowledge of how to fill the gate for a language.
Holds recipes, never binaries. Initiation reads it, and writes back what it had to build.
