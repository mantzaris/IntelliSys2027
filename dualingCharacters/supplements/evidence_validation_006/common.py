from pathlib import Path
import json,hashlib,csv,gzip
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
OLD=ROOT/'supplements/dialogue_interpretation_005'
WORK=HERE/'extracted'
def read(p):return json.loads(Path(p).read_text())
def write(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def rank(s):return hashlib.sha256(s.encode()).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def csv_write(p,rows,fields=None):
 with Path(p).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields or list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
def episodes():return read(WORK/'author/episodes.json')
def action(e,op):return next(t for t in e['turns'] if t['action'] and t['action']['opportunity']==op)
