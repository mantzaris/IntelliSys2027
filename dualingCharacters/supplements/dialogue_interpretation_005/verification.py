"""Artifact-dependent checks with explicit missing-prerequisite reporting."""
import copy
import re
from html.parser import HTMLParser
from pcc.environment import make_family
from pcc.characters import cast,apply_action
from pcc.memory import WorkingMemory
from supplements.behavior_characterization_004.common import verify_science
from .common import *
from .freeze import verify
from .extraction import get_value,validate_pair
from .annotations import validate
from .blinding import reviewer_episode,FORBIDDEN_KEYS

class Links(HTMLParser):
    def __init__(self):super().__init__();self.ids=[];self.links=[];self.remote=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.append(a['id'])
        if 'href' in a:self.links.append(a['href'])
        for key in ['src','href']:
            if a.get(key,'').startswith(('http:','https:','//')):self.remote.append(a[key])

def prerequisites():
    required=[CACHE/'episodes.json',CACHE/'selected_records.jsonl.gz',CACHE/'QUOTATIONS.json',HERE/'AI_READINGS.json',HERE/'DIALOGUE_ATLAS.html',CACHE/'human_review/reviewer/items.json']
    missing=[relative(p) for p in required if not p.exists()]
    report={'ready':not missing,'missing':missing,'meaning':'Missing evidence is a prerequisite, not a failed scientific result. Restore the documented evidence bundle and run reproduce.'}
    write(REPORTS/'PREREQUISITES.json',report);return report

def no_private_keys(value):
    if isinstance(value,dict):
        assert not (set(value)&FORBIDDEN_KEYS)
        assert not any(k.endswith(('_role','_locator')) or k=='locator' for k in value)
        for v in value.values():no_private_keys(v)
    elif isinstance(value,list):
        for v in value:no_private_keys(v)

def run():
    verify();verify_science()
    amended=0
    previous=ROOT/'supplements/behavior_characterization_004'
    for path in sorted(previous.glob('AMENDMENT_*_MANIFEST.json')):
        for name,sha in read(path)['files'].items():verified(previous/name,sha);amended+=1
    ready=prerequisites()
    if not ready['ready']:print(ready);return False
    census=read(HERE/'EVIDENCE_CUTOFF.json');protected=[];missing_old=[]
    for name,sha in census['protected_review_files'].items():
        if not (ROOT/name).exists():missing_old.append(name);continue
        verified(ROOT/name,sha);protected.append(name)
    # All selected original records retain one-based source locators and file hashes.
    raw={}
    for _,item in stream(CACHE/'selected_records.jsonl.gz'):
        key=(item['file'],item['record']);assert key not in raw;raw[key]=item
    known={p:sha for b in census['bound_dialogue_runs'].values() for p,sha in b['raw_files'].items()}
    for p,sha in known.items():verified(ROOT/p,sha)
    def check(location,value):
        record=raw[location['file'],location['record']]
        assert record['file_sha256']==location['sha256']==known[location['file']]
        assert get_value(record['value'],location)==value
    quotes=read(CACHE/'QUOTATIONS.json')
    for q in quotes:check(q['locator'],q['text'])
    episodes=read(CACHE/'episodes.json');validate_pair(episodes);memories=0;sources=0;truths=0
    for e in episodes:
        assert e['available'];assert [t['turn'] for t in e['turns']]==list(range(1,17))
        scenario=next(s for s in make_family('train',int(e['family_id'].split('-')[-1]),16) if s.world==e['world'])
        for s in e['source_bank'].values():check(s['locator'],s['text']);sources+=1
        for t in e['turns']:
            assert t['analyst_only_target']==scenario.truth_at(t['turn']).target(scenario.spec);truths+=1
            location=t['defender_observation_locator']
            original_prompt=get_value(raw[location['file'],location['record']]['value'],location)
            assert json.loads(original_prompt)==t['defender_observation']
            assert 'target' not in t['defender_observation'] and 'analyst_only_target' not in t['defender_observation']
            assert t['user']['text']==scenario.messages[t['turn']-1].text
            a=t['action']
            if not a:continue
            check(a['claim_locator'],a['claim']);assert a['claim']==a['generated_claim'][:240]
            original=raw[a['locator']['file'],a['locator']['record']]['value']
            assert a['actor']==original['actor'];assert a['observation']==json.loads(original['prompt'][1]['content'])
            assert 'target' not in a['observation'] and 'analyst_only_target' not in a['observation']
            actors=cast(e['condition'],e['family_id'],e['seed']);actor=next(c for c in actors if c.alias==a['actor'])
            memory=WorkingMemory(**copy.deepcopy(a['memory_before']))
            applied=apply_action(original['generation']['parsed'],actor,actors,memory,e['condition'],6,a['communication_slot'])
            assert applied['applied']==a['applied'];assert memory.public()==a['memory_before_answer'];memories+=1
        assert all(c['queue_matches'] for c in e['inbox_checks'])
    index={e['episode_id']:e for e in episodes};validate(read(HERE/'AI_READINGS.json'),index)
    safe=read(CACHE/'human_review/reviewer/items.json');assert len(safe)==36
    for item in safe:
        no_private_keys(item);assert item==reviewer_episode(index[item['item_id']])
        text=json.dumps(item);assert not re.search(r'\b(Hyde|Rival|Jekyll|C3|C5|A1)\b',text)
    forms=[]
    for n in [1,2]:
        rows=list(csv.DictReader((CACHE/f'human_review/reviewer/rater_{n}.csv').open()))
        assert [r['item_id'] for r in rows]==[e['item_id'] for e in safe]
        forms.append({'rater':n,'blank':not any(v for r in rows for k,v in r.items() if k!='item_id')})
    html_checks=[]
    for p in [HERE/'DIALOGUE_ATLAS.html',CACHE/'human_review/reviewer/REVIEW.html']:
        parser=Links();parser.feed(p.read_text());assert not parser.remote;assert len(parser.ids)==len(set(parser.ids))
        assert all(x=='#' or not x.startswith('#') or x[1:] in parser.ids for x in parser.links)
        html_checks.append({'file':relative(p),'ids':len(parser.ids),'local_links':len(parser.links),'external_resources':0})
    manuscript=(HERE/'MANUSCRIPT_SECTION.md').read_text();assert 1500<=len(manuscript.split())<=2500
    statement_texts=[q['text'] for q in quotes]
    quoted=re.findall('“([^”]+)”',manuscript)
    for q in quoted:assert any(q in text for text in statement_texts),q
    result={'verified_utc':now(),'status':'passed','prior_scientific_files':127+17,'prior_amendment_files':amended,
        'new_scientific_files':len(read(HERE/'SCIENTIFIC_MANIFEST.json')['files']),'protected_old_review_files_verified':len(protected),
        'prior_review_artifacts_missing':missing_old,'quote_entries_exact':len(quotes),'source_entries_exact':sources,
        'temporal_targets_verified':truths,'memory_transitions_reexecuted':memories,'unique_raw_records':len(raw),
        'matched_triplet_readings':16,'review_items':len(safe),'forms':forms,'html':html_checks,
        'manuscript_word_count':len(manuscript.split()),'manuscript_exact_quoted_spans':len(quoted),'new_model_calls':0}
    write(REPORTS/'VERIFICATION.json',result);print(result);return True

if __name__=='__main__':run()
