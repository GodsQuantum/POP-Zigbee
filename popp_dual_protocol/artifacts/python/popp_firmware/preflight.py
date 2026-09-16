from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path


@dataclass(frozen=True)
class PreflightResult:
    ok: bool
    errors: tuple[str, ...]


def _digest(path: Path) -> str:
    h = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def preflight(
    manifest: dict,
    variant_name: str,
    detected_opn: str,
    bootloader_reachable: bool,
    recovery_path: str | Path,
    recovery_sha256: str | None = None,
) -> PreflightResult:
    errors: list[str] = []
    if detected_opn != manifest.get("target"):
        errors.append("target-opn-mismatch")
    variant = manifest.get("variants", {}).get(variant_name)
    if variant is None:
        errors.append("variant-missing")
    else:
        candidate = Path(variant["path"])
        if not candidate.exists():
            errors.append("candidate-image-missing")
        elif _digest(candidate) != variant.get("sha256"):
            errors.append("candidate-sha256-mismatch")

    recovery = Path(recovery_path)
    if not recovery.exists():
        errors.append("recovery-image-missing")
    elif recovery_sha256 is not None and _digest(recovery) != recovery_sha256:
        errors.append("recovery-sha256-mismatch")

    if not bootloader_reachable:
        errors.append("bootloader-unreachable")

    return PreflightResult(ok=not errors, errors=tuple(errors))
