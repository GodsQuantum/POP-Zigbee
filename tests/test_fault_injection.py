from pathlib import Path
import hashlib
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from popp_supervisor.channel_guard import evaluate_channels
from popp_supervisor.health import aggregate_health
from popp_supervisor.supervisor import RecoveryAction, RecoveryState, choose_recovery
from popp_firmware.preflight import preflight


def healthy(channel=15):
    return aggregate_health(
        usb_present=True,
        cpcd_healthy=True,
        zigbee_bridge_healthy=True,
        otbr_healthy=True,
        channel=evaluate_channels(15, channel),
    )


def test_bridge_failure_stays_local():
    state = healthy()
    state["components"]["zigbee_bridge"] = False
    assert choose_recovery(state, RecoveryState()) is RecoveryAction.RESTART_BRIDGE


def test_otbr_failure_stays_local():
    state = healthy()
    state["components"]["otbr"] = False
    assert choose_recovery(state, RecoveryState()) is RecoveryAction.RESTART_OTBR


def test_cpc_failure_escalates_only_after_retries():
    state = healthy()
    state["components"]["cpcd"] = False
    assert choose_recovery(state, RecoveryState(cpc_failures=0)) is RecoveryAction.RESTART_CPCD
    assert choose_recovery(state, RecoveryState(cpc_failures=3)) is RecoveryAction.RESET_RADIO


def test_channel_mismatch_is_blocked():
    state = healthy(channel=25)
    assert state["ready"] is False
    assert choose_recovery(state, RecoveryState()) is RecoveryAction.BLOCK_UNSAFE_CHANNEL


def test_tampered_manifest_is_rejected(tmp_path):
    image = tmp_path / "candidate.gbl"
    recovery = tmp_path / "recovery.gbl"
    image.write_bytes(b"candidate")
    recovery.write_bytes(b"recovery")
    manifest = {
        "target": "EFR32MG13P632F512GM32",
        "variants": {
            "watchdog-on": {
                "path": str(image),
                "sha256": "0" * 64,
            }
        },
    }
    result = preflight(
        manifest,
        "watchdog-on",
        "EFR32MG13P632F512GM32",
        True,
        recovery,
        recovery_sha256=hashlib.sha256(recovery.read_bytes()).hexdigest(),
    )
    assert result.ok is False
    assert "candidate-sha256-mismatch" in result.errors
