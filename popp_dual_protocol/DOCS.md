# POPP Dual Protocol

Host stack for a POP-Zigbee-converted EFR32MG13 adapter.

## Configuration

- **device** — stable `/dev/serial/by-id/...` path of the converted adapter
- **baudrate** — fixed at `460800`
- **shared_channel** — the common Zigbee + Thread 802.15.4 channel
- **cpcd_trace** — verbose CPC frame tracing; leave off unless debugging

## Services

- `:9999` ZHA EZSP/ASH bridge
- `:8081` OpenThread REST API
- `:9100/healthz` readiness JSON
- `:9100/metrics` Prometheus metrics

Read the repository's `docs/HOME_ASSISTANT.md` before migrating an existing Zigbee or Thread network.
