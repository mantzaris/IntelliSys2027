"""Explicit scientific exclusions; these never remove runs from resource totals."""
from pathlib import Path
import json


def exclusions(root: Path) -> dict[str,str]:
    path=root/"configs/run_exclusions.json"
    return json.loads(path.read_text()) if path.exists() else {}
