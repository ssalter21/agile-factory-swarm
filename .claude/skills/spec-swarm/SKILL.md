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

1. **Work out which run this is.** Look at `.swarm/runs/current/`.

   - **No directory** — a fresh run. Create `.swarm/runs/current/work/`.
   - **`answers.md` present** — the last run blocked and the human has answered. This is a
     **resume**. Leave every file where it is; the drafts in `work/` are what the resume re-enters
     over. Do not touch `brief.md`.
   - **A directory with no `answers.md`, and `spec.md` does not say `status: approved`** — there is
     an unapproved spec sitting there. **Stop.** Say what is in it and ask whether to overwrite.
     Never clear it silently: a blocked run holds questions nobody has answered yet.
   - **A directory whose `spec.md` says `status: approved`** — that spec has been through the seam.
     A new brief overwrites it (§11 allows exactly one run directory). Say so, then clear the
     directory and treat it as fresh.

2. **Write the brief, on a fresh run only.** The user's brief goes to `.swarm/runs/current/brief.md`
   **verbatim** — no tidying, no reformatting, no summarising. If the user pointed at a file, copy
   its contents. §11 requires this file to be the human's words, and the whole swarm reads it as
   the statement of what was asked for.

3. **Read `.swarm/spec.yaml`** for the voices that are `on`. The agile agent and the devil's
   advocate cannot be off; if the config says otherwise, say so and use them anyway (§10).

4. **Run the workflow.** Invoking this skill is the user's opt-in to multi-agent orchestration.

   ```
   Workflow({ name: 'spec-chain', args: { mode: 'fresh' | 'resume', voices: [...] } })
   ```

   It is roughly 18 agents on a fresh run — four voices across three passes, the unblocker in each
   gap, the researcher, and the spec writer. That is what §10 asks for; do not trim it to fit a
   size guideline.

5. **Report what came back**, and nothing more.

   - **`outcome: blocked`** — write the question batch to `.swarm/runs/current/questions.md`, one
     numbered question each with why no assumption was safe. Tell the user to answer in
     `answers.md` beside it and run `/spec-swarm` again. There is no partial spec to read.
   - **`outcome: drafted`** — point at `.swarm/runs/current/spec.md`. Say how many open questions
     it carries and how many assumptions. Say plainly that **nothing is built until they write
     `status: approved` themselves**, and that approval means every open question has been
     dispositioned — answered in the spec, or moved into the assumption register with its cost if
     wrong (§11). Do not offer to approve it. Do not edit the front matter.

## Rules

- **Never write `status: approved`.** Not on request, not as a convenience, not "to save a step".
  It is the one field a human writes alone, and it is the only thing that makes a spec
  authoritative (§11).
- **Never commit the run directory.** `.swarm/runs/` is ignored. The spec is state between two
  invocations, not a record.
- **Do not summarise the spec back at length.** The user reads the artifact; that is the point of
  there being one.
