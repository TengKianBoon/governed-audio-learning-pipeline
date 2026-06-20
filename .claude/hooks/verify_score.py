from __future__ import annotations

import re
import subprocess
import sys


def main() -> int:
    completed = subprocess.run([sys.executable, "tests/score.py"], capture_output=True, text=True)
    print(completed.stdout)
    if completed.returncode != 0:
        print(completed.stderr, file=sys.stderr)
        return completed.returncode
    match = re.search(r"SCORE=(\d+)", completed.stdout)
    if not match or int(match.group(1)) < 80:
        print("Score gate failed.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
