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
What the human does to every open question at the seam: answer it in `answers.md`, in prose. The
spec writer then folds the answers into the spec and deletes `questions.md`. A spec with an
undispositioned question is not approvable, because after the seam no role may ask — and
`questions.md` still existing is what says one is.
_Avoid_: resolve, triage, close

**Questions file**:
`questions.md` in the run directory — everything the human is asked, whether the run blocked early
or reached the seam. The first thing they read, and the only file there that asks them for
something. At most three questions, at most a screen each. Its existence means the seam is open; the
spec writer deletes it on a fold, and that absence is the only mechanical check disposition has.
_Avoid_: question batch (that is the content, not the file), open questions section, TODO

**Fold**:
The third way the spec swarm is invoked, after a resume and a fresh run: the human has answered the
seam's questions, so the spec writer runs alone, writes the answers into the spec, and deletes
`questions.md`. The voices are not re-run — re-arguing a spec the human has read would change text
they had accepted.
_Avoid_: revision, amendment, second pass

**Chosen** / **Assumed**:
The two kinds of register entry. *Chosen* is a disputed point the unblocker ruled on because being
wrong is cheap. *Assumed* is a gap nobody could answer. Naming a ruling an assumption hides that an
argument was won; naming a coin-toss a ruling claims a confidence nobody has.
_Avoid_: decided, settled (that word means research answered it)

**Contested cut**:
A requirement the agile agent vetoed, that another voice then tied to the brief and lost anyway. It
is a decision nobody made, so it reaches the human as a question rather than as a line on the
out-of-scope list.
_Avoid_: disputed veto, rejected requirement

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
`.swarm/runs/current/` — everything for the one in-flight spec. The **artifact** is three files:
`brief.md`, `spec.md`, `acceptance.feature`. Beside them sit the human's side of the conversation
(`questions.md`, `answers.md`) and the swarm's working state (`.work/`, hidden, because the human's
first sight of this directory should not be twelve files that are not for them). Ignored by version
control, overwritten by the next approved spec. The durable record is the pull request QA opens, not
this.
_Avoid_: specs directory, spec folder, output

**Escalation ladder**:
The three-rung rule for an open question: research it, else assume defensibly and record it,
else make it a human question. Human questions accumulate and are asked as a batch. A **disputed
point** — two voices argued and neither won — walks the same ladder, ruled on by what being wrong
costs; only a fatal-if-wrong one reaches the human.

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
