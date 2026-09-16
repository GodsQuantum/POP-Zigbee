# Changelog

## 0.1.2

- form a fresh Thread network on `shared_channel` before OTBR discovery and persist it in app data
- preserve existing Thread datasets while ensuring Thread is started after restarts
- synchronize the preferred Home Assistant Thread dataset to Matter Server every 60 seconds for self-healing
- add `homeassistant_api` access and non-secret provisioning diagnostics to `/healthz`
- raise the minimum Home Assistant version to 2026.9

## 0.1.1

- advertise the embedded OTBR to Home Assistant Core
- wait for REST port 8081 `/node` readiness before discovery
- fixes missing OpenThread Border Router / Thread integration after app startup

## 0.1.0

- CPCd 4.9.1 host stack for GSDK 4.5.1 dual firmware
- ZHA ASH/TCP compatibility bridge on port 9999
- CPC-aware OpenThread Border Router
- transactional CPC reset handling for Bellows startup
- shared-channel readiness guard
- OTBR firewall ipset lifecycle
- health and Prometheus endpoints
