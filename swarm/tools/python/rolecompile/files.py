"""The only module that touches the filesystem. It moves bytes and decides nothing.

It never decodes, never encodes, never translates a line ending, and never opens a file in text
mode: encoding and line endings belong to the compile, and a file handle that helpfully rewrites
newlines would put the platform back into output that must not depend on it.

Paths arrive repo-relative with forward slashes and are joined onto a root here. That join is the
only piece of platform knowledge in the package.
"""

import os

from rolecompile.model import DECLARATION_SUFFIX, PROMPT_SUFFIX, ROLES_DIR, RoleSource


def read_sources(root):
    """Every role definition under `swarm/roles/`, in filename order.

    The directory is the list of roles: there is no manifest to disagree with it. A declaration
    with no prompt beside it raises, naming the file that is not there.
    """
    sources = []
    for name in _role_names(root):
        declaration_path = "%s/%s%s" % (ROLES_DIR, name, DECLARATION_SUFFIX)
        prompt_path = "%s/%s%s" % (ROLES_DIR, name, PROMPT_SUFFIX)
        sources.append(
            RoleSource(
                name=name,
                declaration_path=declaration_path,
                declaration_bytes=read(root, declaration_path),
                prompt_path=prompt_path,
                prompt_bytes=read(root, prompt_path),
            )
        )
    return sources


def read_targets(root, paths):
    """{path: bytes}, with None where there is no file there."""
    found = {}
    for path in paths:
        try:
            found[path] = read(root, path)
        except FileNotFoundError:
            found[path] = None
    return found


def destinations_present(root, directories):
    """Which of `directories` exist. A destination that does not is out of a check run."""
    return {name for name in directories if os.path.isdir(join(root, name))}


def write(root, targets):
    """Put each target's bytes on disk, creating the directories they belong in."""
    for target in targets:
        full = join(root, target.path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "wb") as handle:
            handle.write(target.data)


def read(root, path):
    with open(join(root, path), "rb") as handle:
        return handle.read()


def join(root, path):
    return os.path.join(root, *path.split("/"))


def _role_names(root):
    entries = os.listdir(join(root, ROLES_DIR))
    return sorted(
        entry[: -len(DECLARATION_SUFFIX)]
        for entry in entries
        if entry.endswith(DECLARATION_SUFFIX)
    )
