ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base-debian:trixie
FROM ${BUILD_FROM}
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      avahi-daemon dbus iproute2 ipset iptables \
      libavahi-client3 libavahi-common3 libdbus-1-3 libsystemd0 \
      libstdc++6 netcat-openbsd python3 python3-pip \
 && pip3 install --break-system-packages --no-cache-dir bellows==1.0.1 aiohttp==3.14.3 \
 && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /opt/popp/bin /opt/popp/lib /opt/popp/python /run/popp /etc/iproute2 \
 && echo "88 openthread" >> /etc/iproute2/rt_tables

COPY artifacts/bin/ /opt/popp/bin/
COPY artifacts/lib/ /opt/popp/lib/
COPY artifacts/python/ /opt/popp/python/
COPY artifacts/VERSIONS /opt/popp/VERSIONS
COPY rootfs /

ENV LD_LIBRARY_PATH=/opt/popp/lib \
    PYTHONPATH=/opt/popp/python
RUN chmod +x /opt/popp/bin/* /usr/local/bin/popp-option /usr/local/bin/popp-healthcheck \
 && find /etc/s6-overlay/s6-rc.d -type f -name run -exec chmod +x {} +

HEALTHCHECK --interval=15s --start-period=90s --timeout=5s --retries=3 \
  CMD /usr/local/bin/popp-healthcheck

WORKDIR /
ENTRYPOINT ["/init"]
