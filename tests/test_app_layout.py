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
