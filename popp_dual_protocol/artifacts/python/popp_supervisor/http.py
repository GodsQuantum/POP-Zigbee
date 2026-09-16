from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler
import json


@dataclass
class Metrics:
    ash_retransmits_total: int = 0
    cpc_reconnects_total: int = 0
    radio_resets_total: int = 0
    channel_mismatch: int = 0


def render_healthz(health: dict) -> str:
    return json.dumps(health, sort_keys=True)


def render_metrics(metrics: Metrics) -> str:
    values = {
        "ash_retransmits_total": metrics.ash_retransmits_total,
        "cpc_reconnects_total": metrics.cpc_reconnects_total,
        "radio_resets_total": metrics.radio_resets_total,
        "channel_mismatch": metrics.channel_mismatch,
    }
    return "".join(f"{name} {value}\n" for name, value in values.items())


def build_handler(health_provider, metrics_provider):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/healthz":
                body = render_healthz(health_provider()).encode()
                content_type = "application/json"
                status = 200
            elif self.path == "/metrics":
                body = render_metrics(metrics_provider()).encode()
                content_type = "text/plain; version=0.0.4"
                status = 200
            else:
                body = b"not found\n"
                content_type = "text/plain"
                status = 404
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format, *args):
            return

    return Handler
