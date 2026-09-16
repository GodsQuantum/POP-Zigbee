from pathlib import Path
import json
import os
import socket
import subprocess
import termios

from .channel_guard import evaluate_channels
from .health import aggregate_health
from .http import Metrics



def load_provisioning_status(path: str | Path = "/run/popp/ha-sync-status.json") -> dict:
    default = {
        "state": "waiting",
        "ha_api": False,
        "preferred_thread_dataset": False,
        "matter_thread_synced": False,
    }
    try:
        data = json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError, TypeError):
        return default
    if not isinstance(data, dict):
        return default
    result = default.copy()
    if isinstance(data.get("state"), str):
        result["state"] = data["state"]
    for key in ("ha_api", "preferred_thread_dataset", "matter_thread_synced"):
        if isinstance(data.get(key), bool):
            result[key] = data[key]
    for key in ("last_success", "error"):
        if isinstance(data.get(key), str):
            result[key] = data[key][:128]
    return result

def parse_thread_channel(output: str) -> int | None:
    for token in output.split():
        if token.isdigit():
            value = int(token)
            if 11 <= value <= 26:
                return value
    return None



def tty_probe(device: str | Path) -> bool:
    """Return True only when the configured path is an openable TTY."""
    try:
        fd = os.open(os.fspath(device), os.O_RDONLY | os.O_NONBLOCK)
    except OSError:
        return False
    try:
        termios.tcgetattr(fd)
        return True
    except termios.error:
        return False
    finally:
        os.close(fd)


def tcp_probe(host: str, port: int, timeout: float = 0.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def read_thread_channel(ot_ctl: str = "/opt/popp/bin/ot-ctl") -> int | None:
    try:
        result = subprocess.run(
            [ot_ctl, "channel"], capture_output=True, text=True, timeout=2, check=False
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return parse_thread_channel(result.stdout)


def collect_health(
    *,
    device: str | Path,
    cpc_socket: str | Path,
    shared_channel: int,
    metrics: Metrics,
    device_probe_fn=tty_probe,
    tcp_probe_fn=tcp_probe,
    thread_channel_fn=read_thread_channel,
    provisioning_status_fn=load_provisioning_status,
) -> dict:
    channel = evaluate_channels(shared_channel, thread_channel_fn())
    metrics.channel_mismatch = 0 if channel.safe else 1
    return aggregate_health(
        usb_present=device_probe_fn(device),
        cpcd_healthy=Path(cpc_socket).exists(),
        zigbee_bridge_healthy=tcp_probe_fn("127.0.0.1", 9999),
        otbr_healthy=tcp_probe_fn("127.0.0.1", 8081),
        channel=channel,
        provisioning=provisioning_status_fn(),
    )
