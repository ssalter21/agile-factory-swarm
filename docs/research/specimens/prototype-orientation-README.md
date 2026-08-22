# Prototype: the orientation block

Throwaway artifact for [#16](https://github.com/ssalter21/agile-factory-swarm/issues/16). Written by
hand, not by the swarm. Nothing here is law — writing the law is
[#18](https://github.com/ssalter21/agile-factory-swarm/issues/18).

The subject is [`spec-neutral-role-format.md`](spec-neutral-role-format.md): 559 lines, 6,251 words,
the only spec the swarm has taken through approval to a merged change, and one the principal has not
read. That is what makes it a fair cold-read test today.

| file | what it is |
|---|---|
| [`prototype-orientation-A.md`](prototype-orientation-A.md) | Variant A, **abstract first**. 750 words, two ASCII figures. IETF / Go-design-doc shape: a detachable statement of what the document is, one captioned figure of the mechanism walked immediately in prose, why, cost, then a map of the rest. |
| [`prototype-orientation-B.md`](prototype-orientation-B.md) | Variant B, **context first**. 351 words, no figures, no headings, no document map. Nygard-ADR shape: load the reader with the forces in tension so the requirements read as a response. |
| [`prototype-coldread-A.md`](prototype-coldread-A.md) | The whole spec with variant A spliced in under the title. **Contains one planted error.** This is the instrument. |
| [`prototype-orientation-ANSWER-KEY.md`](prototype-orientation-ANSWER-KEY.md) | Where the planted error is. **Do not open until after the read.** |

## Measurements

| | words | share of the document it fronts | prose reading time @ 200–250 wpm |
|---|---|---|---|
| Variant A | 750 | 10.7% of 7,003 | 3.0–3.8 min, plus two figures |
| Variant B | 351 | 5.3% of 6,602 | 1.4–1.8 min |

For scale, from [`../review-document-prior-art.md`](../review-document-prior-art.md): the orienting
part runs 30–40% below ~1,500 words and collapses to 1–3% above ~10,000. At 6,251 words this spec
sits between those regimes, and both variants land inside the interpolated band — A at the top of
it, B at the bottom. Neither is obviously the wrong size, which is why this has to be read rather
than argued.

Note what the arithmetic says about the destination's "five minutes": at 200–250 wpm that is
1,000–1,250 words, which is **larger than either variant**. Five minutes may be a generous budget
rather than a tight one. No source in the research states a reading-time target at all.

## The protocol

Three questions, in this order, and stop after each.

1. **Read A and B on their own** — about five minutes for the pair. Which one leaves you knowing
   what the change is? Not which reads better: which one you could act on.
2. **Then the timed read.** Open `prototype-coldread-A.md`, start a timer, and read until you feel
   oriented — not until you have read it all. Note the time and what you were looking at when you
   stopped.
3. **Then the error hunt.** There is exactly one planted error in `prototype-coldread-A.md`: a
   sentence that contradicts another sentence in the same document. Find it. The question is not
   whether you find it but **where you looked first**, and whether the orientation sent you there.
   The answer key names it.

Record what misdirected, what was buried, and what needed no explaining. That is the ticket's
resolution.
