# Answer key

**Spoilers. Do not read before the cold read described in
[`prototype-orientation-README.md`](prototype-orientation-README.md).**

---

## The planted error

**R8 — "One compile command, with a write mode and a check mode", line 284.** A third bullet was
added under the two real ones:

> - A **pre-commit hook** runs check mode, so a stale tree cannot be committed.

No such requirement is in the spec. It is contradicted in three places, none of them adjacent:

| where | line | distance from the plant |
|---|---|---|
| the orientation — "the pre-commit hook and the CI job were both cut (V4, V21)" | 93 | 191 lines back |
| **X3** in the assumption register — "the pre-commit hook and the CI job stay cut" | 426 | 142 lines on |
| **V4, V21** on the out-of-scope list — build the automation when staleness has bitten once | 564 | 280 lines on |

It was chosen over the obvious kind of plant — a wrong field in a list, refuted by the next sentence
— because that one is caught by reading the paragraph, which tests nothing. This one is caught only
by carrying something from elsewhere in the document. It is also a realistic failure for a merged
document: a requirement that survives a veto, which is precisely what a spec assembled from six
voices is at risk of.

## What the test is measuring

Not whether you found it. **Where you looked, and what you were carrying when you got to R8.**

- **You snagged at R8 and knew it was wrong without checking** — the orientation loaded. That is the
  case for keeping A's cost.
- **You snagged at R8 but went hunting to confirm** — the orientation registered as a reference you
  could return to, not as something you retained. Weaker, still a result.
- **You found it later, from the out-of-scope list** — the out-of-scope list is doing the
  orienting work, 400 lines in, and #18 should ask why it is at the bottom.
- **You did not find it** — the strongest finding on this file, not the weakest. One captioned
  figure and 750 words at the top do not survive 400 lines of requirements, and #18 should stop
  treating "put a diagram in it" as the answer.

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
