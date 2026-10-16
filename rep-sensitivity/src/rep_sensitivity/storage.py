"""Immutable accepted responses, content hashes and append-only execution journal."""
import gzip
import json
import os
import fcntl
import uuid
from pathlib import Path
from datetime import datetime, timezone
from .schema import canonical, digest


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def immutable_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (canonical(value) + "\n").encode()
    if path.exists():
        if path.read_bytes() != data: raise RuntimeError("Refusing to change immutable artifact: " + str(path))
        return
    temporary=path.with_name('.'+path.name+'.'+uuid.uuid4().hex+'.partial')
    try:
        with temporary.open('xb') as f:
            f.write(data);f.flush();os.fsync(f.fileno())
        try:os.link(temporary,path)  # Atomic publication without overwriting a winner.
        except FileExistsError:
            if path.read_bytes()!=data:raise RuntimeError('Conflicting immutable artifact: '+str(path))
        fsync_directory(path.parent)
    finally:temporary.unlink(missing_ok=True)


def fsync_directory(path):
    fd=os.open(path,os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)


class Ledger:
    def __init__(self, directory):
        self.path = Path(directory)
        (self.path / "calls").mkdir(parents=True, exist_ok=True)
        self._lock=(self.path/".writer.lock").open("a")
        try:
            fcntl.flock(self._lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            self._lock.close()
            raise RuntimeError("Another writer owns this run ledger: "+str(self.path))

    def close(self):
        if not self._lock.closed:
            fcntl.flock(self._lock, fcntl.LOCK_UN)
            self._lock.close()

    def __del__(self):
        if hasattr(self, "_lock"):
            self.close()

    def event(self, kind, **kwargs):
        with (self.path / "events.jsonl").open("a") as f:
            f.write(canonical({"utc": utcnow(), "event": kind, **kwargs}) + "\n")
            f.flush(); os.fsync(f.fileno())

    def key(self, request, settings, trial, stage):
        # Trial includes stochastic repetition. Never cache on prompt alone.
        return digest({"prompt": request, "settings": settings, "trial": trial, "stage": stage})

    def get(self, key):
        p = self.path / "calls" / (key + ".json.gz")
        if p.exists():
            with gzip.open(p, "rt") as f: return json.load(f)
        return None

    def accept(self, key, value):
        if self.get(key) is not None: raise RuntimeError("Duplicate accepted call: " + key)
        path = self.path / "calls" / (key + ".json.gz")
        temp = self.path / "calls" / (key + ".partial")
        # Deterministic gzip timestamps make checksums stable after synchronization.
        with temp.open("wb") as f:
            with gzip.GzipFile(fileobj=f, mode="wb", mtime=0) as z:
                z.write((canonical(value) + "\n").encode())
            f.flush(); os.fsync(f.fileno())
        os.replace(temp, path)
        fsync_directory(path.parent)
        self.event("accepted", request_hash=key, trial_id=value["trial_id"], stage=value["stage"],
                   response_sha256=digest(value["response"]))

    def iter_calls(self):
        for path in sorted((self.path / "calls").glob("*.json.gz")):
            with gzip.open(path, "rt") as f: yield json.load(f)
