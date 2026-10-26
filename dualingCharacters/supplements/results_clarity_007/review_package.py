"""Versioned reviewer view; same fixed stimuli, correct answerer/component distinction."""
import argparse,shutil
from html import escape as h
from .common import *
from .ratings_v2 import provenance_expected,FIELDS
from supplements.dialogue_interpretation_005.rendering import document

def detail(label,value):return '<details><summary>'+h(label)+'</summary><pre>'+h(json.dumps(value,ensure_ascii=False,indent=2))+'</pre></details>'
def response(t,route,label):
 if not t:return '<p>'+h(label)+': no recorded opportunity.</p>'
 if route=='answerer':
  return '<h3>'+h(label)+f' · turn {t["turn"]} · Answerer (structured)</h3><pre>'+h(t['defender']['raw'])+'</pre>'+detail('Actual answerer observation',t['defender_observation'])
 a=t['action']
 if not a:return '<p>No component output recorded at this opportunity.</p>'
 return '<h3>'+h(label)+f' · turn {t["turn"]} · '+h(a['actor'])+'</h3><p>API '+h(a['kind'])+'; opportunity '+str(a['opportunity'])+'</p><blockquote>'+h(a['claim'])+'</blockquote>'+detail('Actual component observation',a['observation'])

def render(items):
 body='<h1>Fixed event review · event006-v2</h1><p>Use RUBRIC.md and the new forms. Rate the incoming statement separately from the recipient response. Same 72 events and evidence windows as v1. No AI interpretations or condition key. Stable anonymous speakers; style and routing can still reveal condition.</p><p>Blank is unassessed, not a negative judgment. Secondary recipient readings belong in secondary_response_notes. Answerer-directed notes have structured answerer responses; they are not component-to-component exchanges.</p>'
 body+='<ol>'+''.join('<li><a href="#'+i['item_id']+'">'+i['item_id']+'</a></li>' for i in items)+'</ol>'
 for i in items:
  w=i['window'];t=w['selected'];a=t['action'];m=w['message'];route=(m or {}).get('recipient_type','no_message')
  body+='<section class="case" id="'+i['item_id']+'"><h2>'+i['item_id']+'</h2><p>Selected opportunity '+str(i['opportunity'])+'; recipient type: '+h(route)+'; mechanical status: '+h(w['status'])+'.</p><h3>User authority (analyst context, not a model correction)</h3>'
  for u in w['authority']:body+='<p>Turn '+str(u['turn'])+' / source #'+str(u['user']['index'])+'</p><blockquote>'+h(u['user']['text'])+'</blockquote>'
  body+='<h3>Incoming output · turn '+str(t['turn'])+' · '+h(a['actor'])+'</h3><blockquote>'+h(a['claim'])+'</blockquote>'
  if a['truncated']:body+='<p>Truncated delivered prefix. The longer generated claim was not fully delivered.</p>'+detail('Generated claim before truncation',a['generated_claim'])
  body+=detail('Actual action, typed fields and sender observation',a)+detail('Recorded route/delivery/visibility',m)
  body+=response(w['recipient_previous'],route,'Recipient’s last prior opportunity')
  for j,p in enumerate(w['recipient_followups']):
   body+=response(p,route,'First following opportunity' if j==0 else 'Second following opportunity (context; secondary response notes)')
   if route!='answerer':body+=detail('Following answerer structured output',p['defender']['parsed'])
   body+=detail('Analyst-only authorized state at this turn',p['analyst_only_target'])
  if not w['recipient_followups']:body+='<p>No follow-up recorded. This is not evidence that a message was ignored.</p>'
  body+=detail('Analyst-only authorized state at selected turn',t['analyst_only_target'])+'<p><a href="EPISODES.html#'+i['review_episode_id']+'">Complete episode</a></p></section>'
 return document('Fixed event review v2',body)

def build(target):
 target=Path(target)
 if target.exists():raise FileExistsError('Use a new directory; never overwrite raters’ work')
 target.mkdir(parents=True)
 old=members('reviewer')
 for name in ['items.json','episodes.json','EPISODES.html']:(target/name).write_bytes(old[name])
 (target/'REVIEW.html').write_text(render(source_json('items.json','reviewer')))
 for p in (HERE/'review').iterdir():
  if p.is_file():shutil.copyfile(p,target/p.name)
 (target/'START_HERE.md').write_text('# Independent fixed-event review v2\n\nOpen REVIEW.html offline; read ANNOTATOR_GUIDE.md and RUBRIC.md. Complete one independent rater form. The older episode/window forms are not additional assigned work. All forms are blank. Do not consult the author interpretation package. Use the authored CALIBRATION_V2.md examples before assessment; they are outside the research sample.\n')
 manifest={'version':'event006-v2','prior_stimulus_member_hashes':{n:hashlib.sha256(old[n]).hexdigest() for n in ['items.json','episodes.json','EPISODES.html']},'binding':provenance_expected(),'files':{p.name:sha(p) for p in sorted(target.iterdir())}}
 write(target/'MANIFEST.json',manifest)
 return manifest

def main():
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);args=p.parse_args();build(args.output);print('New blinded packet created. Same 72 events; blank v2 forms; no human assessment.')
if __name__=='__main__':main()
