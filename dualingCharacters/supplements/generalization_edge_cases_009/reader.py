"""Small offline index and printable one-page overview; no external assets."""
import html,re
from .common import *
from .dialogues import STYLE

def inline(s,links=True):
 s=html.escape(s);s=re.sub(r'\*\*(.*?)\*\*',r'<strong>\1</strong>',s);s=re.sub(r'`(.*?)`',r'<code>\1</code>',s)
 return re.sub(r'\[([^]]+)\]\(([^)]+)\)',r'<a href="\2">\1</a>' if links else r'\1 (\2)',s)
def blocks(s,links=True):
 return '\n'.join('<h1>'+inline(p[2:],links)+'</h1>' if p.startswith('# ') else '<p>'+inline(p,links)+'</p>' for p in s.strip().split('\n\n'))
def main():
 overview=(HERE/'OVERVIEW.md').read_text();body=blocks(overview)
 header='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Stage009: fresh contexts and unusual cases</title><style>'+STYLE+'</style>'
 figures=''.join(f'<section><h2>{title}</h2><img alt="{title}" src="figures/{name}.svg"><p>{caption}</p></section>' for name,title,caption in [
 ('task_outcomes','Final decisive-field paired success','16 paired families per condition/backbone; rollout seed17; point counts. Family-paired contrast intervals appear in RESULTS.md. Full-plan success is a separate endpoint.'),
 ('action_channels','Generated API channels','384 allocated opportunities per condition/backbone. Includes rejected and malformed actions. This is not a semantic strategy or deception classification.'),
 ('persistence','Eligible typed-goal repetition','Valid applied direct actions within actor and episode. Ineligible/peer/pass opportunities remain in action-denominator tables but do not contribute a typed direct pair.'),
 ('trajectories','Revision and non-authorizing trajectories','16 conversations per world/condition/backbone. Correctness includes the decisive value and its clarification status. Dashed line: turn12 paired event; dotted line: turn20 resolution in ambiguity cases only. Curves are descriptive repeated observations, not independent turn samples.')])
 (HERE/'INDEX.html').write_text(header+body+'<nav><a href="DIALOGUES.html">Matched dialogues</a><a href="RESULTS.md">Numerical tables</a><a href="EVIDENCE_INDEX.md">Evidence access</a><a href="REPRODUCE.md">Reproduction</a></nav>'+figures+'</html>')
 printstyle='@page{size:A4;margin:13mm}body{font:10.2pt/1.32 Arial,sans-serif;color:#17212b}h1{font-size:18pt;margin:0 0 12px}p{margin:0 0 11px}code{font-size:9pt}strong{font-weight:700}'
 (HERE/'OVERVIEW_PRINT.html').write_text('<!doctype html><meta charset="utf-8"><title>Stage009 overview</title><style>'+printstyle+'</style>'+blocks(overview,False))
if __name__=='__main__':main()
