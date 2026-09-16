#!/usr/bin/env bash
set -euo pipefail

REPO="https://github.com/GodsQuantum/POP-Zigbee"
VERSION="${POPP_ZIGBEE_VERSION:-v0.1.0}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd || true)"

if [[ -n "$HERE" && -x "$HERE/popp-zigbee" && -f "$HERE/firmware/popp-elu013-mg13-gsdk4.5.1-dual-460800.gbl" ]]; then
  exec "$HERE/popp-zigbee" install "$@"
fi

command -v curl >/dev/null || { echo "curl is required" >&2; exit 1; }
command -v python3 >/dev/null || { echo "python3 is required" >&2; exit 1; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
curl -fsSL "$REPO/archive/refs/tags/$VERSION.tar.gz" -o "$TMP/popp-zigbee.tar.gz"
tar -xzf "$TMP/popp-zigbee.tar.gz" -C "$TMP" --strip-components=1
chmod +x "$TMP/popp-zigbee"
exec "$TMP/popp-zigbee" install "$@"
