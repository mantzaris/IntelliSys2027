from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, gzip
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
ART=ROOT/'artifacts/generalization_edge_cases_009'
def read(p): return json.loads(Path(p).read_text())
def write(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def verify(p):
 d=read(p)
 for n,h in d['files'].items():assert sha(ROOT/n)==h,n
 return d
