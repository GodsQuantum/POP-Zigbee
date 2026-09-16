from popp_bridge.main import build_parser


def test_cli_defaults_match_ha_zha_bridge_contract():
    args = build_parser().parse_args([])

    assert args.instance == "cpcd_0"
    assert args.host == "0.0.0.0"
    assert args.port == 9999
    assert args.read_timeout == 0.25
    assert args.libcpc is None
    assert args.cpcd_service is None


def test_cli_accepts_explicit_runtime_paths_and_ports():
    args = build_parser().parse_args(
        [
            "--instance", "popp_cpc",
            "--libcpc", "/opt/popp/lib/libcpc.so.3",
            "--host", "127.0.0.1",
            "--port", "19999",
            "--read-timeout", "0.10",
            "--cpcd-service", "/run/service/popp-cpcd",
        ]
    )

    assert args.instance == "popp_cpc"
    assert args.libcpc == "/opt/popp/lib/libcpc.so.3"
    assert args.host == "127.0.0.1"
    assert args.port == 19999
    assert args.read_timeout == 0.10
    assert args.cpcd_service == "/run/service/popp-cpcd"
