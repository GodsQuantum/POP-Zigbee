# Supported hardware

POP-Zigbee does **not** flash arbitrary Silicon Labs adapters. A USB VID/PID alone is never treated as proof of compatibility.

## Validated

### POPP ZB-Stick 701554

Validated end to end on physical hardware:

- Elelabs manufacturing token: `ELR023`
- EFR32MG13P family, Series 1
- 512 KiB flash / 64 KiB RAM class
- CH340 USB serial bridge (`1a86:7523`)
- application UART: 115200 before conversion
- Gecko bootloader `1.A.0` at 115200
- dual firmware CPC UART: 460800, no RTS/CTS
- Zigbee CPC endpoint: 5
- Thread/802.15.4 CPC endpoint: 12

This is the profile accepted automatically by the CLI after a positive Elelabs probe.
## Same family, not yet claimed as validated

The following share documented Elelabs/POPP ancestry, but should be treated as **community-validation candidates** until tested end to end with this project:

- Elelabs ELU013
- Elelabs ELR023 as a standalone module
- POPP ZB-Shield 701561

A future profile may enable them automatically once bootloader, UART routing and physical deployment have been independently confirmed.

## Explicitly unsupported by automatic flashing

- ELU012 / ELR022
- MG21/MG24/MG26 adapters
- Sonoff, Nabu Casa, SMLIGHT or other EFR32 products without a dedicated POP-Zigbee profile
- any generic CH340/CH341 serial device

The firmware target, UART pins, bootloader and RF configuration are hardware-specific. Open an issue with probe output if you want to add a profile; do not bypass the guard simply because the MCU family looks similar.
