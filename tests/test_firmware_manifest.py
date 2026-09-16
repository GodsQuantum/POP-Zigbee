import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
MANIFEST = BASE / "firmware/manifest.json"

def test_manifest_matches_validated_production_firmware():
    data = json.loads(MANIFEST.read_text())
    assert data["target"] == "EFR32MG13P632F512GM32"
    assert data["uart"] == {"peripheral":"USART0","tx":"PA0","rx":"PA1","baud":460800,"flow_control":"none"}
    assert data["cpc_security"] == "disabled-local-usb"
    assert data["bootloader_interface"] is True
    prod = data["production"]
    firmware = BASE / prod["path"]
    assert firmware.is_file()
    assert hashlib.sha256(firmware.read_bytes()).hexdigest() == prod["sha256"]
    assert prod["ram_bytes"] < int(prod["ram_limit_bytes"] * 0.90)
    assert prod["watchdog_enabled"] is False
