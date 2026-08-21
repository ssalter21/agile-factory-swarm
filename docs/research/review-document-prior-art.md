# What review documents put first, and how long it is

Primary-source capture for wayfinder ticket #17. Supplies facts to ticket #18, which decides.
Nothing here recommends a design; the one opinion section is at the end and is labelled.

**Method.** Every number below was measured by me from a fetched copy of the real document, not
from a template and not from a blog post about it. Word counts are whitespace-delimited tokens.
Line counts are physical lines of the source (Markdown/AsciiDoc) or of the plain-text RFC after
stripping page headers and `[Page N]` footers. Oxide RFDs are only published as rendered HTML, so
their word counts come from tag-stripped HTML body text; each Oxide page carries about 22 words of
metadata chrome ("This RFD can be accessed by the following groups... State... Authors...
Updated") which I subtract where I quote "preamble prose".

Fetched 2026-08-21. Corpora used:

- `rust-lang/rfcs` @ shallow clone of `master`, 642 files in `text/`, 638 with >= 50 words.
- `arachne-framework/architecture` @ shallow clone, 17 ADRs.
- `adr/madr` @ shallow clone, template plus its own 18-decision log.
- 9 public Oxide RFDs plus the public RFD index (80 RFDs are public).
- 4 IETF RFCs in plain text plus RFC 7322, the RFC Style Guide.
- 2 Go design documents from `golang/proposal`.

---

## 1. Oxide RFDs

Sources: <https://rfd.shared.oxide.computer/rfd/0001> (the process RFD),
<https://rfd.shared.oxide.computer/rfd/0005>, and RFDs
[26](https://rfd.shared.oxide.computer/rfd/0026),
[48](https://rfd.shared.oxide.computer/rfd/0048),
[63](https://rfd.shared.oxide.computer/rfd/0063),
[107](https://rfd.shared.oxide.computer/rfd/0107),
[146](https://rfd.shared.oxide.computer/rfd/0146),
[397](https://rfd.shared.oxide.computer/rfd/0397),
[459](https://rfd.shared.oxide.computer/rfd/0459),
[532](https://rfd.shared.oxide.computer/rfd/0532).

### 1.1 What is first, and what job it does

There is no mandated first section. What every RFD has is an **unnumbered preamble**: prose sitting
between the title block and the first heading. Its job in the RFDs I measured is to say what the
document is about and to hand the reader the prerequisite reading. RFD 63's preamble is almost
entirely a reading list ("It is recommended that readers familiarize themselves with the following
RFDs..." followed by five RFDs and eleven external papers and IETF RFCs). RFD 397's preamble is a
three-sentence history of how the team got into the problem, ending "In this RFD, we'll discuss the
problem space in more detail."

What RFD 1 *does* mandate is a metadata block at the very top: `:authors:`, `:state:`,
`:discussion:` (a link to the integrating PR), `:labels:`. State is one of six: `prediscussion`,
`ideation`, `discussion`, `published`, `committed`, `abandoned`. RFD 1 is explicit that
`committed` means "it is not an idea of some future state but rather an explanation of how a system
works". So the first thing an Oxide reader learns is not what changed but **how much to trust the
document**.

### 1.2 Lengths (measured)

Body word counts from rendered HTML; "preamble prose" is preamble minus ~22 words of chrome.

| RFD | total words | preamble prose | preamble as % | first named section (words) |
| --- | --- | --- | --- | --- |
| 26 Host OS & Hypervisor | 10,804 | 135 | 1.2% | Hypervisor Choices (105) |
| 48 Control Plane Requirements | 7,333 | 13 | 0.2% | Introduction (331) |
| 63 Network Architecture | 20,742 | 215 | 1.0% | Customer and Oxide Benefits and Goals (858) |
| 107 Workflows Engine | 3,059 | ~0 | 0% | Abstract (343), then Introduction (434) |
| 146 Public job descriptions | 2,451 | 67 | 2.7% | tl;dr (64) |
| 397 async/await challenges | 5,128 | 156 | 3.0% | Goals of this RFD (80) |
| 459 Component lifecycle | 2,683 | 31 | 1.2% | Introduction (85) |
| 532 Internal HTTP API versioning | 3,889 | 65 | 1.7% | Assumptions (60) |
| 1 Requests for Discussion | 3,495 | 263 | 7.5% | When to use an RFD (101) |

RFD 397 is the most compact orienting stack I found in the corpus: preamble (156) + "Goals of this
RFD" (80) + "Technical problem summary" (113) = **349 words, 6.8% of a 5,128-word document**, and
the whole problem is stated in one paragraph beginning "Briefest summary:".

"Goals of this RFD" is goals for the **document**, not the system: "The goals of this RFD are to
clearly explain the problem we've run into, its scope, risk factors, etc. ... The goal of this RFD
is not to rearchitect the whole stack or pick any other solution."

### 1.3 How "why does this exist" is handled

Assumed at document level, mandated at decision level. RFD 1 requires that RFDs "Document our
reasoning including data and references wherever possible; making it easy for our future selves
(and those who join in the future) to understand the decisions we've made and why". RFD 5 defines
"determination" - the point at which a direction is committed - and says "Once made, a
determination should be recorded in an RFD." RFD 532 has a section literally headed
`Determinations` (566 words) placed third, before any discussion, and a later section headed "The
disaster we're trying to avoid" (480 words). So the *why* is a named section in some RFDs
(`Determinations`, `Goals of this RFD`, `Customer and Oxide Benefits and Goals`) and narrative in
others. It is not a fixed slot.

### 1.4 Diagrams in the orienting part

Rare, and never at the very top. Across the 9 public RFDs I fetched there is **one** embedded image
in total (RFD 63, 38.6% of the way into the document). Preformatted blocks (ASCII art or code):

- RFD 63: first preformatted block at 7.3% in, inside "High-Level Overview", captioned "Logical
  view". The section says "The following series of images describe different views of the system".
  Subject: **the system**, in several views.
- RFD 397: first preformatted block at 10.0% in, inside "Example with Mutexes". Subject: **the
  failure mode**, as compilable Rust that goes wrong.
- RFD 26: first at 73% in. RFDs 48, 107, 146, 459, 532: none at all.

### 1.5 What it says about its reader

Nothing explicit that I could find. The strings "reader", "audience" and equivalents do not appear
in RFD 1 in any audience-defining sense (the only near-miss is "our future selves (and those who
join in the future)"). What RFD 1 *does* control is access: each RFD page states "This RFD can be
accessed by the following groups: [public]". Audience as permission, not audience as reading level.
RFD 63's preamble names its prerequisites instead, which is an implicit reader definition ("someone
who has read RFDs 9, 21, 24, 58, 62").

### 1.6 Group authorship

`:authors:` is a list, and RFD 1 calls them "The authors (and therefore owners) of an RFD". Of the
sample: RFD 26 has 3 authors, RFD 1 and RFD 107 have 2, the rest 1. **I found no guidance anywhere
in RFD 1 or RFD 5 on how a multi-author RFD reconciles voice.** The prose in practice is
first-person plural ("we"), which reads as the company rather than the authors. The RFD prototype
file (`prototypes/prototype.adoc`, referenced by RFD 1) lives in a private repo and I could not
read it.

---

## 2. Rust RFCs

Sources: <https://github.com/rust-lang/rfcs>, template at
<https://github.com/rust-lang/rfcs/blob/master/0000-template.md>, process at
<https://github.com/rust-lang/rfcs/blob/master/README.md>.

### 2.1 What is first, and what job it does

Four metadata lines (Feature Name, Start Date, RFC PR, Rust Issue), then `## Summary`: "One
paragraph explanation of the feature." Then `## Motivation`, described in the template as "one of
the most important sections of any RFC, and can be lengthy" - its job is to state the user-facing
problem, "including necessary background" and "several specific use cases".

**Note: the template has no author field.** Zero of the 642 files in `text/` carry an `- Author`
line. Authorship lives in git and in the PR, not in the document.

### 2.2 What "guide-level explanation" actually contains, and who it is for

The template (verbatim): "Explain the proposal as if it was already included in the language and
you were teaching it to another Rust programmer. That generally means: Introducing new named
concepts. Explaining the feature largely in terms of examples. Explaining how Rust programmers
should *think* about the feature ... If applicable, provide sample error messages, deprecation
warnings, or migration guidance. If applicable, describe the differences between teaching this to
existing Rust programmers and new Rust programmers." And: "For implementation-oriented RFCs (e.g.
for compiler internals), this section should focus on how compiler contributors should think about
the change."

So: **it is a draft of the future documentation, written in the present tense as if the change had
already shipped, carried by examples.** The reference-level section is then told to "return to the
examples given in the previous section".

The provenance is unusually explicit. The split replaced "Detailed design" + "How We Teach This" on
2017-07-12, commit
[`f026f04f`](https://github.com/rust-lang/rfcs/commit/f026f04f773e53e15a4e26dd5bb687d0c5c9efbe).
Its message states the reasoning:

> These sections replace the "Detailed design" and "How do we teach this?" sections, and switch
> their order. Instead of describing how we would teach a change as a result of a proposal, the
> "Guide-level explanation" section will actually attempt to teach the reader the feature, in a
> lightweight way. The guide-level explanation appears first in order to help RFC writers keep Rust
> users in the front of their minds, and in order to help RFC readers understand how an RFC will
> affect them sooner in the RFC. This will hopefully make the RFC process more accessible to people
> who are Rust users but not compiler or language design experts.

The named audience of the orienting part is therefore **the affected user who is not an expert in
the subsystem being changed**, and the stated purpose is that they learn how it affects them
*sooner*.

### 2.3 Lengths (measured over 638 RFCs)

| measure | min | p25 | median | p75 | max |
| --- | --- | --- | --- | --- | --- |
| total lines | 26 | 110 | **209** | 398 | 2,206 |
| total words | 94 | 665 | **1,330** | 2,720 | 13,457 |
| Summary lines | 3 | 5 | **7** | 12 | 108 |
| Summary words | 3 | 20 | **39** | 73 | 650 |
| Summary as % of words | 0.1% | 1.6% | **3.0%** | 5.0% | 24.8% |
| Motivation words | 5 | 103 | **186** | 393 | 2,971 |
| Summary+Motivation lines | 0 | 21 | **36** | 68 | 452 |
| Summary+Motivation as % | 0.4% | 11.6% | **21.6%** | 32.4% | 97.4% |

Only **245 of 638 (38%)** have a `Guide-level explanation` heading at all; the split postdates
2017, and many RFCs use `Detailed design` or bespoke headings. For those 245:

| measure | min | p25 | median | p75 | max |
| --- | --- | --- | --- | --- | --- |
| total lines | 49 | 174 | **285** | 519 | 2,100 |
| Guide words | 3 | 122 | **299** | 603 | 3,096 |
| Guide as % of words | 0.2% | 8.3% | **14.9%** | 24.7% | 68.8% |
| Summary+Motivation+Guide lines | 15 | 55 | **98** | 175 | 680 |
| Summary+Motivation+Guide as % | 2.6% | 23.9% | **34.8%** | 45.5% | 86.0% |

Named specimens:

| RFC | total | Summary | Motivation | Guide | orienting stack |
| --- | --- | --- | --- | --- | --- |
| [3151 scoped threads](https://github.com/rust-lang/rfcs/blob/master/text/3151-scoped-threads.md) | 295 lines / 1,324 w | 43 w | 144 w | 307 w | 135 lines, 494 w = **37%** |
| [2585 unsafe block in unsafe fn](https://github.com/rust-lang/rfcs/blob/master/text/2585-unsafe-block-in-unsafe-fn.md) | 211 lines / 1,514 w | 33 w | 407 w | 369 w | 97 lines, 809 w = **53%** |
| [2394 async/await](https://github.com/rust-lang/rfcs/blob/master/text/2394-async_await.md) | 657 lines / 4,263 w | 30 w | 396 w | 545 w (3 subsections) | 171 lines, 971 w = **23%** |
| [2094 non-lexical lifetimes](https://github.com/rust-lang/rfcs/blob/master/text/2094-nll.md) | 2,191 lines / 13,457 w | 97 w | 2,593 w (6 subsections) | n/a (pre-2017 form) | 452 lines, 2,690 w = **21%** |

RFC 2094 is the closest analogue to a large merged spec, and its orienting part is worth naming
precisely: after a 97-word Summary, the Motivation is "What is a lifetime?" (549 w) followed by
**four numbered "Problem case #N" sections** (243 / 327 / 777 / 412 w), each a short program that
does not compile today and should. 20% of the document is spent on failing examples before any
design appears.

### 2.4 How "why does this exist" is handled

A required, named, early section (`Motivation`), and the template calls it one of the two most
important. It is user-problem-shaped by instruction: "Any changes to Rust should focus on solving a
problem that users of Rust are having."

### 2.5 Diagrams

Effectively absent. **5 of 642 files (0.8%)** embed an image
(`1644-default-and-expanded-rustc-errors`, `1824-crates.io-default-ranking`,
`1866-more-readable-assert-eq`, `3307-de-rfc-type-ascription`, `3631-rustdoc-cfgs-handling`).
2 mention Mermaid. Every one of those five images is a **screenshot of user-visible output** -
compiler error text, a web ranking, rustdoc badges, a `git diff --shortstat` - not an architecture
diagram. RFC 1644's image sits inside `Motivation`, i.e. in the orienting part, and shows the change
as the user will experience it. I found no Rust RFC whose orienting part diagrams the system.

The load-bearing visual device in Rust RFCs is instead the **fenced code block**: before/after
snippets and error messages.

### 2.6 Group authorship

The document is single-voiced by construction and the group's disagreement is deliberately kept
*out* of it. The README puts the reconciliation in the pull request: "For RFCs with lengthy
discussion, the motion to FCP is usually preceded by a *summary comment* trying to lay out the
current state of the discussion and major tradeoffs/points of disagreement." That summary comment
is not merged into the RFC text. The merged RFC keeps `Drawbacks`, `Rationale and alternatives` and
`Unresolved questions` as the in-document residue of dissent.

---

## 3. Architecture Decision Records

Sources: Michael Nygard, "Documenting Architecture Decisions", 2011-11-15,
<https://www.cognitect.com/blog/2011/11/15/documenting-architecture-decisions>;
<https://github.com/arachne-framework/architecture>; <https://github.com/adr/madr>.

### 3.1 What is first, and what job it does

`Context`. Nygard's own words: "This section describes the forces at play, including technological,
political, social, and project local. These forces are probably in tension, and should be called
out as such. **The language in this section is value-neutral. It is simply describing facts.**"

Its job is to make the decision *inevitable-looking* before it is stated - to load the reader with
the tensions so that `Decision` reads as a response rather than an assertion.

MADR renamed it `Context and Problem Statement` and instructs: "two to three sentences or ... an
illustrative story. You may want to articulate the problem in form of a question. Make the scope of
the decision explicit, for instance, by calling out or pointing at structural architecture elements
(components, connectors, ...)."

### 3.2 Lengths (measured)

Nygard's article is itself an ADR. Its four sections:

| section | words | % of the ADR |
| --- | --- | --- |
| Context | 298 | 38% |
| Decision | 412 | 53% |
| Status | 1 ("Accepted.") | 0% |
| Consequences | 65 | 8% |

Total 784 words. His stated budget: "**The whole document should be one or two pages long.**"

Real corpora:

| corpus | n | median lines | median words | median Context words | median Context share |
| --- | --- | --- | --- | --- | --- |
| arachne-framework | 17 | **75** | **744** | 251 | **37%** |
| MADR's own decision log | 19 | **35** | **172** | 20 | **12%** |

arachne range: 40-277 lines, 384-2,861 words. Two of the 17 have a vestigial Context - ADR 003 has
19 Context words in a 2,030-word document; ADR 014 has 29 in 922 - so the form does not hold under
load without discipline.

### 3.3 How "why does this exist" is handled

It *is* the first section. That is the whole design of the form.

### 3.4 Diagrams

None in the orienting part in either corpus. The only images in the MADR repository are three
screenshots inside ADR 0008 illustrating *formatting options for a status field*. Nygard's format
has no diagram slot and his article argues against non-prose: "This requires good writing style,
with full sentences organized into paragraphs. Bullets are acceptable only for visual style, not as
an excuse for writing sentence fragments."

### 3.5 What it says about its reader

Nygard names the reader outright: "We will write each ADR **as if it is a conversation with a future
developer**." The article's own Context section argues why: "A new person coming on to a project may
be perplexed, baffled, delighted, or infuriated by some past decision. Without understanding the
rationale or consequences, this person has only two choices: blindly accept the decision, [or]
blindly change it."

MADR names the reader by *role* instead, in YAML front matter: `decision-makers`, `consulted`
("everyone whose opinions are sought ... with whom there is a two-way communication"), `informed`
("everyone who is kept up-to-date ... one-way communication"). That is RACI, adopted deliberately -
see MADR ADR
[0015](https://github.com/adr/madr/blob/main/docs/decisions/0015-include-consulting-informed-of-raci.md).

### 3.6 Group authorship

Nygard's format **has no author field at all** - Title, Context, Decision, Status, Consequences.
Voice is prescribed rather than attributed: the Decision "is stated in full sentences, with active
voice. 'We will ...'". The document speaks as the team by fiat. MADR's answer is the RACI front
matter above: name the roles, not the writers.

### 3.7 What they lose by being short

I can only report evidence, not a verdict. Three pieces of primary evidence:

1. **Orientation is distributed across the chain, not present in any one document.** Nygard's own
   Consequences section: "One ADR describes one significant decision ... The consequences of one ADR
   are very likely to become the context for subsequent ADRs." A reader arriving cold at ADR 012
   must walk backwards to orient. There is no per-document system overview and no place for one.
2. **The form has been extended repeatedly by its own users.** MADR's decision log is 18 documented
   changes to Nygard's four sections, adding `Decision Drivers`, `Considered Options`, `Pros and
   Cons of the Options`, `Confirmation`, `More Information`, a status field, and RACI. Two of those
   decisions are explicitly about what belongs above the fold: ADR
   [0016](https://github.com/adr/madr/blob/main/docs/decisions/0016-outcome-before-detailed-pros-cons.md)
   ("Most important information should be above the fold") and ADR
   [0008](https://github.com/adr/madr/blob/main/docs/decisions/0008-add-status-field.md), which
   rejected a `Status:` text line partly because it "uses space at the beginning. When users read
   MADR, they should directly dive into the context and problem and not into the status."
3. **Real ADRs burst the budget when the subject is big.** arachne ADR 003 is 277 lines / 2,030
   words and ADR 015 is 215 lines / 2,861 words, well past "one or two pages", and both have
   near-vestigial Context sections.

Nygard's article contains **no** goals/non-goals slot, no alternatives-considered slot, and no
audience-facing overview of the changed system. MADR added the first two. Nobody added the third.

---

## 4. Google design docs

The honest source note first: **Google does not publish its design doc template.** The Chromium
"Design doc template" linked from
<https://www.chromium.org/developers/design-documents/> is a Google Doc behind sign-in; I fetched it
and could not read the body. So this section rests on (a) a Google engineer's public description,
(b) the free online edition of *Software Engineering at Google*, and (c) Go's public design docs,
which are written by Google employees under a published process and are measurable.

### 4.1 Malte Ubl, "Design Docs at Google", 2020-07-06

<https://industrialempathy.com/posts/design-docs-at-google/>. First-person account by a Google
engineer, not an official Google publication.

Stated anatomy, in order: **Context and scope** -> **Goals and non-goals** -> **The actual design**
-> **Alternatives considered** -> **Cross-cutting concerns**.

- *Context and scope* (verbatim): "This section gives the reader a very rough overview of the
  landscape in which the new system is being built and what is actually being built. This isn't a
  requirements doc. **Keep it succinct!** The goal is that readers are brought up to speed but some
  previous knowledge can be assumed and detailed info can be linked to. This section should be
  entirely focused on **objective background facts**."
- *Goals and non-goals*: "A short list of bullet points ... non-goals aren't negated goals like
  'The system shouldn't crash', but rather things that could reasonably be goals, but are explicitly
  chosen not to be goals."
- *Length*: "Design docs should be sufficiently detailed but **short enough to actually be read by
  busy people. The sweet spot for a larger project seems to be around 10-20ish pages.** If you get
  way beyond that, it might make sense to split up the problem ... It is absolutely possible to
  write a **1-3 page 'mini design doc'**." No guidance is given on how long Context and scope should
  be as a share of that.
- *Diagram*: "In many docs a **system-context-diagram** can be very useful. Such a diagram shows the
  system as part of the larger technical landscape and allows readers to contextualize the new
  design given its environment that they are already familiar with." Note where it sits: this advice
  is under *The actual design*, not under *Context and scope*. Subject: **the system**, in its
  environment.
- *Code*: "Design docs should rarely contain code, or pseudo-code except in situations where novel
  algorithms are described."
- *Why does this exist*: not a named section. It is split between the objective facts in Context and
  scope and the requirements in Goals and non-goals.
- *Reader*: unnamed in the anatomy. The article only says the doc is "shared with a wider audience
  than the original set of authors and close collaborators" at review time.
- *Group authorship*: the article says "the primary author or authors" and "authors and close
  collaborators" and offers no rule for reconciling voice.

### 4.2 *Software Engineering at Google*, ch. 10 "Documentation"

<https://abseil.io/resources/swe-book/html/ch10.html>. Official companion text, freely published.

- "Most teams at Google require an approved design document before starting work on any major
  project. A software engineer typically writes the proposed design document using a specific design
  doc template approved by the team."
- On audience, it is emphatic and it is the strongest primary source I found on question 5: "before
  you begin writing, you should (formally or informally) identify the audience(s) your documents
  need to satisfy ... **Always try to identify a primary audience and write to that audience.**"
- It splits readers into **"seekers"** ("know what they want and want to know if what they are
  looking at fits the bill" - served by consistency) and **"stumblers"** ("might not know exactly
  what they want" - served by clarity, and by "overviews or introductions ... that explain the
  purpose of the code they are looking at").
- On declaring the audience in the document: "sometimes you also need to explicitly call out and
  address the audience in a document. Example: 'This document is for new engineers on the Secret
  Wizard project.'"
- And an opening device: "A lot of documents at Google begin with a 'TL;DR statement' such as
  'TL;DR: if you are not interested in C++ compilers at Google, you can stop reading now.'"

### 4.3 Go design docs (measurable Google-authored specimens)

`golang/proposal`, process at <https://github.com/golang/proposal/blob/master/README.md>.

**[Type Parameters Proposal](https://github.com/golang/proposal/blob/master/design/43651-type-parameters.md)**
(Ian Lance Taylor and Robert Griesemer, 2021-08-20): 4,275 lines / 24,207 words. Header is title,
two author names, one date. Then:

| section | lines | words |
| --- | --- | --- |
| Status (what state this document is in) | 9 | 44 |
| Abstract | 15 | 95 |
| **How to read this proposal** | 17 | 97 |
| Very high level overview | 38 | 283 |
| Background | 34 | 217 |
| **orienting stack total** | **113 (2.6%)** | **736 (3.0%)** |

Two things are unusual and directly relevant. First, there is an explicit navigation section: "This
document is long. Here is some guidance on how to read it," followed by six bullets describing the
document's own shape, ending "Following the examples some minor details are discussed in an
appendix." Second, the overview section declares its own audience and disclaims the rest: "This
section explains the changes suggested by the design very briefly. **This section is intended for
people who are already familiar with how generics would work in a language like Go.** These concepts
will be explained in detail in the following sections." It closes by routing the reader elsewhere:
"You may prefer to skip ahead to the examples to see what generic code written to this design will
look like in practice."

**[Signed shift counts](https://github.com/golang/proposal/blob/master/design/19113-signed-shift-counts.md)**
(Robert Griesemer, 2019): 225 lines / 1,508 words. Summary 41 words (7 lines). Background 4 words -
a single cross-reference. The small doc drops the orienting apparatus almost entirely.

---

## 5. IETF RFCs

Sources: RFC 7322 (RFC Style Guide) <https://www.rfc-editor.org/rfc/rfc7322.txt>; RFC 8446 (TLS
1.3) <https://www.rfc-editor.org/rfc/rfc8446.txt>; RFC 9293 (TCP)
<https://www.rfc-editor.org/rfc/rfc9293.txt>; RFC 6749 (OAuth 2.0)
<https://www.rfc-editor.org/rfc/rfc6749.txt>.

### 5.1 What is first, and what job it does

RFC 7322 section 4 fixes the order and marks what is required:

```
First-page header  *[Required]   Title [Required]   Abstract [Required]
RFC Editor or Stream Note *[Upon request]   Status of This Memo *[Required]
Copyright Notice *[Required]   Table of Contents *[Required]
Body:  1. Introduction [Required] ... 9. Security Considerations [Required] ...
```

"Within the body of the memo, the order shown above is strongly recommended. Exceptions may be
questioned. Outside the body of the memo, the order above is required."

The **Abstract**'s job is defined precisely, and two of its constraints are the interesting ones:

> Every RFC must have an Abstract that provides a concise and comprehensive overview of the purpose
> and contents of the entire document, to give a technically knowledgeable reader a general overview
> of the function of the document. ... **the Abstract should be complete in itself. It will appear in
> isolation in publication announcements and in the online index of RFCs. Therefore, the Abstract
> must not contain citations.** ... an Abstract is not a substitute for an Introduction; the RFC
> should be self-contained as if there were no Abstract.

And: "The body of the memo and the Abstract **must be self-contained and separable**. This may result
in some duplication of text between the Abstract and the Introduction; **this is acceptable**." The
Abstract is designed to be *detached from the document and still work*.

The **Introduction** is required, must be the first body section, and "explains the motivation for
the RFC and (if appropriate) describes the applicability of the document". Alternate titles
"Overview" or "Background" are explicitly permitted.

### 5.2 Lengths (measured, pagination stripped)

| RFC | total lines | total words | Abstract words | Abstract % | first body section | its lines / words | its % |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 8446 TLS 1.3 | 8,485 | 38,754 | 58 | 0.15% | 1. Introduction | 212 / 1,104 | 2.85% |
| 9293 TCP | 5,577 | 34,433 | 157 | 0.46% | 1. Purpose and Scope | 47 / 359 | 1.04% |
| 6749 OAuth 2.0 | 4,033 | 19,235 | 63 | 0.33% | 1. Introduction | 483 / 2,671 | 13.9% |
| 7322 Style Guide | 1,277 | 5,862 | 72 | 1.23% | 1. Introduction | 44 / 269 | 4.59% |

Three orienting devices worth naming, all inside the first tenth of the document:

- **RFC 8446 section 1.2 "Major Differences from TLS 1.2"**: 68 lines / 408 words, beginning at 4.8%
  into the document. A flat bulleted list of what changed against the previous version, prefaced
  "It is not intended to be exhaustive, and there are many minor differences." This is the closest
  thing in the corpus to a diff summary for a reader who knew the old system.
- **RFC 8446 section 2 "Protocol Overview"**: 526 lines / 1,892 words (4.9% of the document),
  containing Figure 1, the full handshake message flow, at 7.1% in.
- **RFC 6749 section 1.2 "Protocol Flow"**: Figure 1 at 8.6% into the document - an abstract
  four-role interaction diagram, followed by six lettered steps (A)-(F) walking it.

RFC 9293 also carries a mechanism worth recording for a requirements-bearing document: every
normative keyword is individually labelled and indexed. "Sentences using 'MUST' are labeled as
'MUST-X' with X being a numeric identifier enabling the requirement to be located easily when
referenced from Appendix B." I counted 144 `MUST-` labels; Appendix B, "TCP Requirement Summary",
begins at 89% into the document.

### 5.3 How "why does this exist" is handled

A required section, and in RFC 9293 it is section 1 and it is the *only* thing in section 1. RFC
9293 §1 "Purpose and Scope" (359 words) is entirely about why the document exists rather than what
TCP is: "For several decades, RFC 793 plus a number of other documents have combined to serve as the
core specification for TCP. ... The purpose of this document is to bring together all of the IETF
Standards Track changes and other clarifications ... and to unify them into an updated version of the
specification." Section 2 is then the Introduction to the protocol. The document separates *why this
document* from *what this thing is* and puts the former first.

### 5.4 Diagrams in the orienting part

Yes, consistently, and the subject is **the mechanism or the message flow**, not the architecture.
RFC 8446 Figure 1 is a handshake message flow; RFC 6749 Figure 1 is a role-interaction flow; RFC
9293 Figure 1 is the TCP header bit layout (5.7% in) and Figure 5 is the connection state machine
(15% in). All are ASCII art, all are in-line, all are numbered and captioned, and each is followed
immediately by a prose walk of its parts. I found no failure-mode diagram in any of the four.

### 5.5 What it says about its reader

Named, and narrowly. RFC 7322 defines the Abstract's reader as "a technically knowledgeable reader".
RFC 9293 §1 closes with: "This document is intended to be useful both in checking existing TCP
implementations for conformance purposes, as well as in writing new implementations." RFC 8446 §1
states relationships instead ("This document supersedes and obsoletes previous versions of TLS,
including version 1.2"), which locates the reader by what they already know.

### 5.6 Group authorship

This is the corpus with an explicit, enforced mechanism, and RFC 9293 is a merged document by
construction - which makes it the nearest analogue to a spec assembled from independent drafts.

- **The "Ed." designation.** RFC 6749 is by "D. Hardt, Ed."; RFC 9293 is by "W. Eddy, Ed." The named
  person is the editor of a working group's output, not its author.
- **A hard cap that forces the role to exist.** RFC 7322 §4.1.1: "The total number of authors or
  editors on the first page is generally limited to five individuals ... If there is a request for
  more than five authors, the stream-approving body needs to consider if **one or two editors should
  have primary responsibility for this document, with the other individuals listed in the
  Contributors or Acknowledgements section**."
- **Accountability attaches to the named few**: "These are the individuals that must sign off on the
  document during the AUTH48 process and respond to inquiries, such as errata."
- **The many are recorded elsewhere, with attribution of parts.** RFC 6749 Appendix C names who
  drafted which section: "The Security Considerations section was drafted by Torsten Lodderstedt,
  Mark McGloin, Phil Hunt, Anthony Nadalin, and John Bradley. The section on use of the
  'application/x-www-form-urlencoded' media type was drafted by Julian Reschke. The ABNF section was
  drafted by Michael B. Jones," followed by a list of dozens of contributors.
- **The merge is declared in the text.** RFC 9293 §1 states what was merged, what was deliberately
  left out ("Some companion documents are referenced for important algorithms ... This is a conscious
  choice"), and what was deliberately not rewritten: "This document does not attempt to alter or
  update this informative text and is focused only on updating the normative protocol specification."
  It then points at a changes appendix: "A list of changes from RFC 793 is contained in Section 5."

---

## 6. Cross-cutting comparison

**Q1. What is first, and what job does it do?**

| source | first thing | job it does |
| --- | --- | --- |
| Oxide RFD | metadata block (`state`, `authors`, `labels`), then an unnumbered prose preamble | tells you **how much to trust the document** (six states), then what it is about and what to read first |
| Rust RFC | 4 metadata lines, then `Summary` (one paragraph) | one-paragraph statement of the feature; `Motivation` then states the user's problem |
| ADR (Nygard) | `Context` | loads the reader with the forces in tension, value-neutrally, so the Decision reads as a response |
| Google (Ubl) | `Context and scope` | rough landscape + what is being built, objective facts only, succinct |
| Go design doc | `Status`, `Abstract`, `How to read this proposal` | document state, then a map of the document itself |
| IETF RFC | `Abstract` (required, no citations, detachable), then `Introduction` (required) | a standalone overview that survives being ripped out of the document; then motivation and applicability |

**Q2. How long is the orienting part, against the whole?** (real documents, not templates)

| source | orienting part | measured size | share of whole |
| --- | --- | --- | --- |
| Oxide RFD | preamble prose | 13-215 words (median ~65) | **0.2-3.0%** |
| Oxide RFD 397 | preamble + Goals + Problem summary | 349 words | 6.8% |
| Rust RFC (n=638) | Summary | median 7 lines / 39 words | median **3.0%** |
| Rust RFC (n=638) | Summary + Motivation | median 36 lines | median **21.6%** |
| Rust RFC (n=245 with Guide) | Summary + Motivation + Guide | median 98 lines of 285 | median **34.8%** |
| ADR, Nygard's own | Context | 298 words of 784 | **38%** |
| ADR, arachne (n=17) | Context | median 251 words of 744 | median **37%** |
| ADR, MADR log (n=19) | Context and Problem Statement | median 20 words of 172 | median **12%** |
| Go type-params (24,207 w) | Status+Abstract+How-to-read+Overview+Background | 113 lines / 736 words | **3.0%** |
| IETF (4 RFCs) | Abstract | 58-157 words | **0.15-1.23%** |
| IETF (4 RFCs) | Abstract + first body section | 417-2,734 words | **1.2-14.2%** |

Whole-document budgets that a primary source states outright: Nygard, "one or two pages"; Ubl,
"10-20ish pages" for a larger project and "1-3 page mini design doc". No source in this corpus
states a target reading time for the orienting part.

**Q3. How is "why does this exist" handled?**

| source | mechanism |
| --- | --- |
| Oxide RFD | mixed. Sometimes a named section (`Determinations`, `Goals of this RFD`, `Customer and Oxide Benefits and Goals`); often narrative in the preamble. RFD 1 requires reasoning be recorded but fixes no slot |
| Rust RFC | **named required section** (`Motivation`), second, explicitly user-problem-shaped, "can be lengthy" |
| ADR | **it is the first section** (`Context`) - the whole point of the form |
| Google (Ubl) | split across `Context and scope` (facts) and `Goals and non-goals` (requirements); no "why" heading |
| IETF | **named required section** (`Introduction`), which "explains the motivation for the RFC". RFC 9293 goes further and gives *why this document exists* its own section 1, separate from the introduction to the subject |

**Q4. Diagrams in the orienting part, and of what?**

| source | present? | subject |
| --- | --- | --- |
| Oxide RFD | rare. 1 image across 9 public RFDs; ASCII blocks in the orienting part in 2 of 9 | RFD 63: **the system**, in several named views. RFD 397: **the failure mode**, as running code |
| Rust RFC | almost never. 5 of 642 files embed an image (0.8%) | all five are **screenshots of user-visible output** (compiler errors, rustdoc badges). None diagram the system. The real visual device is before/after code |
| ADR | none in either corpus | n/a. Nygard's form has no diagram slot and argues for prose paragraphs |
| Google (Ubl) | recommended, but under *The actual design*, not under *Context and scope* | **the system** in its environment ("system-context-diagram") |
| IETF | yes, reliably, within the first tenth | **the mechanism**: message flow (8446 Fig 1 at 7.1%), role interaction (6749 Fig 1 at 8.6%), header layout (9293 Fig 1 at 5.7%), state machine (9293 Fig 5 at 15%). No failure-mode diagrams found |

**Q5. What does it say about its reader?**

| source | named or unstated |
| --- | --- |
| Oxide RFD | **unstated**. Audience is expressed as *access* ("can be accessed by the following groups: [public]"), and implicitly as prerequisites (RFD 63's reading list) |
| Rust RFC | **named**: "another Rust programmer"; "compiler contributors" for internals RFCs; and per the template-change commit, "people who are Rust users but not compiler or language design experts" |
| ADR | **named**: "a conversation with a future developer" (Nygard). MADR names readers by role: `decision-makers`, `consulted`, `informed` |
| Google | **prescribed but not slotted**: SWE-at-Google says "Always try to identify a primary audience and write to that audience", distinguishes seekers from stumblers, and endorses stating it in the doc ("This document is for new engineers on the Secret Wizard project") and a TL;DR bail-out line. Ubl's anatomy has no audience slot |
| Go design doc | **named per section**: "This section is intended for people who are already familiar with how generics would work in a language like Go" |
| IETF | **named**: "a technically knowledgeable reader" (7322); "useful both in checking existing TCP implementations for conformance ... as well as in writing new implementations" (9293 §1) |

**Q6. Group-written? How is the absent single voice handled?**

| source | group-written? | mechanism |
| --- | --- | --- |
| Oxide RFD | sometimes (3 of 9 sampled had 2-3 authors) | authors are listed and are "therefore owners". **No voice guidance found in RFD 1 or RFD 5.** Prose defaults to corporate "we" |
| Rust RFC | no - single-authored by convention | **the template has no author field at all** (0 of 642 files carry one). Dissent is kept out of the document: the FCP "summary comment" laying out disagreement lives on the pull request. In-document residue is `Drawbacks`, `Rationale and alternatives`, `Unresolved questions` |
| ADR | yes, implicitly - it is a team record | **no author field**; voice is prescribed instead: "stated in full sentences, with active voice. 'We will ...'". MADR adds RACI front matter: `decision-makers` / `consulted` / `informed` |
| Google | yes ("the primary author or authors") | **no mechanism described** in either source |
| IETF | **yes, by design** - this is the corpus built for it | (a) the "Ed." designation - RFC 6749 "D. Hardt, Ed.", RFC 9293 "W. Eddy, Ed."; (b) a five-name cap on the front page that forces an editor role above it; (c) `Contributors` / `Acknowledgements` carrying the rest, with **per-section attribution** ("The Security Considerations section was drafted by ..."); (d) AUTH48 sign-off pinning accountability to the named few; (e) for a merged document, RFC 9293 §1 declares what was merged, what was consciously excluded, and where the change list lives |

---

## 7. What I could not establish

- **The Chromium / Google design doc template.** Linked publicly from chromium.org but served as a
  Google Doc requiring sign-in. I fetched it and got only the page chrome. No official Google design
  doc template is published that I could find. Everything in section 4.1 is one engineer's public
  account.
- **The Oxide RFD template.** RFD 1 references `prototypes/prototype.adoc` in
  `oxidecomputer/rfd`, which is a private repository. Only the rendered site is public, and the
  `.adoc` source is not served (404). Oxide section headings above are therefore observed practice,
  not a declared template.
- **Any stated target reading time.** No source in this corpus says "a reader should orient in N
  minutes". The closest are Nygard's "one or two pages" and Ubl's "short enough to actually be read
  by busy people".
- **Whether short ADRs cost their readers anything measurably.** I found evidence of the form being
  extended and of real ADRs bursting the budget (section 3.7), but no primary source that studies or
  claims a cost.
- **Oxide's rule for reconciling voice in a multi-author RFD.** I searched RFD 1 and RFD 5 and found
  nothing. Absence of a rule in those two documents is not proof that no rule exists internally.

---

## 8. Opinion (not fact) - clearly marked, and not a recommendation

Ticket #18 decides; the following are my inferences from the above, offered so they can be argued
with. Each is separable from the facts in sections 1-6.

1. The corpus splits cleanly by **document size**, not by community. Below ~1,500 words the
   orienting part is 30-40% of the document (ADRs, small Rust RFCs). Above ~10,000 words it collapses
   to 1-3% (Oxide RFDs, IETF RFCs, the Go generics proposal) and the job is taken over by a
   *detachable* short piece plus a *navigational* piece. A 559-line spec sits between those regimes.
2. The two devices that appear in the long documents and nowhere in the short ones are (a) a
   statement of the document's own state and scope before any content, and (b) a map of the document
   ("How to read this proposal", the RFC's fixed section order). Both are cheap in lines.
3. The only corpus that solved the merged-document problem explicitly is IETF, and its answer is
   structural rather than stylistic: name one accountable editor, push everyone else into an
   attributed contributors list, and have the document state in prose what was merged and what was
   consciously left out.
4. Diagrams are not the differentiator. The IETF pattern - one captioned ASCII figure of the
   *mechanism*, early, immediately walked in prose - is the only diagram convention in this corpus
   that appears consistently in orienting positions.
5. At a rough 200-250 words per minute, "orient in five minutes" is on the order of 1,000-1,250
   words. That is the arithmetic, not a finding; no source states it.
