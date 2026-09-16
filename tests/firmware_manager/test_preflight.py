import hashlib
import json

from popp_firmware.preflight import preflight
from popp_firmware.rollback import rollback_plan


def make_case(tmp_path):
    image = tmp_path / "candidate.gbl"
    image.write_bytes(b"candidate")
    recovery = tmp_path / "recovery.gbl"
    recovery.write_bytes(b"recovery")
    manifest = {
        "target": "EFR32MG13P632F512GM32",
        "variants": {
            "watchdog-on": {
                "path": str(image),
                "sha256": hashlib.sha256(image.read_bytes()).hexdigest(),
            }
        },
    }
    return manifest, image, recovery


def test_preflight_accepts_matching_reversible_case(tmp_path):
    manifest, _, recovery = make_case(tmp_path)
    result = preflight(manifest, "watchdog-on", "EFR32MG13P632F512GM32", True, recovery)
    assert result.ok is True
    assert result.errors == ()


def test_preflight_rejects_wrong_opn(tmp_path):
    manifest, _, recovery = make_case(tmp_path)
    result = preflight(manifest, "watchdog-on", "EFR32MG21A020F1024", True, recovery)
    assert "target-opn-mismatch" in result.errors


def test_preflight_rejects_bad_candidate_hash(tmp_path):
    manifest, image, recovery = make_case(tmp_path)
    image.write_bytes(b"tampered")
    result = preflight(manifest, "watchdog-on", "EFR32MG13P632F512GM32", True, recovery)
    assert "candidate-sha256-mismatch" in result.errors


def test_preflight_rejects_missing_recovery(tmp_path):
    manifest, _, recovery = make_case(tmp_path)
    recovery.unlink()
    result = preflight(manifest, "watchdog-on", "EFR32MG13P632F512GM32", True, recovery)
    assert "recovery-image-missing" in result.errors


def test_preflight_rejects_unreachable_bootloader(tmp_path):
    manifest, _, recovery = make_case(tmp_path)
    result = preflight(manifest, "watchdog-on", "EFR32MG13P632F512GM32", False, recovery)
    assert "bootloader-unreachable" in result.errors


def test_rollback_plan_stops_consumers_before_bootloader():
    plan = rollback_plan("recovery.gbl")
    assert plan.index("stop-otbr") < plan.index("enter-bootloader")
    assert plan.index("stop-bridge") < plan.index("enter-bootloader")
    assert plan.index("flash-recovery:recovery.gbl") > plan.index("enter-bootloader")
    assert plan[-1] == "verify-dual-protocol-health"


def test_preflight_rejects_bad_recovery_hash(tmp_path):
    manifest, _, recovery = make_case(tmp_path)
    result = preflight(
        manifest,
        "watchdog-on",
        "EFR32MG13P632F512GM32",
        True,
        recovery,
        recovery_sha256="0" * 64,
    )
    assert "recovery-sha256-mismatch" in result.errors

def test_split_bootloader_recovery_plan_supports_different_serial_settings():
    from popp_firmware.rollback import split_bootloader_recovery_plan

    plan = split_bootloader_recovery_plan("recovery.gbl")
    assert "enter-bootloader:application-config" in plan
    assert "connect-bootloader:bootloader-config" in plan
    assert plan.index("enter-bootloader:application-config") < plan.index("connect-bootloader:bootloader-config")
    assert plan.index("connect-bootloader:bootloader-config") < plan.index("flash-recovery:recovery.gbl")
