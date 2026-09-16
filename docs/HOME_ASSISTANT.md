# Home Assistant OS setup

This is the validated deployment path for a converted POPP 701554 on Home Assistant 2026.9+.

## 1. Add the App repository

In Home Assistant:

**Settings → Apps → Install app → Repositories**

Add:

`https://github.com/GodsQuantum/POP-Zigbee`

Install **POPP Dual Protocol**. Select the stable `/dev/serial/by-id/...` path for the stick and choose one shared 802.15.4 channel. Channel 15 is the validated baseline.

The App exposes:

- `9999/tcp` — EZSP/ASH bridge for ZHA
- `8081/tcp` — OTBR REST API
- `9100/tcp` — `/healthz` and Prometheus `/metrics`

The App should report `ready=true` before moving ZHA.
## 2. Keep Zigbee and Thread on the same channel

MG13 exposes one 802.15.4 transceiver. POP-Zigbee therefore treats channel mismatch as unsafe.

For a fresh ZHA network, pin the channel in `configuration.yaml`:

```yaml
zha:
  zigpy_config:
    network:
      channel: 15
```

Run `ha core check` before restarting Home Assistant.

If you already have a Zigbee network with paired devices, **do not reform it just to match this example**. Plan a coordinated channel migration or use another radio instead.

## 3. Move ZHA to the bridge

Configure the existing ZHA entry to use:

`socket://<HOME_ASSISTANT_IP>:9999`

Baud/flow-control values are irrelevant to the TCP side; the App owns the physical 460800 CPC UART.
## 4. Thread / Matter

On a **fresh POP-Zigbee installation with no Active Dataset**, the App creates a secure OpenThread dataset exactly once, forces the configured `shared_channel`, commits it active and stores it in persistent App data. Home Assistant then discovers the OTBR and imports that dataset into its Thread integration.

If an Active Dataset already exists, POP-Zigbee never replaces it automatically. This protects commissioned Thread devices and migrations from another installation. The bootstrap only ensures the existing network is started again after a restart.

`POPP Dual Protocol` also connects to Home Assistant Core through the supported App WebSocket proxy. Every 60 seconds it reads **only the Home Assistant preferred Thread dataset** and calls the Matter integration's `matter/set_thread`. The dataset itself is never logged or persisted by POP-Zigbee; only a SHA-256 fingerprint is kept for diagnostics. Periodic reapplication lets Matter Server recover automatically if its stored Thread credentials are cleared or rebuilt.

For Matter commissioning, Bluetooth is still supplied by the normal Home Assistant path: the Companion app, a Bluetooth adapter available to Home Assistant, or a supported Bluetooth/ESPHome proxy. POP-Zigbee's EFR32MG13 remains the Zigbee + Thread radio; it is not a Bluetooth adapter.

If commissioning from Android, sync the preferred Thread credentials to the phone in the Home Assistant Companion app before pairing. With a Home Assistant Bluetooth path, direct server-side commissioning can also be used.

See [Matter / Thread commissioning](COMMISSIONING.md) for the end-to-end readiness checklist and troubleshooting sequence.

## 5. Verify

Check:

```bash
curl -fsS http://<HOME_ASSISTANT_IP>:9100/healthz
```

Healthy output must include `ready: true`, all four components true, and `zigbee_channel == thread_channel`.

A Home Assistant Core restart intentionally causes one secondary reset during Bellows startup. The bridge holds the ASH `RSTACK` until CPCd and endpoint 5 are genuinely back. OTBR reconnects endpoint 12 and retains the Thread dataset.

## Known harmless warning

The GSDK 4.5.1 OTBR snapshot uses Avahi. On HAOS host networking, Avahi can warn that another mDNS stack exists. This was left unchanged because replacing the validated GSDK-matched OTBR solely to remove that cosmetic warning would add unnecessary risk.

## Moving the stick to another Home Assistant instance

The dual-protocol firmware is persistent **on the USB stick**, but the Thread Active Operational Dataset is host-managed state. Moving only the stick to a brand-new Home Assistant instance does not carry an existing Thread mesh with it.

- For a genuinely fresh home: install POPP Dual Protocol and let it form a new secure dataset on `shared_channel`.
- To preserve an existing Matter-over-Thread mesh: restore/import the previous Thread dataset or Home Assistant backup before commissioning/reconnecting devices.

Never regenerate the Thread dataset merely to fix a commissioning problem; changing it changes the Thread network credentials.
