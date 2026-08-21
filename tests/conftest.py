"""The tools this repo ships install nothing and are not on the path.

Put each one's parent directory on sys.path the same way running the package directory does, so
the tests exercise the tools exactly as the gate does.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TOOLS = ROOT / "swarm" / "gate" / "tools" / "python"
ROLECOMPILE = ROOT / "swarm" / "tools" / "python"

for entry in (TOOLS, ROLECOMPILE):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))
