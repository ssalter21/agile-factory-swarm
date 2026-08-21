# Answers

**How these were decided, and it matters for the record.** The human delegated all three, asking
for the lowest-effort answer to each rather than adjudicating them on their merits. The brief is a
proving run: its purpose is to exercise the swarm, not to buy a role compiler. So every answer below
takes the cheapest branch that keeps the run moving, and none of them is a considered ruling on what
the right product is. Treat all three as decisions that would be revisited if this compiler were
ever the actual deliverable.

## A1 — Is the GitHub output meant to run a swarm, or to be a published artifact?

**A published artifact.**

`.github/agents/*.agent.md` is a set of files that exist and validate against the documented schema.
That is the whole of it. **Nobody may claim the swarm runs on GitHub**, and the spec must say that
in a sentence a human reads, not bury it. No requirement may be written about a chain, a seam or a
gate on that harness, because none of those is in scope here.

This is the cheap branch by a wide margin, and it is also the only one that does not restart the
run: the Unblocker recorded that "runnable" is premise-breaking, because all four drafts were
written against a deliverable of twelve compiled prompts.

The missing research finding (R8 — whether GitHub has an equivalent of the Workflow tool) is not
needed to answer this. If it turns out GitHub could run a swarm, that is a fact about a future
effort, not about this one.

## A2 — May the compiler write this repo's live `.claude/agents/*.md`, inside a run?

**Yes, in place. No staging path, no promotion step.**

The compiler writes `.claude/agents/*.md` directly. That is cheaper than inventing a staging
directory and a human promotion step, and it is what makes this brief worth running at all: the
correct output already exists, so **the acceptance criterion is that recompiling leaves the twelve
tracked files byte-identical**. A staging path would put a manual step between the compiler and the
only check that proves it works.

Two ordering constraints go in the spec as requirements, both stated plainly:

1. The compiler must be shown faithful — a clean diff against the twelve tracked files — **before**
   it is permitted to write them.
2. **The run that builds the compiler must not run it.** Regeneration happens on a later
   invocation.

Constraint 2 is belt-and-braces rather than a live hazard: research settled (S13) that a
regeneration cannot reach any role downstream of the compiler within the same run, so the damage the
fatal-if-wrong mark was made against does not exist. It is stated anyway because it costs one
sentence and removes the question.

## A3 — Is front-matter `tools` a YAML sequence or a comma-separated string?

**Sidestep it. Emit the comma-separated string form.**

All twelve tracked files already use the string form, so emitting it is what a byte-identical diff
requires — the question answers itself the moment A2 fixes the acceptance criterion. No probe agent,
no research round.

The spec should record the limit honestly: **whether Claude Code also accepts a YAML sequence is
unknown and untested**, and nothing here depends on the answer. For the GitHub emitter, write
whatever that schema documents; under A1 those files are artifacts that must validate, so the schema
is the authority and there is nothing to guess.
