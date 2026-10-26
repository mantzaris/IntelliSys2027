"""Optional local-browser inspection: uses installed websocket-client, no web services."""
import base64,json,subprocess,tempfile,time,urllib.request
from pathlib import Path
import websocket

HERE=Path(__file__).resolve().parent

def main():
    profile=tempfile.mkdtemp(prefix='dialogue005-visual-');log=open('/tmp/dialogue005-browser.log','w')
    process=subprocess.Popen(['/usr/bin/google-chrome','--headless','--no-sandbox','--disable-gpu','--disable-background-networking',
        '--disable-extensions','--disable-component-update','--no-first-run','--remote-debugging-port=0','--user-data-dir='+profile,'about:blank'],stdout=log,stderr=log)
    ws=None;counter=0;report=[];events=[]
    try:
        deadline=time.monotonic()+15;portfile=Path(profile)/'DevToolsActivePort'
        while not portfile.exists() and time.monotonic()<deadline:time.sleep(.1)
        port=portfile.read_text().splitlines()[0]
        pages=json.load(urllib.request.urlopen('http://127.0.0.1:'+port+'/json/list'))
        page=next(p for p in pages if p.get('type')=='page' and p.get('url')=='about:blank')
        ws=websocket.create_connection(page['webSocketDebuggerUrl'],suppress_origin=True,timeout=15)
        def call(method,params=None):
            nonlocal counter
            counter+=1;ident=counter;ws.send(json.dumps({'id':ident,'method':method,'params':params or {}}))
            while True:
                result=json.loads(ws.recv())
                if result.get('method')=='Runtime.exceptionThrown':events.append(result)
                if result.get('id')==ident:
                    if 'error' in result:raise RuntimeError(result['error'])
                    return result.get('result',{})
        def evaluate(expression):
            result=call('Runtime.evaluate',{'expression':expression,'returnByValue':True})
            if result.get('exceptionDetails'):raise RuntimeError(result['exceptionDetails'])
            return result['result'].get('value')
        call('Page.enable');call('Runtime.enable');call('Network.enable');call('Network.setBlockedURLs',{'urls':['http://*','https://*']})
        def load(path,width,height,fragment=''):
            call('Emulation.setDeviceMetricsOverride',{'width':width,'height':height,'deviceScaleFactor':1,'mobile':width<500})
            call('Page.navigate',{'url':path.as_uri()+fragment})
            for _ in range(300):
                ready=evaluate('({state:document.readyState,url:location.href,script:typeof revealHash,main:document.querySelectorAll("main").length})')
                if ready['state']=='complete' and ready['url'].startswith(path.as_uri()) and ready['main']==1 and (path.name=='CASEBOOK.html' or ready['script']=='function'):break
                time.sleep(.1)
            else:raise RuntimeError({'load_state':ready,'script_exceptions':events})
            time.sleep(.25)
        atlas=HERE/'DIALOGUE_ATLAS.html'
        load(atlas,1440,1100)
        for name,target,width,height in [('matched','DI5-a4c89ffad4',1440,1100),('action','D5E-2fd1ee13eac3-t12',1440,1100),('opposite-mobile','DI5-e743bcb1a6-authorized',390,1000)]:
            call('Emulation.setDeviceMetricsOverride',{'width':width,'height':height,'deviceScaleFactor':1,'mobile':width<500})
            evaluate('location.hash='+json.dumps(target)+';revealHash();true');time.sleep(.25)
            state=evaluate('(()=>{const e=document.getElementById('+json.dumps(target)+');return {target:!!e,top:e.getBoundingClientRect().top,visible:!!e.getClientRects().length,world:e.closest("[data-world]")?.dataset.world,scrollWidth:document.documentElement.scrollWidth,width:innerWidth}})()')
            screenshot='/tmp/dialogue005-'+name+'-checked.png';Path(screenshot).write_bytes(base64.b64decode(call('Page.captureScreenshot',{'format':'png'})['data']))
            report.append({'view':name,'screenshot':screenshot,**state});assert state['visible'] and abs(state['top'])<10
        reviewer=HERE.parents[1]/'artifacts/dialogue_interpretation_005/human_review/reviewer/REVIEW.html'
        load(reviewer,1200,1000)
        target=evaluate('document.querySelector("article.episode").id')+'-t12'
        evaluate('location.hash='+json.dumps(target)+';revealHash();true');time.sleep(.25)
        Path('/tmp/dialogue005-reviewer-checked.png').write_bytes(base64.b64decode(call('Page.captureScreenshot',{'format':'png'})['data']))
        report.append({'view':'blinded reviewer','screenshot':'/tmp/dialogue005-reviewer-checked.png','target':target,'no_ai_readings':not evaluate('document.body.innerText.includes("AI-assisted interpretation")')})
        load(HERE/'CASEBOOK.html',1200,1000)
        data=call('Page.printToPDF',{'printBackground':True,'paperWidth':8.5,'paperHeight':11,'marginTop':.35,'marginBottom':.35,'marginLeft':.4,'marginRight':.4})
        (HERE/'CASEBOOK.pdf').write_bytes(base64.b64decode(data['data']))
        report.append({'view':'casebook PDF','file':'CASEBOOK.pdf','bytes':(HERE/'CASEBOOK.pdf').stat().st_size})
        (HERE/'reports/VISUAL_CHECK.json').write_text(json.dumps({'browser':'installed Chrome150; offline file URLs; all HTTP(S) resources blocked','checks':report,'human_visual_inspection':'Screenshots subsequently inspected by the assistant; not human scientific ratings.'},indent=2)+'\n')
        print(report)
    finally:
        if ws:ws.close()
        process.terminate()
        try:process.wait(timeout=5)
        except subprocess.TimeoutExpired:process.kill();process.wait()
        log.close()

if __name__=='__main__':main()
