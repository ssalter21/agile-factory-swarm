"""The mutation runner installs nothing and is not on the path.

Put its parent directory on sys.path the same way running the package directory does, so the
tests exercise the tool exactly as the gate does.
"""

import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "swarm" / "gate" / "tools" / "python"

if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))
