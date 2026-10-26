"""Bounded, local evidence helpers; no model work on import."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,csv,gzip
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
ART=ROOT/'artifacts/automated_evaluation_008'
def now():return datetime.now(timezone.utc).isoformat()
def read(p):return json.loads(Path(p).read_text())
def write(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def rank(s):return hashlib.sha256(s.encode()).hexdigest()
def stream(p):
 with (gzip.open if str(p).endswith('.gz') else open)(p,'rt') as f:
  for n,line in enumerate(f,1):
   if line.strip():yield n,json.loads(line)
def csv_write(p,rows):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 if not rows:p.write_text('');return
 with p.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
def freeze(path,files,**meta):
 if Path(path).exists():raise FileExistsError('Preserve earlier freeze')
 write(path,{'frozen_utc':now(),**meta,'files':{str(p.relative_to(ROOT)):sha(p) for p in files}})
def verify(path):
 d=read(path)
 for n,h in d['files'].items():assert sha(ROOT/n)==h,n
 return d
