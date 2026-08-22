# Orientation, variant A — abstract first

*Prototype for [#16](https://github.com/ssalter21/agile-factory-swarm/issues/16). Hand-written, not
swarm-produced. This is the block that would sit at the top of
[`spec-neutral-role-format.md`](spec-neutral-role-format.md), directly under the title and above the
degraded-run warning. Throwaway: it exists to be reacted to, not to be adopted as written.*

*Shape borrowed from IETF and the Go design docs — a detachable statement of what the document is,
one captioned figure of the mechanism walked immediately in prose, then why, then cost, then a map
of the rest. See [`../review-document-prior-art.md`](../review-document-prior-art.md) §6.*

---

## What this document is

The spec for one change, approved on 2026-08-20 and merged as PR #13. It moves the twelve role
definitions the swarm runs on out of the files that are their authority today, and makes those files
generated instead. Everything below is requirements, the assumptions they rest on, and what was
deliberately cut.

## The change

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

       Figure 1: one role, before and after. Twelve roles, so multiply by twelve.
```

Today the left-hand column does not exist and the right-hand column is what a human edits. After
this change you edit the left, run one command, and the right is written for you — twice, once per
harness. The Claude files carry all five fields and must come out **byte-identical to the twelve
files tracked today**. That one sentence is the acceptance criterion of the entire change, and most
of what follows exists to serve it. The GitHub files carry three of the five, because `model` and
`effort` have no home there, and **nothing in this repo dispatches to them** — they are a published
artifact that demonstrates the format is neutral, not a second working swarm.

## Why it exists, and what it costs

A role is one file today, and that file is both what a human edits and what the harness loads. That
holds exactly as long as there is one harness. A second harness means either editing the same prompt
in two places forever or accepting that the two drift. This change buys **one point of edit**.

It pays in file count, and the spec says so rather than overselling: twelve files become forty-eight,
twelve of which no consumer reads. And it *creates* a failure that does not exist today — one
authority per role becomes a source and a generated copy that can disagree.

## What can go wrong, once this is merged

```text
  the question check mode asks of one agent file:
  does compiling its role definition reproduce the file on disk?

                                    |
                 +------------------+------------------+
                 | yes                                 | no
                 v                                     v
          +--------------+                     differs how?
          |   IN SYNC    |                             |
          +--------------+          +------------------+------------------+
          exit 0, "unchanged"       | bytes                               | line endings only
                                    v                                     v
                          +-------------------+              +---------------------------+
                          |   STALE           |              |  SAME FILE, DIFFERENT     |
                          |   the source      |              |  CHECKOUT                 |
                          |   moved and the   |              |  a git config, not a bug  |
                          |   output did not  |              +---------------------------+
                          +-------------------+               named as such (R9, X16)
                           named, exit non-zero

  and the state the figure cannot draw, because it leaves no trace at all:

                          +----------------------------------------------+
                          |   HAND-EDITED                                |
                          |   someone opened a generated file and        |
                          |   changed it. Nothing inside the file says   |
                          |   it is generated — the "do not edit" banner |
                          |   was cut (V12) because a banner would break |
                          |   byte-identity. Write mode overwrites the   |
                          |   edit without comment.                      |
                          +----------------------------------------------+

       Figure 2: four states. Two of them are silent until someone runs check mode
       by hand, and check mode reports the last two identically.
```

Check mode is the only detector, it is a command nobody is forced to run, and the spec knows it: the
pre-commit hook and the CI job were both cut (V4, V21) on the grounds that automation should wait
until staleness has bitten once.

## What this change does *not* decide

The language the compiler is written in, what invokes it, and what the command is literally called.
All three are the architect's (§1, §11). R14 is the only constraint on that space: the compiler must
be reachable by the commands `.swarm/gate.yaml` declares for `tests` and `coverage`.

## How to read the rest

- **Requirements (R1–R14)** — what must be true. R4 and R5 are load-bearing; the rest hang off them.
- **Assumptions** — `X`/`C` entries are calls somebody made between two defensible options and the
  losing argument is recorded. `A` entries are things nobody knew. Read the `If wrong:` clause of
  each; it states the blast radius.
- **Out of scope** — twenty-four things deliberately not done, each with the price of not doing it.

**Read this first, though:** the degraded-run warning immediately below. The gate that would have
checked this change could not execute in the worktree it was built in.
