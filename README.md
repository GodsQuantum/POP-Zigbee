# POP-Zigbee

[![Tests](https://github.com/GodsQuantum/POP-Zigbee/actions/workflows/tests.yml/badge.svg)](https://github.com/GodsQuantum/POP-Zigbee/actions/workflows/tests.yml) [![Release](https://img.shields.io/github/v/release/GodsQuantum/POP-Zigbee)](https://github.com/GodsQuantum/POP-Zigbee/releases) [![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE) ⚡

### One EFR32MG13 radio. Zigbee **and** Thread. No deprecated RCP Multi-PAN stack.

[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2026.9%2B-41BDF5?logo=homeassistant&logoColor=white)](https://www.home-assistant.io/)
[![Silicon Labs](https://img.shields.io/badge/GSDK-4.5.1-00AEEF)](https://github.com/SiliconLabs/gecko_sdk)
[![License: GPL v3](https://img.shields.io/badge/code-GPLv3-blue.svg)](LICENSE)
[![Hardware](https://img.shields.io/badge/validated-POPP%20701554-success)](docs/SUPPORTED_HARDWARE.md)

**POP-Zigbee** turns the inexpensive POPP ZB-Stick 701554 / Elelabs MG13 family into a practical dual-purpose radio:

- 🟦 **Zigbee NCP** → ZHA through a CPC↔ASH compatibility bridge
- 🟩 **OpenThread RCP** → OTBR → Matter-over-Thread
- 🛟 guarded flashing + known-good Zigbee rollback path
- 🩺 `/healthz` + Prometheus metrics + channel guard
- 🔁 transactional reset handling so ZHA restarts do not leave the NCP in `StackAlreadyRunning`

## ✅ What has actually been validated

On a physical **POPP ZB-Stick 701554**:

- Elelabs board identity: `ELR023` token / EFR32MG13 family
- Gecko bootloader `1.A.0` @ 115200
- custom GSDK 4.5.1 `zigbee_ncp-ot_rcp-uart` firmware @ CPC 460800
- Zigbee CPC endpoint **5** + Thread CPC endpoint **12** simultaneously
- ZHA/Bellows using `socket://<HA-IP>:9999`
- OTBR Thread **leader** on the same 802.15.4 channel as Zigbee
- repeated Home Assistant Core restarts with automatic CPC reset/reconnect
- CPCd 4.9.1 + OTBR on Home Assistant OS amd64
- recovery path back to a known-good Zigbee-only Elelabs firmware

The tested production baseline is **watchdog OFF**. A watchdog-enabled firmware exists for development but is not the default until longer soak testing is complete.

## 🚀 Quick start

### Option A — clone and convert the radio

```bash
git clone https://github.com/GodsQuantum/POP-Zigbee.git
cd POP-Zigbee
./popp-zigbee doctor --device /dev/serial/by-id/your-stick
./popp-zigbee install --device /dev/serial/by-id/your-stick
```

Or use the bootstrapper after a release is published:

```bash
curl -fsSL https://raw.githubusercontent.com/GodsQuantum/POP-Zigbee/main/install.sh | bash -s -- \
  --device /dev/serial/by-id/your-stick
```

The installer probes the board first, stores pre-flash metadata, verifies the firmware SHA256, flashes through the existing Gecko bootloader, and verifies CPC after reboot. **It refuses unknown hardware by default.**

### Option B — Home Assistant OS

1. Add this repository in **Settings → Apps → Install app → Repositories**:
   `https://github.com/GodsQuantum/POP-Zigbee`
2. Install **POPP Dual Protocol**.
3. Select the stable serial device and one shared 802.15.4 channel.
4. Point ZHA to `socket://<HOME_ASSISTANT_IP>:9999`.
5. Use the OTBR discovery created by the app for Thread/Matter.

The App builds locally in Home Assistant from the pinned host artifacts included in this repository; no private container registry is required.

See [Home Assistant setup](docs/HOME_ASSISTANT.md) for the migration sequence. The radio and Thread must use the **same 802.15.4 channel** on MG13; the app treats a mismatch as unsafe instead of hiding it.

## 🧠 Architecture

```text
POPP / Elelabs EFR32MG13
       │  CPC @ 460800
       ▼
     CPCd 4.9.1
      ├─ endpoint 5  → raw EZSP → ASH/TCP :9999 → ZHA
      └─ endpoint 12 → Spinel/CPC → OTBR → Thread → Matter
```

Unlike the old Home Assistant Silicon Labs Multiprotocol design, Zigbee remains an **NCP on the radio**; there is no host-side `zigbeed`.

## 🔌 Hardware support

| Adapter | Status | Notes |
|---|---|---|
| **POPP ZB-Stick 701554** | ✅ Validated | Physical flash + dual-stack runtime tested |
| Elelabs ELU013 | 🟡 Same board family | Same documented MG13 target/pinout; community validation wanted |
| Elelabs ELR023 | 🟡 Same board family | Same firmware family; community validation wanted |
| POPP ZB-Shield 701561 | 🟡 Same board family | Rebranded ELR023; UART deployment differs from USB stick |
| ELU012 / ELR022 / other EFR32 boards | ❌ Not automatic | Different MCU/pinout; a dedicated profile is required |

See [Supported hardware](docs/SUPPORTED_HARDWARE.md). A CH340 VID/PID is **not** enough to authorize a flash.

## 🧰 CLI

```text
popp-zigbee doctor    probe board + bootloader and refuse unknown hardware
popp-zigbee backup    save pre-flash identity/config metadata
popp-zigbee flash     guarded dual-protocol flash
popp-zigbee verify    verify CPC and optional HA host endpoints
popp-zigbee rollback  restore known-good Zigbee-only firmware
popp-zigbee install   doctor + backup + flash + verify
```

## 🛡️ Safety model

The project treats firmware flashing as a hardware operation, not a convenience button:

- board identity must match a supported profile
- firmware and recovery images are SHA256-pinned
- the existing Gecko bootloader is probed before flashing
- the tested baseline keeps the radio watchdog disabled
- ZHA resets are transactional: CPCd resets the secondary, libcpc reconnects, then ASH sends `RSTACK`
- Thread dataset survives those resets and OTBR reattaches automatically
- `Channel Guard` reports unknown/mismatched Zigbee/Thread channels as **not ready**

If anything goes wrong, read [Recovery](docs/RECOVERY.md) before experimenting.

## ⚠️ One-radio reality

This is still one 2.4 GHz transceiver. It is not equivalent to two independent radios. On MG13, Zigbee and Thread should be kept on the **same 802.15.4 channel**; POP-Zigbee is designed around that constraint.

## 📚 Docs

- [Home Assistant setup](docs/HOME_ASSISTANT.md)
- [Matter / Thread commissioning](docs/COMMISSIONING.md)
- [Supported hardware](docs/SUPPORTED_HARDWARE.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Recovery / rollback](docs/RECOVERY.md)
- [Building from source](docs/DEVELOPMENT.md)
- [Licensing and third-party components](NOTICE.md)

## License

Project-authored source code is GPL-3.0. Firmware and Silicon Labs components are **not relicensed** by this repository; see [NOTICE.md](NOTICE.md) and the applicable upstream licenses.
