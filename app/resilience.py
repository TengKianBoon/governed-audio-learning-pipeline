from __future__ import annotations

from dataclasses import dataclass
import subprocess
import time
from collections.abc import Mapping


@dataclass(frozen=True)
class RetryPolicy:
    max_retries: int = 3
    backoff_seconds: int = 1


class RetryExhausted(RuntimeError):
    pass


def run_command_with_retries(
    command: list[str],
    *,
    policy: RetryPolicy,
    failure_label: str,
    env: Mapping[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    attempts = max(1, policy.max_retries)
    last: subprocess.CompletedProcess[str] | None = None
    for attempt in range(1, attempts + 1):
        last = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            env=env,
        )
        if last.returncode == 0:
            return last
        if attempt < attempts:
            time.sleep(policy.backoff_seconds * attempt)
    stderr = (last.stderr if last else "").strip()
    raise RetryExhausted(f"{failure_label} failed after {attempts} attempt(s). {stderr}".strip())
