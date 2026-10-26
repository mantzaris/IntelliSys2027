"""Standalone ReportLab PDF renderer; internal destinations, no workstation URLs.
Run with a Python that has reportlab. Uses only exported JSON, not original traces.
"""
import json,hashlib
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,KeepTogether,Table,TableStyle
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
HERE=Path(__file__).resolve().parent
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
pdfmetrics.registerFont(TTFont('Evidence',FONT))
pdfmetrics.registerFont(TTFont('EvidenceBold','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
styles=getSampleStyleSheet()
for name in ['Normal','BodyText','Title','Heading1','Heading2','Heading3']:
 styles[name].fontName='Evidence';styles[name].textColor=colors.HexColor('#17323a')
styles['Title'].fontSize=22;styles['Title'].leading=27
styles['Heading1'].fontSize=16;styles['Heading1'].leading=20
styles['Heading2'].fontSize=11;styles['Heading2'].leading=13;styles['Heading2'].spaceBefore=7;styles['Heading2'].spaceAfter=4
styles['Normal'].fontSize=8.5;styles['Normal'].leading=11
styles.add(ParagraphStyle('Quote',parent=styles['Normal'],leftIndent=9,rightIndent=5,spaceBefore=2,spaceAfter=3,borderColor=colors.HexColor('#b6c7cb'),borderWidth=.5,borderPadding=3))
styles.add(ParagraphStyle('Small',parent=styles['Normal'],fontSize=7,leading=9,spaceAfter=2))
styles.add(ParagraphStyle('EvidenceCode',parent=styles['Normal'],fontSize=7,leading=9,backColor=colors.HexColor('#f0f4f2'),borderPadding=4,spaceAfter=6))
story=[];registry={};case_refs={}
def para(text,style='Normal',raw=False):
 story.append(Paragraph(text if raw else escape(str(text)),styles[style]))
def ref(loc,case):
 key=json.dumps(loc,sort_keys=True);rid='Q'+hashlib.sha256(key.encode()).hexdigest()[:8]
 registry[rid]=loc;case_refs.setdefault(case,set()).add(rid);return rid
def quotation(text,loc,case):
 rid=ref(loc,case)
 story.append(KeepTogether([Paragraph(escape(text),styles['Quote']),Paragraph('<a href="#source-'+rid+'" color="#075d63">Source '+rid+'</a> · exact quoted text',styles['Small'])]))
def claim(x,label,case):
 if x is None:para(label+': absent from recorded opportunities.','Small');return
 a=x['action']
 if not a:
  para(label+' — answerer turn '+str(x['turn'])+' (structured).','Small');decision(x,case);return
 para(label+' — turn '+str(x['turn'])+', '+a['neutral_speaker']+', opportunity '+str(a['opportunity'])+', API '+a['kind']+'.','Small')
 quotation(a['claim'],a['claim_locator'],case)
 para('Typed slot/value: '+str(a['slot'])+'/'+str(a['value'])+'; cited source '+str(a['source'])+'; applied='+str(a['applied'])+'.'+(' Quotation ends at delivery limit; generated suffix was not delivered.' if a['truncated'] else ''),'Small')
def decision(x,case):
 para(x['answer']['raw'],'EvidenceCode');rid=ref(x['answer']['locator'],case)
 para('<a href="#source-'+rid+'" color="#075d63">Exact structured-output source '+rid+'</a>','Small',True)
def footer(canvas,doc):
 canvas.saveState();canvas.setFont('Evidence',7);canvas.setFillColor(colors.HexColor('#526772'))
 canvas.drawString(40,24,'Evidence validation 006 · casebook v2 · AI interpretations unvalidated')
 canvas.drawRightString(572,24,str(doc.page));canvas.restoreState()

def run():
 data=json.loads((HERE/'tables/EXCHANGE_CONTEXTS.json').read_text())
 para('Recorded exchanges, evidence routes, and following actions','Title')
 para('CASEBOOK V2 · portable internal evidence links','Heading2')
 para('C3 = generic adversarial components. C5 = biography plus explicit motives. A1 = the same motives without biography text.')
 para('These are authored synthetic user scripts, not live human conversations. Each episode has 16 user/answerer turns and 12 intervention opportunities. Components use frozen shared Qwen weights, recorded action history and bounded memory. A dialogue example is not a prevalence estimate. Matched conditions share scripts, but their later states are not counterfactual replays.')
 para('Six original paper selections are retained. DI5-2e4899b66b is an explicitly added unsupported-correction contrast. Quotations are verbatim. Edits are action events; answerer JSON is a structured decision. Analyst truth and AI-assisted readings are separate. No human semantic ratings or causal delivery result is asserted.')
 para('How to read','Heading2')
 para('A is the actual user authority in the internal evidence appendix. B is the recipient’s recorded prior position. C is the selected message or shared-note action. D identifies actual delivery and visibility. E is the first subsequent opportunity; an optional second opportunity clarifies later continuation. F is the following structured answer. Missing or unrelated responses remain visible.')
 para('All blue links stay inside this PDF. The complete chronological transcripts are in companion extracted/author/DIALOGUE_ATLAS.html, keyed by the stable episode IDs printed on every page. Generate that file with the offline reader command in EVIDENCE_INDEX.md. No workstation URL or future website is required.')
 for c in data:
  para('<a href="#case-'+c['case_id']+'" color="#075d63">'+escape(c['case_id']+' — '+c['title'])+'</a>','Small',True)
 story.append(PageBreak())
 for c in data:
  cid=c['case_id']
  para('<a name="case-'+cid+'"/>'+escape(cid+': '+c['title']),'Heading1',True)
  para('Added contrast; not an original paper selection.' if c['added_contrast'] else 'Original preselected paper case.','Small')
  para('Chronological selected exchanges follow. A–F labels identify evidence roles; routine omitted turns remain in the full companion transcript.','Small')
  para('Provisional interpretation','Heading2');para(c['supported']);para('Not established: '+c['not_established'])
  story.append(Spacer(1,10))
  for x in c['cells']:
   para(cid+' / '+x['condition'],'Heading1');para(x['episode_id']+' · '+x['family_id']+' · seed '+str(x['seed'])+' · '+x['world'],'Small');para('; '.join(a['neutral']+' = '+a['alias'] for a in x['actor_key']),'Small')
   para('<a href="#case-'+cid+'" color="#075d63">A. Exact shared user instructions</a> · <a href="#appendix-'+cid+'" color="#075d63">Analyst evidence appendix</a>','Small',True)
   for card in x['timeline']:
    para('Turn '+str(card['turn']),'Heading2')
    para('A. Scripted user, source #'+str(card['user']['index']),'Small');quotation(card['user']['text'],card['user']['locator'],cid)
    z=card['position']
    if z:claim(z,'; '.join(card['labels']),cid)
    if card['route']:
     r=card['route'];para('D. '+r['type']+'; delivered='+str(r['delivered'])+'; observed='+str(r['visible'])+'. '+r['explanation'],'Small')
     payload=r['actual_delivered_payload']
     if isinstance(payload,list):compact=[{k:v for k,v in p.items() if k!='claim'} for p in payload]
     elif isinstance(payload,dict):compact={k:v for k,v in payload.items() if k!='claim'}
     else:compact=payload
     para('Actual recipient fields: '+json.dumps(compact,ensure_ascii=False,separators=(',',':'))+'. The claim field equals the exact C quotation.' if payload else 'No actual recipient payload is recorded.','EvidenceCode')
     a=x['selected']['action'];delta={k:[a['memory_before'][k],a['memory_before_answer'][k]] for k in ['state','evidence'] if a['memory_before'][k]!=a['memory_before_answer'][k]}
     para('Same-turn state/evidence change: '+(json.dumps(delta,ensure_ascii=False) if delta else 'none')+'. Notes changed='+str(a['memory_before']['notes']!=a['memory_before_answer']['notes'])+'.','Small')
    if card['answer'] and z:
     para('F. Following recorded structured decision (not speech)','Small');decision(z,cid)
   para('Companion complete transcript: extracted/author/DIALOGUE_ATLAS.html, episode '+x['episode_id']+'.','Small')
   story.append(Spacer(1,16))
  story.append(PageBreak())
 # One evidence appendix per case; exact source locations and hashes are internal PDF destinations.
 for c in data:
  cid=c['case_id'];para('<a name="appendix-'+cid+'"/>'+escape('Evidence appendix: '+cid),'Heading1',True)
  para('<a href="#case-'+cid+'" color="#075d63">Return to case and actual user instructions</a>','Small',True)
  for x in c['cells']:
   para(x['condition']+' / '+x['episode_id'],'Heading2')
   para('Analyst-only authorized state at selected turn '+str(x['selected']['turn'])+': '+json.dumps(x['selected']['truth'],ensure_ascii=False),'EvidenceCode')
   para('Actual sender-visible source IDs: '+str([s['index'] for s in x['actual_visible_sources']])+'. The complete source text, inbox and memory are in companion HTML at this episode ID. Analyst availability is not actor visibility.','Small')
   source=x['cited_source']
   para('Selected action audit source field: '+str(x['selected']['action']['source'])+'; visible to sender='+str(x['cited_source_visible_to_sender'])+'. This field may be omitted by its delivery route.','Small')
   if source:
    para('Original '+source['author']+' source #'+str(source['index'])+' (structured JSON remains a recorded answer, not speech):','Small');quotation(source['text'],source['locator'],cid)
   else:para('No source record for this reference exists in the selected episode evidence.','Small')
  para('Exact selected-record locators','Heading2')
  for rid in sorted(case_refs[cid]):
   l=registry[rid];field='.'.join(map(str,l['field']))
   if l.get('decoded'):field+='; decoded '+'.'.join(map(str,l['decoded']))
   story.append(KeepTogether([Paragraph('<a name="source-'+rid+'"/>'+escape(rid+' — '+l['file']),styles['Small']),Paragraph(escape('One-based decompressed JSONL record '+str(l['record'])+'; '+field+'. SHA256 of original containing file: '+l['sha256']),styles['Small'])]))
  para('The portable archive includes these exact original records, not the entire original files. Its hash checks establish selected-package identity, not recomputation of omitted whole-file hashes.','Small')
  if c is not data[-1]:story.append(PageBreak())
 doc=SimpleDocTemplate(str(HERE/'CASEBOOK_V2.pdf'),pagesize=(612,792),rightMargin=40,leftMargin=40,topMargin=38,bottomMargin=40,title='Recorded exchanges — portable casebook v2',author='Research author review',pageCompression=1)
 doc.build(story,onFirstPage=footer,onLaterPages=footer)
 print('Wrote CASEBOOK_V2.pdf with internal evidence destinations only.')
if __name__=='__main__':run()
