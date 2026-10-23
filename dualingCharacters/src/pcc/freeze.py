"""One guard for every confirmatory entry point."""
from pathlib import Path
import json
from .resources import sha256


def verify_freeze(root: Path) -> dict:
    path=root/"configs/freeze.json"
    if not path.exists():raise PermissionError("No frozen confirmatory plan exists")
    frozen=json.loads(path.read_text())
    if not frozen.get("pilot_gates_passed"):raise PermissionError("Pilot gates are incomplete")
    for name,expected in frozen["files"].items():
        if sha256(root/name)!=expected:raise ValueError(f"Frozen input changed: {name}")
    return frozen
