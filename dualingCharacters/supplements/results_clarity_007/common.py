"""Read verified committed inputs without copying bulk evidence or changing prior outputs."""
from pathlib import Path
from functools import lru_cache
import json,csv,hashlib,tarfile
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
PREVIOUS=ROOT/'supplements/evidence_validation_006'
DIALOGUE=ROOT/'supplements/dialogue_interpretation_005'
BEHAVIOR=ROOT/'supplements/behavior_characterization_004'

def read(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,value):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def csv_write(path,rows,fields=None):
 with Path(path).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields or list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
def csv_read(path):return list(csv.DictReader(Path(path).open()))
@lru_cache(maxsize=2)
def members(which='author'):
 manifest=read(PREVIOUS/'evidence'/('AUTHOR_MANIFEST.json' if which=='author' else 'REVIEWER_MANIFEST.json'))
 path=PREVIOUS/manifest['archive'];assert sha(path)==manifest['sha256']
 with tarfile.open(path,'r:gz') as arc:
  result={m.name:arc.extractfile(m).read() for m in arc.getmembers() if m.isfile()}
 assert set(result)==set(manifest['members'])
 for name,data in result.items():assert hashlib.sha256(data).hexdigest()==manifest['members'][name]['sha256'],name
 return result
def source_json(name,which='author'):return json.loads(members(which)[name])
def episodes():return source_json('episodes.json')
def event_selection():return read(PREVIOUS/'EVENT_SELECTION.json')['items']
def now():return datetime.now(timezone.utc).isoformat()
