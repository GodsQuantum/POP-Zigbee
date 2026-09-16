from dataclasses import dataclass


@dataclass(frozen=True)
class ChannelStatus:
    zigbee_channel: int | None
    thread_channel: int | None
    aligned: bool
    safe: bool


def evaluate_channels(
    zigbee_channel: int | None,
    thread_channel: int | None,
) -> ChannelStatus:
    known = zigbee_channel is not None and thread_channel is not None
    aligned = bool(known and zigbee_channel == thread_channel)
    return ChannelStatus(
        zigbee_channel=zigbee_channel,
        thread_channel=thread_channel,
        aligned=aligned,
        safe=aligned,
    )
