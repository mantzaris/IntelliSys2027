"""Reproduce with only tracked baseline + intended009files, no original artifacts."""
import os,subprocess,tarfile,shutil,sys
from .common import *
def main():
 repo=ROOT.parent;dest=Path('/tmp/edge009-clean-export');assert not dest.exists(),'Use a fresh export directory; preserve earlier verification'
 dest.mkdir();archive=subprocess.Popen(['git','archive','HEAD'],cwd=repo,stdout=subprocess.PIPE)
 with tarfile.open(fileobj=archive.stdout,mode='r|') as tar:tar.extractall(dest,filter='data')
 assert archive.wait()==0
 names=subprocess.check_output(['git','ls-files','--others','--exclude-standard','dualingCharacters/supplements/generalization_edge_cases_009'],cwd=repo,text=True).splitlines()
 names+=subprocess.check_output(['git','ls-files','dualingCharacters/supplements/generalization_edge_cases_009'],cwd=repo,text=True).splitlines()
 for name in sorted(set(names)):
  source=repo/name;target=dest/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
 clean=dest/'dualingCharacters';newhere=clean/'supplements/generalization_edge_cases_009';assert not (clean/'artifacts').exists();data=dest/'evidence';data.mkdir()
 manifest=read(newhere/'evidence/MANIFEST.json');assert sha(newhere/'evidence'/manifest['archive'])==manifest['sha256']
 with tarfile.open(newhere/'evidence'/manifest['archive'],'r:gz') as tar:tar.extractall(data,filter='data')
 for name,entry in manifest['files'].items():assert sha(data/name)==entry['sha256']
 python=str(ROOT/'.venv/bin/python');env=dict(os.environ,PYTHONPATH='src:.',MPLCONFIGDIR='/tmp/edge009-mpl-clean');commands=[]
 def run(args):
  commands.append(args);subprocess.run([python,*args],cwd=clean,env=env,check=True,timeout=180,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
 for module in ['analysis','report','exposure','trajectory_details','dialogues','counterexamples','replay_analysis','verify']:
  run(['-m','supplements.generalization_edge_cases_009.'+module,'--run-root',str(data/'runs')])
 run(['-m','unittest','discover','-s','supplements/generalization_edge_cases_009/tests','-v'])
 tables=['episodes.json','families.json','contrasts.json','summary.json','behavior_contrasts.json','opportunity_strata.csv','decisive_field_exposure.json','CLARIFICATION_SUMMARY.json','REPLAY_SUMMARY.json']
 for name in tables:assert sha(HERE/'tables'/name)==sha(newhere/'tables'/name),name
 report={'utc':now(),'status':'passed','export_root':str(dest),'original_artifact_directory_available_to_export':False,'committed_archive_files_verified':len(manifest['files']),'numeric_tables_identical':tables,'commands':commands,'local_python_dependencies':'Existing pinned venv executable supplies dependencies; imported study source and all evidence come from clean export. No model cache/GPU/private access required.'};write(HERE/'reports/CLEAN_EXPORT.json',report);print({k:v for k,v in report.items() if k!='commands'})
if __name__=='__main__':main()
