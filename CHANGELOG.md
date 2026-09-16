# Changelog

## 0.1.0 — 2026-09-16

Initial public release.

- validated POPP ZB-Stick 701554 dual Zigbee + Thread firmware
- guarded `doctor / backup / flash / verify / rollback / install` CLI
- Home Assistant OS App with CPCd 4.9.1, CPC-aware OTBR and ZHA ASH/TCP bridge
- transactional Bellows reset handling across CPCd restarts
- shared-channel guard and `/healthz` + Prometheus metrics
- pinned recovery path to known-good Elelabs Zigbee firmware
- repeated Home Assistant Core restart recovery validated on physical hardware
