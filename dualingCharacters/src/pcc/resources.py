"""Exclusive GPU queue, conservative reservation accounting, durable registry."""
from contextlib import AbstractContextManager
from dataclasses import asdict
from pathlib import Path
import fcntl
import hashlib
import json
import os
import subprocess
import time
import tarfile
import threading
import shutil
from .config import RunConfig


def append_json(path: Path, value: dict):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(value,sort_keys=True)+"\n"); f.flush(); os.fsync(f.fileno())


def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()


def used_seconds(registry: Path) -> float:
    if not registry.exists(): return 0.0
    latest={}
    for line in registry.read_text().splitlines():
        row=json.loads(line); latest[row["run_id"]]=row
    # Interrupted/stale reservations retain time up to last heartbeat; runner
    # writes at every generation batch/optimizer step. Never silently zero them.
    return sum(float(r.get("gpu_reserved_seconds",0)) for r in latest.values())


class RunLedger(AbstractContextManager):
    def __init__(self, root: Path, run_id: str, config: RunConfig):
        self.root=root; self.run_id=run_id; self.config=config
        self.registry=root/"run_registry.jsonl"
        self.run_dir=root/"runs"/run_id
        self.tokens_in=0; self.tokens_out=0; self.calls=0; self.train_tokens=0
        self.peak_vram_bytes=0; self.metadata={}; self.previous_seconds=0

    def __enter__(self):
        self.root.mkdir(parents=True,exist_ok=True)
        if shutil.disk_usage(self.root).free < 3*1024**3:
            raise RuntimeError("Less than 3 GiB artifact storage remains; preserve evidence and stop")
        self.lock=(self.root/"gpu.lock").open("a+")
        fcntl.flock(self.lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if self.run_dir.exists():
            raise FileExistsError(f"Run {self.run_id} exists; use a fresh ID or explicit checkpoint resume")
        self.previous_seconds=used_seconds(self.registry)
        if self.previous_seconds >= self.config.active_gpu_hours_ceiling*3600:
            raise RuntimeError("Authorized GPU-hour budget exhausted")
        active=subprocess.run(["nvidia-smi","--query-compute-apps=pid","--format=csv,noheader"],capture_output=True,text=True,check=True).stdout.strip()
        if active: raise RuntimeError(f"GPU is occupied; do not interrupt other jobs (PIDs {active})")
        self.run_dir.mkdir(parents=True)
        self.config.save(self.run_dir/"config.json")
        self.start=time.monotonic(); self.started_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
        self.code_commit=os.environ.get("PCC_CODE_COMMIT","UNRECORDED")
        source_root=Path(__file__).resolve().parents[2]
        source_hashes={str(p.relative_to(source_root)):sha256(p) for p in sorted((source_root/"src").rglob("*.py"))}
        self.metadata["source_hashes"]=source_hashes
        snapshot=self.run_dir/"source_snapshot.tar.gz"
        with tarfile.open(snapshot,"w:gz") as archive:
            for directory in ("src","tests","configs","scripts","data/manifests"):
                for path in sorted((source_root/directory).rglob("*")):
                    if path.is_file() and "__pycache__" not in path.parts:
                        archive.add(path,arcname=str(path.relative_to(source_root)))
            for path in sorted(source_root.glob("requirements*.txt")):
                archive.add(path,arcname=path.name)
            archive.add(source_root/"pyproject.toml",arcname="pyproject.toml")
        self.metadata["source_snapshot_sha256"]=sha256(snapshot)
        self.metadata["process_pid"]=os.getpid()
        if os.environ.get("PCC_SUPERSEDES_JOB"):self.metadata["supersedes_run_id"]=os.environ["PCC_SUPERSEDES_JOB"]
        self.monitor_stop=threading.Event();self.busy_seconds=0.;self.utilization_seconds=0.;self.telemetry_samples=0
        self.monitor=threading.Thread(target=self._sample_gpu,daemon=True);self.monitor.start()
        self.heartbeat("running")
        return self

    def _sample_gpu(self):
        previous=time.monotonic()
        while not self.monitor_stop.wait(5):
            now=time.monotonic();interval=now-previous;previous=now
            try:
                raw=subprocess.run(["nvidia-smi","--query-gpu=utilization.gpu,memory.used,power.draw","--format=csv,noheader,nounits"],capture_output=True,text=True,check=True,timeout=3).stdout.strip().split(",")
                utilization,memory,power=map(float,raw)
                self.busy_seconds+=interval*(utilization>0);self.utilization_seconds+=interval*utilization/100;self.telemetry_samples+=1
                append_json(self.run_dir/"gpu_telemetry.jsonl",{"elapsed_seconds":now-self.start,"interval_seconds":interval,"gpu_utilization_percent":utilization,"resident_vram_mib":memory,"power_watts":power})
            except (ValueError,subprocess.SubprocessError):
                append_json(self.run_dir/"gpu_telemetry.jsonl",{"elapsed_seconds":now-self.start,"sampling_error":True})

    def heartbeat(self,status: str="running"):
        elapsed=time.monotonic()-self.start
        row={"run_id":self.run_id,"status":status,"config":asdict(self.config),"started_utc":self.started_utc,
             "code_commit":self.code_commit,"gpu_reserved_seconds":elapsed,"input_tokens":self.tokens_in,
             "output_tokens":self.tokens_out,"train_tokens":self.train_tokens,"model_calls":self.calls,
             "peak_vram_bytes":self.peak_vram_bytes,"artifact_path":str(self.run_dir),"known_cost_usd":None,
             **self.metadata}
        append_json(self.registry,row)
        (self.run_dir/"status.json").write_text(json.dumps(row,indent=2)+"\n")
        if status=="running" and (elapsed>self.config.max_run_seconds or self.previous_seconds+elapsed>self.config.active_gpu_hours_ceiling*3600):
            raise RuntimeError("GPU time budget reached; stop before starting another operation")

    def __exit__(self,kind,value,tb):
        self.monitor_stop.set();self.monitor.join(timeout=4)
        self.metadata.update(sampled_gpu_busy_seconds=self.busy_seconds,utilization_weighted_seconds=self.utilization_seconds,
                             gpu_telemetry_samples=self.telemetry_samples,telemetry_qualification="5-second samples; approximate activity, not the hard budget. Reservation time governs the ceiling.")
        self.metadata["error"]=str(value) if value else None
        self.heartbeat("failed" if kind else "completed")
        fcntl.flock(self.lock,fcntl.LOCK_UN); self.lock.close()
        return False
