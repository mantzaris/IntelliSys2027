"""Cache official external data and conference template, without credentials."""
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import urllib.request
from urllib.parse import urljoin
import zipfile

root=Path(__file__).resolve().parents[1]
out=root/"artifacts/public_assets";out.mkdir(parents=True,exist_ok=True)
records=[]


def get(url,name):
    req=urllib.request.Request(url,headers={"User-Agent":"Research-reproducibility-audit/1.0"})
    with urllib.request.urlopen(req,timeout=120) as response:raw=response.read()
    path=out/name;path.write_bytes(raw)
    records.append({"url":url,"path":str(path.relative_to(root)),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)})
    return raw


class Links(HTMLParser):
    def __init__(self):super().__init__();self.links=[];self.href=None;self.text=""
    def handle_starttag(self,tag,attrs):
        if tag=="a":self.href=dict(attrs).get("href");self.text=""
    def handle_data(self,data):
        if self.href:self.text+=data
    def handle_endtag(self,tag):
        if tag=="a" and self.href:self.links.append((self.text.strip(),self.href));self.href=None


try:
    url="https://saiconference.com/IntelliSys/CallforPapers"
    raw=get(url,"intellisys_cfp.html")
    parser=Links();parser.feed(raw.decode())
    latex=[(label,urljoin(url,href)) for label,href in parser.links if "latex" in label.lower()]
    for label,link in latex:
        data=get(link,"conference_template.zip")
        with zipfile.ZipFile(out/"conference_template.zip") as z:
            for member in z.infolist():
                if member.filename.endswith((".cls",".tex",".bst",".txt",".sty")):
                    # Extract safe basenames only; do not execute downloaded code.
                    (out/Path(member.filename).name).write_bytes(z.read(member))
except Exception as exc:
    records.append({"asset":"conference_template","error":str(exc)})

api=json.loads(get("https://huggingface.co/api/datasets/xiaowu0162/longmemeval-cleaned","longmemeval_api.json"))
revision=api["sha"]
get(f"https://huggingface.co/datasets/xiaowu0162/longmemeval-cleaned/resolve/{revision}/README.md","longmemeval_README.md")
get(f"https://huggingface.co/datasets/xiaowu0162/longmemeval-cleaned/resolve/{revision}/longmemeval_s_cleaned.json","longmemeval_s_cleaned.json")
gh=json.loads(get("https://api.github.com/repos/xiaowu0162/LongMemEval/commits/main","longmemeval_github_commit.json"))
commit=gh["sha"]
get(f"https://raw.githubusercontent.com/xiaowu0162/LongMemEval/{commit}/LICENSE","longmemeval_LICENSE")
get(f"https://raw.githubusercontent.com/xiaowu0162/LongMemEval/{commit}/src/evaluation/evaluate_qa.py","longmemeval_evaluate_qa.py")
rows=json.loads((out/"longmemeval_s_cleaned.json").read_text())
# Selection uses identifiers only, never answers or generated model outputs.
selected=sorted(rows,key=lambda r:hashlib.sha256(("pcc-external-v1:"+str(r["question_id"])).encode()).hexdigest())[:50]
selection={"dataset":"xiaowu0162/longmemeval-cleaned","revision":revision,"code_commit":commit,
           "license":"MIT","subset_rule":"50 lowest SHA256(pcc-external-v1:question_id)",
           "question_ids":[r["question_id"] for r in selected]}
(root/"data/manifests/external.json").write_text(json.dumps(selection,indent=2)+"\n")
(out/"assets.json").write_text(json.dumps({"retrieved_utc":datetime.now(timezone.utc).isoformat(),"records":records},indent=2)+"\n")
print(json.dumps({"assets":len(records),"external_items":len(rows),"selected":len(selected),"revision":revision,"code_commit":commit}),flush=True)
