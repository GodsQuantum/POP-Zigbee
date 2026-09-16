from popp_supervisor.channel_guard import ChannelStatus, evaluate_channels
from popp_supervisor.health import aggregate_health


def test_same_channel_is_safe():
    status = evaluate_channels(15, 15)
    assert status == ChannelStatus(15, 15, aligned=True, safe=True)


def test_mismatched_channels_are_unsafe():
    status = evaluate_channels(15, 25)
    assert status.aligned is False
    assert status.safe is False


def test_unknown_channel_is_not_production_ready():
    status = evaluate_channels(15, None)
    assert status.aligned is False
    assert status.safe is False


def test_health_requires_components_and_safe_channel():
    status = evaluate_channels(15, 15)
    health = aggregate_health(
        usb_present=True,
        cpcd_healthy=True,
        zigbee_bridge_healthy=True,
        otbr_healthy=True,
        channel=status,
    )
    assert health["ready"] is True
    assert health["channel"]["safe"] is True
