from popp_supervisor.http import Metrics
from popp_supervisor.runtime import collect_health, parse_thread_channel


def test_parse_thread_channel():
    assert parse_thread_channel("15\nDone\n") == 15
    assert parse_thread_channel("disabled\nDone\n") is None


def test_collect_health_uses_real_component_probes(tmp_path):
    device = tmp_path / "ttyUSB0"
    cpc_socket = tmp_path / "ctrl.cpcd.sock"
    device.touch()
    cpc_socket.touch()
    metrics = Metrics()

    def probe(host, port):
        return port in {9999, 8081}

    health = collect_health(
        device=device,
        cpc_socket=cpc_socket,
        shared_channel=15,
        metrics=metrics,
        device_probe_fn=lambda path: True,
        tcp_probe_fn=probe,
        thread_channel_fn=lambda: 15,
    )
    assert health["ready"] is True
    assert metrics.channel_mismatch == 0


def test_collect_health_flags_channel_mismatch(tmp_path):
    device = tmp_path / "ttyUSB0"
    cpc_socket = tmp_path / "ctrl.cpcd.sock"
    device.touch()
    cpc_socket.touch()
    metrics = Metrics()
    health = collect_health(
        device=device,
        cpc_socket=cpc_socket,
        shared_channel=15,
        metrics=metrics,
        tcp_probe_fn=lambda host, port: True,
        thread_channel_fn=lambda: 25,
    )
    assert health["ready"] is False
    assert health["channel"]["safe"] is False
    assert metrics.channel_mismatch == 1


def test_service_parser_accepts_device_channel_and_port():
    from popp_supervisor.service import build_parser

    args = build_parser().parse_args(
        ["--device", "/dev/ttyUSB0", "--shared-channel", "15", "--port", "9100"]
    )
    assert args.device == "/dev/ttyUSB0"
    assert args.shared_channel == 15
    assert args.port == 9100


def test_collect_health_requires_a_real_tty(tmp_path):
    fake_device = tmp_path / "not-a-tty"
    fake_device.touch()
    metrics = Metrics()
    health = collect_health(
        device=fake_device,
        cpc_socket=tmp_path / "missing.sock",
        shared_channel=15,
        metrics=metrics,
        tcp_probe_fn=lambda host, port: False,
        thread_channel_fn=lambda: None,
    )
    assert health["components"]["usb"] is False


def test_runtime_uses_packaged_ot_ctl_by_default():
    import inspect
    from popp_supervisor.runtime import read_thread_channel

    default = inspect.signature(read_thread_channel).parameters["ot_ctl"].default
    assert default == "/opt/popp/bin/ot-ctl"


def test_missing_provisioning_status_is_safe_waiting_state(tmp_path):
    from popp_supervisor.runtime import load_provisioning_status

    status = load_provisioning_status(tmp_path / "missing.json")
    assert status == {
        "state": "waiting",
        "ha_api": False,
        "preferred_thread_dataset": False,
        "matter_thread_synced": False,
    }


def test_provisioning_status_whitelists_fields_and_drops_secrets(tmp_path):
    from popp_supervisor.runtime import load_provisioning_status
    import json

    path = tmp_path / "status.json"
    path.write_text(json.dumps({
        "state": "synced",
        "ha_api": True,
        "preferred_thread_dataset": True,
        "matter_thread_synced": True,
        "updated_at": __import__("datetime").datetime.now(__import__("datetime").UTC).isoformat(),
        "last_success": "2026-09-16T20:00:00+00:00",
        "thread_operation_dataset": "SECRET",
    }))
    status = load_provisioning_status(path)
    assert status["state"] == "synced"
    assert status["matter_thread_synced"] is True
    assert "thread_operation_dataset" not in status
    assert "SECRET" not in repr(status)

def test_stale_provisioning_status_expires_false_success(tmp_path):
    from popp_supervisor.runtime import load_provisioning_status
    import json

    path = tmp_path / "status.json"
    path.write_text(json.dumps({
        "state": "synced",
        "ha_api": True,
        "preferred_thread_dataset": True,
        "matter_thread_synced": True,
        "updated_at": "2000-01-01T00:00:00+00:00",
    }))
    status = load_provisioning_status(path)
    assert status == {
        "state": "stale",
        "ha_api": False,
        "preferred_thread_dataset": False,
        "matter_thread_synced": False,
    }
