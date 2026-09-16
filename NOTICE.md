# Licensing & third-party notice

POP-Zigbee's project-authored Python, shell and documentation are distributed under GPL-3.0.

The repository and runtime also interact with third-party components under their own licenses. Those components are **not relicensed** by POP-Zigbee.

## Silicon Labs

The EFR32 firmware in `firmware/` is a compiled Licensed Program built from Silicon Labs Gecko SDK 4.5.1 for use on compatible Silicon Labs EFR32MG13 devices. Gecko SDK components are subject to the Silicon Labs Master Software License Agreement (MSLA) unless a file states another license.

CPCd and some Silicon Labs host-side sources are also distributed under the MSLA. The Home Assistant App ships pinned CPCd/libcpc host artifacts for use with the supported Silicon Labs radio; their SHA256 values are recorded in `popp_dual_protocol/artifacts/SHA256SUMS`.

- GSDK license: https://github.com/SiliconLabs/gecko_sdk/blob/gsdk_4.5/License.txt
- MSLA: https://www.silabs.com/about-us/legal/master-software-license-agreement

## Bellows / zigpy

The compatibility bridge subclasses and imports Bellows ASH/EZSP protocol code at runtime. Bellows is GPL-3.0 and remains under its upstream license.

## OpenThread / OTBR

OpenThread and ot-br-posix retain their upstream BSD-style licensing and notices. POP-Zigbee does not claim ownership of those components.

## Recovery firmware

`popp-zigbee rollback` downloads the recovery image from `zha-ng/EZSP-Firmware` and validates its pinned SHA256. The recovery binary is intentionally not duplicated in this repository. Review the upstream repository and license terms before use.

POPP, Elelabs, Silicon Labs, Home Assistant and OpenThread are trademarks or names of their respective owners. This is an independent community project and is not endorsed by those vendors/projects.
