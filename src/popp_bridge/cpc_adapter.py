"""Thin libcpc adapter exposing the Zigbee EZSP CPC endpoint."""

import errno
import os
from ctypes import create_string_buffer

from libcpc.libcpc import CPC, CPCTimeval, Endpoint

READ_SIZE = 4087


class CpcZigbeeEndpoint:
    """Packet-preserving adapter around CPC endpoint 5 (Zigbee/EZSP)."""

    def __init__(self, cpc, endpoint, read_timeout: float = 0.25) -> None:
        self.cpc = cpc
        self.endpoint = endpoint
        self.read_timeout = read_timeout

    def read(self) -> bytes:
        buffer = create_string_buffer(READ_SIZE)
        ret = self.cpc.lib_cpc.cpc_read_endpoint(
            self.endpoint, buffer, READ_SIZE, 0
        )
        if ret == -errno.EAGAIN:
            return b""
        if ret < 0:
            raise OSError(-ret, os.strerror(-ret))
        return bytes(buffer.raw[:ret])

    def write(self, data: bytes) -> int:
        return self.endpoint.write(data)

    def close(self):
        return self.endpoint.close()

    def reconnect(self) -> None:
        try:
            self.endpoint.close()
        except Exception:
            pass
        self.cpc.restart()
        self.endpoint = self.cpc.open_endpoint(Endpoint.Id.ZIGBEE, tx_window_size=1)
        self.endpoint.read_timeout = CPCTimeval(self.read_timeout)


def open_zigbee_endpoint(
    *,
    instance_name: str = "cpcd_0",
    library_name: str | None = None,
    read_timeout: float = 0.25,
    cpc_factory=CPC,
) -> CpcZigbeeEndpoint:
    """Connect to CPCd and open the standard Zigbee/EZSP endpoint 5."""
    cpc = cpc_factory(
        library_name=library_name,
        instance_name=instance_name,
    )
    endpoint = cpc.open_endpoint(Endpoint.Id.ZIGBEE, tx_window_size=1)
    endpoint.read_timeout = CPCTimeval(read_timeout)
    return CpcZigbeeEndpoint(cpc, endpoint, read_timeout=read_timeout)
