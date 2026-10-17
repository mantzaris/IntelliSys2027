"""Prospective operational allowance; frozen scientific configurations stay intact."""
import hashlib
import json
from pathlib import Path


ALLOWANCE_RECORD = Path('records/amendments/additional-gpu-allowance-v2.json')
ALLOWANCE_SHA256 = 'de046f823637a439a434b47c79aa488eb06aae05a46e74da9e17b0cee59ac0b9'


def authorized_cap(frozen_cap_seconds=7200, *, path=ALLOWANCE_RECORD,
                   expected_sha256=ALLOWANCE_SHA256):
    raw = Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise RuntimeError('Changed GPU allowance authorization')
    record = json.loads(raw)
    cap = record['cumulative_cap_seconds']
    if (type(cap) is not int or cap <= 0 or
            record['previous_cap_seconds'] != frozen_cap_seconds or
            cap < frozen_cap_seconds or record['scientific_design_changed']):
        raise RuntimeError('Invalid operational allowance amendment')
    return cap
