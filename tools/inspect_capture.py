"""Validate a Smartochrome ZIP without extracting files or installing dependencies."""
import argparse, json, statistics, struct, zipfile
from pathlib import Path

def jpeg_size(data):
    if data[:2]!=b'\xff\xd8':raise ValueError('Not a JPEG')
    i=2
    while i+3<len(data):
        if data[i]!=255:i+=1;continue
        while i<len(data) and data[i]==255:i+=1
        if i>=len(data):break
        marker=data[i];i+=1
        if marker in (0xd9,0xda):break
        if marker==1 or 0xd0<=marker<=0xd7:continue
        size=int.from_bytes(data[i:i+2],'big')
        if size<2 or i+size>len(data):break
        if marker in (0xc0,0xc1,0xc2,0xc3,0xc5,0xc6,0xc7,0xc9,0xca,0xcb,0xcd,0xce,0xcf):
            height,width=struct.unpack('!HH',data[i+3:i+7]);return width,height
        i+=size
    raise ValueError('JPEG dimensions not found')

def inspect(path):
    with zipfile.ZipFile(path) as z:
        if sum(i.file_size for i in z.infolist())>80*1024*1024:raise ValueError('Archive exceeds 80 MiB')
        if len(z.namelist())!=len(set(z.namelist())):raise ValueError('Duplicate entries')
        bad=z.testzip()
        if bad:raise ValueError('CRC mismatch: '+bad)
        s=json.loads(z.read('session.json'))
        if s.get('schema')!='smartochrome-capture/1':raise ValueError('Unsupported schema')
        frames=s['frames'];previous=-float('inf')
        for i,f in enumerate(frames):
            if f['index']!=i or f['name']!=f'frames/{i:04d}.jpg':raise ValueError('Frame index/name mismatch')
            data=z.read(f['name'])
            if len(data)!=f['bytes']:raise ValueError('JPEG size mismatch')
            if jpeg_size(data)!=(f['width'],f['height']):raise ValueError('JPEG dimension mismatch')
            if f['elapsedMs']<=previous:raise ValueError('Non-monotonic clock')
            previous=f['elapsedMs']
        if set(n for n in z.namelist() if n.startswith('frames/'))!={f['name'] for f in frames}:raise ValueError('Unexpected frames')
    gaps=[b['elapsedMs']-a['elapsedMs'] for a,b in zip(frames,frames[1:])]
    return {'id':s['id'],'state':s['state'],'mode':s['mode'],'images':len(frames),'dimensions':s['output'],'saved_fps':1000*(len(frames)-1)/(frames[-1]['elapsedMs']-frames[0]['elapsedMs']) if len(frames)>1 else 0,'largest_gap_ms':max(gaps,default=None),'median_encode_ms':statistics.median(f['encodeMs'] for f in frames) if frames else None,'reference':s['reference'],'note':s['note'],'summary':s.get('summary'),'caution':'Integrity only: no geometry or optical quality verified.'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('archive',type=Path);p.add_argument('--output',type=Path);a=p.parse_args()
    text=json.dumps(inspect(a.archive),indent=2,ensure_ascii=False);print(text)
    if a.output:a.output.write_text(text+'\n',encoding='utf-8')
