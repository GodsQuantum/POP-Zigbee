from pathlib import Path


def rollback_plan(recovery_image: str | Path) -> list[str]:
    name = Path(recovery_image).name
    return [
        "stop-supervisor",
        "stop-otbr",
        "stop-bridge",
        "stop-cpcd",
        "enter-bootloader",
        f"flash-recovery:{name}",
        "start-cpcd",
        "verify-cpc",
        "start-bridge",
        "start-otbr",
        "verify-dual-protocol-health",
    ]


def split_bootloader_recovery_plan(recovery_image: str | Path) -> list[str]:
    name = Path(recovery_image).name
    return [
        "stop-supervisor",
        "stop-otbr",
        "stop-bridge",
        "stop-cpcd",
        "enter-bootloader:application-config",
        "connect-bootloader:bootloader-config",
        f"flash-recovery:{name}",
        "start-cpcd",
        "verify-cpc",
        "start-bridge",
        "start-otbr",
        "verify-dual-protocol-health",
    ]
