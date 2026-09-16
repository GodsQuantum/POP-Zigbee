#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
THIRD="$ROOT/third_party"
mkdir -p "$THIRD"

CPC_COMMIT="87f6dbda4eef05e4538589c195099c3daf8f6f6b"
GSDK_TAG="v4.5.1"

if [ ! -d "$THIRD/cpc-daemon/.git" ]; then
  git clone https://github.com/SiliconLabs/cpc-daemon.git "$THIRD/cpc-daemon"
fi
git -C "$THIRD/cpc-daemon" fetch --depth 1 origin "$CPC_COMMIT"
git -C "$THIRD/cpc-daemon" checkout --detach "$CPC_COMMIT"

if [ ! -d "$THIRD/gecko_sdk/.git" ]; then
  git clone --filter=blob:none --no-checkout \
    https://github.com/SiliconLabs/gecko_sdk.git "$THIRD/gecko_sdk"
fi
git -C "$THIRD/gecko_sdk" fetch --depth 1 origin "refs/tags/$GSDK_TAG:refs/tags/$GSDK_TAG"
git -C "$THIRD/gecko_sdk" sparse-checkout init --cone
git -C "$THIRD/gecko_sdk" sparse-checkout set \
  util/third_party/ot-br-posix \
  util/third_party/openthread \
  protocol/openthread/platform-abstraction/posix

git -C "$THIRD/gecko_sdk" checkout --detach "$GSDK_TAG"

printf 'CPCd: %s\n' "$(git -C "$THIRD/cpc-daemon" rev-parse --short=12 HEAD)"
printf 'GSDK: %s\n' "$(git -C "$THIRD/gecko_sdk" describe --tags --exact-match HEAD)"
