#!/usr/bin/with-contenv bashio
# Send OTBR REST discovery information to Home Assistant Core only after REST is ready.
set -e

ready=0
for _ in $(seq 1 60); do
  if python3 - <<'PY' >/dev/null 2>&1
import urllib.request
with urllib.request.urlopen("http://127.0.0.1:8081/node", timeout=1) as response:
    raise SystemExit(0 if response.status == 200 else 1)
PY
  then
    ready=1
    break
  fi
  sleep 1
done

if [ "$ready" -ne 1 ]; then
  bashio::log.error "OTBR REST API did not become ready on port 8081."
  exit 1
fi

config=$(bashio::var.json \
  host "$(bashio::addon.hostname)" \
  port "^8081" \
  device "$(bashio::config 'device')" \
  firmware "$(/opt/popp/bin/ot-ctl rcp version | head -n 1)" \
)

if bashio::discovery "otbr" "${config}" >/dev/null; then
  bashio::log.info "Successfully sent OTBR discovery information to Home Assistant."
else
  bashio::log.error "OTBR discovery message to Home Assistant failed."
  exit 1
fi
