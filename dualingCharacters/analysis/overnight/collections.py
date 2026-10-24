"""Incrementally extend already completed collection/behavior audits."""
from pathlib import Path
from pcc.campaign import jobs,load_overrides,resolve_job
from pcc.freeze import verify_freeze
from pcc.resources import sha256
from supplements.review_001.audit import collection,action_audit
from supplements.review_001.common import write_csv
from .common import ROOT,OUT,CACHE,read,write,utc,log


def main():
    existing=read(ROOT/'supplements/review_001/results/collection_audit.json')
    routes=read(ROOT/'supplements/review_001/results/communication_routing.json')
    old_provenance=read(ROOT/'supplements/review_001/results/cpu_provenance.json')['inputs']
    rows=[];routing=[];coord=[];provenance={};new=[]
    for original in jobs(verify_freeze(ROOT)['plan']):
        if original['command']!='collect':continue
        job=resolve_job(original,load_overrides(ROOT))
        if read(ROOT/'artifacts/campaign_state.json',{}).get('active_job',{}).get('id')==job['id']:continue # wait for final mirror boundary
        run=ROOT/'artifacts/runs'/job['id'];path=run/'status.json'
        if not path.exists() or read(path)['status']!='completed':continue
        meta=read(path);cached=CACHE/'collections'/f'{run.name}.json';checksum=sha256(path)
        if cached.exists():
            item=read(cached);assert item['status_sha256']==checksum
        else:
            previous=next((r for r in existing if r['run_id']==run.name),None)
            if previous and old_provenance[str(path.relative_to(ROOT))]==checksum:
                item={'status_sha256':checksum,'collection':previous,'routing':[r for r in routes if r['run_id']==run.name],
                      'coordination':None,'inputs':{k:v for k,v in old_provenance.items() if '/'+run.name+'/' in k},'reused_prior_validation':True}
            else:
                inputs={str(path.relative_to(ROOT)):checksum};result=collection(run,meta,inputs);action_rows,coordinates=action_audit(run,meta,inputs)
                item={'status_sha256':checksum,'collection':result,'routing':action_rows,'coordination':coordinates,'inputs':inputs,'reused_prior_validation':False}
                new.append(run.name);log(f'Extended collection audit for {run.name}: {result["clean_valid"]} clean and {result["failed_eligible"]} failed eligible windows; temporal severity remains noncausal.')
            write(cached,item)
        rows.append(item['collection']);routing+=item['routing'];provenance[run.name]={'inputs':item['inputs'],'reused_prior_validation':item['reused_prior_validation']}
        if item['coordination']:coord.append({'run_id':run.name,**item['coordination']})
    write(OUT/'collections.json',rows);write(OUT/'routing_counts.json',routing);write_csv(OUT/'routing_counts.csv',routing);write(OUT/'new_coordination.json',coord)
    write(OUT/'collection_provenance.json',{'utc':utc(),'runs':provenance,'new':new,'qualification':'Frozen audit functions; completed eligible training collections only; temporal action/error associations are not causal effects.'})
    print({'new_collections':new,'audited_collections':len(rows)})
    return new


if __name__=='__main__':main()
