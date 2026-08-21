---
slug: neutral-role-format
status: approved
revision: 1
approved_by: Sam Salter (delegated in session; not read line by line)
approved_at: 2026-08-20
---

# A neutral role format, compiled to two harnesses

> **Degraded run (§2).** `.swarm/gate.yaml` declares `missing` for **duplication**, **mutation**,
> **CRAP** and **acceptance**. On top of that, the two steps §2 says always apply — **tests** and
> **coverage** — are declared as `.venv/Scripts/pytest.exe` and `.venv/Scripts/coverage.exe`, and no
> `.venv` exists in this worktree. A `.venv` with both executables does exist one level up, in the
> main checkout, and a worktree does not share it. So a build run started here has **no executable
> gate step at all**.
>
> Approve knowing that: nothing in this repo will check duplication, mutation, CRAP or acceptance,
> and the two mandatory steps only run if the build is run somewhere the declared paths resolve.
> Repairing the gate is initiation's job (§4) and is not in this change. R14 below requires the
> compiler to be *reachable* by those commands; nothing here claims they were run.

---

## Requirements

### Words this spec uses

The Domain Modeller's glossary is this spec's language. Every term below is used with the meaning
given here and no other.

| term | meaning |
|---|---|
| **role** | one named agent of the swarm. All twelve are roles; *spec role* and *builder role* are the qualified forms. |
| **role definition** | the authoritative statement of one role: one declaration plus one prompt. Lives under `swarm/roles/`. |
| **declaration** | the five-field data a harness needs to load a role: `name`, `description`, `tools`, `model`, `effort`. |
| **prompt** | the instruction text the agent reads — the markdown body. Not a field. |
| **neutral format** | the shape all declarations share. |
| **harness** | a tool that defines an agent-file format. Two here: Claude Code, which the swarm runs on, and GitHub Copilot, which this change emits files for and which nothing here dispatches to. |
| **agent file** | one file a harness loads to obtain one role: `.claude/agents/<name>.md` or `.github/agents/<name>.agent.md`. Generated; not authoritative. |
| **front matter** | the YAML block at the head of an agent file. |
| **compiler** | the code that produces agent files from role definitions. |
| **emitter** | the part of the compiler that writes one harness's agent files. One per harness. |
| **compile command** | the entry point a developer runs. It has a write mode and a check mode. |
| **check mode** | compiles, compares against the agent files on disk, writes nothing, and exits non-zero naming every stale file. |
| **stale** | of an agent file: its content is not what compiling its role definition would produce. |
| **dropped field** | one (field, harness) pair with no home. `model` and `effort` on GitHub: two of ten. |
| **unmapped tool name** | a value inside a carried field that a harness does not recognise. `Skill` on GitHub, and nothing else. |
| **undeclared field** | a field in a declaration that the neutral format does not define. |
| **full fidelity** | of a compile: every declared field is carried. Field coverage only — it says nothing about bytes. |
| **byte-identical** | of a comparison: the two files are the same bytes. |
| **lossy** | of a compile: at least one field is dropped. |
| **tool allowlist** | the set of tool names a role may use — the `tools` field. |
| **declared effort** | the effort a role definition states, and the value the compiler writes to the Claude agent file. It does not govern dispatch: what a run uses is decided by the workflow script, which today hardcodes `effort: 'medium'` for the rebut pass. |
| **effort level** | one of `low`, `medium`, `high`, `xhigh`, `max`. |

Words this spec does **not** use, because they already mean something else here: *degraded* of a
compile (that is the gate's word — a compile is **lossy**), *drift* of an agent file (that is spec
drift's word — an agent file is **stale**), *target* of a harness (GitHub's own format has a
`target` property inside the files we emit), *manifest*, *generate*, *transpile*, *translate*,
*personality*.

### The shape of it

```text
  edited in ONE place                       read by TWO harnesses
  -------------------                       ---------------------
  swarm/roles/researcher.yaml   compile     .claude/agents/researcher.md
  swarm/roles/researcher.md    --------->   name, description, tools, model, effort
   (declaration + prompt)          |        + the prompt, unchanged     [full fidelity]
                                   |
                                   +----->  .github/agents/researcher.agent.md
                                            name, description, tools
                                            + the prompt, unchanged     [lossy: model
                                              and effort are dropped]
```

### R1 — The role definitions are twelve pairs of files

`swarm/roles/<name>.yaml` holds a role's declaration; `swarm/roles/<name>.md` holds its prompt. One
pair per role, for all twelve roles that exist today: `agile-agent`, `architect`, `cleaner`,
`coder`, `devils-advocate`, `domain-modeller`, `hardener`, `qa`, `researcher`, `spec-writer`,
`unblocker`, `user-voice`.

All twelve, not a subset. A partial move leaves two authorities for a role, which is the thing the
brief exists to remove, and it cannot produce the empty diff R4 requires.

### R2 — A declaration carries exactly five fields

`name`, `description`, `tools`, `model`, `effort`. These are the five all twelve roles use today,
and no role uses a sixth. The neutral format carries **no field with zero current users** — not
`color`, `permissionMode`, `maxTurns`, `skills`, `disallowedTools`, `background`, `memory`,
`target`, a per-harness override, or a switch for which harnesses a role compiles to. `isolation` is
forbidden outright by §12.

`name` is data, declared in the `.yaml`. It is never derived from the filename: the same string is
the filename on both harnesses, the `agentType` the workflow scripts dispatch on, and the voice key
in `.swarm/spec.yaml`. The filename must match the declared name.

A role definition is a declaration plus a prompt. **The prompt is not a field.**

### R3 — The prompts move unchanged

The twelve prompt bodies are today's twelve bodies, byte for byte. No rewording in this change. One
prompt per role; there is no per-harness prompt.

### R4 — The Claude compile reproduces the twelve tracked files exactly

Compiling produces `.claude/agents/<name>.md` for all twelve roles, carrying all five fields and the
prompt, **byte-identical to the twelve files tracked today**. This is the acceptance criterion of
the change, and it is the human's own answer (answer 2): recompiling leaves the twelve tracked files
byte-identical.

Byte-identical is measured against **the twelve files as they sit in the working tree** — that is
what check mode can see, and the working tree and the index currently disagree about line endings
(the index holds LF; the working tree holds CRLF, because of a machine-wide `core.autocrlf=true`).
R5's pin is what makes the two readings converge.

### R5 — The emitted bytes are specified, not left to a YAML library

A general-purpose YAML dumper breaks R4 in four ways at once, so the output rule is stated here
rather than rediscovered:

- UTF-8, **no BOM**.
- **One final newline**, present on every file.
- Front-matter field order fixed: `name`, `description`, `tools`, `model`, `effort`. Not sorted.
- **No line folding.** `researcher`'s description is a single unwrapped line of about 160 characters
  and must stay one line.
- `tools` is written as the **comma-separated string** form — `Read, Grep, Glob, ...` — on both
  harnesses. That is what all twelve tracked files use, and GitHub's schema documents both the
  string and the list form, so one shape serves both emitters. This is the human's answer 3. Whether
  Claude Code would also accept a YAML sequence is unknown and untested, and nothing here depends on
  the answer.
- **One line ending, emitted unconditionally on every platform**, and that line ending is **pinned
  in `.gitattributes`** for the agent-file paths, the way `*.js text eol=lf` is already pinned in
  the same file. Which line ending is pinned is the architect's call — either works once it is
  pinned. That it is pinned is the requirement.

Hardcoding today's CRLF without the pin would make the change's only test a property of one
machine's git configuration: a correct compiler would fail on the first clone taken with
`core.autocrlf=false`, and look like a compiler bug when it did.

### R6 — The GitHub compile emits four things and nothing else

`.github/agents/<name>.agent.md` for all twelve roles, carrying `name`, `description`, `tools`, and
the prompt as the body. `model` and `effort` are **dropped** — there is no correct value to write
(Opus does not appear in the Copilot CLI's model list at all, and no short alias is documented on
any GitHub surface), and the one field name that could carry effort appears on one GitHub surface
while being absent from the schema that claims to cover it.

Tool names are **copied unchanged**. All nine names these roles use appear verbatim in GitHub's own
compatible-variations table except `Skill`, which is copied too and is simply inert there. Nothing
is renamed. No key beyond the four documented ones is emitted, on either harness.

### R7 — Nobody may claim the swarm runs on GitHub

This is the human's answer 1, and it is stated here because it is the sentence most likely to be
lost. `.github/agents/*.agent.md` is a **published artifact**: twelve files that exist and are
constrained to the four fields GitHub's schema documents. Nothing in this repo dispatches to them,
and no requirement in this spec may be justified by what a Copilot agent would experience.

The brief's framing invites the opposite reading, so, plainly: the roles are not the swarm. The
swarm is the roles *plus* the chain, the four statuses, the gate and the seam, and none of those
exists on the GitHub side. Compiling twelve prompts there shows the format is neutral. It does not
produce a working second harness.

There is also no executable check on that half. No JSON Schema, linter or validation procedure for
`.agent.md` is published anywhere, and `acceptance` is `missing` in this repo's gate. "Validates
against the documented schema" therefore means the emit is constrained to the four documented
fields, and it is verified by a person reading the files once.

### R8 — One compile command, with a write mode and a check mode

One command, run from the repo root, discoverable from `AGENTS.md`. Its literal name, and the
language behind it, are the architect's.

- **Write mode** brings both trees up to date.
- **Check mode** compiles, compares against the agent files on disk, **writes nothing** to
  `.claude/agents/` or `.github/agents/`, and exits non-zero naming every file that differs.

Where the compiler needs somewhere to put intermediate output, `.scratch/` is that place (§8). Check
mode is not a staging path: it writes nothing to either destination, so it satisfies both of the
human's constraints at once — a clean diff *before* the compiler is permitted to write, and no
staging path a human promotes from.

### R9 — What the command tells the developer

- **One line per agent file**, path first, saying `written` or `unchanged`. A command whose only
  report is its side effect cannot be told apart from a command that silently did nothing.
- **Non-zero exit** on any failure.
- Where the **only** difference between the compiled output and the file on disk is the line ending,
  check mode says so on that file's line. This is one clause inside the per-file report, and it is
  what turns twelve inexplicable stale files on a differently configured clone into one instruction.
- The output does **not** narrate what the GitHub emit drops. That fact is stated once, in R6, where
  a human reads it.
- No glossary word — *lossy*, *full fidelity*, *dropped field*, *stale* — appears in the command's
  output. Those are words for this document. The command speaks in ordinary words.

### R10 — Three input checks, and no more

Each of these fails the compile, names the file and the field, and writes nothing:

1. two declarations with the same `name`;
2. a declared `name` that does not match its filename;
3. an omitted `tools` field — and the message says that an omitted allowlist on Claude inherits
   every tool.

Nothing else is validated: no schema checker, no legal-value lists, no remediation text. The
compiler may **fail on the first problem it finds**; it does not accumulate errors.

The third check earns its place on its own: the twelve existing roles are protected by R4's
byte-identity, and the thirteenth role anyone adds is protected by nothing else. An absent allowlist
is a permission change dressed as a formatting choice, in a repo where the roles are the product.

**The compiler validates every input before it writes any output.** No partial writes. A crash
part-way through the write is not designed around; the recovery is to run check mode, which names
every file that differs.

### R11 — Nothing changed means nothing rewritten

Run the compile command twice with nothing edited in between, and the second run reports every file
`unchanged` and writes nothing.

This is not a restatement of R4. R4 is a property of the checkout's line-ending configuration; this
is a property of the compiler, and it holds on every machine, because both runs are the same
compiler on the same machine. A compiler that rewrites twelve files on every run puts twelve files
in every diff, and the developer stops reading diffs.

### R12 — The order: two invocations

```text
  INVOCATION ONE - builds the compiler, writes no agent file
  ---------------------------------------------------------
    write swarm/roles/, the compiler, the .gitattributes line
              |
              v
    run CHECK MODE  --> must exit 0 against the twelve tracked agent files
              |         nothing is written to .claude/agents/
              |         or to .github/agents/
              v
    the compiler has been shown faithful; only now may it write
              |
  ============|====== a later invocation ==========================
              v
  INVOCATION TWO - the first write, and everything downstream
  ----------------------------------------------------------
    run the compile command --> both trees written
    idempotence, round-trip an edit, add a role, run the swarm
```

Both halves are the human's answer 2, stated as requirements:

1. The compiler must be shown faithful — check mode clean against the twelve tracked files —
   **before** it is permitted to write them.
2. **The run that builds the compiler must not write the compiled trees.** Regenerating happens on a
   later invocation. Check mode *may* run in the building run, because it writes nothing to either
   destination; under the stricter reading nothing could execute the only acceptance criterion the
   change has.

The second constraint is belt-and-braces rather than a live hazard: a compile inside one invocation
cannot reach any role later in that same chain, because agent definitions are snapshotted when the
invocation begins. It is stated anyway, because it costs one sentence and removes the question.

### R13 — Both compiled trees stay in version control

`.claude/agents/*.md` stay tracked, as they are today, and `.github/agents/*.agent.md` are tracked
too. A fresh clone must have working agents before anything is compiled, and a published artifact
that is not in the repository is not published.

### R14 — The compiler is reachable by the gate

Cited from §2 and §3 rather than invented here: steps 1 and 2 of the gate always apply, and a gate
number computed over untestable code is a lie. The **compiler** — the code, as distinct from the
compile command — must be reachable by the commands `.swarm/gate.yaml` declares for `tests` and
`coverage`, which are `pytest` and `coverage`.

This spec states that the compiler must be reachable by those commands. It does **not** state or
imply that they were run: see the degraded-gate warning at the top. Note also that a compiler in a
language `pytest` cannot reach would force a change to the gate declaration.

### What this change costs, stated so the spec does not oversell it

- **It is not a simplification.** Twelve files become twelve declarations, twelve prompts, twelve
  Claude agent files and twelve GitHub agent files — forty-eight, and twelve of those have no
  consumer. What it buys is a single point of edit: it trades file count for that.
- **It creates staleness; it does not remove it.** Today there is one authority per role and nothing
  for it to disagree with. This change turns one reviewable file per role into two files that can
  disagree, and check mode (R8) is the only thing that detects it.

---

## Assumptions

The Unblocker's register, carried forward. **CHOSEN** means the Unblocker ruled on a disputed point,
because being wrong is cheap. **ASSUMED** means nobody knew, and a defensible assumption holds. The
full text of every entry is in `.work/assumptions.md`, `.work/assumptions-gap3.md`,
`.work/assumptions-gap3-research.md` and `.work/assumptions-gap4.md`, read in that order.

A note on the labels, because two numbering schemes meet here: register entries are `C`/`X` for
chosen and `A` for assumed; the human's three answers are numbered 1-3 in `answers.md`, and where
this spec means one of those it says "the human's answer". Facts settled by research are not listed
below — they are in the requirements above, and the research is linked at the foot of this file.

### Chosen

- **C1 — the Claude emit stays inside the documented Claude schema.** No provenance key and no
  neutral-only key, even though unknown keys are proven harmless today. Nobody argued the other
  side. If wrong: a `provenance:` line a reader might have liked is not there. One line to reverse.
- **C2 — §12 is satisfied by the declaration, not by every harness honouring it.** The neutral role
  definition *is* where model and effort belong; a harness that cannot express them is a fidelity
  loss, not a breach of the law. If wrong: the GitHub files are, on a strict reading, ungoverned on
  runtime policy — but §12 applies to the orchestrator, and no orchestrator runs on that side.
- **X1 — the prompt is a sibling file, not a block scalar inside the YAML.** Both voices that
  addressed it landed there independently. If wrong: two files per role where one would have done.
- **X2 — the compiled outputs stay in version control.** Two voices argued for it, none against. If
  wrong: generated files in the tree can silently disagree with their source; the remedy is a
  `.gitignore` line and a regeneration step.
- **X3 — check mode exists.** Ruled for the User Voice and the Devil's Advocate against the Agile
  Agent's "`git status` is the check": `git status` can only be consulted after the destructive act,
  and it cannot tell "stale because the source moved" from "I edited this a minute ago". The
  pre-commit hook and the CI job stay cut. If wrong: the human bought the largest single piece of
  the change they did not ask for; deleting it is one requirement and one criterion.
- **X4 — "must not run it" means must not *write* the compiled trees.** Check mode may run in the
  building run. If wrong: a command was run in a run where the human wanted nothing run. Nothing was
  written either way.
- **X5 — three input checks, failing on the first problem found.** The Agile Agent's own filename
  rule was already validation, so the category could not be cut whole; the Agile Agent won on error
  accumulation. If wrong: three `if` statements the human did not ask for.
- **X6 — the compiler must be gate-reachable, written as a citation of §2 and §3, not as a new
  rule.** Every voice wanted this in some form. If wrong: the architect is constrained away from a
  language the declared gate cannot reach.
- **X7 — one line per agent file, and a non-zero exit on failure.** The Agile Agent's ground for
  trimming it (that no-op accounting needs compare-before-write machinery) disappeared once X3 built
  that machinery for a reason the human gave. If wrong: twelve to twenty-four lines of output nobody
  wanted.
- **X8 — the compile output does not narrate the dropped fields.** Ruled for the Agile Agent: the
  User Voice's justification was a Copilot run, and the human's answer 1 forbids claiming one. The
  User Voice did not concede at the time, and concedes now, asking that a condition be attached —
  see the out-of-scope line. If wrong: someone edits `effort` and has to read this document to learn
  that one output ignores it.
- **X9 — amending `CONTEXT.md`'s glossary is out of scope. This is a contested cut, ruled here
  rather than sent to you**, because it is not fatal-if-wrong (§5). The Domain Modeller tied it to
  the brief properly and lost on scope: the inconsistency predates the brief, the constitution
  outranks `CONTEXT.md`, and nothing reads it at dispatch. If wrong: a glossary file disagrees with
  the name of the directory this change creates. Fixable in one commit by anyone.
- **X10 — no character-count check on emitted bodies.** The voice that demanded it withdrew, and the
  criterion cannot be stated without picking a unit. If wrong: a body over 30,000 characters
  eventually produces a GitHub file that fails the documented cap, with nothing catching it. The
  margin today is 4.7x.
- **X11 — the glossary carries only terms a surviving line uses.** Both voices argued from the same
  rule (§11). If wrong: the spec is slightly poorer or slightly wordier in a few sentences.
- **X12 (first half) — the output byte rule and the `.gitattributes` pin are the spec's, not the
  architect's.** The Devil's Advocate raised it, no voice argued the other side, and research turned
  it from an unknown into a fork with a known cheaper side. If wrong: one tracked line and one
  sentence of scope the human did not ask for, revertible in one commit. *Its second half — a
  renormalising checkout as a requirement — is withdrawn and replaced by X14.*
- **X13 — no tool-name legality check on the GitHub side.** Recorded because it was a live
  conditional: research found no legality constraint to check against, so the check that would have
  been worth having does not exist to be had. If wrong: a malformed emit is caught by nobody.
- **X14 — the renormalising checkout is not a requirement. The spec states the output rule, the pin
  and the end state; bringing an existing working tree into line is the architect's.** **The Agile
  Agent won this argument**: a `git checkout` invocation is a mechanic for reconciling a tree with an
  attribute git already knows about, and writing it into the spec would have QA validating a git
  command. Nobody defended the mechanism — the Devil's Advocate said in the same paragraph that if
  it moved anyone it should be on the mechanism, not the requirement. What replaces it is an
  acceptance criterion: on a fresh checkout of the branch, check mode exits 0 against the twelve
  tracked agent files. That also catches a failure the mechanic did not — pinning one line ending
  and emitting the other. If wrong: the architect does not reconcile the existing tree, the first
  check-mode run reports all twelve files as differing, and someone runs one git command. Loud,
  immediate, one commit — and under X16 the report names line endings as the reason.
- **X15 — idempotence (R11) stands as its own requirement and is not folded into R4.** **The User
  Voice won this**, on a fact that arrived after the Agile Agent made its case: byte-identity against
  the tracked files depends on the checkout's line-ending configuration and idempotence does not, so
  two properties that fail independently are two requirements. If wrong: one duplicate requirement
  and one duplicate QA step.
- **X16 — check mode says when the only difference is line endings.** Ruled for the User Voice, and
  the Unblocker recorded this as **the weakest of its rulings**: it is new scope arriving at rebut,
  the `.gitattributes` pin closes most of the scenario, and the User Voice offered a fallback. It
  stands because X14 makes the twelve-unexplained-stale-files state *more* reachable, and removing a
  guard while declining the cheap diagnostic that replaces it is two cuts dressed as one. If wrong:
  one clause of output, deletable in one line with nothing depending on it.
- **X17 — the third-harness consequence goes on the out-of-scope list.** Not a disputed point; both
  voices agreed, and it was placed because an item with no owner at the last gap is what gets
  dropped between passes. If wrong: one line on a list nobody needed.

### Assumed

- **A1 — "instructions" in the brief means the markdown body below the front matter.** GitHub's
  schema has no `instructions` property; its docs call the body "the prompt". If wrong: the GitHub
  agents carry no instructions — which fails visibly the first time one is loaded.
- **A5 — the GitHub compile drops `model` and `effort` rather than translating them** (supersedes
  A3). If wrong: the Copilot CLI could have carried effort faithfully and does not. A fidelity loss,
  not a breakage; adding an emit later is additive.
- **A6 — where two GitHub references disagree, the narrower one governs the emit.** The
  cross-environment schema omits `reasoningEffort`; the CLI reference documents it; nothing
  reconciles them. If wrong: the omission was documentation lag, and a workable field was left on the
  table.
- **A7 — unknown-key behaviour on the GitHub side is not designed around** (extends A2, which said
  the same of harness-side validation generally). No source states what any GitHub surface does with
  an unrecognised front-matter key. If wrong: a future decision to emit an extra key could silently
  lose an agent — but under A6 no such key is emitted, so nothing depends on the answer yet.
- **A9 — the compiler runs in this repo only. No role output lands in a target repo, and the neutral
  format carries no version story.** If wrong: the format needs versioning, and a format already
  installed elsewhere cannot be changed as freely as one with a single consumer. Nothing distributes
  role files today.
- **A10 — there is one compile command, discoverable from `AGENTS.md`.** If wrong: every criterion
  citing "the compile command" has to be reworded; the requirements themselves do not change.
- **A11 — the fidelity baseline is the twelve tracked files, and byte-exactness is required of the
  compiler's own output rather than asserted about the current tree.** Recorded before the human made
  byte-identity *the* criterion; it stands as recorded, narrowed by A16.
- **A12 — "validates against the documented schema" means the emit is constrained to the four
  documented fields, and the spec says plainly that no executable validator exists** (R7). If wrong:
  half the outputs are verified by one human reading one document once, and a schema violation ships
  undetected. Nothing dispatches to those files, so it costs nobody a run.
- **A13 and A17 — fixed front-matter field order, no line folding, UTF-8 without BOM, and a final
  newline are stated in the spec rather than left to the architect** (R5). All four are derivable
  from the human's own criterion; the assumption is that they are worth writing down rather than
  rediscovering. If wrong: the architect reads four sentences it did not need. The omission costs the
  naive implementation failing the change's only test, which was rated near-certain.
- **A14 — validate every input before writing any output; an interrupted write is not designed
  around** (R10). If wrong: a crash mid-write leaves the swarm running on a half-updated role set
  with no marker. Check mode makes that one command away from visible.
- **A15 — the building run's gate is disclosed as unexecutable from a worktree, and repairing it is
  not this change's job.** If wrong: the builder swarm runs here, executes no gate step, and ships
  the change with nothing run against it — including the compiler R14 requires be gate-reachable.
  The same commands resolve in the main checkout, so the repair is one command, and the failure is
  loud rather than silent.
- **A16 — "byte-identical" is measured against the twelve files as they sit in the working tree**
  (R4). If wrong: the human meant `git diff` is clean, which is line-ending-agnostic here and would
  have needed no `.gitattributes` change at all. Under R5's pin the two readings converge.
- **A18 — the `.gitattributes` pin covers the agent-file paths only, not `*.md` repository-wide.**
  Nobody argued the scope either way. If wrong: the human wanted one rule for all markdown and gets a
  narrower one. The narrow direction is the conservative one — widening it later is one line, whereas
  assuming the wide rule would renormalise every markdown file in the repository on the next
  checkout.

*A3 and A4 are superseded, by A5 and X2. A8 — neutralising the four harness-specific prompt lines —
is void: it bound only if nobody argued the point, and three voices argued it. The outcome is V1 on
the out-of-scope list.*

---

## Out of scope

Everything the Agile Agent vetoed, with the line you read at the seam. Every cut is reversible;
asking for one back is a new brief rather than an amendment to this one.

- **Rewriting the four harness-specific prompt lines (V1)** — Prompts move unchanged, so this change
  cannot alter how any agent behaves. The price: two of the twelve published GitHub files
  (`researcher`, `domain-modeller`) carry an instruction to run a `/research` or `/domain-modeling`
  command that has no GitHub equivalent, and nothing dispatches to those files. On the Claude side
  both commands resolve today against the user's global skill install, and the Claude agent files are
  byte-identical, so those two roles keep working exactly as they do now.
- **A `skills:` field in the neutral format (V2)** — A field with zero current users, added to solve
  a problem we have chosen not to solve (V1). No role declares a skill today except in prose.
- **Schema validation of the neutral files, beyond the three checks in R10 (V3)** — The compiler is
  the only reader of a format with twelve known instances. Byte-identity catches more than a schema
  checker would, and costs nothing.
- **A pre-commit hook or a CI job that the compiled trees are current (V4, V21)** — Check mode is a
  command anyone can run at any time. Build the automation when staleness has actually bitten once.
- **Emitting `reasoningEffort` on the GitHub side (V5)** — One GitHub surface would read it, and two
  GitHub references contradict each other about whether it exists. Emitting nothing is the reversible
  choice; the harness falls back to the session's own effort.
- **Translating `model` for the GitHub side (V6)** — There is no correct value to write. Opus does
  not appear in the Copilot CLI's model list at all. A wrong model is worse than no model.
- **The full GitHub/VS Code tool-alias table and MCP namespacing (V7)** — We copy the nine tool names
  our twelve roles use, and research confirms none of them is renamed. A general translation table is
  a table with no second customer.
- **`target`, `user-invocable`, `disable-model-invocation`, `mcp-servers`, `metadata` and `handoffs`
  on the GitHub side (V8)** — The brief names four things to emit. These are the other six the schema
  allows, and no role needs one.
- **Untracking the compiled `.claude/agents/*.md` (V9)** — Keeping them tracked is the status quo,
  costs nothing, and is what makes "regenerate and diff" possible.
- **Installing `swarm/roles/` into target repos, or any story about how other repos consume this
  format (V10)** — The brief asks for a format and two compile targets in this repo. §11 already
  fixes what the swarm may leave in a target repo.
- **A manifest listing the roles (V11)** — The directory is the list.
- **A "generated — do not edit" banner in the compiled files (V12)** — This is a consequence of the
  human's own acceptance criterion rather than a scope judgement: the twelve tracked files contain no
  banner, so emitting one makes the diff non-empty. The price, which the User Voice asked be shown: a
  developer opening `.claude/agents/architect.md` — a file they have hand-edited for months — is told
  nothing inside the file that it is generated. Check mode is the only remaining guard.
- **Exhaustive error reporting (V14)** — The compiler fails on the first problem, names the file and
  the field, and writes nothing. Enumerating every mistake in one run, with remediation text, is
  polish on a tool with twelve known inputs. Four mistakes in one file now cost four runs.
- **The dangling-role-reference check (V15)** — Warning about role names in `.swarm/spec.yaml` or the
  workflow scripts that no role defines is a good idea and a separate change; it needs none of this to
  be built. What we are choosing to leave without a symptom: a voice switched on in `.swarm/spec.yaml`
  that never runs produces a run that looks entirely normal. Any future version must be scoped to
  `.swarm/spec.yaml` alone — half the references live in JavaScript that only a heuristic can read,
  and a clean result the developer trusts would be worse than today's nothing.
- **A dropped-fields line on every compile (V16)** — Nothing runs on the GitHub side, so nobody is
  surprised at run time; R6 states the drop once. **Condition attached:** the moment anything
  dispatches to `.github/agents/`, this cut is revisited in the same breath. Until then the
  developer's exposure is one trip to this document to learn that `model` and `effort` are not
  written to those files.
- **Fresh-clone install guidance, and a legibility requirement on the GitHub files (V17)** — The only
  user is the tool's author, on a machine already known to have the runtimes; and "the role still
  reads like the role" is not something QA can pass or fail. The price: the first command on a machine
  that is not this one may fail with a missing runtime, and what the developer sees in that case is
  not specified.
- **Amending `CONTEXT.md`'s Role and Personality entries (V18)** — *A contested cut: the Domain
  Modeller tied it to the brief and lost anyway, and the Unblocker ruled it onto this list rather than
  sending it to you, because being wrong is cheap (X9).* The inconsistency predates the brief and the
  constitution already outranks `CONTEXT.md`. The price: a developer reads `CONTEXT.md` to find out
  what a role is, and is told that seven of the twelve things in `swarm/roles/` are not roles. Fixable
  in one commit by anyone, at any time.
- **Coined glossary terms with no requirement behind them (V19)** — `role registry`, `mapping`,
  `carried`, `carried renamed`, `harness schema`, `extra key`, `effective effort`, `corpus`,
  `fidelity baseline`, `faithful`. §11 says a coined term is defined where it is used, or it is not
  used; one of these named an outcome that never occurs.
- **`swarm` and `fixed` fields on a role definition (V20)** — Both facts already live somewhere that
  works, and nothing this change builds reads either one. A second authority whose only symptom on
  disagreement is a voice that runs when the config says off.
- **A dropped-fields note inside the emitted GitHub files (V22)** — It would make the GitHub prompt
  differ from the Claude prompt by a paragraph about the build, to warn a reader on a harness nothing
  runs on.
- **A 30,000-character cap check on emitted bodies (V23)** — The largest body is a fifth of the cap.
  The scenario that closes that gap is a feature nobody has proposed.
- **Designing for a third harness (V24)** — There is no third harness and, under R7, no second
  consumer either. Two consequences the Devil's Advocate asked be visible: **a third harness needing
  a field that neither Claude Code nor GitHub has would require changing the neutral format itself,
  not adding an emitter**; and the neutral format's five fields *are* Claude Code's front-matter
  fields, so the format already is the shape of one emitter — accepted as the right trade for a
  proving run, not defended as a principle.

Also deliberately not decided here, because it is *how*, and *how* is the architect's (§1, §11): what
language the compiler is written in, what invokes it, and what the command is literally called. R14
is the only constraint on that space.

---

## Research

Links, not copies. Paths are relative to `.swarm/runs/current/`.

- [`.work/research-sweep.md`](.work/research-sweep.md) — the opening sweep: the twelve tracked agent
  files and their fields, both harnesses' documented schemas, the size caps, and the workflow
  scripts' dispatch on role names.
- [`.work/research-draft.md`](.work/research-draft.md) — R7: when a harness reads agent definitions.
  They are snapshotted when an invocation begins, so a compile cannot reach a later role in the same
  chain.
- [`.work/research-critique-1.md`](.work/research-critique-1.md) — R9: the byte-level survey of the
  twelve tracked files. UTF-8, no BOM, CRLF in the working tree, LF in the index, a final newline on
  every file, and `.gitattributes` pinning only `*.js`. R4 and R5 are built on this.
- [`.work/research-critique-2.md`](.work/research-critique-2.md) — R10: GitHub's `tools` property
  accepts both a comma-separated string and a list, is not a closed set, and none of the nine tool
  names is renamed.
- [`.work/research-critique-3.md`](.work/research-critique-3.md) — R11: the declared `tests` and
  `coverage` commands do not resolve in this worktree. The degraded-gate warning at the top of this
  file rests on it.

One research question was never answered: **R8, whether any GitHub surface has an equivalent of the
harness's Workflow tool.** Four researchers wrote to one file in an earlier round and three findings
were overwritten. The human answered question 1 without it, and recorded that if GitHub could run a
swarm, that is a fact about a future effort rather than about this one.

The debate itself — four drafts, four critiques, four rebuttals and the four-file assumption register
— is in `.work/`. It is not part of the artifact.
