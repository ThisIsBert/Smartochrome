"""Local-only Smartochrome analysis UI. Run with Python + NumPy + Pillow."""
import argparse
import hashlib
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import io
import json
from pathlib import Path
import secrets
import threading
from urllib.parse import urlparse,parse_qs
import webbrowser
import zipfile
from PIL import Image
from lab_engine import analyze,render

ROOT=Path(__file__).resolve().parents[1]


class Lab:
    def __init__(self,folders,output):
        self.folders=folders;self.output=output;self.token=secrets.token_urlsafe(32);self.jobs={};self.captures={};self.lock=threading.Lock();self.busy=False
    def listing(self):
        items=[]
        for folder in self.folders:
            for path in sorted(folder.glob('*.zip')):
                key=hashlib.sha256(str(path.resolve()).encode()).hexdigest()[:20]
                try:
                    with zipfile.ZipFile(path) as z:
                        entry=z.getinfo('session.json')
                        if entry.file_size>4*1024*1024:continue
                        s=json.loads(z.read(entry))
                    if s.get('schema')!='smartochrome-capture/1' or not s.get('frames'):continue
                    self.captures[key]=path
                    item={'id':key,'name':path.name,'mode':s['mode'],'frames':len(s['frames']),'width':s['output']['width'],'height':s['output']['height'],'region':s.get('referenceRegion')}
                    for saved in (ROOT/'output'/'real-captures').glob('refined-*/analysis.json'):
                        try:
                            previous=json.loads(saved.read_text())
                            if previous['archive']==path.name:item.update(suggestedRoi=previous['roi'],suggestedBackground=previous['backgroundRoi']);break
                        except (ValueError,KeyError,OSError):pass
                    items.append(item)
                except (ValueError,KeyError,OSError,zipfile.BadZipFile):continue
        return items
    def start(self,operation,payload):
        with self.lock:
            if self.busy:raise ValueError('Eine Berechnung läuft bereits. Bitte warten.')
            if operation=='analyze':
                path=self.captures.get(payload.get('captureId'))
                if path is None:raise ValueError('Bildfolge nicht gefunden. Liste aktualisieren.')
                boxes=[]
                for key in ('roi','backgroundRoi'):
                    box=payload.get(key)
                    if not isinstance(box,list) or len(box)!=4 or any(not isinstance(v,(int,float)) for v in box):raise ValueError('Bitte beide Bildbereiche markieren.')
                    box=[round(v) for v in box]
                    if min(box[:2])<0 or min(box[2:])<24:raise ValueError('Bereiche müssen mindestens 24 Bildpixel groß sein.')
                    boxes.append(box)
                job_id=secrets.token_hex(8); folder=self.output/job_id
                job={'id':job_id,'state':'running','message':'Auswertung startet …','path':str(path),'folder':str(folder)}
                self.jobs[job_id]=job
                def work():
                    job['report']=analyze(path,*boxes,folder,lambda message:job.update(message=message))
            else:
                job=self.jobs.get(payload.get('analysisId'))
                if job is None or 'report' not in job:raise ValueError('Zuerst Bildfolge ausrichten.')
                aperture=float(payload.get('aperture',1));taper=float(payload.get('taper',1));area=bool(payload.get('area',False));full=bool(payload.get('full',False))
                if not .2<=aperture<=1 or not 0<=taper<=1:raise ValueError('Ungültige Öffnung oder Randgewichtung.')
                job_id=job['id'];job.update(state='running',message='Vollauflösung berechnen …' if full else 'Vorschau berechnen …')
                def work():job['result']=render(job['path'],job['folder'],aperture,taper,area,full)
            self.busy=True
        def worker():
            try:work();job.update(state='done',message='Berechnung abgeschlossen.')
            except Exception as e:job.update(state='error',message=str(e))
            finally:
                with self.lock:self.busy=False
        threading.Thread(target=worker,daemon=True).start()
        return {'id':job_id}


def handler_for(lab):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def send(self,data,kind='application/json',code=200):
            if not isinstance(data,bytes):data=json.dumps(data,ensure_ascii=False).encode()
            self.send_response(code);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Referrer-Policy','no-referrer');self.end_headers();self.wfile.write(data)
        def allowed(self,private=False):
            expected=f'127.0.0.1:{self.server.server_port}'
            if self.headers.get('Host')!=expected:return False
            origin=self.headers.get('Origin')
            if origin and origin!='http://'+expected:return False
            query=parse_qs(urlparse(self.path).query)
            token=self.headers.get('X-Lab-Token') or query.get('token',[''])[0]
            return not private or secrets.compare_digest(token,lab.token)
        def do_GET(self):
            route=urlparse(self.path);private=route.path.startswith(('/api/','/result/'))
            if not self.allowed(private):self.send({'error':'Zugriff nicht erlaubt.'},code=403);return
            q=parse_qs(route.query)
            try:
                if route.path in ('/','/lab.js','/lab.css'):
                    filename={'/':'lab.html','/lab.js':'lab.js','/lab.css':'lab.css'}[route.path];content=(ROOT/'local-lab'/filename).read_text(encoding='utf-8').replace('__TOKEN__',lab.token)
                    self.send(content.encode(),{'/':'text/html; charset=utf-8','/lab.js':'text/javascript; charset=utf-8','/lab.css':'text/css; charset=utf-8'}[route.path]);return
                if route.path=='/api/captures':self.send(lab.listing());return
                if route.path=='/api/status':
                    job=lab.jobs[q['id'][0]];self.send({k:v for k,v in job.items() if k not in ('path','folder')});return
                if route.path=='/api/reference':
                    path=lab.captures[q['id'][0]]
                    with zipfile.ZipFile(path) as z:
                        s=json.loads(z.read('session.json'));entry=z.getinfo(s['frames'][len(s['frames'])//2]['name'])
                        if entry.file_size>12*1024*1024:raise ValueError('Bild zu groß.')
                        content=z.read(entry)
                    self.send(content,'image/jpeg');return
                if route.path.startswith('/result/'):
                    _,_,job_id,name=route.path.split('/')
                    if name not in ('reference.jpg','preview.jpg','synthese.jpg','analysis.json','export-settings.json'):raise ValueError('Unbekannte Ergebnisdatei.')
                    job=lab.jobs[job_id];data=(Path(job['folder'])/name).read_bytes();self.send(data,'image/jpeg' if name.endswith('.jpg') else 'application/json');return
                self.send({'error':'Nicht gefunden'},code=404)
            except (KeyError,ValueError,OSError,zipfile.BadZipFile) as e:self.send({'error':str(e)},code=400)
        def do_POST(self):
            if not self.allowed(True):self.send({'error':'Zugriff nicht erlaubt.'},code=403);return
            try:
                size=int(self.headers.get('Content-Length','0'))
                if size<1 or size>32768:raise ValueError('Ungültige Anfragegröße.')
                payload=json.loads(self.rfile.read(size));operation={'/api/analyze':'analyze','/api/render':'render'}[urlparse(self.path).path]
                self.send(lab.start(operation,payload))
            except (ValueError,KeyError,TypeError) as e:self.send({'error':str(e)},code=400)
    return Handler


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--port',type=int,default=8024);parser.add_argument('--captures',type=Path,action='append');parser.add_argument('--no-browser',action='store_true');args=parser.parse_args()
    folders=args.captures or [ROOT/'captures',ROOT/'tests'/'Diagnosedateien']
    (ROOT/'captures').mkdir(exist_ok=True)
    lab=Lab(folders,ROOT/'output'/'local-lab');server=ThreadingHTTPServer(('127.0.0.1',args.port),handler_for(lab))
    url=f'http://127.0.0.1:{server.server_port}/';print('Smartochrome-Auswertung: '+url+'\nNur auf diesem Rechner erreichbar. Beenden mit Strg+C.',flush=True)
    if not args.no_browser:webbrowser.open(url)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()


if __name__=='__main__':main()
