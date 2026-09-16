import asyncio
import queue
import time

import pytest
from bellows import ash
import bellows.types as t

from popp_bridge.server import start_bridge_server
from popp_bridge.ash_ncp import AshNcpProtocol


class FakeEndpoint:
    def __init__(self):
        self.writes = []
        self.incoming = queue.Queue()

    def write(self, data):
        self.writes.append(bytes(data))
        return len(data)

    def read(self):
        try:
            return self.incoming.get(timeout=0.05)
        except queue.Empty:
            return b""

    def push(self, data):
        self.incoming.put(bytes(data))


def wire(frame):
    return AshNcpProtocol._stuff_bytes(frame.to_bytes()) + bytes([ash.Reserved.FLAG])


def parse_wire(data):
    assert data[-1] == ash.Reserved.FLAG
    return ash.parse_frame(AshNcpProtocol._unstuff_bytes(data[:-1]))


async def recv_frame(reader):
    return parse_wire(await asyncio.wait_for(reader.readuntil(bytes([ash.Reserved.FLAG])), 1))


async def wait_for_write(endpoint, expected):
    deadline = time.monotonic() + 1
    while time.monotonic() < deadline:
        if endpoint.writes == expected:
            return
        await asyncio.sleep(0.005)
    assert endpoint.writes == expected


@pytest.mark.asyncio
async def test_tcp_ash_and_raw_cpc_round_trip():
    endpoint = FakeEndpoint()
    server = await start_bridge_server(endpoint, host="127.0.0.1", port=0)
    port = server.sockets[0].getsockname()[1]
    reader, writer = await asyncio.open_connection("127.0.0.1", port)
    try:
        writer.write(wire(ash.RstFrame()))
        await writer.drain()
        assert await recv_frame(reader) == ash.RStackFrame(
            version=2,
            reset_code=t.NcpResetCode.RESET_SOFTWARE,
        )

        host_frame = ash.DataFrame(
            frm_num=0,
            re_tx=False,
            ack_num=0,
            ezsp_frame=b"\x01\x02\x03",
        )
        writer.write(wire(host_frame))
        await writer.drain()
        assert await recv_frame(reader) == ash.AckFrame(
            res=0, ncp_ready=0, ack_num=1
        )
        await wait_for_write(endpoint, [b"\x01\x02\x03"])

        endpoint.push(b"\xaa\xbb")
        outbound = await recv_frame(reader)
        assert isinstance(outbound, ash.DataFrame)
        assert outbound.ezsp_frame == b"\xaa\xbb"
        writer.write(
            wire(
                ash.AckFrame(
                    res=0,
                    ncp_ready=0,
                    ack_num=(outbound.frm_num + 1) % 8,
                )
            )
        )
        await writer.drain()
        await asyncio.sleep(0.02)
    finally:
        writer.close()
        await writer.wait_closed()
        server.close()
        await server.wait_closed()
