"""Offline local-browser verification. Own temporary Chrome only; no network resources."""
import base64,json,subprocess,tempfile,time,urllib.request
from pathlib import Path
import websocket
HERE=Path(__file__).resolve().parent

def main():
 profile=tempfile.mkdtemp(prefix='evidence006-browser-');log=open(profile+'/chrome.log','w')
 browser=subprocess.Popen(['/usr/bin/google-chrome','--headless','--no-sandbox','--disable-gpu','--disable-background-networking','--disable-extensions','--disable-component-update','--no-first-run','--remote-debugging-port=0','--user-data-dir='+profile,'about:blank'],stdout=log,stderr=log)
 ws=None;counter=0;errors=[];report=[]
 out=HERE/'reports/screenshots/browser';out.mkdir(parents=True,exist_ok=True)
 try:
  limit=time.monotonic()+15;portfile=Path(profile)/'DevToolsActivePort'
  while not portfile.exists() and time.monotonic()<limit:time.sleep(.1)
  port=portfile.read_text().splitlines()[0];pages=json.load(urllib.request.urlopen('http://127.0.0.1:'+port+'/json/list'))
  page=next(p for p in pages if p.get('type')=='page' and p.get('url')=='about:blank')
  ws=websocket.create_connection(page['webSocketDebuggerUrl'],suppress_origin=True,timeout=20)
  def call(method,params=None):
   nonlocal counter
   counter+=1;key=counter;ws.send(json.dumps({'id':key,'method':method,'params':params or {}}))
   while True:
    result=json.loads(ws.recv())
    if result.get('method')=='Runtime.exceptionThrown':errors.append(result)
    if result.get('id')==key:
     if 'error' in result:raise RuntimeError(result['error'])
     return result.get('result',{})
  def evaluate(s):
   result=call('Runtime.evaluate',{'expression':s,'returnByValue':True})
   if result.get('exceptionDetails'):raise RuntimeError(result['exceptionDetails'])
   return result['result'].get('value')
  call('Page.enable');call('Runtime.enable');call('Network.enable');call('Network.setBlockedURLs',{'urls':['http://*','https://*']})
  def inspect(name,path,target,width=1400,height=1050):
   call('Emulation.setDeviceMetricsOverride',{'width':width,'height':height,'deviceScaleFactor':1,'mobile':width<500})
   call('Page.navigate',{'url':path.as_uri()})
   for _ in range(250):
    ready=evaluate('({state:document.readyState,url:location.href,main:document.querySelectorAll("main").length})')
    if ready['state']=='complete' and ready['url'].startswith(path.as_uri()) and ready['main']==1:break
    time.sleep(.1)
   else:raise RuntimeError('Local HTML load failed: '+repr(ready))
   if target is None:target=evaluate('document.querySelector("section.case").id')
   evaluate('location.hash='+json.dumps(target)+';revealHash();true');time.sleep(.2)
   state=evaluate('(()=>{const e=document.getElementById('+json.dumps(target)+');return {target:!!e,visible:!!e?.getClientRects().length,top:e?.getBoundingClientRect().top,width:innerWidth,scrollWidth:document.documentElement.scrollWidth}})()')
   assert state['visible'] and abs(state['top'])<20 and state['scrollWidth']<=state['width']+2,state
   screenshot=out/(name+'.png');screenshot.write_bytes(base64.b64decode(call('Page.captureScreenshot',{'format':'png'})['data']))
   report.append({'view':name,'file':str(path.relative_to(HERE)),'screenshot':str(screenshot.relative_to(HERE)),**state})
  inspect('chronological-desktop',HERE/'DIALOGUE_EXCHANGES.html','DI5-a4c89ffad4')
  inspect('chronological-mobile',HERE/'DIALOGUE_EXCHANGES.html','DI5-ceecfe5fb4',390,1000)
  atlas=HERE/'extracted/author/DIALOGUE_ATLAS.html';inspect('complete-episode',atlas,'D5E-2fd1ee13eac3-t12')
  # A linked opposite-world episode must reveal its otherwise hidden world pane.
  es=json.loads((HERE/'extracted/author/episodes.json').read_text());opposite=next(e['episode_id'] for e in es if e['case_id']=='DI5-e743bcb1a6' and not e['anchor'] and e['condition']=='C5')
  inspect('opposite-world-mobile',atlas,opposite+'-t8',390,1000)
  reviewer=HERE/'extracted/reviewer/REVIEW.html';inspect('blinded-fixed-event',reviewer,None)
  assert not evaluate('document.body.innerText.includes("AI-assisted interpretation")')
  # Follow a real relative companion-episode link, then reveal its fragment.
  target=evaluate('document.querySelector("a[href^=EPISODES]").getAttribute("href")')
  inspect('blinded-full-context',reviewer.parent/'EPISODES.html',target.split('#')[1],390,1000)
  assert not errors,errors
  (HERE/'reports/BROWSER_VERIFICATION.json').write_text(json.dumps({'status':'passed','browser':'Installed Chrome; HTTP(S) requests blocked; offline file documents','views':report,'script_exceptions':0,'scientific_human_review':False},indent=2)+'\n')
  print(json.dumps(report,indent=2))
 finally:
  if ws:ws.close()
  browser.terminate()
  try:browser.wait(timeout=5)
  except subprocess.TimeoutExpired:browser.kill();browser.wait()
  log.close()
if __name__=='__main__':main()
