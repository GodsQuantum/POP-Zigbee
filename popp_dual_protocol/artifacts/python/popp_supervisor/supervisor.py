from dataclasses import dataclass
from enum import Enum


class RecoveryAction(str, Enum):
    NONE = "none"
    WAIT_FOR_USB = "wait_for_usb"
    RESTART_BRIDGE = "restart_bridge"
    RESTART_OTBR = "restart_otbr"
    RESTART_CPCD = "restart_cpcd"
    RESET_RADIO = "reset_radio"
    BLOCK_UNSAFE_CHANNEL = "block_unsafe_channel"


@dataclass(frozen=True)
class RecoveryState:
    bridge_failures: int = 0
    otbr_failures: int = 0
    cpc_failures: int = 0


def choose_recovery(health: dict, state: RecoveryState) -> RecoveryAction:
    components = health["components"]
    if not components["usb"]:
        return RecoveryAction.WAIT_FOR_USB
    if not components["cpcd"]:
        return (
            RecoveryAction.RESET_RADIO
            if state.cpc_failures >= 3
            else RecoveryAction.RESTART_CPCD
        )
    if not components["zigbee_bridge"]:
        return RecoveryAction.RESTART_BRIDGE
    if not components["otbr"]:
        return RecoveryAction.RESTART_OTBR
    if not health["channel"]["safe"]:
        return RecoveryAction.BLOCK_UNSAFE_CHANNEL
    return RecoveryAction.NONE
