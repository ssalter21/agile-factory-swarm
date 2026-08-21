"""The command line, end to end, with --root pointed at a role tree in tmp_path.

The exit code is what a developer and a script both read, so every one of them is pinned here.
Nothing in this file points at this repository's own agent directories.
"""

import pytest

from rolecompile.__main__ import main, parse_args

DECLARED = "name: qa\ndescription: Verifies.\ntools: Read\nmodel: opus\neffort: high\n"

SUCCESS = 0
OUT_OF_DATE = 1
PROBLEM = 2


@pytest.fixture
def project(tmp_path):
    """A one-role tree, and nothing compiled yet."""
    roles = tmp_path / "swarm" / "roles"
    roles.mkdir(parents=True)
    (roles / "qa.yaml").write_bytes(DECLARED.encode("utf-8"))
    (roles / "qa.md").write_bytes(b"You are QA.\n")
    return tmp_path


def run(project, *extra):
    return main(["--root", str(project), *extra])


def role(project, name):
    return project / "swarm" / "roles" / name


def claude(project, name="qa.md"):
    return project / ".claude" / "agents" / name


def github(project, name="qa.agent.md"):
    return project / ".github" / "agents" / name


# --- the defaults ------------------------------------------------------------------------------


def test_the_command_writes_by_default_and_runs_where_it_is_invoked():
    args = parse_args([])
    assert args.check is False
    assert args.root == "."


def test_check_is_a_flag_not_a_value():
    assert parse_args(["--check"]).check is True


# --- write mode --------------------------------------------------------------------------------


def test_write_mode_produces_both_agent_files_and_names_them(project, capsys):
    assert run(project) == SUCCESS
    printed = capsys.readouterr().out.splitlines()
    assert printed == [".claude/agents/qa.md written", ".github/agents/qa.agent.md written"]
    assert claude(project).exists() and github(project).exists()


def test_the_written_claude_file_carries_all_five_fields(project):
    run(project)
    assert claude(project).read_bytes() == (
        b"---\r\nname: qa\r\ndescription: Verifies.\r\ntools: Read\r\nmodel: opus\r\n"
        b"effort: high\r\n---\r\n\r\nYou are QA.\r\n"
    )


def test_the_written_github_file_carries_three(project):
    run(project)
    assert github(project).read_bytes() == (
        b"---\r\nname: qa\r\ndescription: Verifies.\r\ntools: Read\r\n---\r\n\r\nYou are QA.\r\n"
    )


def test_a_second_run_with_nothing_edited_writes_nothing(project, capsys):
    run(project)
    before = claude(project).stat().st_mtime_ns, github(project).stat().st_mtime_ns
    capsys.readouterr()

    assert run(project) == SUCCESS
    printed = capsys.readouterr().out.splitlines()
    assert printed == [".claude/agents/qa.md unchanged", ".github/agents/qa.agent.md unchanged"]
    assert (claude(project).stat().st_mtime_ns, github(project).stat().st_mtime_ns) == before


def test_an_edited_prompt_reaches_both_harnesses(project, capsys):
    run(project)
    role(project, "qa.md").write_bytes(b"You are QA.\nSay BANANA.\n")
    capsys.readouterr()

    assert run(project) == SUCCESS
    printed = capsys.readouterr().out.splitlines()
    assert printed == [".claude/agents/qa.md written", ".github/agents/qa.agent.md written"]
    assert b"Say BANANA." in claude(project).read_bytes()
    assert b"Say BANANA." in github(project).read_bytes()


# --- check mode --------------------------------------------------------------------------------


def test_check_mode_is_clean_once_both_trees_are_current(project, capsys):
    run(project)
    capsys.readouterr()

    assert run(project, "--check") == SUCCESS
    assert capsys.readouterr().out.splitlines() == [
        ".claude/agents/qa.md unchanged",
        ".github/agents/qa.agent.md unchanged",
    ]


def test_check_mode_ignores_a_destination_that_does_not_exist(project, capsys):
    (project / ".claude" / "agents").mkdir(parents=True)
    main(["--root", str(project)])
    (project / ".github" / "agents" / "qa.agent.md").unlink()
    (project / ".github" / "agents").rmdir()
    capsys.readouterr()

    assert run(project, "--check") == SUCCESS
    assert capsys.readouterr().out.splitlines() == [".claude/agents/qa.md unchanged"]


def test_check_mode_names_a_stale_file_and_writes_nothing(project, capsys):
    run(project)
    role(project, "qa.md").write_bytes(b"You are QA.\nSay BANANA.\n")
    was = claude(project).read_bytes()
    capsys.readouterr()

    assert run(project, "--check") == OUT_OF_DATE
    assert capsys.readouterr().out.splitlines() == [
        ".claude/agents/qa.md out of date",
        ".github/agents/qa.agent.md out of date",
    ]
    assert claude(project).read_bytes() == was


def test_check_mode_says_when_line_endings_are_the_whole_difference(project, capsys):
    run(project)
    for path in (claude(project), github(project)):
        path.write_bytes(path.read_bytes().replace(b"\r\n", b"\n"))
    capsys.readouterr()

    assert run(project, "--check") == OUT_OF_DATE
    printed = capsys.readouterr().out.splitlines()
    assert printed == [
        ".claude/agents/qa.md out of date - the line endings differ, nothing else",
        ".github/agents/qa.agent.md out of date - the line endings differ, nothing else",
    ]


def test_check_mode_does_not_create_a_missing_agent_file(project, capsys):
    run(project)
    claude(project).unlink()
    capsys.readouterr()

    assert run(project, "--check") == OUT_OF_DATE
    assert not claude(project).exists()
    assert ".claude/agents/qa.md out of date" in capsys.readouterr().out


def test_a_hand_edited_agent_file_is_caught(project, capsys):
    run(project)
    claude(project).write_bytes(claude(project).read_bytes() + b"Edited by hand.\r\n")
    capsys.readouterr()

    assert run(project, "--check") == OUT_OF_DATE
    printed = capsys.readouterr().out.splitlines()
    assert printed[0] == ".claude/agents/qa.md out of date"
    assert printed[1] == ".github/agents/qa.agent.md unchanged"


# --- the three input checks ----------------------------------------------------------------------


def probe(project, declared):
    role(project, "probe.yaml").write_bytes(declared.encode("utf-8"))
    role(project, "probe.md").write_bytes(b"You are a probe.\n")


def test_two_declarations_with_one_name_stop_the_compile(project, capsys):
    run(project)
    before = claude(project).read_bytes()
    probe(project, DECLARED)
    capsys.readouterr()

    assert run(project) == PROBLEM
    result = capsys.readouterr()
    # Filename order, so probe.yaml claims the name first and qa.yaml is the one that collides.
    assert result.err.strip() == (
        "swarm/roles/qa.yaml: the field 'name' is 'qa', "
        "which swarm/roles/probe.yaml already declares."
    )
    assert result.out == ""
    assert claude(project).read_bytes() == before
    assert not claude(project, "probe.md").exists()


def test_a_name_that_is_not_the_filename_stops_the_compile(project, capsys):
    probe(project, DECLARED.replace("name: qa", "name: prober"))

    assert run(project) == PROBLEM
    assert capsys.readouterr().err.strip() == (
        "swarm/roles/probe.yaml: the field 'name' is 'prober', but the file is named 'probe'."
    )
    assert not claude(project).exists()


def test_an_omitted_tools_field_stops_the_compile_and_says_why(project, capsys):
    role(project, "qa.yaml").write_bytes(
        DECLARED.replace("tools: Read\n", "").encode("utf-8")
    )

    assert run(project) == PROBLEM
    assert capsys.readouterr().err.strip() == (
        "swarm/roles/qa.yaml: the field 'tools' is missing. A role with no tools line "
        "inherits every tool on Claude Code."
    )
    assert not claude(project).exists()


def test_a_problem_writes_nothing_at_all_even_for_the_roles_that_are_fine(project, capsys):
    probe(project, DECLARED.replace("name: qa", "name: prober"))

    assert run(project) == PROBLEM
    assert not (project / ".claude").exists()
    assert not (project / ".github").exists()


# --- error paths -------------------------------------------------------------------------------


def test_a_missing_prompt_names_the_file_rather_than_raising(project, capsys):
    role(project, "qa.md").unlink()

    assert run(project) == PROBLEM
    printed = capsys.readouterr().err
    assert printed.startswith(str(role(project, "qa.md")))
    assert "Traceback" not in printed


def test_no_role_directory_names_it_rather_than_raising(tmp_path, capsys):
    assert run(tmp_path) == PROBLEM
    assert "Traceback" not in capsys.readouterr().err


def test_a_source_that_is_not_utf_8_names_the_file(project, capsys):
    role(project, "qa.md").write_bytes(b"\xff\xfe not text")

    assert run(project) == PROBLEM
    assert capsys.readouterr().err.strip() == "swarm/roles/qa.md: the file is not valid UTF-8."
