#!/usr/bin/with-contenv bashio
set -euo pipefail

shared_channel="$(popp-option shared_channel 15)"
bashio::log.info "Ensuring persistent Thread dataset on shared channel ${shared_channel}..."

for _ in $(seq 1 60); do
  if python3 -m popp_supervisor.thread_bootstrap --shared-channel "$shared_channel"; then
    exit 0
  fi
  sleep 1
done

bashio::exit.nok "Thread bootstrap did not become ready within 60 seconds"
