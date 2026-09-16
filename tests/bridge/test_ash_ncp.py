import asyncio

import pytest
from bellows import ash
import bellows.types as t

from popp_bridge.ash_ncp import AshNcpProtocol


class Sink:
    def __init__(self):
        self.frames = []
        self.errors = []

    def connection_made(self, protocol):
        self.protocol = protocol

    def connection_lost(self, exc):
        pass

    def eof_received(self):
        pass

    def data_received(self, data):
        self.frames.append(data)

    def reset_received(self, code):
        pass
    def error_received(self, code):
        self.errors.append(code)


class FakeTransport:
    def __init__(self):
        self.writes = []
        self.closed = False

    def write(self, data):
        self.writes.append(bytes(data))

    def close(self):
        self.closed = True

    def is_closing(self):
        return self.closed


def wire(frame):
    return AshNcpProtocol._stuff_bytes(frame.to_bytes()) + bytes([ash.Reserved.FLAG])


def parse_wire(data):
    assert data[-1] == ash.Reserved.FLAG
    return ash.parse_frame(AshNcpProtocol._unstuff_bytes(data[:-1]))
def make_protocol():
    sink = Sink()
    transport = FakeTransport()
    proto = AshNcpProtocol(sink)
    proto.connection_made(transport)
    return proto, sink, transport


def test_reset_is_answered_with_rstack():
    proto, _, transport = make_protocol()

    proto.data_received(wire(ash.RstFrame()))

    assert parse_wire(transport.writes[-1]) == ash.RStackFrame(
        version=2,
        reset_code=t.NcpResetCode.RESET_SOFTWARE,
    )


def test_host_data_is_acked_and_forwarded_raw():
    proto, sink, transport = make_protocol()
    frame = ash.DataFrame(frm_num=0, re_tx=False, ack_num=0, ezsp_frame=b"\x01\x02")

    proto.data_received(wire(frame))

    assert sink.frames == [b"\x01\x02"]
    assert parse_wire(transport.writes[-1]) == ash.AckFrame(res=0, ncp_ready=0, ack_num=1)
@pytest.mark.asyncio
async def test_raw_cpc_frame_is_wrapped_for_zha():
    proto, _, transport = make_protocol()

    task = asyncio.create_task(proto.send_data(b"\xaa\xbb"))
    await asyncio.sleep(0)

    sent = parse_wire(transport.writes[-1])
    assert isinstance(sent, ash.DataFrame)
    assert sent.frm_num == 0
    assert bool(sent.re_tx) is False
    assert sent.ezsp_frame == b"\xaa\xbb"

    proto.data_received(wire(ash.AckFrame(res=0, ncp_ready=0, ack_num=1)))
    await task


@pytest.mark.asyncio
async def test_nak_retransmits_same_frame_number():
    proto, _, transport = make_protocol()

    task = asyncio.create_task(proto.send_data(b"\xde\xad"))
    await asyncio.sleep(0)
    first = parse_wire(transport.writes[-1])

    proto.data_received(wire(ash.NakFrame(res=0, ncp_ready=0, ack_num=0)))
    await asyncio.sleep(0)
    second = parse_wire(transport.writes[-1])
    assert isinstance(first, ash.DataFrame)
    assert isinstance(second, ash.DataFrame)
    assert second.frm_num == first.frm_num == 0
    assert bool(second.re_tx) is True
    assert second.ezsp_frame == first.ezsp_frame == b"\xde\xad"

    proto.data_received(wire(ash.AckFrame(res=0, ncp_ready=0, ack_num=1)))
    await task


@pytest.mark.asyncio
async def test_reset_waits_for_backend_before_rstack():
    started = asyncio.Event()
    release = asyncio.Event()

    async def reset_handler():
        started.set()
        await release.wait()

    sink = Sink()
    transport = FakeTransport()
    proto = AshNcpProtocol(sink, reset_handler=reset_handler)
    proto.connection_made(transport)

    proto.data_received(wire(ash.RstFrame()))
    await asyncio.wait_for(started.wait(), 1)
    assert transport.writes == []

    release.set()
    await asyncio.sleep(0)
    await asyncio.sleep(0)
    assert parse_wire(transport.writes[-1]) == ash.RStackFrame(
        version=2, reset_code=t.NcpResetCode.RESET_SOFTWARE
    )


@pytest.mark.asyncio
async def test_reset_backend_failure_closes_transport_without_fake_rstack():
    async def reset_handler():
        raise RuntimeError("reset failed")

    sink = Sink()
    transport = FakeTransport()
    proto = AshNcpProtocol(sink, reset_handler=reset_handler)
    proto.connection_made(transport)

    proto.data_received(wire(ash.RstFrame()))
    await asyncio.sleep(0)
    await asyncio.sleep(0)

    assert transport.writes == []
    assert transport.closed is True
