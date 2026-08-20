"""Compiling one role definition into the agent file each harness loads.

A role is edited in one place: `swarm/roles/<name>.yaml` holds its five declared fields and
`swarm/roles/<name>.md` holds its prompt. This tool turns that pair into the files the harnesses
read. Standard library only, nothing to install. Run the package directory from the repo root.

    python swarm/tools/python/rolecompile           # write both trees
    python swarm/tools/python/rolecompile --check   # compare only, write nothing

Claude Code gets `.claude/agents/<name>.md` with all five fields. GitHub Copilot gets
`.github/agents/<name>.agent.md` with `name`, `description` and `tools`; `model` and `effort` are
dropped there because there is no correct value to write. Nothing in this repository dispatches to
the GitHub files: they are published, not run.

The twelve Claude agent files that already exist are the test of this tool. Compiling must
reproduce them byte for byte, so the output bytes are specified here rather than left to a YAML
dumper: fixed field order, no folding, UTF-8 with no byte-order mark, CRLF on every platform, and
one newline at the end. `.gitattributes` pins the same line ending so a checkout cannot move it.

    module        holds
    ------------  ----------------------------------------------------------------
    model         the shapes and paths that cross the filesystem boundary
    text          decoding bytes, and splitting text into lines
    declaration   reading one role definition: its fields and its prompt
    validate      the three input checks, first problem wins
    emit          the bytes of an agent file, per harness
    compare       what the file on disk is, relative to the one we would write
    report        the wording of every line the command prints
    compiler      the whole compile, as pure functions
    files         the only module that touches the filesystem
    __main__      the command line

`compiler` and everything it imports are pure: no file access, no `os`, no `sys`. `files` moves
bytes and decides nothing. That split is what makes the tool testable without a repository.
"""
