import json

from popp_supervisor.channel_guard import evaluate_channels
from popp_supervisor.health import aggregate_health
from popp_supervisor.http import Metrics, render_healthz, render_metrics
from popp_supervisor.supervisor import RecoveryAction, RecoveryState, choose_recovery


def healthy_snapshot():
    return aggregate_health(
        usb_present=True,
        cpcd_healthy=True,
        zigbee_bridge_healthy=True,
        otbr_healthy=True,
        channel=evaluate_channels(15, 15),
    )


def test_bridge_restart_precedes_cpc_or_radio_reset():
    health = healthy_snapshot()
    health["components"]["zigbee_bridge"] = False
    state = RecoveryState(bridge_failures=1)
    assert choose_recovery(health, state) is RecoveryAction.RESTART_BRIDGE


def test_otbr_restart_precedes_cpc_or_radio_reset():
    health = healthy_snapshot()
    health["components"]["otbr"] = False
    state = RecoveryState(otbr_failures=1)
    assert choose_recovery(health, state) is RecoveryAction.RESTART_OTBR


def test_repeated_cpc_failure_can_escalate_to_radio_reset():
    health = healthy_snapshot()
    health["components"]["cpcd"] = False
    state = RecoveryState(cpc_failures=3)
    assert choose_recovery(health, state) is RecoveryAction.RESET_RADIO


def test_healthz_serializes_aggregate_health():
    body = render_healthz(healthy_snapshot())
    payload = json.loads(body)
    assert payload["ready"] is True
    assert payload["channel"]["aligned"] is True


def test_metrics_exports_required_counters():
    metrics = Metrics(
        ash_retransmits_total=3,
        cpc_reconnects_total=2,
        radio_resets_total=1,
        channel_mismatch=0,
    )
    text = render_metrics(metrics)
    assert "ash_retransmits_total 3" in text
    assert "cpc_reconnects_total 2" in text
    assert "radio_resets_total 1" in text
    assert "channel_mismatch 0" in text


def test_http_server_exposes_healthz_and_metrics():
    import threading
    import urllib.request
    from http.server import ThreadingHTTPServer
    from popp_supervisor.http import build_handler

    metrics = Metrics(channel_mismatch=0)
    handler = build_handler(lambda: healthy_snapshot(), lambda: metrics)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        health = urllib.request.urlopen(f"http://{host}:{port}/healthz").read()
        prom = urllib.request.urlopen(f"http://{host}:{port}/metrics").read()
        assert json.loads(health)["ready"] is True
        assert b"channel_mismatch 0" in prom
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

def test_channel_mismatch_is_blocked_not_restarted():
    health = healthy_snapshot()
    health["channel"] = evaluate_channels(15, 25).__dict__
    health["ready"] = False
    assert choose_recovery(health, RecoveryState()) is RecoveryAction.BLOCK_UNSAFE_CHANNEL


def test_provisioning_state_does_not_gate_radio_readiness():
    health = aggregate_health(
        usb_present=True,
        cpcd_healthy=True,
        zigbee_bridge_healthy=True,
        otbr_healthy=True,
        channel=evaluate_channels(15, 15),
        provisioning={
            "state": "waiting_preferred_dataset",
            "ha_api": True,
            "preferred_thread_dataset": False,
            "matter_thread_synced": False,
        },
    )
    assert health["ready"] is True
    assert health["provisioning"]["matter_thread_synced"] is False
