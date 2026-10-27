"""Reproduce the controlled response interval from compact event records."""
from pathlib import Path
import csv,json
import numpy as np
P=Path(__file__).resolve().parents[1]
def main():
    d=P/'data';rows=list(csv.DictReader((d/'compatibility_event_counts.csv').open()))
    assert len(rows)==256 and len({(r['arm'],r['family_id'],r['world'],r['opportunity']) for r in rows})==256
    summary=json.loads((d/'compatibility_responses.json').read_text());families=sorted({r['family_id'] for r in rows});assert len(families)==16
    for expected in summary:
        counts={arm:sum(r['arm']==arm and r['category']==expected['category'] for r in rows) for arm in ['compatible','incompatible']}
        assert counts['compatible']==expected['compatible_count'] and counts['incompatible']==expected['incompatible_count']
        values=[]
        for f in families:
            a=[r['category']==expected['category'] for r in rows if r['family_id']==f and r['arm']=='incompatible']
            b=[r['category']==expected['category'] for r in rows if r['family_id']==f and r['arm']=='compatible']
            assert len(a)==len(b)==8;values.append(np.mean(a)-np.mean(b))
        x=np.array(values);rng=np.random.default_rng(600017);draw=x[rng.integers(0,16,(10000,16))].mean(1)
        assert np.allclose([x.mean(),*np.quantile(draw,[.025,.975])],[expected['difference_rate'],*expected['family_interval']],rtol=0,atol=1e-12)
    episodes=json.loads((d/'compatibility_episodes.json').read_text());assert len(episodes)==64
    for arm,correct in [('compatible',5),('incompatible',7)]:
        selected=[e for e in episodes if e['arm']==arm];assert len(selected)==32
        assert sum(e['switch_value_correct'] for e in selected)==25
        assert sum(all(e['success'] for e in selected if e['family_id']==f) for f in families)==correct
    report={'reserved_opportunities':256,'families':16,'response_contrasts_reproduced':len(summary),'completed_conversations':64,'paired_successes':[5,7],
      'qualification':'Typed matches and observed plans; no new semantic or causal interpretation.'}
    (P/'.build/controlled_verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
