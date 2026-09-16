import ctypes
import errno

from libcpc.libcpc import Endpoint

from popp_bridge.cpc_adapter import CpcZigbeeEndpoint, open_zigbee_endpoint


class FakeLib:
    def __init__(self, replies):
        self.replies = list(replies)

    def cpc_read_endpoint(self, endpoint, buffer, count, flags):
        reply = self.replies.pop(0)
        if isinstance(reply, int):
            return reply
        ctypes.memmove(buffer, reply, len(reply))
        return len(reply)


class FakeCpc:
    def __init__(self, library_name=None, instance_name=None):
        self.library_name = library_name
        self.instance_name = instance_name
        self.lib_cpc = FakeLib([])
        self.opened = []

    def open_endpoint(self, endpoint_id, tx_window_size=1):
        endpoint = FakeEndpoint(self)
        self.opened.append((endpoint_id, tx_window_size, endpoint))
        return endpoint


class FakeEndpoint:
    def __init__(self, cpc):
        self.cpc_handle = cpc
        self.read_timeout = None
        self.writes = []

    def write(self, data):
        self.writes.append(bytes(data))
        return len(data)

    def close(self):
        pass


def test_open_uses_zigbee_endpoint_and_read_timeout():
    adapter = open_zigbee_endpoint(
        instance_name="popp_cpc",
        library_name="/tmp/libcpc.so.3",
        read_timeout=0.25,
        cpc_factory=FakeCpc,
    )

    endpoint_id, tx_window, endpoint = adapter.cpc.opened[0]
    assert endpoint_id == Endpoint.Id.ZIGBEE
    assert tx_window == 1
    assert endpoint.read_timeout.seconds == 0
    assert endpoint.read_timeout.microseconds == 250000


def test_read_converts_eagain_to_empty_poll():
    cpc = FakeCpc()
    cpc.lib_cpc = FakeLib([-errno.EAGAIN])
    endpoint = FakeEndpoint(cpc)
    adapter = CpcZigbeeEndpoint(cpc, endpoint)

    assert adapter.read() == b""


def test_read_returns_complete_raw_ezsp_packet():
    cpc = FakeCpc()
    cpc.lib_cpc = FakeLib([b"\x01\x02\x03"])
    endpoint = FakeEndpoint(cpc)
    adapter = CpcZigbeeEndpoint(cpc, endpoint)

    assert adapter.read() == b"\x01\x02\x03"


def test_write_delegates_to_libcpc_endpoint():
    cpc = FakeCpc()
    endpoint = FakeEndpoint(cpc)
    adapter = CpcZigbeeEndpoint(cpc, endpoint)

    assert adapter.write(b"\xaa\xbb") == 2
    assert endpoint.writes == [b"\xaa\xbb"]


class RestartableFakeCpc(FakeCpc):
    def __init__(self, library_name=None, instance_name=None, reset_callback=None):
        super().__init__(library_name=library_name, instance_name=instance_name)
        self.reset_callback = reset_callback
        self.restart_calls = 0

    def restart(self):
        self.restart_calls += 1


def test_reconnect_restarts_libcpc_and_reopens_zigbee_endpoint():
    adapter = open_zigbee_endpoint(
        instance_name="cpcd_0",
        library_name="/tmp/libcpc.so.3",
        read_timeout=0.25,
        cpc_factory=RestartableFakeCpc,
    )
    first = adapter.endpoint

    adapter.reconnect()

    assert adapter.cpc.restart_calls == 1
    assert adapter.endpoint is not first
    assert adapter.cpc.opened[-1][0] == Endpoint.Id.ZIGBEE
    assert adapter.endpoint.read_timeout.microseconds == 250000
