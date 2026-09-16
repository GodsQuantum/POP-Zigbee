# Home Assistant Thread → Matter autosync design

## Goal

A POP-Zigbee-converted EFR32MG13 attached to a fresh Home Assistant OS installation must be usable for Zigbee and Matter-over-Thread without LLM-assisted repair steps.

The radio firmware remains dual-protocol and persistent on the adapter. Thread credentials remain host-managed, matching Home Assistant's architecture: the Active Operational Dataset is not stored on the USB adapter itself.

## Native Home Assistant behavior

Home Assistant 2026.9 can configure an OTBR with no active dataset: its `otbr` config flow creates a secure dataset and enables Thread. It also imports an OTBR dataset into the Thread integration.

However, Home Assistant only constrains the Thread channel to the Zigbee channel for its recognized Silicon Labs multiprotocol URL. POP-Zigbee uses its own OTBR URL, so a blank OTBR can otherwise be created on Home Assistant's default Thread channel instead of the app's `shared_channel`.

Home Assistant Core also exposes admin WebSocket commands `thread/list_datasets`, `thread/get_dataset_tlv`, and `matter/set_thread`. Apps with `homeassistant_api: true` can reach Core through `ws://supervisor/core/websocket` using `SUPERVISOR_TOKEN`.
## Architecture

### 1. Thread bootstrap

Add a one-shot `popp-thread-bootstrap` service between OTBR startup and OTBR discovery.

If OTBR already has an Active Dataset, it does nothing. If OTBR is blank, it generates a secure OpenThread dataset with `dataset init new`, forces the configured `shared_channel`, commits it active, enables the interface, and starts Thread. The dataset then persists in `/data/thread` through the existing OTBR storage mapping.

This makes fresh installs deterministic on the selected shared radio channel and lets Home Assistant discover/import the already-valid dataset instead of creating one on an unrelated default channel.

It never overwrites an existing Active Dataset. Existing-network migrations remain explicit operations.

### 2. Home Assistant → Matter sync

Add a long-running `popp-ha-sync` service. It connects to Home Assistant Core through the documented Supervisor WebSocket proxy, waits for the Thread and Matter APIs, finds the single dataset marked `preferred`, fetches its TLV transiently, and calls `matter/set_thread`.

The TLV is never logged or persisted by POP-Zigbee. Only a SHA-256 fingerprint is retained in `/data/ha-sync-state.json` for diagnostics. The preferred dataset is deliberately resent idempotently on each sync cycle so Matter Server self-heals if its stored Thread credentials are cleared or rebuilt.

The service reconnects after Core restarts and rechecks periodically so a changed preferred dataset is propagated without manual intervention.
### 3. Health semantics

Radio readiness must not depend on Matter being installed yet, otherwise a fresh installation could restart-loop before onboarding finishes. Existing `/healthz.ready` keeps its current radio/runtime meaning.

Add a separate `provisioning` object reporting non-secret state such as `ha_api`, `preferred_thread_dataset`, `matter_thread_synced`, `last_success`, and a sanitized error category. A status file under `/run/popp/` is used for communication between the sync service and health service.

### 4. Matter commissioning

POP-Zigbee does not pretend the EFR32MG13 radio is Bluetooth. Matter BLE commissioning remains Home Assistant's normal path: Companion app Bluetooth, a local HA Bluetooth controller, or an ESPHome/Home Assistant BLE proxy.

When Matter Server has the preferred Thread dataset, adding a new Matter-over-Thread device must no longer require manually copying the dataset into Matter Server.

## Safety and compatibility

- Never print Active Dataset TLVs, Network Keys, PSKc values, Matter setup codes, or derived secrets.
- Never replace an existing OTBR dataset automatically.
- Never select a different Home Assistant preferred Thread network automatically.
- If no preferred dataset exists yet, wait and report that state rather than mutating Home Assistant.
- Preserve ZHA bridge behavior and existing reset transaction logic.
- Keep `shared_channel` as the authoritative channel for a freshly formed POP-Zigbee Thread network.
- Minimum supported Home Assistant remains 2025.7, but autosync capability requires the WebSocket commands available in current HA 2026.9; older Core versions degrade by retrying without breaking Zigbee/OTBR.

## Validation

Unit tests cover bootstrap idempotence, configured channel enforcement, preferred-dataset selection, no-secret logging/state, sync idempotence, reconnect behavior, and health-state rendering. Live validation removes Matter Server's Thread credential, restarts only relevant apps/Core as needed, and verifies POP-Zigbee restores it automatically while ZHA and OTBR remain healthy.