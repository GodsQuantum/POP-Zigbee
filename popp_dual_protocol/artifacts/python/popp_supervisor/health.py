from dataclasses import asdict

from .channel_guard import ChannelStatus


def aggregate_health(
    *,
    usb_present: bool,
    cpcd_healthy: bool,
    zigbee_bridge_healthy: bool,
    otbr_healthy: bool,
    channel: ChannelStatus,
) -> dict:
    components = {
        "usb": usb_present,
        "cpcd": cpcd_healthy,
        "zigbee_bridge": zigbee_bridge_healthy,
        "otbr": otbr_healthy,
    }
    return {
        "ready": all(components.values()) and channel.safe,
        "components": components,
        "channel": asdict(channel),
    }
