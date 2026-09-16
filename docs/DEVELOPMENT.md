# Development

Normal users do **not** need to rebuild CPCd, OTBR or the radio firmware. Release images are published for the validated amd64 Home Assistant OS path.

## Run the Python tests

```bash
git clone https://github.com/GodsQuantum/POP-Zigbee
cd POP-Zigbee
python -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
./scripts/fetch-sources.sh
PYTHONPATH="src:third_party/cpc-daemon/lib/bindings/python/src" pytest -q
```

CPCd is fetched because bridge tests exercise the official Python libcpc binding.

## Rebuild CPCd + CPC-aware OTBR

Requires Podman and an amd64 host:

```bash
./scripts/build-host.sh
```

The build runs inside the Home Assistant Debian Trixie base image to avoid host-GLIBC leakage into HAOS.
## Rebuild the EFR32 firmware

The radio image is built from Silicon Labs GSDK 4.5.1 project `zigbee_ncp-ot_rcp-uart` for target `EFR32MG13P632F512GM32` with:

- USART0 TX `PA0`, RX `PA1`
- 460800 baud, no hardware flow control
- CPC security disabled for the local USB link
- bootloader interface enabled
- watchdog disabled in the validated production baseline

Recreating the GBL requires Silicon Labs tooling (SLC/Simplicity Commander and the supported ARM GCC toolchain) and acceptance of the applicable Silicon Labs license terms. The repository therefore ships the tested object-code GBL plus its SHA256 and manifest instead of silently downloading/provisioning those proprietary build tools.

The production image in `firmware/` is the exact watchdog-off image validated on the physical POPP 701554. The experimental watchdog-on build is intentionally not the default release artifact until it receives an equivalent long-running hardware soak test.

## Release checklist

Before a release: run the full Python suite, validate the firmware SHA256, build/smoke-test the HA App image, run the secret/PII scrub, and verify on hardware that ZHA is connected, `/healthz` is ready, and Thread returns to `leader` after a Home Assistant Core restart.
