"""Fresh-clone numerical reproduction from committed sufficient outcomes, without weights."""
from collections import defaultdict
from .common import *
from pcc.analysis import paired_success,contrast

def run():
 rows=read(HERE/'inputs/core_summary_outcomes.json');counts=read(HERE/'tables/CORE_COUNTS.json');contrasts=read(HERE/'tables/CORE_CONTRASTS.json');group=defaultdict(list)
 for r in rows:group[r['model'],r['condition']].append(r)
 for c in counts:
  subset=[r for r in group[c['model'],c['condition']] if r['seed']==c['seed']];assert len(subset)==480
  assert sum(paired_success(subset).values())==c['paired_successes'];assert sum(r['success'] for r in subset)==c['conversation_successes']
 for c in contrasts:
  model=c['model'];control=c['comparison'].split('-')[1];seeds=c['matched_seeds']
  result=contrast([r for r in group[model,'C5'] if r['seed'] in seeds],[r for r in group[model,control] if r['seed'] in seeds])
  for k in ['difference','ci95','per_seed']:assert result[k]==c[k],(model,control,k)
 report={'completed_evaluation_cells':len(counts),'contrasts':len(contrasts),'summary_hash':sha(HERE/'inputs/core_summary_outcomes.json'),'status':'passed','scope':'Sufficient-outcome reproduction, not a new validation of original full traces or absent model weights.'};write(HERE/'reports/COMPACT_CORE_VERIFICATION.json',report);print(report)
if __name__=='__main__':run()
