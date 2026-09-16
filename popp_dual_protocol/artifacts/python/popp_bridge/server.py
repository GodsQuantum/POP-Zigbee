"""Async TCP/ASH front-end backed by a raw EZSP CPC endpoint."""

import asyncio
import contextlib

from .ash_ncp import AshNcpProtocol


class _RawEzspSink:
    def __init__(self, outgoing: asyncio.Queue[bytes]) -> None:
        self.outgoing = outgoing

    def connection_made(self, protocol) -> None:
        self.protocol = protocol

    def connection_lost(self, exc) -> None:
        pass

    def eof_received(self) -> None:
        pass

    def data_received(self, data: bytes) -> None:
        self.outgoing.put_nowait(bytes(data))

    def reset_received(self, code) -> None:
        pass

    def error_received(self, code) -> None:
        pass


class _WriterTransport:
    def __init__(self, writer: asyncio.StreamWriter) -> None:
        self.writer = writer

    def write(self, data: bytes) -> None:
        self.writer.write(data)

    def close(self) -> None:
        self.writer.close()

    def is_closing(self) -> bool:
        return self.writer.is_closing()


async def _tcp_to_protocol(reader, protocol) -> None:
    while True:
        data = await reader.read(4096)
        if not data:
            return
        protocol.data_received(data)


async def _queue_to_cpc(outgoing, endpoint, protocol) -> None:
    while True:
        data = await outgoing.get()
        try:
            await asyncio.to_thread(endpoint.write, data)
        except OSError:
            if not protocol.reset_in_progress:
                raise
            await asyncio.sleep(0.01)


async def _cpc_to_protocol(endpoint, protocol) -> None:
    while True:
        try:
            data = await asyncio.to_thread(endpoint.read)
        except OSError:
            if not protocol.reset_in_progress:
                raise
            await asyncio.sleep(0.01)
            continue
        if data:
            await protocol.send_data(bytes(data))
        else:
            await asyncio.sleep(0.005)


async def _serve_client(endpoint, reader, writer, reset_backend=None) -> None:
    outgoing = asyncio.Queue()
    sink = _RawEzspSink(outgoing)

    async def reset_handler():
        await reset_backend()
        await asyncio.to_thread(endpoint.reconnect)

    protocol = AshNcpProtocol(
        sink, reset_handler=reset_handler if reset_backend is not None else None
    )
    protocol.connection_made(_WriterTransport(writer))

    tasks = {
        asyncio.create_task(_tcp_to_protocol(reader, protocol)),
        asyncio.create_task(_queue_to_cpc(outgoing, endpoint, protocol)),
        asyncio.create_task(_cpc_to_protocol(endpoint, protocol)),
    }
    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    for task in pending:
        task.cancel()
    for task in pending:
        with contextlib.suppress(asyncio.CancelledError):
            await task
    for task in done:
        task.result()

    protocol.connection_lost(None)
    if not writer.is_closing():
        writer.close()
    with contextlib.suppress(ConnectionError):
        await writer.wait_closed()


async def start_bridge_server(
    endpoint, host="127.0.0.1", port=9999, reset_backend=None
):
    """Start a single-owner ASH server backed by one CPC Zigbee endpoint."""
    lock = asyncio.Lock()
    active = False

    async def client_connected(reader, writer):
        nonlocal active
        async with lock:
            if active:
                writer.close()
                await writer.wait_closed()
                return
            active = True
        try:
            await _serve_client(endpoint, reader, writer, reset_backend=reset_backend)
        finally:
            async with lock:
                active = False

    return await asyncio.start_server(client_connected, host=host, port=port)
