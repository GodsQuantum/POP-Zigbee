#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
THIRD="$ROOT/third_party"
OUT="$ROOT/build/host-trixie"
IMAGE="ghcr.io/home-assistant/amd64-base-debian:trixie"

"$ROOT/scripts/fetch-sources.sh"
mkdir -p "$OUT"

podman run --rm --entrypoint /bin/bash \
  -v "$ROOT:$ROOT:Z" -w "$ROOT" "$IMAGE" -lc '
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends \
  build-essential cmake pkg-config python3 \
  libsystemd-dev libavahi-client-dev libavahi-common-dev libdbus-1-dev
rm -rf /var/lib/apt/lists/*

ROOT="'"$ROOT"'"
THIRD="$ROOT/third_party"
OUT="$ROOT/build/host-trixie"
CPC_WORK="$OUT/cpcd"
rm -rf "$CPC_WORK"
mkdir -p "$CPC_WORK/build" "$CPC_WORK/install"
cmake -S "$THIRD/cpc-daemon" -B "$CPC_WORK/build" \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX="$CPC_WORK/install" \
  -DBUILD_TESTING=OFF -DENABLE_ENCRYPTION=FALSE
cmake --build "$CPC_WORK/build" -j"$(nproc)"
cmake --install "$CPC_WORK/build"

OTBR_WORK="$OUT/otbr" CMAKE_BIN=cmake "$ROOT/scripts/build-otbr-cpc.sh"

for f in \
  "$CPC_WORK/install/bin/cpcd" \
  "$OUT/otbr/install/sbin/otbr-agent" \
  "$OUT/otbr/install/sbin/ot-ctl"; do
  max="$(strings "$f" | grep -o "GLIBC_[0-9.]*" | sort -Vu | tail -1)"
  echo "ABI $(basename "$f"): $max"
done
'

"$ROOT/scripts/prepare-app-artifacts.sh"
