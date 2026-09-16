# Home Assistant Thread → Matter Autosync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make fresh POP-Zigbee Home Assistant installs form Thread on `shared_channel` and automatically propagate Home Assistant's preferred Thread dataset to Matter Server.

**Architecture:** A one-shot Thread bootstrap runs before OTBR discovery and only creates a dataset when OTBR is blank. A separate long-running Home Assistant sync service uses the Supervisor WebSocket proxy, sends only the preferred dataset to Matter, persists only a fingerprint, and exposes non-secret provisioning state to `/healthz`.

**Tech Stack:** Python 3, aiohttp WebSocket client, s6-overlay services, Home Assistant App/Supervisor API, OpenThread CLI, pytest.

**Spec:** `docs/superpowers/specs/2026-09-16-ha-matter-autosync-design.md`

## Global Constraints

- Do not expose Thread TLVs, Network Keys, PSKc values, or Matter setup credentials in logs, state, tests, docs, or Git history.
- Never overwrite an existing OTBR Active Dataset automatically.
- Never change Home Assistant's preferred Thread network automatically.
- Fresh dataset creation must honor `shared_channel`.
- Existing Zigbee bridge/reset behavior must remain unchanged.
- `/healthz.ready` remains radio/runtime readiness; Matter provisioning is reported separately.

---
### Task 1: Thread bootstrap

**Files:**
- Create: `src/popp_supervisor/thread_bootstrap.py`
- Create: `tests/supervisor/test_thread_bootstrap.py`
- Create: `popp_dual_protocol/rootfs/etc/s6-overlay/s6-rc.d/popp-thread-bootstrap/type`
- Create: `popp_dual_protocol/rootfs/etc/s6-overlay/s6-rc.d/popp-thread-bootstrap/up`
- Create dependency links under `popp-thread-bootstrap/dependencies.d`, `popp-otbr-discovery/dependencies.d`, and `user/contents.d`.

**Interfaces:** `ensure_thread_dataset(ot_ctl, shared_channel) -> BootstrapResult`; result states are `existing`, `created`, or `error` and never contain TLV data.

- [ ] Write tests proving an existing dataset causes no mutation and a blank dataset triggers `dataset init new`, `dataset channel <shared_channel>`, `dataset commit active`, `ifconfig up`, and `thread start`.
- [ ] Run the new tests and confirm they fail because the module does not exist.
- [ ] Implement the minimal bootstrap module and s6 one-shot wrapper.
- [ ] Run bootstrap tests and the existing supervisor tests.
- [ ] Add an app-layout test proving discovery depends on bootstrap.

### Task 2: Home Assistant WebSocket client and Matter sync

**Files:**
- Create: `src/popp_supervisor/ha_sync.py`
- Create: `tests/supervisor/test_ha_sync.py`
- Modify: `popp_dual_protocol/config.yaml`
- Create: `popp_dual_protocol/rootfs/etc/s6-overlay/s6-rc.d/popp-ha-sync/run`
- Create: `popp_dual_protocol/rootfs/etc/s6-overlay/s6-rc.d/popp-ha-sync/type`
- Create user/dependency links for `popp-ha-sync`.
**Interfaces:** `HomeAssistantClient` wraps `ws://supervisor/core/websocket`; `sync_once()` returns a sanitized `SyncOutcome`. `DatasetFingerprintStore` persists only SHA-256 and timestamp.

- [ ] Write tests for WebSocket auth/command framing, selecting only `preferred: true`, no preferred dataset, successful sync, and repeated idempotent resync for Matter self-healing.
- [ ] Run the tests and confirm expected RED failures.
- [ ] Implement the minimal aiohttp-based client using `SUPERVISOR_TOKEN`; add `homeassistant_api: true` to the app manifest.
- [ ] Implement retry/backoff loop and `/data/ha-sync-state.json` fingerprint persistence with atomic writes and mode 0600.
- [ ] Add the s6 longrun service and run focused tests.

### Task 3: Provisioning health

**Files:**
- Modify: `src/popp_supervisor/runtime.py`
- Modify: `src/popp_supervisor/health.py`
- Modify: `tests/supervisor/test_runtime.py`
- Modify: `tests/supervisor/test_supervisor.py`

**Interfaces:** sync service writes `/run/popp/ha-sync-status.json`; health exposes it as `provisioning` but does not gate top-level `ready`.

- [ ] Add failing tests for synced, waiting, stale/missing, and sanitized-error states.
- [ ] Implement status loading with safe defaults and no secret-bearing fields.
- [ ] Verify `/healthz.ready` is unchanged when provisioning is waiting.
- [ ] Run all project tests.

### Task 4: Release metadata and docs

**Files:**
- Modify: `popp_dual_protocol/config.yaml`, `popp_dual_protocol/CHANGELOG.md`, `CHANGELOG.md`, `README.md`, `docs/HOME_ASSISTANT.md`, `docs/COMMISSIONING.md`, `docs/ARCHITECTURE.md`.

- [ ] Bump app version to `0.1.2` and document fresh-install bootstrap + persistent host-managed dataset behavior.
- [ ] Replace the old manual Matter-dataset repair guidance with normal HA commissioning paths and an explicit troubleshooting fallback.
- [ ] Document that moving only the USB stick does not carry Thread credentials; moving an existing Thread mesh requires restoring/importing its dataset.
- [ ] Run secret-pattern scan and docs/config tests.
### Task 5: Live HAOS validation and cleanup

**Live system:** Cloud9 HAOS VM 100; do not reboot the Proxmox host.

- [ ] Build/prepare the app artifacts from the feature tree and install/deploy `0.1.2` to the local HA app repository.
- [ ] Restart only POPP Dual Protocol as required and verify ZHA bridge, OTBR role, channel alignment, and `/healthz` recovery.
- [ ] Verify `popp-ha-sync` authenticates through the Supervisor Core WebSocket proxy without exposing the dataset.
- [ ] Test persistence by removing Matter Server's stored Thread credential through its supported API, then confirm the sync service restores `thread_credentials_set: true` without manual intervention.
- [ ] Restart Home Assistant Core and verify the sync service reconnects and state remains correct.
- [ ] Confirm the commissioned ALPSTUGA is reachable after being powered on; do not treat prior user-initiated power-off as a radio failure.
- [ ] Restore Matter Server to its normal configuration: port 5580 not exposed and temporary external BLE-proxy mode removed unless Home Assistant itself requires/uses it.
- [ ] Stop the temporary Pegasus `matter-ble-proxy`, remove `/tmp/matter-ble-proxy-venv`, and remove other task-only temp files.

### Task 6: Final verification and integration

- [ ] Run `PYTHONPATH=src:third_party/cpc-daemon/lib/bindings/python/src pytest tests -q` in the final feature tree.
- [ ] Verify public firmware and bundled runtime SHA256 manifests.
- [ ] Run `git diff --check`, secret-pattern scans, and inspect `git status`.
- [ ] Review the implementation against this plan and the design spec; fix any Critical/Important findings.
- [ ] Commit the complete change, merge to `main`, rerun the test suite on merged `main`, push `origin/main`, and verify local/main/origin SHAs agree.
- [ ] Remove the temporary worktree/feature branch and ensure the primary checkout is clean.