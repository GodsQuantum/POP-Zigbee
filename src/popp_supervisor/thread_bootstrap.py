from __future__ import annotations

import argparse
from dataclasses import dataclass
import re
import subprocess
from typing import Callable


@dataclass(frozen=True)
class BootstrapResult:
    state: str
    channel: int


def _has_dataset(output: str) -> bool:
    for line in output.splitlines():
        value = line.strip()
        if re.fullmatch(r"[0-9a-fA-F]+", value) and len(value) % 2 == 0:
            return True
    return False


def _run_command(runner: Callable, args: list[str]):
    result = runner(args, capture_output=True, text=True, timeout=5, check=False)
    combined = f"{result.stdout}\n{result.stderr}"
    if result.returncode != 0 or "Error " in combined:
        raise RuntimeError(f"OpenThread command failed: {' '.join(args[1:])}")
    return result

def ensure_thread_dataset(
    ot_ctl: str,
    shared_channel: int,
    *,
    runner: Callable = subprocess.run,
) -> BootstrapResult:
    if not 11 <= shared_channel <= 26:
        raise ValueError("shared_channel must be in 11..26")

    active = runner(
        [ot_ctl, "dataset", "active", "-x"],
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    combined = f"{active.stdout}\n{active.stderr}"
    if _has_dataset(active.stdout):
        _run_command(runner, [ot_ctl, "ifconfig", "up"])
        _run_command(runner, [ot_ctl, "thread", "start"])
        return BootstrapResult("existing", shared_channel)
    if active.returncode != 0 and "NotFound" not in combined:
        raise RuntimeError("OpenThread active dataset query failed")
    if "Error " in combined and "NotFound" not in combined:
        raise RuntimeError("OpenThread active dataset query failed")

    for command in (
        ["dataset", "init", "new"],
        ["dataset", "channel", str(shared_channel)],
        ["dataset", "commit", "active"],
        ["ifconfig", "up"],
        ["thread", "start"],
    ):
        _run_command(runner, [ot_ctl, *command])
    return BootstrapResult("created", shared_channel)

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Initialize POP-Zigbee Thread once")
    parser.add_argument("--ot-ctl", default="/opt/popp/bin/ot-ctl")
    parser.add_argument("--shared-channel", type=int, required=True)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = ensure_thread_dataset(args.ot_ctl, args.shared_channel)
    print(f"Thread bootstrap: {result.state} on channel {result.channel}")


if __name__ == "__main__":
    main()