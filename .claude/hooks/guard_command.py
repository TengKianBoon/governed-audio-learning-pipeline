from __future__ import annotations

import json
import sys


BLOCKED = [
    "rm -rf",
    "remove-item -recurse -force",
    "git reset --hard",
    "git push --force",
    "setx path",
    "[environment]::setenvironmentvariable(\"path\"",
]


def main() -> int:
    payload = sys.stdin.read()
    command = payload
    try:
        data = json.loads(payload) if payload.strip() else {}
        command = str(data.get("command", payload))
    except json.JSONDecodeError:
        pass
    lowered = command.lower()
    for blocked in BLOCKED:
        if blocked in lowered:
            print(f"Blocked command pattern: {blocked}", file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
