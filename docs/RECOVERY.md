# Recovery and rollback

The validated POPP 701554 exposes a Gecko bootloader `1.A.0` at 115200 baud. Bootloader entry and return-to-application were tested before the first dual-protocol flash.

## Preferred rollback

Use the CLI:

```bash
./popp-zigbee rollback --device /dev/serial/by-id/...
```

The command:

- downloads the pinned Elelabs ELU013 Zigbee recovery GBL from `zha-ng/EZSP-Firmware`
- verifies SHA256 before use
- enters the existing Gecko bootloader
- flashes the Zigbee-only recovery application
- probes EZSP again after reboot

The recovery image is intentionally not copied into this repository.
## If the application does not answer

Do not repeatedly power-cycle or flash random MG13 images.

1. Stop any process that owns the serial port.
2. Confirm the USB serial device still exists.
3. Probe the Gecko bootloader at 115200.
4. Use the pinned recovery image only after its checksum passes.
5. After rollback, move ZHA back to the physical serial adapter at 115200 if you are abandoning POP-Zigbee.

## What POP-Zigbee does not back up

The Gecko bootloader path used here does not provide a complete raw flash dump. `popp-zigbee backup` therefore saves probe metadata and, when supplied, Home Assistant Zigbee database/config files. The rollback guarantee is based on a known-good upstream application image, not on a byte-for-byte dump of the original flash.

## Never flash the bootloader casually

A bootloader update image may exist upstream, but POP-Zigbee does not update the bootloader during normal installation. The already-working bootloader is part of the recovery path and should be left untouched unless a separately documented recovery procedure requires otherwise.
