---
name: spec-swarm
description: Turn a brief into a spec for the human to approve. Runs the spec swarm — four voices, the researcher, the unblocker, and the spec writer — and stops at the seam.
disable-model-invocation: true
---

# Run the spec swarm

The workflow script has no filesystem access. Everything the blackboard needs is written **here**,
before the workflow is invoked, and read back **here** after it returns. Read
[`swarm/constitution.md`](../../../swarm/constitution.md) §10 and §11 before you start.

## Steps

1. **Work out which run this is.** Look at `.swarm/runs/current/`. §10 names three invocations —
   **fresh**, **resume**, **fold** — and they are told apart by what is on disk:

   ```text
     no directory                                          -> FRESH
     spec.md complete, answers.md newer than it            -> FOLD
     drafts in .work/, answers.md present, no spec.md      -> RESUME (answered block)
     drafts in .work/, no answers.md, no spec.md           -> RESUME (budget stop)
     no drafts, no answers.md, no spec.md                  -> FRESH over the same directory
     spec.md present, no answers.md, not approved          -> STOP and ask
     spec.md present and approved                          -> a new brief overwrites it
   ```

   - **FRESH** — create `.swarm/runs/current/.work/`.
   - **FOLD** — the run reached the seam, the human has answered its questions, and nothing needs
     re-arguing. Only the spec writer runs. Leave every file where it is.
   - **RESUME (answered block)** — the last run blocked and the human has answered. Leave every file
     where it is; the drafts in `.work/` are what the resume re-enters over. Do not touch
     `brief.md`.
   - **RESUME (budget stop)** — the last run stopped for budget (§12) after drafting but before it
     wrote anything for the human. Pass `answers: false` so the voices are not sent to a file that
     does not exist, and leave every file where it is.
   - **FRESH over the same directory** — a budget stop in the sweep or the draft pass, so there is
     nothing to re-enter over. Keep `brief.md` exactly as it is, and clear `.work/`.
   - **STOP and ask** — an unapproved spec is sitting there with no answers beside it. Say what is
     in it, and whether `questions.md` exists, and ask whether to overwrite. Never clear it
     silently: it may hold questions nobody has answered yet.
   - **A new brief overwrites an approved spec** — §11 allows exactly one run directory. Say so,
     then clear the directory and treat it as fresh.

   `questions.md` existing means the seam is still open (§11). Never delete it yourself; only a fold
   removes it, and only the spec writer does that.

2. **Write the brief, on a fresh run only.** The user's brief goes to `.swarm/runs/current/brief.md`
   **verbatim** — no tidying, no reformatting, no summarising. If the user pointed at a file, copy
   its contents. §11 requires this file to be the human's words, and the whole swarm reads it as
   the statement of what was asked for.

3. **Read `.swarm/spec.yaml`** for the voices that are `on`, and for
   `limits.research_rounds_per_gap`. The agile agent and the devil's advocate cannot be off; if the
   config says otherwise, say so and use them anyway (§10).

4. **Run the workflow.** Invoking this skill is the user's opt-in to multi-agent orchestration.

   ```
   Workflow({ name: 'spec-chain', args: {
     mode: 'fresh' | 'resume' | 'fold',
     answers: true | false,          // resume only: false when the resume is a budget stop, not an answered block
     voices: [...],
     researchRoundsPerGap: <limits.research_rounds_per_gap, default 1>,
   } })
   ```

   Twenty or more agents on a fresh run — four voices across three passes, the unblocker in each
   gap, the opening researcher, the spec writer, and a researcher per question the unblocker names
   in a gap. That is what §10 asks for; do not trim it to fit a size guideline.

   A **fold** is one agent: the spec writer alone (§10). Do not run the voices on a fold — the human
   has already read that spec, and re-arguing it changes text they accepted.

5. **Report what came back**, and nothing more.

   - **`outcome: blocked`** — write the unblocker's batch to `.swarm/runs/current/questions.md`,
     **verbatim**, using `swarm/templates/questions.md`. §11 fixes the shape: at most three
     questions, at most a screen each, every question titled on the first screen. Tell the user to
     answer in `answers.md` beside it and run `/spec-swarm` again. There is no partial spec to read.
   - **`outcome: drafted`** — **`questions.md` is rewritten from the returned batch, always.** Where
     the batch is empty, **delete** any `questions.md` that is sitting there: it was answered on the
     way here, and a stale one is read by §11 as a seam that is still open, which would make the
     spec permanently unapprovable. Where there is a batch, write it the same way as above, then
     point the user at it **first**. Say how many questions there are, and that answering them
     is what approval is (§11): they write `answers.md` in prose, run `/spec-swarm` again, and the
     spec writer folds the answers in and deletes `questions.md`. Point at `spec.md` second, and say
     how many assumptions it carries. Say plainly that **nothing is built until the spec is
     approved**. Where the unblocker emitted no batch, say so — there is nothing to answer and the
     spec only has to be read and approved.
   - **`outcome: folded`** — the spec writer wrote the answers into `spec.md` and deleted
     `questions.md`. Confirm `questions.md` is gone; if it is not, the fold did not finish and the
     spec is not approvable. Point at `spec.md` and say nothing is left to answer.
   - **`outcome: budget-exhausted`** — the run stopped one pass short of spending the token budget
     (§12). Name the pass it stopped at. There is no spec to read yet, but the blackboard in
     `.work/` survives: `/spec-swarm` with a larger budget resumes over it if the drafts were
     reached, and starts over if they were not. Do not re-run it on the same budget.

## Rules

- **Write `status: approved` only when the user tells you to.** It is their judgement and theirs to
  delegate (§11), but never yours to volunteer: do not offer it, do not infer it from enthusiasm
  about the spec, and never write it in the same breath as reporting the spec exists. When they do
  delegate it, fill `approved_by` with their name **and the fact that it was delegated**, so the
  record never implies they read what they did not read.
- **Never approve a spec this session produced without the user in the loop at all.** A run may not
  approve its own output (§11). If nobody has said the word, the field stays `draft`.
- **Never commit the run directory.** `.swarm/runs/` is ignored. The spec is state between two
  invocations, not a record.
- **Do not summarise the spec back at length.** The user reads the artifact; that is the point of
  there being one.
- **`questions.md` is the gate, so never touch it outside the two places above.** You write it from
  the unblocker's batch; the spec writer deletes it on a fold. Its presence means the seam is open,
  and that is the only mechanical check §11's disposition rule has.
- **Do not answer a question for the user, and do not recommend an answer the unblocker did not.**
  A recommendation in `questions.md` reports which voice won an argument (§11). Where there is none,
  the voices were tied, and inventing one at this layer would stand in for the human.
