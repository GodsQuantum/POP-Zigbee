# Security

POP-Zigbee flashes radio firmware and runs privileged networking components. Treat unexpected flashing behavior, unsafe hardware detection, command injection, path traversal, exposed secrets, or remotely reachable management interfaces as security-sensitive.

Please report security issues privately through GitHub's security advisory feature when available rather than opening a public issue with exploit details.

## Design boundaries

- automatic flash requires a positive supported-hardware probe
- firmware/recovery artifacts are SHA256 pinned
- CPC encryption is disabled only on the local USB transport
- health and OTBR APIs are intended for the trusted Home Assistant host/LAN environment
- the project does not intentionally expose arbitrary shell or firmware-upload endpoints

Do not place ports 9999, 8081 or 9100 directly on the public Internet.
