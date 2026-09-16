# Matter / Thread commissioning

This checklist is for Home Assistant installations using POP-Zigbee as the local Thread Border Router and Zigbee coordinator.

## Server-side readiness

Before pairing a Matter-over-Thread device, verify all of the following:

- POPP Dual Protocol reports `/healthz` with `ready=true`.
- Zigbee and Thread use the same 802.15.4 channel.
- OTBR is attached (`leader`, `router`, or `child` as appropriate for the topology).
- Home Assistant contains the `otbr`, `thread`, `matter`, and `zha` config entries.
- The Thread integration has an Active Dataset and marks that dataset as preferred.
- IPv6 is enabled on the Home Assistant LAN interface.
- `_meshcop._udp` advertises the POPP/OpenThread border router on the LAN.
- Matter Server is running and healthy.
- `/healthz` reports `provisioning.matter_thread_synced=true` once Home Assistant has a preferred Thread dataset and Matter is available.

A server can satisfy every item above and commissioning can still fail if the phone does not know the Thread credentials.

## Commissioning paths

POP-Zigbee automatically handles the Thread credential handoff from Home Assistant to Matter Server. You should not need to copy an Active Dataset manually.

### Home Assistant Companion app

For Android commissioning, Bluetooth comes from the phone. Before pairing, use **Settings → Companion app → Troubleshooting → Sync Thread credentials** so the phone knows the Home Assistant preferred Thread network. Then add the device through Home Assistant's normal Matter flow.

### Home Assistant Bluetooth / BLE proxy

If Matter Server has Bluetooth through Home Assistant (local controller or supported proxy), it can commission a new Thread device directly. POP-Zigbee supplies the Thread network; Bluetooth remains a separate transport for initial Matter commissioning.

## If QR commissioning fails

First verify that the device is still in Matter pairing mode and that the Thread credentials were synced to the phone.

On current Home Assistant releases, there have also been reports where QR-code commissioning fails before the request reaches Matter Server while the numeric Matter setup code works. If the QR flow fails without any corresponding commissioning event in Matter Server logs, retry once with the device's numeric setup code before changing the Thread radio or rebuilding the network.

Do not recreate the Thread dataset as an early troubleshooting step. Doing so changes Thread credentials and can strand already commissioned devices. First inspect `/healthz` → `provisioning`, Matter Server logs, and whether the device is in its commissioning window.

## Restart persistence test

A production installation should survive both of these independently:

1. Restart POPP Dual Protocol and confirm the same Thread dataset returns, the same channel remains active, and `/healthz` becomes ready again.
2. Restart Home Assistant Core and confirm the same preferred dataset and the `otbr`, `thread`, `matter`, and `zha` integrations remain present.
3. Confirm `provisioning.matter_thread_synced` returns to `true` automatically; no manual `matter/set_thread` repair should be required.

Compare dataset identity or a local hash; never publish the Active Dataset TLV, Network Key, or PSKc in logs, issues, documentation, or screenshots.

## Radio warnings

Occasional `ChannelAccessFailure` or `NoAck` messages can occur on a busy 2.4 GHz 802.15.4 channel. Do not classify them from isolated log lines. Correlate them with device traffic and commissioning failures.

Persistent CPC endpoint checksum errors, repeated RCP recovery loops, or loss of `ready=true` require investigation before the installation should be considered production-ready.
