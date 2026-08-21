---
slug: <short-name>
status: draft
revision: 1
approved_by:
approved_at:
---

# <Title>

<!-- Section order is fixed by §11 and this template is that order. The gate warning comes first
     because it changes what approval means. The requirements come next because once the open
     questions live in `questions.md`, the main reader of this file is the architect.

     Ordinary technical English throughout. A term this run invented is defined where it is first
     used, or it is not used. Where an idea is a chain, a fork or a set of states, draw it as a
     plain-text diagram instead of describing it. Plain text, not mermaid: this file is read in an
     editor. -->

> **Degraded run (§2).** <Delete this block entirely when the gate declares a command for all six
> steps.> `.swarm/gate.yaml` declares `missing` for <steps>. Approve knowing those steps are
> checked by no tool in this repo.

## Requirements

<!-- What to build, in the Domain Modeller's language. Behaviour, not implementation. -->

## Assumptions

<!-- The Unblocker's register. One line each: the assumption, what it costs if wrong, why that cost
     is survivable. Every entry says which it is:
       CHOSEN   the Unblocker ruled on a disputed point, because being wrong is cheap
       ASSUMED  nobody knew, and a defensible assumption holds
     Do not flatten one into the other. Calling a ruling an assumption hides that an argument was
     won; calling a coin-toss a ruling claims a confidence nobody has. -->

- **<assumption>** — ASSUMED. If wrong: <cost>. Survivable because <reason>.
- **<disputed point>** — CHOSEN: <the side taken>, because <which voice won, or "neither won, so
  this was picked">. If wrong: <cost>.

## Out of scope

<!-- Everything the Agile Agent vetoed, each with the one-line challenge. The human reads this at
     the seam, so every cut is visible and reversible.

     A CONTESTED cut does not belong here: where another voice tied the requirement to the brief
     and lost anyway, it is a decision nobody made, and it reaches the human as a question in
     `questions.md` instead (§10). -->

- **<requirement>** — <the challenge that cut it>

## Research

<!-- Links, never copies. -->

<!-- There is NO open-questions section. Every disputed point was ruled on by the Unblocker in the
     last gap: what it settled is text above with a register entry, and what it could not settle is
     the human's batch in `questions.md`, which the Spec Writer does not write. -->
