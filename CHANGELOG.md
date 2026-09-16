# Changelog

## 0.1.2 — 2026-09-16

- bootstrap a secure persistent Thread dataset on the configured `shared_channel` when a fresh OTBR has none
- automatically synchronize Home Assistant's preferred Thread dataset to Matter Server through the supported Core WebSocket API
- periodically reapply the preferred dataset so Matter Server self-heals after credential loss or rebuild
- expose non-secret Home Assistant/Matter provisioning state in `/healthz`
- require Home Assistant 2026.9+ for the automatic Thread → Matter provisioning path
- validated Matter-over-Thread commissioning with an IKEA ALPSTUGA E2495 through the POP-Zigbee OTBR

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
