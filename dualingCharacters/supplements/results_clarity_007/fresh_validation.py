"""Export intended Git files only; deny access to original artifact/cache paths during checks."""
import argparse,os,subprocess,sys,tempfile,shutil
from .common import *
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);args=parser.parse_args();out=Path(args.output)
 if out.exists():raise FileExistsError('Choose a fresh export directory')
 repo=ROOT.parent;out.mkdir(parents=True)
 tracked=subprocess.check_output(['git','ls-files','-z'],cwd=repo).decode().split('\0')
 new=subprocess.check_output(['git','ls-files','--others','--exclude-standard','-z','--',str(HERE.relative_to(repo))],cwd=repo).decode().split('\0')
 paths=sorted(set(p for p in tracked+new if p));initial={}
 for name in paths:
  src=repo/name
  if not src.is_file():continue
  dst=out/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
  if src.is_relative_to(HERE):initial[str(src.relative_to(HERE))]=sha(src)
 dc=out/'dualingCharacters';env=os.environ.copy();env['PYTHONPATH']=str(dc/'src')+os.pathsep+str(dc);env['MPLCONFIGDIR']=str(out/'mpl-cache')
 # Each run is a fresh process with an audit hook installed before any project import.
 guard="""import sys,os,runpy
original=%r
def audit(event,args):
 if event=='open' and args and isinstance(args[0],(str,bytes,os.PathLike)):
  name=os.path.abspath(os.fsdecode(args[0]))
  if name.startswith(original+'/dualingCharacters/artifacts/') or (name.startswith(original+'/dualingCharacters/supplements/') and '/extracted/' in name):
   raise PermissionError('Original artifact/cache access prohibited: '+name)
sys.addaudithook(audit)
"""%str(repo)
 commands=[('006 selected evidence and complete atlas',"runpy.run_module('supplements.evidence_validation_006.reader',run_name='__main__')"),('007 changed products',"runpy.run_module('supplements.results_clarity_007.build',run_name='__main__')"),('007 quotes/forms/selections',"runpy.run_module('supplements.results_clarity_007.verify',run_name='__main__')"),('v2 blinded packet',"from supplements.results_clarity_007.review_package import build; build('supplements/results_clarity_007/extracted/reviewer_v2_final')"),('module origins',"import pcc.characters,supplements.results_clarity_007.common as c; assert str(c.ROOT)==os.getcwd(); assert pcc.characters.__file__.startswith(os.getcwd()); print(c.ROOT,pcc.characters.__file__)")]
 results=[]
 for label,code in commands:
  run=subprocess.run([sys.executable,'-c',guard+code],cwd=dc,env=env,capture_output=True,text=True)
  results.append({'step':label,'exit_code':run.returncode,'stdout':run.stdout[-5000:],'stderr':run.stderr[-2000:]})
  if run.returncode:break
 if all(r['exit_code']==0 for r in results):
  run=subprocess.run(['/usr/bin/python3','supplements/results_clarity_007/pdf_build.py'],cwd=dc,env=env,capture_output=True,text=True);results.append({'step':'PDF regeneration','exit_code':run.returncode,'stdout':run.stdout,'stderr':run.stderr})
 comparable=['AUTHOR_EVENT_ANALYSIS.csv','READER_EDITION.html','READER_EDITION.md','FINDINGS_BRIEF.md','READER_EDITION.pdf','FINDINGS_BRIEF.pdf','tables/MECHANICAL_COUNTS.csv','tables/CHANNELS_AND_CHANGES.csv','tables/CONTRASTS.json','tables/READER_CONTENT.json','tables/READER_QUOTATIONS.json']
 checks={name:sha(dc/'supplements/results_clarity_007'/name)==initial[name] for name in comparable}
 report={'status':'passed' if all(r['exit_code']==0 for r in results) and all(checks.values()) else 'failed','export':str(out),'copied_files':len(paths),'original_artifact_and_cache_access':'blocked by Python audit hook','module_imports':'checked inside clean export','steps':results,'byte_identical_changed_outputs':checks,'scope':'Clean export of tracked plus intended007 files; no original artifacts or cached episodes. Interpreter dependencies reused, not model/data caches.'}
 write(HERE/'reports/FRESH_EXPORT.json',report);print(json.dumps(report,indent=2))
 if report['status']!='passed':raise SystemExit(1)
if __name__=='__main__':main()
