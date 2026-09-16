# Changelog

## 0.1.1 — 2026-09-16

- register the embedded OTBR with Home Assistant Supervisor discovery
- wait for the OTBR REST API before announcing discovery to avoid startup races
- validated automatic creation of OTBR + Thread integrations and preferred Thread dataset

## 0.1.0 — 2026-09-16

Initial public release.

- validated POPP ZB-Stick 701554 dual Zigbee + Thread firmware
- guarded `doctor / backup / flash / verify / rollback / install` CLI
- Home Assistant OS App with CPCd 4.9.1, CPC-aware OTBR and ZHA ASH/TCP bridge
- transactional Bellows reset handling across CPCd restarts
- shared-channel guard and `/healthz` + Prometheus metrics
- pinned recovery path to known-good Elelabs Zigbee firmware
- repeated Home Assistant Core restart recovery validated on physical hardware
