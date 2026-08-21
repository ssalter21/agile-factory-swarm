"""The approved acceptance criteria for `neutral-role-format`, as something that runs.

The criteria were written in Gherkin and this repository has no Gherkin runner, so they graduate
into the test tree as ordinary tests and the feature file dies with the run directory
(constitution section 11). Every test below is named for the scenario it carries, and its
docstring quotes that scenario's title verbatim, so the two can still be read against each other.

These are QA's checks, not the coder's, and they differ from `test_rolecompile_cli.py` on purpose:
they drive the **command** in a subprocess, the way a developer does, rather than calling
`main()`. Nothing here calls into the package. Constitution section 9: exercise the thing through
its user interface only.

Two scenarios are not here.

* "The swarm still runs on the compiled agent files" needs a fresh invocation of the harness
  against compiled agent files that this invocation is forbidden to write. It is deferred, and
  QA's report says so.
* "Check mode is clean on a fresh checkout, not only on the machine that built it" is a property
  of a `git clone`, not of a process. What is checkable without a clone is here: the
  `.gitattributes` pin that makes a fresh checkout produce the bytes the compiler emits, and a
  tree whose agent files carry that pinned ending comparing clean. QA ran the clone itself once,
  by hand, and reported it.

Only one test touches this repository, and it runs check mode, which writes nothing anywhere.
Every other test builds a role tree in `tmp_path`.
"""

import hashlib
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
COMMAND = ROOT / "swarm" / "tools" / "python" / "rolecompile"

CLAUDE_AGENTS = ROOT / ".claude" / "agents"

SUCCESS = 0
EOL = b"\r\n"

ROLES = (
    "agile-agent",
    "architect",
    "cleaner",
    "coder",
    "devils-advocate",
    "domain-modeller",
    "hardener",
    "qa",
    "researcher",
    "spec-writer",
    "unblocker",
    "user-voice",
)

DECLARED = "name: qa\ndescription: Verifies.\ntools: Read, Grep\nmodel: opus\neffort: high\n"
PROMPT = b"You are QA.\n"


class Run:
    """What the developer sees: the two streams, the exit code, and the report as lines."""

    def __init__(self, completed):
        self.code = completed.returncode
        self.out = completed.stdout
        self.err = completed.stderr

    @property
    def lines(self):
        return self.out.splitlines()


def compile_command(root, *extra):
    """Run the command the way `AGENTS.md` tells a developer to run it."""
    return Run(
        subprocess.run(
            [sys.executable, str(COMMAND), "--root", str(root), *extra],
            capture_output=True,
            text=True,
            timeout=120,
        )
    )


@pytest.fixture
def project(tmp_path):
    """A role tree with one role in it, and nothing compiled yet."""
    roles = tmp_path / "swarm" / "roles"
    roles.mkdir(parents=True)
    (roles / "qa.yaml").write_bytes(DECLARED.encode("utf-8"))
    (roles / "qa.md").write_bytes(PROMPT)
    return tmp_path


def declare(project, name, text, prompt=PROMPT):
    (project / "swarm" / "roles" / (name + ".yaml")).write_bytes(text.encode("utf-8"))
    (project / "swarm" / "roles" / (name + ".md")).write_bytes(prompt)


def claude(project, name="qa.md"):
    return project / ".claude" / "agents" / name


def github(project, name="qa.agent.md"):
    return project / ".github" / "agents" / name


def fingerprint(directory):
    """Every file in a directory, by name and content, so a rewrite cannot hide."""
    if not directory.exists():
        return None
    return {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(directory.iterdir())
    }


def front_matter(path):
    """The lines between the two fences, in the order the file carries them."""
    lines = path.read_bytes().decode("utf-8").split("\r\n")
    assert lines[0] == "---"
    return lines[1 : lines.index("---", 1)]


# --- the criteria this invocation discharges (@invocation-one) ------------------------------


def test_check_mode_is_clean_before_the_compiler_is_allowed_to_write_anything():
    """Scenario: Check mode is clean before the compiler is allowed to write anything.

    Run against this repository, whose twelve agent files were hand-written before the compiler
    existed. This is the whole test of the change, and it is the human's own criterion.

    The scenario also says `.github/agents/` has not been created. That is true of the invocation
    that built the compiler and false of every invocation after it, so it is a fact QA checked by
    hand and reported, not a property to hold this repository to for ever. What is asserted here
    is the durable half: every destination that exists compares clean, and check mode moved no
    byte.
    """
    before = fingerprint(CLAUDE_AGENTS)

    run = compile_command(ROOT, "--check")

    assert run.code == SUCCESS, run.err
    assert [line for line in run.lines if line.startswith(".claude/agents/")] == [
        ".claude/agents/%s.md unchanged" % name for name in ROLES
    ]
    assert all(line.endswith("unchanged") for line in run.lines)
    assert fingerprint(CLAUDE_AGENTS) == before


def test_the_compiled_claude_tree_is_exactly_the_twelve_roles():
    """Scenario: The building run writes no agent file.

    The half of it a process can check for ever: this repository's `.claude/agents/` holds one
    file per role and nothing else, each carrying the pinned line ending. Whether the working
    tree holds only the compiler, the `.gitattributes` line and the twenty-four role files is a
    question for `git status`, and QA answered it by running one.
    """
    assert sorted(path.name for path in CLAUDE_AGENTS.iterdir()) == [
        "%s.md" % name for name in ROLES
    ]
    for name in ROLES:
        assert EOL in (CLAUDE_AGENTS / ("%s.md" % name)).read_bytes()


def test_the_line_ending_the_compiler_emits_is_pinned_for_both_agent_directories():
    """Scenario: Check mode is clean on a fresh checkout, not only on the machine that built it.

    A fresh checkout matches only because git is told what these files' line ending is. Without
    the pin, a clone taken with a different `core.autocrlf` reports twelve files out of date and
    looks like a compiler fault.
    """
    pins = (ROOT / ".gitattributes").read_text(encoding="utf-8")

    assert ".claude/agents/*.md" in pins
    assert ".github/agents/*.agent.md" in pins
    for line in pins.splitlines():
        if line.startswith((".claude/agents/", ".github/agents/")):
            assert line.endswith("text eol=crlf")


def test_a_tree_carrying_the_pinned_line_ending_compares_clean(project):
    """Scenario: Check mode is clean on a fresh checkout, not only on the machine that built it.

    The other half: agent files carrying the pinned ending are what the compiler would write.
    """
    assert compile_command(project).code == SUCCESS

    assert claude(project).read_bytes().endswith(EOL)
    assert compile_command(project, "--check").code == SUCCESS


def test_a_line_ending_only_difference_is_named_as_one(project):
    """Scenario: A line-ending-only difference is named as one."""
    compile_command(project)
    for directory in (claude(project).parent, github(project).parent):
        for path in directory.iterdir():
            path.write_bytes(path.read_bytes().replace(EOL, b"\n"))

    run = compile_command(project, "--check")

    assert run.code != SUCCESS
    assert run.lines
    for line in run.lines:
        assert "line endings" in line
        assert line.endswith("nothing else")


def test_the_compiler_is_reachable_by_the_gate_commands_the_repo_declares():
    """Scenario: The compiler is reachable by the gate commands the repo declares.

    `tests` and `coverage` are `pytest` and `coverage` over this tree. This file is in that tree
    and it drives the compiler, so running either command reaches it -- which is what the
    scenario asks. Whether the declared executables resolve in a given checkout is the scenario's
    other clause, and that clause asks for a report rather than a passing test: where they do not
    resolve, QA names them as missing gate steps.
    """
    declared = (ROOT / ".swarm" / "gate.yaml").read_text(encoding="utf-8")

    assert "pytest" in declared and "coverage" in declared
    assert COMMAND.is_dir()
    assert compile_command(ROOT, "--check").code == SUCCESS


def test_two_declarations_with_the_same_name_fail_the_compile(project):
    """Scenario: Two declarations with the same name fail the compile."""
    declare(project, "probe", DECLARED)
    before = fingerprint(claude(project).parent)

    run = compile_command(project)

    assert run.code != SUCCESS
    assert "swarm/roles/probe.yaml" in run.err
    assert "swarm/roles/qa.yaml" in run.err
    assert "'name'" in run.err
    assert "Traceback" not in run.err
    assert fingerprint(claude(project).parent) == before
    assert not github(project).parent.exists()


def test_a_declared_name_that_does_not_match_its_filename_fails_the_compile(project):
    """Scenario: A declared name that does not match its filename fails the compile."""
    declare(project, "probe", DECLARED.replace("name: qa", "name: prober"))

    run = compile_command(project)

    assert run.code != SUCCESS
    assert "swarm/roles/probe.yaml" in run.err
    assert "'name'" in run.err
    assert "Traceback" not in run.err
    assert not claude(project).parent.exists()
    assert not github(project).parent.exists()


def test_an_omitted_tools_field_fails_the_compile_and_says_why_it_matters(project):
    """Scenario: An omitted tools field fails the compile, and the message says why it matters."""
    without = "".join(
        line for line in DECLARED.splitlines(True) if not line.startswith("tools:")
    )
    (project / "swarm" / "roles" / "qa.yaml").write_bytes(without.encode("utf-8"))

    run = compile_command(project)

    assert run.code != SUCCESS
    assert "swarm/roles/qa.yaml" in run.err
    assert "'tools'" in run.err
    assert "inherits every tool" in run.err
    assert "Claude Code" in run.err
    assert "Traceback" not in run.err
    assert not claude(project).parent.exists()


# --- the criteria a later invocation discharges (@invocation-two) ----------------------------
#
# R12 forbids *this* invocation from writing this repository's compiled trees. It says nothing
# about a role tree in tmp_path, so the behaviour those criteria describe is checked here and the
# criteria themselves stay deferred until the invocation that is allowed to write.


def test_the_first_write_produces_both_trees_and_names_every_file(project):
    """Scenario: The first write leaves the twelve tracked Claude agent files byte-identical.

    Byte-identity against this repository's own twelve is `test_rolecompile_fidelity.py`, which
    reads and writes nothing. What is left is the reporting promise: every file that appeared was
    named, and nothing appeared that was not.
    """
    run = compile_command(project)

    assert run.code == SUCCESS
    assert run.lines == [
        ".claude/agents/qa.md written",
        ".github/agents/qa.agent.md written",
    ]
    named = {line.split(" ")[0].split("/")[-1] for line in run.lines}
    assert named == {"qa.md", "qa.agent.md"}


def test_running_the_compile_twice_writes_nothing_the_second_time(project):
    """Scenario: Running the compile twice writes nothing the second time."""
    compile_command(project)
    stamps = {
        path: path.stat().st_mtime_ns
        for directory in (claude(project).parent, github(project).parent)
        for path in directory.iterdir()
    }

    run = compile_command(project)

    assert run.code == SUCCESS
    assert run.lines == [
        ".claude/agents/qa.md unchanged",
        ".github/agents/qa.agent.md unchanged",
    ]
    assert all(path.stat().st_mtime_ns == stamp for path, stamp in stamps.items())


def test_a_prompt_edit_reaches_both_harnesses_from_one_place(project):
    """Scenario: A prompt edit reaches both harnesses from one place."""
    compile_command(project)
    (project / "swarm" / "roles" / "qa.md").write_bytes(
        PROMPT + b"Say BANANA in your handoff.\n"
    )

    run = compile_command(project)

    assert run.lines == [
        ".claude/agents/qa.md written",
        ".github/agents/qa.agent.md written",
    ]
    assert b"Say BANANA in your handoff." in claude(project).read_bytes()
    assert b"Say BANANA in your handoff." in github(project).read_bytes()


def test_check_mode_names_a_stale_agent_file_and_writes_nothing(project):
    """Scenario: Check mode names a stale agent file and writes nothing."""
    compile_command(project)
    (project / "swarm" / "roles" / "qa.md").write_bytes(PROMPT + b"Edited since.\n")
    before = fingerprint(claude(project).parent), fingerprint(github(project).parent)

    run = compile_command(project, "--check")

    assert run.code != SUCCESS
    assert ".claude/agents/qa.md out of date" in run.out
    assert ".github/agents/qa.agent.md out of date" in run.out
    assert (fingerprint(claude(project).parent), fingerprint(github(project).parent)) == before

    assert compile_command(project).code == SUCCESS
    assert compile_command(project, "--check").code == SUCCESS


def test_a_hand_edit_to_a_compiled_file_is_caught_and_there_is_no_banner(project):
    """Scenario: A hand edit to a compiled file is caught, and there is no banner warning."""
    compile_command(project)
    claude(project).write_bytes(claude(project).read_bytes() + b"Edited by hand." + EOL)

    run = compile_command(project, "--check")

    assert run.code != SUCCESS
    assert ".claude/agents/qa.md out of date" in run.out
    body = claude(project).read_bytes().decode("utf-8").lower()
    assert "generated" not in body
    assert "do not edit" not in body


def test_the_researcher_description_survives_the_round_trip_on_one_line(project):
    """Scenario: The researcher description survives the round trip on one line.

    The real declaration, copied into tmp_path so nothing in this repository is written.
    """
    source = ROOT / "swarm" / "roles" / "researcher.yaml"
    declaration = source.read_bytes()
    (project / "swarm" / "roles" / "researcher.yaml").write_bytes(declaration)
    (project / "swarm" / "roles" / "researcher.md").write_bytes(
        (ROOT / "swarm" / "roles" / "researcher.md").read_bytes()
    )

    assert compile_command(project).code == SUCCESS

    compiled = claude(project, "researcher.md")
    declared = [
        line
        for line in declaration.decode("utf-8").splitlines()
        if line.startswith("description:")
    ]
    emitted = [line for line in front_matter(compiled) if line.startswith("description:")]
    assert emitted == declared
    assert "—" in emitted[0] and ";" in emitted[0]
    assert [line.split(":")[0] for line in front_matter(compiled)] == [
        "name",
        "description",
        "tools",
        "model",
        "effort",
    ]
    raw = compiled.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf")
    assert raw.decode("utf-8")
    assert raw.endswith(EOL) and not raw.endswith(EOL + EOL)


def test_adding_a_role_produces_both_agent_files_under_the_declared_name(project):
    """Scenario: Adding a role produces both agent files under the declared name."""
    compile_command(project)
    declare(project, "probe", DECLARED.replace("name: qa", "name: probe"))

    run = compile_command(project)

    assert ".claude/agents/probe.md written" in run.out
    assert ".github/agents/probe.agent.md written" in run.out
    assert "name: probe" in claude(project, "probe.md").read_text(encoding="utf-8")
    assert "name: probe" in github(project, "probe.agent.md").read_text(encoding="utf-8")


def test_the_github_agent_file_carries_four_things_and_nothing_more(project):
    """Scenario: The GitHub agent file carries four fields and nothing more."""
    compile_command(project)

    fields = front_matter(github(project))

    assert [line.split(":")[0] for line in fields] == ["name", "description", "tools"]
    assert "tools: Read, Grep" in fields
    body = github(project).read_bytes().decode("utf-8").split("---" + EOL.decode())[2]
    assert body == EOL.decode() + PROMPT.decode().replace("\n", EOL.decode())


def test_everything_restores(project):
    """Scenario: Everything restores."""
    compile_command(project)
    settled = fingerprint(claude(project).parent), fingerprint(github(project).parent)

    declare(project, "probe", DECLARED.replace("name: qa", "name: probe"))
    compile_command(project)
    for suffix in (".yaml", ".md"):
        (project / "swarm" / "roles" / ("probe" + suffix)).unlink()
    claude(project, "probe.md").unlink()
    github(project, "probe.agent.md").unlink()

    assert compile_command(project).code == SUCCESS
    assert compile_command(project, "--check").code == SUCCESS
    assert (fingerprint(claude(project).parent), fingerprint(github(project).parent)) == settled
