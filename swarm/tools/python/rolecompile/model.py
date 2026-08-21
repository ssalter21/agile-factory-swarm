"""The vocabulary that crosses the boundary between the filesystem and everything else.

Data only, and no imports from this package. Every path here is repo-relative and uses forward
slashes on every platform, so what the command prints does not depend on where it is run from.
Joining a path onto a root is `files`, and only `files`.
"""

from dataclasses import dataclass

ROLES_DIR = "swarm/roles"
CLAUDE_DIR = ".claude/agents"
GITHUB_DIR = ".github/agents"

DECLARATION_SUFFIX = ".yaml"
PROMPT_SUFFIX = ".md"
CLAUDE_SUFFIX = ".md"
GITHUB_SUFFIX = ".agent.md"


@dataclass(frozen=True)
class RoleSource:
    """One role definition as it sits on disk: both files, read as bytes and not yet decoded."""

    name: str
    declaration_path: str
    declaration_bytes: bytes
    prompt_path: str
    prompt_bytes: bytes


@dataclass(frozen=True)
class TargetFile:
    """One agent file, and exactly the bytes that belong in it."""

    path: str
    data: bytes
