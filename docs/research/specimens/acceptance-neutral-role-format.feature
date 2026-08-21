# Acceptance criteria for slug: neutral-role-format
#
# Drawn from the User Voice's consolidated QA procedure. Terminal only, plus reading files.
# Two invocations, because the run that builds the compiler must not write the compiled trees
# (spec.md R12). Scenarios tagged @invocation-one are the ones the building run can discharge;
# @invocation-two waits for a later invocation.
#
# Names used below are real: the twelve roles are agile-agent, architect, cleaner, coder,
# devils-advocate, domain-modeller, hardener, qa, researcher, spec-writer, unblocker, user-voice.
# "the compile command" is the single command spec.md R8 requires; "--check" is its check mode.

Feature: One role definition, compiled to both harnesses

  Background:
    Given a clean checkout of the branch with "git status" reporting no changes
    And ".claude/agents/" holds twelve agent files
    And "swarm/roles/" holds twelve declarations and twelve prompts

  @invocation-one
  Scenario: Check mode is clean before the compiler is allowed to write anything
    Given the compiler exists and has never been run in write mode
    When I run the compile command with "--check"
    Then it exits 0
    And it prints one line per agent file, path first, each saying "unchanged"
    And nothing under ".claude/agents/" or ".github/agents/" has been written

  @invocation-one
  Scenario: Check mode is clean on a fresh checkout, not only on the machine that built it
    Given a fresh checkout of the branch, taken after the ".gitattributes" line is in place
    When I run the compile command with "--check"
    Then it exits 0 against the twelve tracked files in ".claude/agents/"

  @invocation-one
  Scenario: The building run writes no agent file
    When I run "git status" after the compile command has run in check mode only
    Then the twelve files under ".claude/agents/" are unmodified
    And ".github/agents/" does not exist
    And the only changes are the compiler, the ".gitattributes" line and the twenty-four files under "swarm/roles/"

  @invocation-one
  Scenario: A line-ending-only difference is named as one
    Given a checkout whose working-tree line ending differs from the ending the compiler emits
    When I run the compile command with "--check"
    Then it exits non-zero
    And each of the twelve lines says the difference is line endings alone
    And no line reports a content difference

  @invocation-one
  Scenario: The compiler is reachable by the gate commands the repo declares
    When I run the command ".swarm/gate.yaml" declares for "tests" and then the one it declares for "coverage"
    Then those commands exercise the compiler
    And where either command cannot resolve in this checkout, the handoff and the final report name it as a missing gate step

  @invocation-one
  Scenario: Two declarations with the same name fail the compile
    Given "swarm/roles/probe.yaml" declaring 'name: researcher'
    When I run the compile command
    Then it exits non-zero
    And the message names both source paths and the field "name"
    And "git status" shows no agent file written or truncated

  @invocation-one
  Scenario: A declared name that does not match its filename fails the compile
    Given "swarm/roles/probe.yaml" declaring 'name: prober'
    When I run the compile command
    Then it exits non-zero
    And the message names "swarm/roles/probe.yaml" and the field "name"
    And "git status" shows no agent file written or truncated

  @invocation-one
  Scenario: An omitted tools field fails the compile, and the message says why it matters
    Given "swarm/roles/researcher.yaml" with its "tools" line deleted
    When I run the compile command
    Then it exits non-zero
    And the message names "swarm/roles/researcher.yaml" and the field "tools"
    And the message says that an omitted allowlist on Claude Code inherits every tool
    And "git status" shows no agent file written or truncated

  @invocation-two
  Scenario: The first write leaves the twelve tracked Claude agent files byte-identical
    When I run the compile command
    Then it exits 0
    And it prints one line per agent file, path first, saying "written" or "unchanged"
    And "git diff .claude/agents" reports no change to any of the twelve files
    And ".github/agents/" holds twelve files, one per role, named "<role>.agent.md"
    And nothing changed that the report did not name

  @invocation-two
  Scenario: Running the compile twice writes nothing the second time
    Given the compile command has just run and exited 0
    When I run the compile command again with nothing edited in between
    Then every line of the report says "unchanged"
    And no file under ".claude/agents/" or ".github/agents/" has a new modification time
    And "git status" shows nothing new

  @invocation-two
  Scenario: A prompt edit reaches both harnesses from one place
    Given the line "Say BANANA in your handoff." added to the end of "swarm/roles/qa.md"
    When I run the compile command
    Then the report names ".claude/agents/qa.md" and ".github/agents/qa.agent.md" as written
    And ".claude/agents/qa.md" contains "Say BANANA in your handoff."
    And ".github/agents/qa.agent.md" contains "Say BANANA in your handoff."

  @invocation-two
  Scenario: Check mode names a stale agent file and writes nothing
    Given the line "Say BANANA in your handoff." has been removed from "swarm/roles/qa.md" without recompiling
    When I run the compile command with "--check"
    Then it exits non-zero
    And ".claude/agents/qa.md" and ".github/agents/qa.agent.md" are named as stale
    And neither file has changed on disk
    And when I then run the compile command and run check mode again, it exits 0

  @invocation-two
  Scenario: A hand edit to a compiled file is caught, and there is no banner warning against it
    Given the line "Edited by hand." added to ".claude/agents/architect.md"
    When I run the compile command with "--check"
    Then it exits non-zero
    And ".claude/agents/architect.md" is named
    And ".claude/agents/architect.md" contains no notice that it is generated

  @invocation-two
  Scenario: The researcher description survives the round trip on one line
    When I compile the role "researcher"
    Then the "description" line in ".claude/agents/researcher.md" is byte-identical to the one in "swarm/roles/researcher.yaml"
    And its em dash, its semicolon and its commas are unchanged
    And it is one unwrapped line, not folded
    And the front-matter fields appear in the order name, description, tools, model, effort
    And the file is UTF-8 with no byte-order mark and ends in exactly one newline

  @invocation-two
  Scenario: Adding a role produces both agent files under the declared name
    Given "swarm/roles/probe.yaml" and "swarm/roles/probe.md" copied from "researcher" with a changed description
    When I run the compile command
    Then ".claude/agents/probe.md" and ".github/agents/probe.agent.md" are created and named in the report
    And the "name" field inside each of them is "probe"

  @invocation-two
  Scenario: The GitHub agent file carries four fields and nothing more
    When I open ".github/agents/architect.agent.md"
    Then it carries "name", "description" and "tools", and the whole prompt as its body
    And it carries no "model" field and no "effort" field
    And its "tools" value is the comma-separated string form
    And it carries no key beyond those three plus the body

  @invocation-two
  Scenario: The swarm still runs on the compiled agent files
    Given the compiled trees are up to date and check mode exits 0
    When I start a fresh invocation and run the spec swarm on the one-line brief "Add a hello command."
    Then it completes
    And every voice switched on in ".swarm/spec.yaml" has produced a draft under ".swarm/runs/current/.work/"

  @invocation-two
  Scenario: Everything restores
    Given the "probe" files are deleted and every edit above is reverted
    When I run the compile command and then run it with "--check"
    Then both exit 0
    And "git status" reports no changes

  # Fails acceptance if: check mode ever writes to ".claude/agents/" or ".github/agents/"; any run
  # writes a partial set of agent files; an error path produces a stack trace instead of a message
  # naming the file; the report claims a file was written that "git diff" does not show, or the
  # reverse; the second compile writes anything; or the spec-swarm run loses a voice.
