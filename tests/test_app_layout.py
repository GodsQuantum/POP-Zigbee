from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADDON = ROOT / "popp_dual_protocol"


def test_addon_config_has_required_haos_capabilities():
    config = (ADDON / "config.yaml").read_text()
    assert "arch:\n  - amd64" in config
    assert "host_network: true" in config
    assert "  - NET_ADMIN" in config
    assert "  - IPC_LOCK" in config
    assert "  - /dev/net/tun" in config
    assert "9999/tcp" in config
    assert "9100/tcp" in config


def test_service_dependency_order_is_explicit():
    base = ADDON / "rootfs/etc/s6-overlay/s6-rc.d"
    assert (base / "popp-bridge/dependencies.d/popp-cpcd").exists()
    assert (base / "popp-otbr/dependencies.d/popp-cpcd").exists()
    assert (base / "popp-supervisor/dependencies.d/popp-bridge").exists()
    assert (base / "popp-supervisor/dependencies.d/popp-otbr").exists()


def test_runtime_scripts_and_dockerfile_exist():
    dockerfile = (ADDON / "Dockerfile").read_text()
    assert "amd64-base-debian:trixie" in dockerfile
    assert "COPY rootfs /" in dockerfile
    assert "bellows==1.0.1" in dockerfile
    assert "aiohttp==3.14.3" in dockerfile

    base = ADDON / "rootfs/etc/s6-overlay/s6-rc.d"
    for service in ("popp-cpcd", "popp-bridge", "popp-otbr", "popp-supervisor"):
        run = base / service / "run"
        assert run.exists()
        assert run.read_text().startswith("#!/usr/bin/with-contenv bashio")


def test_user_bundle_contains_all_services():
    contents = ADDON / "rootfs/etc/s6-overlay/s6-rc.d/user/contents.d"
    for service in ("popp-cpcd", "popp-bridge", "popp-otbr", "popp-supervisor"):
        assert (contents / service).exists()


def test_artifact_preparer_is_part_of_build_recipe():
    script = ROOT / "scripts/prepare-app-artifacts.sh"
    assert script.exists()
    text = script.read_text()
    assert "otbr-agent" in text
    assert "cpcd" in text
    assert "libcpc.so" in text

def test_container_healthcheck_requires_full_readiness():
    helper = ADDON / "rootfs/usr/local/bin/popp-healthcheck"
    assert helper.exists()
    dockerfile = (ADDON / "Dockerfile").read_text()
    assert "popp-healthcheck" in dockerfile

def test_runtime_does_not_depend_on_supervisor_api_for_networking():
    otbr_run = (ADDON / "rootfs/etc/s6-overlay/s6-rc.d/popp-otbr/run").read_text()
    assert "bashio::api.supervisor" not in otbr_run
    assert "ip -4 route show default" in otbr_run


def test_bridge_wires_transactional_cpc_reset_service():
    base = ADDON / "rootfs/etc/s6-overlay/s6-rc.d"
    bridge_run = (base / "popp-bridge/run").read_text()
    cpc_finish = (base / "popp-cpcd/finish").read_text()
    assert "--cpcd-service /run/service/popp-cpcd" in bridge_run
    assert "intentional-cpc-reset" in cpc_finish
    assert 'rm -f "$marker"' in cpc_finish
    assert "sleep 3" in cpc_finish


def test_otbr_precreates_and_cleans_firewall_ipsets():
    base = ADDON / "rootfs/etc/s6-overlay/s6-rc.d/popp-otbr"
    run = (base / "run").read_text()
    finish = (base / "finish").read_text()
    for name in (
        "otbr-ingress-deny-src",
        "otbr-ingress-deny-src-swap",
        "otbr-ingress-allow-dst",
        "otbr-ingress-allow-dst-swap",
    ):
        assert f"ipset create -exist {name} hash:net family inet6" in run
        assert name in finish


def test_pinned_runtime_artifacts_are_present_and_hashed():
    import hashlib

    artifacts = ADDON / "artifacts"
    sums = artifacts / "SHA256SUMS"
    assert sums.is_file()
    expected = {
        "artifacts/bin/cpcd",
        "artifacts/bin/otbr-agent",
        "artifacts/bin/ot-ctl",
        "artifacts/lib/libcpc.so.4.9.1",
    }
    seen = set()
    for line in sums.read_text().splitlines():
        digest, rel = line.split(maxsplit=1)
        rel = rel.lstrip(" *")
        target = ADDON / rel
        assert target.is_file(), rel
        assert hashlib.sha256(target.read_bytes()).hexdigest() == digest
        seen.add(rel)
    assert expected <= seen


def test_otbr_discovery_service_registers_with_home_assistant():
    base = ADDON / "rootfs/etc/s6-overlay/s6-rc.d"
    svc = base / "popp-otbr-discovery"
    assert (svc / "type").read_text().strip() == "oneshot"
    assert (svc / "dependencies.d/popp-otbr").exists()
    assert (svc / "up").exists()
    script = ADDON / "rootfs/etc/s6-overlay/scripts/popp-otbr-discovery.sh"
    text = script.read_text()
    assert 'bashio::discovery "otbr"' in text
    assert 'port "^8081"' in text
    assert "http://127.0.0.1:8081/node" in text
    assert "/opt/popp/bin/ot-ctl rcp version" in text
    assert (base / "user/contents.d/popp-otbr-discovery").exists()


def test_thread_bootstrap_runs_before_otbr_discovery():
    base = ADDON / "rootfs/etc/s6-overlay/s6-rc.d"
    bootstrap = base / "popp-thread-bootstrap"
    discovery = base / "popp-otbr-discovery"
    assert (bootstrap / "type").read_text().strip() == "oneshot"
    assert (bootstrap / "dependencies.d/popp-otbr").exists()
    up = bootstrap / "up"
    assert up.read_text().strip() == "/etc/s6-overlay/scripts/popp-thread-bootstrap.sh"
    assert (discovery / "dependencies.d/popp-thread-bootstrap").exists()
    assert (base / "user/contents.d/popp-thread-bootstrap").exists()
    script = ADDON / "rootfs/etc/s6-overlay/scripts/popp-thread-bootstrap.sh"
    text = script.read_text()
    assert text.startswith("#!/usr/bin/with-contenv bashio")
    assert "popp-option shared_channel" in text
    assert "popp_supervisor.thread_bootstrap" in text
    assert "seq 1 60" in text
    assert "sleep 1" in text

def test_home_assistant_sync_service_has_core_api_access():
    config = (ADDON / "config.yaml").read_text()
    assert "homeassistant_api: true" in config
    base = ADDON / "rootfs/etc/s6-overlay/s6-rc.d"
    sync = base / "popp-ha-sync"
    assert (sync / "type").read_text().strip() == "longrun"
    assert (sync / "dependencies.d/popp-thread-bootstrap").exists()
    assert not (sync / "dependencies.d/popp-otbr-discovery").exists()
    assert (sync / "run").exists()
    assert (base / "user/contents.d/popp-ha-sync").exists()
    run = (sync / "run").read_text()
    assert "SUPERVISOR_TOKEN" in run
    assert "popp_supervisor.ha_sync" in run