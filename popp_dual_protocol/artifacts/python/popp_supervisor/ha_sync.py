from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import aiohttp


class SyncError(RuntimeError):
    """Sanitized Home Assistant synchronization error."""


@dataclass(frozen=True)
class SyncOutcome:
    state: str
    dataset_id: str | None = None
    network_name: str | None = None


def select_preferred_dataset(datasets: list[dict[str, Any]]) -> dict[str, Any] | None:
    preferred = [item for item in datasets if item.get("preferred") is True]
    if len(preferred) > 1:
        raise SyncError("multiple_preferred_datasets")
    return preferred[0] if preferred else None

class DatasetFingerprintStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def save(self, *, dataset_id: str, tlv: str) -> None:
        try:
            raw = bytes.fromhex(tlv)
        except ValueError as err:
            raise SyncError("invalid_thread_dataset_tlv") from err
        payload = {
            "dataset_id": dataset_id,
            "fingerprint": hashlib.sha256(raw).hexdigest(),
            "updated_at": datetime.now(UTC).isoformat(),
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, separators=(",", ":"))
                handle.write("\n")
            os.replace(tmp, self.path)
            os.chmod(self.path, 0o600)
        finally:
            try:
                tmp.unlink()
            except FileNotFoundError:
                pass


class HomeAssistantClient:
    def __init__(
        self,
        *,
        token: str,
        url: str = "ws://supervisor/core/websocket",
    ):
        self.token = token
        self.url = url
        self.session: aiohttp.ClientSession | None = None
        self.ws: Any = None
        self._next_id = 0

    async def authenticate(self, ws: Any) -> None:
        hello = await ws.receive_json()
        if hello.get("type") != "auth_required":
            raise SyncError("unexpected_websocket_auth_state")
        await ws.send_json({"type": "auth", "access_token": self.token})
        result = await ws.receive_json()
        if result.get("type") != "auth_ok":
            raise SyncError("home_assistant_auth_failed")

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        try:
            self.ws = await self.session.ws_connect(self.url, heartbeat=20)
            await self.authenticate(self.ws)
        except Exception:
            await self.session.close()
            self.session = None
            raise
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self.ws is not None:
            await self.ws.close()
            self.ws = None
        if self.session is not None:
            await self.session.close()
            self.session = None

    async def command(self, command: str, **kwargs: Any) -> Any:
        if self.ws is None:
            raise SyncError("home_assistant_websocket_not_connected")
        self._next_id += 1
        message_id = self._next_id
        payload = {"id": message_id, "type": command, **kwargs}
        await self.ws.send_json(payload)
        while True:
            response = await self.ws.receive_json()
            if response.get("id") != message_id:
                continue
            if response.get("type") != "result":
                raise SyncError(f"unexpected_response:{command}")
            if response.get("success") is not True:
                error = response.get("error") or {}
                code = error.get("code", "unknown")
                raise SyncError(f"command_failed:{command}:{code}")
            return response.get("result")


async def sync_once(
    client: HomeAssistantClient,
    store: DatasetFingerprintStore,
) -> SyncOutcome:
    listed = await client.command("thread/list_datasets")
    dataset = select_preferred_dataset(listed.get("datasets", []))
    if dataset is None:
        return SyncOutcome("waiting_preferred_dataset")
    dataset_id = str(dataset["dataset_id"])
    tlv_result = await client.command("thread/get_dataset_tlv", dataset_id=dataset_id)
    tlv = tlv_result.get("tlv")
    if not isinstance(tlv, str) or not tlv:
        raise SyncError("missing_thread_dataset_tlv")

    await client.command("matter/set_thread", thread_operation_dataset=tlv)
    store.save(dataset_id=dataset_id, tlv=tlv)
    return SyncOutcome(
        "synced",
        dataset_id=dataset_id,
        network_name=dataset.get("network_name"),
    )


def write_status(path: str | Path, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, separators=(",", ":")) + "\n")
    os.replace(tmp, target)


async def run_forever(
    *,
    token: str,
    interval: float,
    state_path: str | Path,
    status_path: str | Path,
) -> None:
    store = DatasetFingerprintStore(state_path)
    while True:
        status = {"ha_api": False, "preferred_thread_dataset": False, "matter_thread_synced": False}
        try:
            async with HomeAssistantClient(token=token) as client:
                status["ha_api"] = True
                outcome = await sync_once(client, store)
                status["state"] = outcome.state
                status["preferred_thread_dataset"] = outcome.dataset_id is not None
                status["matter_thread_synced"] = outcome.state == "synced"
                if outcome.state == "synced":
                    status["last_success"] = datetime.now(UTC).isoformat()
        except Exception as err:  # retry loop must survive Core/Matter restarts
            status["state"] = "error"
            status["error"] = type(err).__name__
        write_status(status_path, status)
        await asyncio.sleep(interval)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sync Home Assistant Thread credentials to Matter")
    parser.add_argument("--interval", type=float, default=60.0)
    parser.add_argument("--state-path", default="/data/ha-sync-state.json")
    parser.add_argument("--status-path", default="/run/popp/ha-sync-status.json")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    token = os.environ.get("SUPERVISOR_TOKEN")
    if not token:
        raise SystemExit("SUPERVISOR_TOKEN is required")
    asyncio.run(
        run_forever(
            token=token,
            interval=args.interval,
            state_path=args.state_path,
            status_path=args.status_path,
        )
    )


if __name__ == "__main__":
    main()
