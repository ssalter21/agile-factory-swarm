# Specimens

Real artifacts the swarm produced, kept as evidence for efforts that study the swarm's own output.
Map [#15](https://github.com/ssalter21/agile-factory-swarm/issues/15) needs them: it is trying to
make the spec a document a cold reader can review, and it cannot do that without specimens of what
the spec actually looks like today.

**These are historical records, not documentation.** Each one is what the swarm wrote on a date,
under the law as it stood then. None of them describes current code, none is maintained, and none
may be cited as how anything works now — which is why they do not breach the rule that nothing
durable may represent the code. They are the same kind of thing as a merged pull request body: a
record of what was decided, frozen.

The run directory they came from is gitignored and overwritten by the next run (§11), so a specimen
that is not copied here is destroyed. The `swarm doctor` spec — the one whose failure started map
#15 — was lost exactly that way.

| specimen | what it is |
|---|---|
| `spec-neutral-role-format.md` | 559 lines. The only spec the swarm has taken through approval to a merged change ([PR #13](https://github.com/ssalter21/agile-factory-swarm/pull/13)). Its three seam questions were delegated, not adjudicated, and its approval was delegated too. |
| `acceptance-neutral-role-format.feature` | The Gherkin from the same run. Never executed as Gherkin — no runner exists — so it graduated into `tests/test_rolecompile_acceptance.py` and this file is what died with the run directory. |
| `answers-neutral-role-format.md` | The human's side of that seam, written by the agent on the human's explicit instruction to take the lowest-effort branch each time. Recorded as such in the file. |

Add a specimen when a run produces something an open effort needs to study. Do not add one
speculatively: an unused specimen is prose accumulating in a repo.
