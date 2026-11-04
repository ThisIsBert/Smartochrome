"""Suggest nearby focus regions using real multi-frame consistency, not AI depth."""
import io,json,zipfile
from pathlib import Path
import numpy as np
from PIL import Image
from refine_aperture import register,pyramid


def suggest(path,roi,progress=lambda text:None):
    with zipfile.ZipFile(path) as z:
        s=json.loads(z.read('session.json'));n=len(s['frames']);mid=n//2
        indices=sorted(set([0,n//6,n//3,mid,2*n//3,5*n//6,n-1]))
        # Always preserve the true middle frame as the registration reference.
        frames=[Image.open(io.BytesIO(z.read(s['frames'][i]['name']))).convert('RGB') for i in indices]
    if len(frames)!=7:raise ValueError('Für Bereichsvorschläge mindestens sieben Bilder verwenden.')
    width,height=frames[0].size;scale=min(1,1280/max(width,height));pyr=[pyramid(f.resize((round(width*scale),round(height*scale)))) for f in frames]
    x,y,w,h=roi;cx=x+w/2;cy=y+h/2;side=min(w,h)
    boxes=[roi]
    for factor,dx,dy in [(1,0,0),(.8,0,0),(1,-.18,0),(1,.18,0),(1,0,-.18),(1,0,.18)]:
        size=max(48,round(side*factor));size=min(size,width,height)
        boxes.append([round(max(0,min(width-size,cx+dx*side-size/2))),round(max(0,min(height-size,cy+dy*side-size/2))),size,size])
    results=[];seen=set()
    # Reuse full-sequence evidence when the same local capture was already analyzed.
    for saved in (Path(__file__).resolve().parents[1]/'output'/'local-lab').glob('*/analysis.json'):
        try:
            previous=json.loads(saved.read_text())
            if previous.get('archive')!=Path(path).name or previous.get('total')!=n:continue
            box=previous['roi'];px,py,pw,ph=box
            if np.hypot(px+pw/2-cx,py+ph/2-cy)>max(w,h):continue
            fraction=previous['accepted']/n
            if fraction<.6:continue
            errors=[r['holdoutMedianPx'] for r in previous['frames'] if r.get('holdoutMedianPx') is not None and r['frame']!=mid]
            residual=float(np.median(errors)) if errors else 99.
            if residual>1.5:continue
            results.append({'roi':box,'acceptedSamples':previous['accepted'],'sampleCount':n,'holdoutMedianPx':residual,'featureCount':previous['featureCount'],'score':fraction-min(1,residual)*.15,'evidence':'previous-full-sequence-analysis'})
            seen.add(tuple(box))
        except (OSError,ValueError,KeyError):continue
    for i,box in enumerate(boxes):
        box=[round(v) for v in box]
        if tuple(box) in seen:continue
        seen.add(tuple(box));progress(f'Bereichsvorschlag {i+1}/{len(boxes)} anhand von sieben Bildern prüfen …')
        try:
            records,count=register(pyr,[round(v*scale) for v in box]);good=[r for r in records if 'transform' in r]
            if len(good)<5:continue
            errors=[r['holdoutMedianPx'] for r in good if r.get('holdoutMedianPx') is not None and r['frame']!=len(frames)//2]
            residual=float(np.median(errors)) if errors else 99.
            score=len(good)/7-min(1,residual)*.15
            results.append({'roi':box,'acceptedSamples':len(good),'sampleCount':7,'holdoutMedianPx':residual,'featureCount':count,'score':score})
        except ValueError:continue
    results.sort(key=lambda r:r['score'],reverse=True)
    if not results:raise ValueError('Keine geeignete strukturierte Region gefunden. Einen anderen Punkt auf dem Hauptmotiv markieren.')
    return {'candidates':results[:3],'sampleIndices':indices,'method':'real-multiframe-consistency','caution':'Vorschläge aus einer Siebenbild-Stichprobe oder einer früheren vollständigen Auswertung derselben ZIP. Keine Tiefenkarte. Motivzugehörigkeit visuell prüfen.'}
