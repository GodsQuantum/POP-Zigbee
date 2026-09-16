#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SDK="$ROOT/third_party/gecko_sdk"
CPCD="$ROOT/third_party/cpc-daemon"
OTBR_UP="$SDK/util/third_party/ot-br-posix"
OT_UP="$SDK/util/third_party/openthread"
PLAT="$SDK/protocol/openthread/platform-abstraction/posix"
WORK="${OTBR_WORK:-$ROOT/build/otbr-cpc}"
SRC="$WORK/src"
BUILD="$WORK/build"
INSTALL="$WORK/install"
VENDOR="$WORK/vendor"
CMAKE="${CMAKE_BIN:-cmake}"

rm -rf "$SRC" "$BUILD" "$INSTALL" "$VENDOR"
mkdir -p "$SRC" "$BUILD" "$INSTALL" "$VENDOR"
cp -a "$OTBR_UP"/. "$SRC"/
cp -a "$PLAT"/. "$VENDOR"/
mkdir -p "$SRC/third_party/openthread"
ln -s "$OT_UP" "$SRC/third_party/openthread/repo"

python3 - "$VENDOR/cpc_interface.cpp" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); s=p.read_text(); old="OT_ASSERT(ret == 0);"
assert s.count(old) == 3
p.write_text(s.replace(old, "VerifyOrDie(ret == 0, OT_EXIT_ERROR_ERRNO);"))
PY
"$CMAKE" -S "$SRC" -B "$BUILD" -G 'Unix Makefiles' \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
  -DCMAKE_INSTALL_PREFIX="$INSTALL" \
  -DBUILD_SHARED_LIBS=OFF -DBUILD_TESTING=OFF -DINSTALL_SYSTEMD_UNIT=OFF \
  -DOT_THREAD_VERSION=1.3 \
  -DOT_MULTIPAN_RCP=ON \
  -DOT_POSIX_RCP_HDLC_BUS=ON \
  -DOT_POSIX_RCP_SPI_BUS=OFF \
  -DOT_POSIX_RCP_VENDOR_BUS=ON \
  -DOT_POSIX_CONFIG_RCP_VENDOR_DEPS_PACKAGE="$VENDOR/posix_vendor_rcp.cmake" \
  -DOT_POSIX_CONFIG_RCP_VENDOR_INTERFACE="$VENDOR/cpc_interface.cpp" \
  -DOT_PLATFORM_CONFIG="$VENDOR/openthread-core-silabs-posix-config.h" \
  -DCPCD_SOURCE_DIR="$CPCD" -DENABLE_ENCRYPTION=FALSE \
  -DOTBR_BORDER_ROUTING=ON -DOTBR_REST=ON \
  -DOTBR_DNSSD_DISCOVERY_PROXY=ON -DOTBR_SRP_ADVERTISING_PROXY=ON \
  -DOTBR_INFRA_IF_NAME=eth0 \
  -DOTBR_RADIO_URL='spinel+cpc://cpcd_0?iid=0&iid-list=0'

"$CMAKE" --build "$BUILD" --target otbr-agent -j"$(nproc)"
"$CMAKE" --install "$BUILD"
printf 'OTBR_AGENT=%s\n' "$INSTALL/sbin/otbr-agent"
