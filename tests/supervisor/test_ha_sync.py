import json
from pathlib import Path

import pytest

from popp_supervisor.ha_sync import (
    DatasetFingerprintStore,
    HomeAssistantClient,
    SyncError,
    select_preferred_dataset,
    sync_once,
)


class FakeClient:
    def __init__(self, datasets, tlv="001122"):
        self.datasets = datasets
        self.tlv = tlv
        self.calls = []

    async def command(self, command, **kwargs):
        self.calls.append((command, kwargs))
        if command == "thread/list_datasets":
            return {"datasets": self.datasets}
        if command == "thread/get_dataset_tlv":
            return {"tlv": self.tlv}
        if command == "matter/set_thread":
            return None
        raise AssertionError(command)


def preferred(dataset_id="preferred"):
    return {"dataset_id": dataset_id, "preferred": True, "network_name": "ha-thread-test"}


def test_select_preferred_dataset_requires_exactly_one_preferred():
    assert select_preferred_dataset([preferred("a")])["dataset_id"] == "a"
    assert select_preferred_dataset([{"dataset_id": "x", "preferred": False}]) is None
    with pytest.raises(SyncError, match="multiple_preferred"):
        select_preferred_dataset([preferred("a"), preferred("b")])


@pytest.mark.asyncio
async def test_no_preferred_dataset_waits_without_touching_matter(tmp_path):
    client = FakeClient([{"dataset_id": "x", "preferred": False}])
    store = DatasetFingerprintStore(tmp_path / "state.json")
    outcome = await sync_once(client, store)
    assert outcome.state == "waiting_preferred_dataset"
    assert [name for name, _ in client.calls] == ["thread/list_datasets"]


@pytest.mark.asyncio
async def test_preferred_dataset_is_sent_to_matter_and_only_hash_is_persisted(tmp_path):
    client = FakeClient([preferred()], tlv="001122334455")
    state_path = tmp_path / "state.json"
    outcome = await sync_once(client, DatasetFingerprintStore(state_path))
    assert outcome.state == "synced"
    assert [name for name, _ in client.calls] == [
        "thread/list_datasets",
        "thread/get_dataset_tlv",
        "matter/set_thread",
    ]
    raw = state_path.read_text()
    assert "001122334455" not in raw
    persisted = json.loads(raw)
    assert len(persisted["fingerprint"]) == 64
    assert persisted["dataset_id"] == "preferred"


class FakeWs:
    def __init__(self, incoming):
        self.incoming = list(incoming)
        self.sent = []

    async def receive_json(self):
        return self.incoming.pop(0)

    async def send_json(self, payload):
        self.sent.append(payload)


@pytest.mark.asyncio
async def test_websocket_auth_uses_supervisor_token():
    ws = FakeWs([{"type": "auth_required"}, {"type": "auth_ok"}])
    client = HomeAssistantClient(token="supervisor-token")
    await client.authenticate(ws)
    assert ws.sent == [{"type": "auth", "access_token": "supervisor-token"}]


@pytest.mark.asyncio
async def test_command_uses_home_assistant_websocket_framing():
    ws = FakeWs([{"id": 1, "type": "result", "success": True, "result": {"datasets": []}}])
    client = HomeAssistantClient(token="token")
    client.ws = ws
    result = await client.command("thread/list_datasets")
    assert result == {"datasets": []}
    assert ws.sent == [{"id": 1, "type": "thread/list_datasets"}]


@pytest.mark.asyncio
async def test_same_preferred_dataset_is_resent_for_matter_self_healing(tmp_path):
    client = FakeClient([preferred()], tlv="001122334455")
    store = DatasetFingerprintStore(tmp_path / "state.json")
    await sync_once(client, store)
    await sync_once(client, store)
    matter_sets = [call for call in client.calls if call[0] == "matter/set_thread"]
    assert len(matter_sets) == 2
