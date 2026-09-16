"""Command-line entry point for the POPP CPC-to-ASH bridge."""

import argparse
import asyncio
import contextlib
from pathlib import Path
import signal

from .cpc_adapter import open_zigbee_endpoint
from .server import start_bridge_server


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Expose CPC Zigbee/EZSP endpoint 5 as standard ASH/TCP for ZHA."
    )
    parser.add_argument("--instance", default="cpcd_0")
    parser.add_argument("--libcpc", default=None)
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=9999)
    parser.add_argument("--read-timeout", type=float, default=0.25)
    parser.add_argument("--cpcd-service", default=None)
    return parser


async def restart_cpcd_service(service_path: str) -> None:
    marker = Path("/run/popp/intentional-cpc-reset")
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.touch()
    try:
        for mode, wait_mode in (("-d", "-wD"), ("-u", "-wU")):
            proc = await asyncio.create_subprocess_exec(
                "s6-svc", mode, wait_mode, "-T", "1500", service_path
            )
            if await proc.wait() != 0:
                raise RuntimeError(f"failed to transition CPCd service {mode}")
    finally:
        # The CPCd finish script normally consumes this marker. Remove a stale
        # marker if the service transition failed before finish could run.
        with contextlib.suppress(FileNotFoundError):
            marker.unlink()


async def run(args) -> None:
    endpoint = open_zigbee_endpoint(
        instance_name=args.instance,
        library_name=args.libcpc,
        read_timeout=args.read_timeout,
    )
    reset_backend = None
    if args.cpcd_service is not None:
        async def reset_backend():
            await restart_cpcd_service(args.cpcd_service)

    server = await start_bridge_server(
        endpoint, host=args.host, port=args.port, reset_backend=reset_backend
    )
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    def request_stop() -> None:
        stop_event.set()

    installed_signals = []
    for sig in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(sig, request_stop)
            installed_signals.append(sig)

    try:
        async with server:
            await stop_event.wait()
    finally:
        server.close()
        await server.wait_closed()
        endpoint.close()
        for sig in installed_signals:
            with contextlib.suppress(NotImplementedError):
                loop.remove_signal_handler(sig)


def main() -> None:
    args = build_parser().parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
