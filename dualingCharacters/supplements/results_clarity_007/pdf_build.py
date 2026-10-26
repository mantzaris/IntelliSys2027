"""Portable text-first PDFs; system Python3+ReportLab, no browser/network dependencies."""
from pathlib import Path
import json,re,html
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,Table,TableStyle,KeepTogether
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab import rl_config
rl_config.invariant=1
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
HERE=Path(__file__).resolve().parent
from prose import tidy
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';BOLD='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
pdfmetrics.registerFont(TTFont('Readable',FONT));pdfmetrics.registerFont(TTFont('ReadableBold',BOLD));pdfmetrics.registerFontFamily('Readable',normal='Readable',bold='ReadableBold',italic='Readable',boldItalic='ReadableBold')
STYLES=getSampleStyleSheet()
for name,size,leading in [('BodyText',10.2,13),('Heading1',17,21),('Heading2',13.5,17),('Heading3',11,14)]:
 STYLES[name].fontName='Readable';STYLES[name].fontSize=size;STYLES[name].leading=leading;STYLES[name].spaceAfter=6
STYLES.add(ParagraphStyle('Quote',fontName='Readable',fontSize=10.1,leading=12.6,leftIndent=9,borderColor=colors.HexColor('#ccd6df'),borderWidth=.5,borderPadding=5,spaceBefore=3,spaceAfter=4))
STYLES.add(ParagraphStyle('Small',fontName='Readable',fontSize=7.8,leading=9.8,spaceAfter=4))
def p(text,style='BodyText'):return Paragraph(html.escape(text if style=='Quote' else tidy(text)),STYLES[style])
def rich(text,style='BodyText'):return Paragraph(text,STYLES[style])
def footer(canvas,doc):
 canvas.saveState();canvas.setFont('Readable',8);canvas.drawString(35,23,'results_clarity_007 · author interpretation; independent semantic validation pending');canvas.drawRightString(560,23,str(doc.page));canvas.restoreState()
def quote(q,short_user=False):
 text=q['text'];omission=''
 if short_user and ' The catalog contains' in text:text=text.split(' The catalog contains')[0];omission=' [Catalog-rule sentence omitted here; exact full source in companion HTML.]'
 return [p(q['label'],'Small'),p(text,'Quote'),rich('<link href="#sources" color="#235570">'+html.escape(q['short_locator'])+'</link>'+html.escape(omission),'Small')]
def build_reader():
 d=json.loads((HERE/'tables/READER_CONTENT.json').read_text());story=[]
 story += [p(d['title'],'Heading1'),p('Short reader edition · 007','Heading2'),p(d['legend']),p(d['selection']),p('All interpretations are AI-assisted and unvalidated. This is an author-facing edition, separate from the blinded human packet. No new model calls or human judgments were obtained.'),p('How to read an exchange','Heading2'),p('A user authority; B recipient’s prior position; C incoming statement; D actual delivery; E first following opportunity; F second follow-up where needed; G answerer’s structured decision; H observation and competing readings. Turn numbers show chronology. Routine intervening turns are omitted, never invented. JSON is a plan, not speech.'),p('Four layers to keep separate','Heading2')]
 for title,text in [('API','The emitted kind and typed slot/value are mechanical labels.'),('Proposition','The words may recommend an option, claim approval, criticize a peer, or combine these.'),('Payload','The route determines which fields and source references reach a recipient.'),('Response','The next action or structured plan may repeat, change, or address another issue. Delivery is not persuasion.')]:story += [p(title+': '+text)]
 story += [p('Scope and prior outcomes','Heading2'),p('The broader mechanical comparison uses150 unique paired families repeated across three generator seeds. The short illustrations come from the locked48-episode evidence package. Trained C5 paired success trails C3 at all three completed matched Qwen seeds in the retained context table. No task advantage, semantic prevalence, rivalry or causal message influence is claimed.'),p('Full context','Heading2'),p('The unchanged62-page CASEBOOK_V2.pdf and48-episode atlas in evidence_validation_006 remain evidence appendices. This PDF uses internal source destinations, never machine-local file URLs. Companion READER_EDITION.html provides expandable matched trajectories and relative full-context links after the documented offline extraction command.'),PageBreak()]
 for g in d['groups']:
  c=next(c for c in g['cells'] if c['condition']==g['primary']);story+=[p(g['id']+' — '+g['title'],'Heading2'),p(c['condition']+' · '+c['episode_id']+' · '+c['family']+' / seed '+str(c['seed'])+' / '+c['world'],'Small'),p('; '.join(a['neutral']+' = '+a['alias'] for a in c['alias_map']),'Small')]
  for q in c['authorization']:
   if (g['id']=='DI5-e743bcb1a6' and 'source #15' in q['label']) or (g['id']=='DI5-adc5b43b95' and 'source #11' in q['label']) or (g['id']=='DI5-2e4899b66b' and 'source #15' in q['label']):
    continue # Additional different-field user revision retained in full HTML, not silently shortened inside quote.
   story+=quote(q,True)
  for j,q in enumerate(c['extra']):
   if j and q['text']==c['extra'][j-1]['text']:
    story += [p(q['label']+' — the exact full sentence immediately above is repeated; this is an analyst annotation, not additional dialogue.','Small'),rich('<link href="#sources">'+html.escape(q['short_locator'])+'</link>','Small')]
   else:story+=quote(q)
  if c['prior']:story+=quote(c['prior'])
  else:story+=[p('B. No recorded prior recipient opportunity.')]
  story+=quote(c['selected'])
  if c['truncated']:story+=[p('Exact240-character delivered prefix above; generated suffix was not delivered.','Small')]
  route=c['route'];story+=[p('D. '+route['type']+'; delivered='+str(route['delivered'])+'; actually visible='+str(route['visible'])+'. '+('Separate numeric source is retained in the peer inbox.' if route['type']=='component' else 'Shared note omits the separate numeric source.'),'Small')]
  for q in c['followups'][:(2 if g['id']=='DI5-ceecfe5fb4' else 1)]:story+=quote(q)
  if len(c['followups'])>1 and g['id']!='DI5-ceecfe5fb4':story+=[p('F. Second follow-up retained separately in companion HTML; not substituted for the first.','Small')]
  z=c['answer_turns'][-1 if g['id']=='DI5-ceecfe5fb4' else 1];story+=[p('G. Answerer turn '+str(z['turn'])+' — exact parsed plan field (other fields in full trace):','Small'),p(json.dumps(z['parsed'].get('plan'),ensure_ascii=False),'Quote')]
  story+=[p('Matched context (same script/schedule; different generated histories)','Heading3')]
  for other in g['cells']:
   if other['condition']==c['condition']:continue
   q=other['selected'];story+=[p(other['condition']+' · '+q['label'],'Small'),p(q['text'],'Quote'),rich('<link href="#sources">'+html.escape(q['short_locator'])+'</link>','Small')]
  # Detailed alternatives remain in HTML; concise reading retains both evidence and limit.
  story+=[p('H. '+g['observation']),p(g['interpretation'] if g['id']=='DI5-a4c89ffad4' else g['interpretation'].split('. ')[0]+'.'),p('Limit: '+g['alternative'].split('. ')[0]+'. Full reading and omitted different-field user context are in companion HTML.'),PageBreak()]
 story+=[rich('<a name="sources"/>Source and reproduction appendix','Heading1'),p('Quoted text maps to original selected records in the committed006 author archive. S-keys plus record and field locators identify every displayed quote. Full hashes below identify the original files; verifying selected records does not verify omitted full-archive bytes.'),p('Read full matched context in companion READER_EDITION.html. Its links use relative paths. The complete prior atlas is evidence_validation_006/extracted/author/DIALOGUE_ATLAS.html, generated by the documented006 reader command. Keep the two supplement directories together when relocating.'),p('Selected source files','Heading2')]
 for s in d['sources']:story +=[p(s['id']+' · '+s['file'],'Small'),p('SHA256 '+s['sha256'],'Small')]
 SimpleDocTemplate(str(HERE/'READER_EDITION.pdf'),pagesize=(595.28,841.89),leftMargin=35,rightMargin=35,topMargin=32,bottomMargin=40).build(story,onFirstPage=footer,onLaterPages=footer)

def md_blocks(text,small=False):
 styles=STYLES;out=[];lines=text.splitlines();i=0
 while i<len(lines):
  line=lines[i].strip();i+=1
  if not line:continue
  if line.startswith('|'):
   table=[line]
   while i<len(lines) and lines[i].strip().startswith('|'):table.append(lines[i].strip());i+=1
   data=[]
   for row in table:
    if re.match(r'^\|[-: |]+\|$',row):continue
    data.append([p(x.strip(),'Small') for x in row.strip('|').split('|')])
   t=Table(data,colWidths=[525/len(data[0])]*len(data[0]),hAlign='LEFT');t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),.5,colors.grey),('BOTTOMPADDING',(0,0),(-1,-1),2),('TOPPADDING',(0,0),(-1,-1),2)]));out+=[t,Spacer(1,5)];continue
  level=len(line)-len(line.lstrip('#'))
  if level:out.append(p(line[level:].strip(),'Heading1' if level==1 else 'Heading3'));continue
  line=re.sub(r'\*\*(.*?)\*\*',r'<b>\1</b>',html.escape(line));out.append(rich(line,'Small' if small else 'BodyText'))
 return out

def build_brief():
 text=(HERE/'FINDINGS_BRIEF.md').read_text();a,b=text.split('## 2.',1)
 story=md_blocks(a,True)+[PageBreak()]+md_blocks('## 2.'+b,True)
 SimpleDocTemplate(str(HERE/'FINDINGS_BRIEF.pdf'),pagesize=(595.28,841.89),leftMargin=35,rightMargin=35,topMargin=30,bottomMargin=38).build(story,onFirstPage=footer,onLaterPages=footer)
if __name__=='__main__':build_reader();build_brief()
