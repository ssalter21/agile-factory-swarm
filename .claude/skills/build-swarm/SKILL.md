---
name: build-swarm
description: Turn an approved spec into a merged change. Runs the builder chain — architect, coder, cleaner, hardener, architect, QA — and opens the pull request.
disable-model-invocation: true
---

# Run the builder swarm

Everything past this point is bound by the approved spec and nothing else. Read
[`swarm/constitution.md`](../../../swarm/constitution.md) §6 and §11 before you start.

## Steps

1. **Check approval, before spending anything.** Read the front matter of
   `.swarm/runs/current/spec.md`.

   - No run directory, or no `spec.md` — **stop**. There is nothing to build. Point at
     `/spec-swarm`.
   - `status` is anything but `approved` — **stop**, and name what you found. The builder swarm
     refuses to start on a spec that is not approved (§11).
   - `.swarm/runs/current/questions.md` **exists** — **stop**, and list what it asks. The seam is
     still open: that file's presence is what says a question is undispositioned, and after the seam
     no role may ask, so an open question has no route (§11). Point at `/spec-swarm` for the fold.

   This check is here rather than inside the workflow because a refused run should cost nothing.

2. **Get on the right branch.** The `slug` in the front matter is the branch name and the task name
   every hop preserves (§6).

   - Already on it — stay. This is a re-invocation after a halt, and the halted run's commits stay
     (§11).
   - Not on it — create it from the repo's default branch.

3. **Say what the gate will not check.** Read `.swarm/gate.yaml`. Any step that says `missing`
   makes this a **degraded run** (§2). Name them now, before the run, not only in the report.

4. **Run the workflow.** Invoking this skill is the user's opt-in to multi-agent orchestration.

   ```
   Workflow({ name: 'build-chain' })
   ```

   It takes no args: everything it needs is on the blackboard. Six agents on a clean pass, more if
   the chain appeals or bounces.

5. **Report what came back**, and nothing more.

   - **`outcome: built`** — give the gate table, the missing steps, and the pull request. The PR
     body is the durable record; the run directory is not.
   - **`outcome: halted`** — the approved spec is wrong. Name the contradiction. The human amends
     `spec.md`, bumps `revision`, and runs `/build-swarm` again; it restarts at the architect on
     this same branch, keeping the commits already made.
   - **`outcome: human-question`** — the chain used up its appeals, bounced the same thing twice,
     or an agent died. Name which, and what was being asked.
   - **`outcome: budget-exhausted`** — the run stopped one hop short of spending the token budget
     (§12). Name the role it stopped at. Nothing is lost: the branch and the run directory are
     intact, and `/build-swarm` with a larger budget restarts at the architect. Do not re-run it
     on the same budget.

## Rules

- **There is no resume.** §11 gives re-invocation as the only re-entry, and the chain already
  starts at the architect, so running this skill again *is* the restart. Do not build a resume
  path, and do not reach for `resumeFromRunId` — a halt means the spec changed underneath the
  cached plan.
- **Never approve the spec yourself** to get past step 1. If it is not approved, the answer is to
  stop and say so.
- **Never commit `.scratch/` or `.swarm/runs/`.** The plan is a handover, not an artifact.
