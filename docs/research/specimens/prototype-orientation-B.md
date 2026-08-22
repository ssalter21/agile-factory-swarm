# Orientation, variant B — context first, no figures

*Prototype for [#16](https://github.com/ssalter21/agile-factory-swarm/issues/16). The deliberate
opposite of [variant A](prototype-orientation-A.md): no figure, no document map, no section
headings. Shape borrowed from Nygard's ADR `Context` — load the reader with the forces in tension in
plain prose, so the requirements read as a response to something. Tests whether the failure-state
diagram the map assumes is necessary is actually doing work, or whether prose carries it.*

---

Each of the swarm's twelve roles is one file in `.claude/agents/`, hand-edited, and that file is
both what a human changes and what the harness loads. There has only ever been one harness, so one
file has been enough. The brief behind this spec asks for a second — GitHub Copilot — and the moment
there are two, one file per role stops working: either the same prompt is edited in two places
forever, or the two quietly disagree.

The change is to demote those twelve files. The authority moves to `swarm/roles/`, a pair of files
per role — a five-field declaration and a prompt — and a compiler writes the harness files from
them: twelve for Claude carrying all five fields, twelve for GitHub carrying three, because `model`
and `effort` have nowhere to go there. Nothing in this repo dispatches to the GitHub half. It exists
to show the format is neutral, and the spec says outright that nobody may claim the swarm runs there.

The human who commissioned this set one acceptance criterion and it governs everything below:
recompiling must leave the twelve tracked Claude files **byte-identical**. That is why the spec
specifies emitted bytes rather than delegating to a YAML library, why it pins a line ending in
`.gitattributes`, why the compiler must prove itself in check mode before it is allowed to write,
and why there is no "generated — do not edit" banner in the output — a banner would change the
bytes.

Read the requirements knowing what the change costs, because it is not a simplification. Twelve
files become forty-eight and twelve of those have no reader. Where today one file per role can be
wrong only by being wrong, after this a source and a generated copy can disagree — silently, since
nothing in a generated file admits to being generated, and check mode is a command nobody is obliged
to run. The spec cut the pre-commit hook and the CI job that would have forced it, on the grounds
that automation should wait until staleness has bitten once. It has not bitten yet.
