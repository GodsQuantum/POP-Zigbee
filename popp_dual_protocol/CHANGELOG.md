# Changelog

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
