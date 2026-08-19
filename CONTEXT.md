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
A named builder agent with a remit, a tool allowlist, and at most one step of the quality gate to
own. A role may own no gate step and earn its place another way — the architect owns the plan.
_Avoid_: worker, agent (too general)

**Personality**:
A named spec-swarm agent with a point of view it argues from. Distinct from a Role — a
personality argues about what to build, a role builds it.
_Avoid_: persona, character

**Spec swarm**:
The personalities that turn a brief into a spec. Runs before the seam.

**Builder swarm**:
The roles that turn an approved spec into a merged change. Runs after the seam. Its chain is
architect → coder → cleaner → hardener → architect → QA; the architect runs twice, first to plan
and last to check conformance.

**Plan**:
The architect's instruction to the roles downstream of it: module boundaries, dependency
direction, the testability boundary, and what is forbidden. A **handover, not an artifact** — it
travels in the handoff, lives in `.scratch/` for the run, and is never committed. The code is the
definition of the architecture.
_Avoid_: design doc, architecture doc, spec (that word is taken)

**Appeal**:
A downstream role's request to the architect to amend the plan that is blocking it. Work stops
until the architect rules. Three per task, then it becomes a human question.
_Avoid_: exception, override

**Bounce**:
Sending a real problem back to the earlier role that owns it, once, with a reproduction. A second
failure of the same thing becomes a human question.
_Avoid_: reject, fail back

**Handoff contract**:
The fixed set of fields every hop carries — task, plan, changed, gate, deviations, request,
status. A role that cannot fill them in has not finished.

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
swarm's only authority on what to build. Approval is `status: approved` in its front matter,
written by a human and nobody else.

**Disposition**:
What the human does to every open question at the seam: answer it in the spec, or move it to the
assumption register with its cost if wrong. A spec with an undispositioned question is not
approvable, because after the seam no role may ask.
_Avoid_: resolve, triage, close

**Restatement**:
The architect's account of the approved spec in its own words, written before it plans. Diffing it
against the spec is what catches spec drift at the cheapest moment.
_Avoid_: summary, understanding, echo

**Interpretation**:
An ambiguity in the spec that the architect resolved defensibly rather than halting on. Named in
the restatement, carried in the handoff, and checked by QA at the end. A contradiction is not an
interpretation — it halts.
_Avoid_: assumption (that word is taken by the spec swarm), judgement call

**Blackboard**:
The files under `.swarm/` that roles read and write instead of passing messages through a queue.
File state *is* the queue. Config (`gate.yaml`, `spec.yaml`) is committed; the run directory is
not.
_Avoid_: shared context, workspace, scratch

**Run directory**:
`.swarm/runs/current/` — the seam's artifact for the one in-flight spec: `brief.md`, `spec.md`,
`acceptance.feature`. Ignored by version control, overwritten by the next approved spec. The
durable record is the pull request QA opens, not this.
_Avoid_: specs directory, spec folder, output

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
