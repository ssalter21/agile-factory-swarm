# Answer key

**Spoilers. Do not read before the cold read described in
[`prototype-orientation-README.md`](prototype-orientation-README.md).**

---

## The planted error

**R6 — "The GitHub compile emits four things and nothing else".** Its opening sentence was changed
to read:

> `.github/agents/<name>.agent.md` for all twelve roles, carrying `name`, `description`, `tools`,
> `model`, and the prompt as the body.

The original says `name`, `description`, `tools` and the prompt — three fields, not four. The
planted `model` contradicts three other places in the same document:

1. **Figure 1** in the orientation, which shows the GitHub emit as `name, description, tools` and
   labels it `[lossy: model and effort are dropped]`.
2. **R6's own next sentence**, two lines later: "`model` and `effort` are **dropped**".
3. **A5** in the assumption register, and **V6** on the out-of-scope list, which give the reason:
   there is no correct model value to write.

It is also self-refuting against R6's own title, which says four things — and with `model` added the
list is five.

## What the test is measuring

Not whether you found it. Whether the orientation put your eye on the field table before you reached
R6, so that a wrong field list read as wrong on sight rather than as something to check.

- **If you caught it at R6 and had to go back to Figure 1 to confirm** — the figure worked, but as a
  reference you consulted, not as something you were carrying.
- **If you caught it at R6 immediately, without re-checking** — the figure loaded, which is the case
  for keeping it.
- **If you did not catch it** — that is the strongest result on the file, not the weakest. It means
  a mechanism figure at the top does not survive 400 lines, and #18 should stop treating "put a
  diagram in it" as the answer.

## A second thing, not planted — found while writing the orientation

Writing variant A surfaced what may be a genuine hole in the spec, and it is recorded here because
it is evidence about whether the orientation is worth its cost, not because #16 has to resolve it.

**X3** rules that check mode must exist, against the Agile Agent's "`git status` is the check", on
two grounds: `git status` can only be consulted *after* the destructive act, and it cannot tell
"stale because the source moved" from "I edited this a minute ago".

The first ground holds. **The second appears to apply to check mode equally.** Check mode compares
compiled output against the file on disk; a moved source and a hand-edited output produce the same
signal. It cannot distinguish them either. So half of the stated justification for the single
largest piece of scope the human did not ask for looks like it does not survive contact.

That is not certain — it may be that X3 only ever meant the first ground and the second is colour.
But four voices, a critique and a rebuttal pass did not catch it, and one person writing 750 words
of orientation did, in an afternoon.
