"""The one module that touches the filesystem, against a role tree in tmp_path.

Nothing here points at this repository's own agent directories. A test that needs a role tree
builds one.
"""

import pytest

from rolecompile import files
from rolecompile.model import TargetFile

DECLARED = "name: qa\ndescription: Verifies.\ntools: Read\nmodel: opus\neffort: high\n"


@pytest.fixture
def project(tmp_path):
    """A two-role tree, written with the line endings a source file is allowed to have."""
    roles = tmp_path / "swarm" / "roles"
    roles.mkdir(parents=True)
    for name in ("qa", "coder"):
        (roles / (name + ".yaml")).write_bytes(
            DECLARED.replace("name: qa", "name: " + name).encode("utf-8")
        )
        (roles / (name + ".md")).write_bytes(("You are %s.\n" % name).encode("utf-8"))
    return tmp_path


def test_sources_come_back_in_filename_order(project):
    assert [source.name for source in files.read_sources(project)] == ["coder", "qa"]


def test_a_source_carries_repo_relative_paths_with_forward_slashes(project):
    source = files.read_sources(project)[0]
    assert source.declaration_path == "swarm/roles/coder.yaml"
    assert source.prompt_path == "swarm/roles/coder.md"


def test_a_source_carries_the_bytes_on_disk_untranslated(project):
    (project / "swarm" / "roles" / "qa.md").write_bytes(b"You are qa.\r\n")
    prompts = {source.name: source.prompt_bytes for source in files.read_sources(project)}
    assert prompts["qa"] == b"You are qa.\r\n"


def test_a_stray_file_in_the_role_directory_is_not_a_role(project):
    (project / "swarm" / "roles" / "notes.txt").write_bytes(b"scratch")
    assert [source.name for source in files.read_sources(project)] == ["coder", "qa"]


def test_a_prompt_with_no_declaration_beside_it_is_not_a_role(project):
    (project / "swarm" / "roles" / "orphan.md").write_bytes(b"You are nobody.\n")
    assert [source.name for source in files.read_sources(project)] == ["coder", "qa"]


def test_a_declaration_with_no_prompt_beside_it_names_the_missing_file(project):
    (project / "swarm" / "roles" / "qa.md").unlink()
    with pytest.raises(OSError) as caught:
        files.read_sources(project)
    assert caught.value.filename.endswith("qa.md")


def test_no_role_directory_at_all_raises_rather_than_compiling_nothing(tmp_path):
    with pytest.raises(OSError):
        files.read_sources(tmp_path)


def test_reading_targets_marks_an_absent_file_as_none(project):
    found = files.read_targets(project, [".claude/agents/qa.md"])
    assert found == {".claude/agents/qa.md": None}


def test_reading_targets_returns_the_bytes_on_disk(project):
    agents = project / ".claude" / "agents"
    agents.mkdir(parents=True)
    (agents / "qa.md").write_bytes(b"---\r\nname: qa\r\n")
    assert files.read_targets(project, [".claude/agents/qa.md"]) == {
        ".claude/agents/qa.md": b"---\r\nname: qa\r\n"
    }


def test_destinations_present_reports_only_the_directories_that_exist(project):
    (project / ".claude" / "agents").mkdir(parents=True)
    found = files.destinations_present(project, (".claude/agents", ".github/agents"))
    assert found == {".claude/agents"}


def test_a_file_where_a_destination_directory_should_be_is_not_a_destination(project):
    (project / ".claude").mkdir()
    (project / ".claude" / "agents").write_bytes(b"not a directory")
    assert files.destinations_present(project, (".claude/agents",)) == set()


def test_writing_creates_the_directory_and_puts_the_bytes_there(project):
    files.write(project, [TargetFile(path=".github/agents/qa.agent.md", data=b"---\r\n")])
    assert (project / ".github" / "agents" / "qa.agent.md").read_bytes() == b"---\r\n"


def test_writing_does_not_translate_a_line_ending(project):
    files.write(project, [TargetFile(path=".claude/agents/qa.md", data=b"a\r\nb\r\n")])
    assert (project / ".claude" / "agents" / "qa.md").read_bytes() == b"a\r\nb\r\n"


def test_writing_nothing_creates_nothing(project):
    files.write(project, [])
    assert not (project / ".claude").exists()
    assert not (project / ".github").exists()


def test_writing_replaces_a_file_rather_than_appending_to_it(project):
    target = TargetFile(path=".claude/agents/qa.md", data=b"second\r\n")
    files.write(project, [TargetFile(path=".claude/agents/qa.md", data=b"first\r\n")])
    files.write(project, [target])
    assert (project / ".claude" / "agents" / "qa.md").read_bytes() == b"second\r\n"
