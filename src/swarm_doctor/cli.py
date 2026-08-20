"""The process edge: argv, the working directory, one file read, stdout."""

import sys
from pathlib import Path

from swarm_doctor import doctor, gate


def main() -> int:
    looked_in = str(Path.cwd())
    try:
        gate_bytes = (Path(looked_in) / gate.GATE_RELATIVE_PATH).read_bytes()
    except OSError:
        gate_bytes = None
    report = doctor.run(sys.argv[1:], gate_bytes, looked_in)
    print("\n".join(report.lines))
    return report.exit_code


if __name__ == "__main__":
    sys.exit(main())
