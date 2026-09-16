# Home Assistant OS setup

This is the validated deployment path for a converted POPP 701554.

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

If no Thread Active Dataset exists yet, create or import one through Home Assistant/OpenThread and keep it on the same shared channel. The validated runtime used channel 15 and reached Thread role `leader`.

Do not automatically overwrite an existing Active Dataset. Existing Thread credentials may already be used by commissioned Matter devices.

## 5. Verify

Check:

```bash
curl -fsS http://<HOME_ASSISTANT_IP>:9100/healthz
```

Healthy output must include `ready: true`, all four components true, and `zigbee_channel == thread_channel`.

A Home Assistant Core restart intentionally causes one secondary reset during Bellows startup. The bridge holds the ASH `RSTACK` until CPCd and endpoint 5 are genuinely back. OTBR reconnects endpoint 12 and retains the Thread dataset.

## Known harmless warning

The GSDK 4.5.1 OTBR snapshot uses Avahi. On HAOS host networking, Avahi can warn that another mDNS stack exists. This was left unchanged because replacing the validated GSDK-matched OTBR solely to remove that cosmetic warning would add unnecessary risk.
