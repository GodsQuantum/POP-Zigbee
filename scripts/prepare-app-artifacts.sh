#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP="$ROOT/popp_dual_protocol"
ART="$APP/artifacts"
CPC="$ROOT/build/host-trixie/cpcd/install"
OTBR="$ROOT/build/host-trixie/otbr/install"
CPC_SRC="$ROOT/third_party/cpc-daemon"

rm -rf "$ART"
mkdir -p "$ART/bin" "$ART/lib" "$ART/python"

install -m 0755 "$CPC/bin/cpcd" "$ART/bin/cpcd"
cp -a "$CPC/lib/"libcpc.so* "$ART/lib/"
install -m 0755 "$OTBR/sbin/otbr-agent" "$ART/bin/otbr-agent"
install -m 0755 "$OTBR/sbin/ot-ctl" "$ART/bin/ot-ctl"

cp -a "$CPC_SRC/lib/bindings/python/src/libcpc" "$ART/python/"
cp -a "$ROOT/src/popp_bridge" "$ART/python/"
cp -a "$ROOT/src/popp_supervisor" "$ART/python/"
cp -a "$ROOT/src/popp_firmware" "$ART/python/"
find "$ART/python" -type d -name __pycache__ -prune -exec rm -rf {} +

printf 'cpcd=4.9.1\notbr=%s\n' \
  "$("$OTBR/sbin/otbr-agent" -V)" > "$ART/VERSIONS"
echo "Prepared $ART"
