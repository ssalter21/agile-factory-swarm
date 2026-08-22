---
slug: <short-name>
status: draft
revision: 1
approved_by:
approved_at:
---

# <Title>

<!-- Section order is fixed by §11 and this template is that order. The orientation comes first
     because a warning about a change nobody can picture yet is noise; it ends by pointing at the
     warning one line below. The requirements come after both, because once the open questions live
     in `questions.md`, the main reader of that part is the architect.

     Ordinary technical English throughout. A term this run invented is defined where it is first
     used, or it is not used. Where an idea is a chain, a fork or a set of states, draw it as a
     plain-text diagram instead of describing it. Plain text, not mermaid: this file is read in an
     editor. -->

## Orientation

<!-- §11. Written for the human three months from now, who has not seen this change and is not
     hunting errors. Six headings, in this order, none dropped. Reword a heading to fit the change;
     a slot with nothing under it says so in one line. Roughly a tenth of the spec and under a
     thousand words — a guideline, not a cap. Exceed it and say why.

     The Spec Writer holds this pen alone. It selects what matters most to a reader (§10); it does
     not adjudicate, add a requirement, soften a veto or drop an attack. -->

### What this document is

<!-- The change in a sentence, and where it stands. -->

### The change

<!-- What it does, carried by AT LEAST ONE captioned plain-text figure of the mechanism, walked
     immediately in the prose beneath it. A change with nothing graph-shaped in it says so in one
     line instead — that is the only way out of the figure. Plain text, not mermaid: read in an
     editor. -->

### Why it exists, and what it costs

<!-- The forces, and what is paid for the fix. Do not oversell: name what this change makes worse
     and what failure it creates that does not exist today. -->

### What can go wrong, once this is merged

<!-- The failure states. The Devil's Advocate's ranked list is the raw material (§10). -->

### What this does not decide

<!-- What is left to the architect (§1). "Nothing" is an acceptable answer, in one line. -->

### How to read the rest

<!-- The map of the document, then the cuts: AT MOST FIVE of the uncontested cuts from the
     out-of-scope list below, and a line stating how many were left behind and where they are.
     A pointer is not a summary — a reader who is oriented stops reading, and a vetoed requirement
     surviving into the requirements is only visible against the cuts. Contested cuts are not here;
     they are questions (§10). -->

<!-- LAST LINE OF THE ORIENTATION, always present: one line naming anything that made this
     orientation weaker than usual — no figure and why, voices that supplied little, a slot nobody
     could fill — and then, if the run is degraded, pointing at the warning immediately below.
     A thin orientation ships. It may not be silent. -->

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
