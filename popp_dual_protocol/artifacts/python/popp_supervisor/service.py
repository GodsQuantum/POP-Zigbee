import argparse
from http.server import ThreadingHTTPServer

from .http import Metrics, build_handler
from .runtime import collect_health


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="POPP dual-protocol health service")
    parser.add_argument("--device", required=True)
    parser.add_argument("--shared-channel", type=int, required=True)
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=9100)
    parser.add_argument(
        "--cpc-socket",
        default="/dev/shm/cpcd/cpcd_0/ctrl.cpcd.sock",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    metrics = Metrics()

    def health_provider():
        return collect_health(
            device=args.device,
            cpc_socket=args.cpc_socket,
            shared_channel=args.shared_channel,
            metrics=metrics,
        )
    handler = build_handler(health_provider, lambda: metrics)
    server = ThreadingHTTPServer((args.host, args.port), handler)
    try:
        server.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
