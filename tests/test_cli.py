from swarm_doctor import cli, doctor
from swarm_doctor.diagnosis import Verdict

GATE = b"""shell: pwsh

steps:
  tests:       "run the suite"
  coverage:    "run the suite; report --fail-under=0"
  duplication: missing
  mutation:    missing
  crap:        missing
  acceptance:  missing
"""


def write_gate(root, raw):
    directory = root / ".swarm"
    directory.mkdir()
    (directory / "gate.yaml").write_bytes(raw)


def invoke(monkeypatch, capsys, root, argv=("doctor",)):
    monkeypatch.chdir(root)
    monkeypatch.setattr("sys.argv", ["swarm", *argv])
    exit_code = cli.main()
    return exit_code, capsys.readouterr().out


def test_it_diagnoses_the_gate_of_the_directory_it_is_invoked_from(
    monkeypatch, capsys, tmp_path
):
    write_gate(tmp_path, GATE)
    exit_code, out = invoke(monkeypatch, capsys, tmp_path)
    lines = out.splitlines()
    assert exit_code == doctor.EXIT_ANSWERED
    assert lines[0].startswith(Verdict.DEGRADED.value)
    assert [line.split()[0] for line in lines[1:]] == [
        "tests",
        "coverage",
        "duplication",
        "mutation",
        "crap",
        "acceptance",
    ]


def test_an_empty_directory_yields_one_line_and_the_could_not_answer_code(
    monkeypatch, capsys, tmp_path
):
    exit_code, out = invoke(monkeypatch, capsys, tmp_path)
    assert exit_code == doctor.EXIT_COULD_NOT_ANSWER
    assert out.splitlines() == [
        f"{Verdict.UNUSABLE.value} no gate declaration found at "
        f".swarm/gate.yaml, under {tmp_path}."
    ]
    assert "Traceback" not in out


def test_a_gate_path_that_is_a_directory_reads_as_an_absent_declaration(
    monkeypatch, capsys, tmp_path
):
    (tmp_path / ".swarm" / "gate.yaml").mkdir(parents=True)
    exit_code, out = invoke(monkeypatch, capsys, tmp_path)
    assert exit_code == doctor.EXIT_COULD_NOT_ANSWER
    assert "no gate declaration found" in out


def test_the_arguments_come_from_the_command_line(monkeypatch, capsys, tmp_path):
    write_gate(tmp_path, GATE)
    exit_code, out = invoke(monkeypatch, capsys, tmp_path, argv=("frobnicate",))
    assert exit_code == doctor.EXIT_COULD_NOT_ANSWER
    assert out == "usage: swarm doctor\n"


def test_it_writes_nothing_where_it_is_invoked(monkeypatch, capsys, tmp_path):
    write_gate(tmp_path, GATE)
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    digest = (tmp_path / ".swarm" / "gate.yaml").read_bytes()
    invoke(monkeypatch, capsys, tmp_path)
    assert sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*")) == before
    assert (tmp_path / ".swarm" / "gate.yaml").read_bytes() == digest
