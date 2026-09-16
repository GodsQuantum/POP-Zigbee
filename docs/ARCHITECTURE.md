# Architecture

POP-Zigbee deliberately avoids the deprecated host-side Multi-PAN design.

```text
EFR32MG13
  │
  │ CPC @ 460800
  ▼
CPCd 4.9.1
  ├─ endpoint 5  ─ raw EZSP ─ ASH/TCP bridge ─ :9999 ─ ZHA
  └─ endpoint 12 ─ Spinel/CPC ─ OTBR ─ Thread ─ Matter
```

## Why this layout

The firmware is Silicon Labs GSDK 4.5.1 `zigbee_ncp-ot_rcp-uart`:

- Zigbee stays an NCP on the EFR32.
- OpenThread is exposed as an RCP to the host.
- `zigbeed` is not required.
- Zigbee and Thread use distinct CPC endpoints.
- CPC encryption is disabled only on the local USB transport; Zigbee and Thread network security remain independent.

This gives ZHA a conventional Bellows/EZSP interface while preserving an OpenThread Border Router path for Matter.
## Transactional ZHA reset

Bellows starts by sending an ASH `RST`. A synthetic `RSTACK` is not enough: the NCP must really be reset before Bellows registers endpoints.

The bridge therefore performs:

1. mark an intentional CPC reset
2. stop CPCd through s6
3. let the secondary hard-reset
4. restart CPCd and wait for it to be up
5. restart libcpc and reopen endpoint 5
6. only then send ASH `RSTACK`

OTBR sees the RCP reset, reconnects endpoint 12 and reattaches to the persistent Thread dataset. Repeated Home Assistant Core restarts were validated with ZHA reconnecting and Thread returning to `leader`.

## Channel Guard

A Series-1 MG13 does not become two independent radios. `Channel Guard` therefore reports the host stack as not ready when Zigbee and Thread channels are different or unknown.

The validated installation used channel 15 for both networks.

## Fresh-install Thread bootstrap

The host App owns the persistent OTBR state under `/data/thread`. After `otbr-agent` starts, the one-shot `popp-thread-bootstrap` service checks for an Active Dataset.

- Existing dataset: preserve it byte-for-byte and only ensure `ifconfig up` + `thread start`.
- No dataset: run OpenThread's secure `dataset init new`, set `shared_channel`, commit active, then start Thread.

OTBR discovery is emitted only after this bootstrap completes, so Home Assistant imports a real, channel-aligned network instead of independently creating one on an unrelated default channel.

## Home Assistant → Matter credential sync

`popp-ha-sync` uses the Home Assistant App Core WebSocket proxy (`ws://supervisor/core/websocket`) and `SUPERVISOR_TOKEN`. It lists Home Assistant Thread datasets, selects only the dataset marked preferred, obtains its TLV transiently, and calls `matter/set_thread`.

The TLV is never written to POP-Zigbee state or logs. `/data/ha-sync-state.json` stores only dataset ID, SHA-256 fingerprint and timestamp. The set operation is deliberately repeated every 60 seconds so Matter Server self-heals after a reset/rebuild. `/healthz` exposes only sanitized provisioning state and does not make Matter onboarding a prerequisite for radio readiness.
