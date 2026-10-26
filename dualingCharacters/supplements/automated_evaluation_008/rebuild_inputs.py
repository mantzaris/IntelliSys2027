"""Regenerate frozen judge inputs from portable selected episodes, without original mirrors."""
from .common import *
from .sampling import event_input
from .calibration import make_controls
from supplements.results_clarity_007.common import episodes,event_selection

def check_bytes(path,value):
 data=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode();assert hashlib.sha256(data).hexdigest()==sha(path),str(path)

def main():
 selected=json.loads(gzip.decompress((HERE/'inputs/selected_episodes.json.gz').read_bytes()));families=set(read(HERE/'ALLOCATION.json')['family_order']);by={(e['run_id'],e['family_id'],e['world']):e for e in selected}
 expected=[r for r in read(HERE/'inputs/BROAD_SELECTION.json')['items'] if r['family_id'] in families]
 broad=[event_input(by[r['run_id'],r['family_id'],r['world']],r,'broad') for r in expected]
 historical={e['episode_id']:e for e in episodes()};fixed=[event_input(historical[r['episode_id']],r,'fixed72') for r in event_selection()]
 controls=make_controls();check_bytes(HERE/'inputs/calibration.json',controls)
 research=[r for r in controls if r['population']=='synthetic_holdout']+fixed+broad;check_bytes(HERE/'inputs/research.json',research)
 ids=read(HERE/'ALLOCATION.json')['probe_items'];lookup={r['item_id']:r for r in research};probes=[lookup[i] for i in ids];check_bytes(HERE/'inputs/probes.json',probes)
 write(HERE/'reports/PORTABLE_INPUT_REPRODUCTION.json',{'status':'passed','research_inputs':len(research),'broad_events':len(broad),'fixed_events':len(fixed),'synthetic_holdout':80,'probe_events':len(probes),'selected_episodes':len(selected),'original_private_artifact_directory_required':False,'qualification':'Regeneration from packaged selected reconstructed records, not full original archive rehash.'});print('Portable frozen input reconstruction passed')
if __name__=='__main__':main()
