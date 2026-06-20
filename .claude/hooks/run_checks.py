from __future__ import annotations

import subprocess
import sys


def main() -> int:
    completed = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests"], text=True)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
