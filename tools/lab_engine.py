"""Local analysis and interactive rendering; all inputs/outputs stay on disk."""
import io
import json
from pathlib import Path
import zipfile
import numpy as np
from PIL import Image
from inspect_capture import inspect
from refine_aperture import register,parallax_positions,pyramid,warp_linear,srgb,full_coverage_crop


from aperture_quality import spatial_weights, recommend


def analyze(path,roi,background_roi,out,progress=lambda text:None):
    out=Path(out); out.mkdir(parents=True,exist_ok=True)
    progress('ZIP-Datei und Bilder prüfen …'); integrity=inspect(path)
    if not 5<=integrity['images']<=180:raise ValueError('Für die Auswertung werden 5 bis 180 Bilder benötigt.')
    with zipfile.ZipFile(path) as z:
        session=json.loads(z.read('session.json')); original_size=(session['output']['width'],session['output']['height'])
        if max(original_size)>4096 or min(original_size)<64:raise ValueError('Bildgröße außerhalb des unterstützten Bereichs.')
        scale=min(1,1280/max(original_size)); size=tuple(round(v*scale) for v in original_size)
        frames=[Image.open(io.BytesIO(z.read(f['name']))).convert('RGB').resize(size) for f in session['frames']]
    scaled=lambda box:[round(v*scale) for v in box]
    focus=scaled(roi); background=scaled(background_roi)
    progress('Schärfebereich über die Bildfolge verfolgen. Das kann einige Minuten dauern …')
    pyramids=[pyramid(f) for f in frames]
    try:records,count=register(pyramids,focus)
    except ValueError as e:raise ValueError('Der Schärfebereich konnte nicht verfolgt werden. Einen ausreichend großen, strukturierten Bereich auf einem unbewegten Objekt wählen.') from e
    accepted=[r for r in records if 'transform' in r]
    if len(accepted)<5:raise ValueError('Zu wenige Bilder ausgerichtet. Einen kleineren, strukturierten Schärfebereich auf einem unbewegten Objekt wählen.')
    retention=len(accepted)/len(frames)
    if retention<.6:raise ValueError(f'Nur {len(accepted)} von {len(frames)} Bildern zuverlässig ausgerichtet. Bitte zuerst Bereichsvorschläge prüfen; eine Synthese würde zu viele Blickpunkte verlieren.')
    progress(f'{len(accepted)} von {len(frames)} Bildern ausgerichtet. Hintergrund verfolgen …')
    try:_,trajectory=parallax_positions(pyramids,background,records,min_span=0)
    except ValueError as e:raise ValueError('Zu wenige Hintergrundmerkmale über die ganze Folge verfolgt. Einen größeren, strukturierten Bereich auf einer unbewegten Hintergrundfläche wählen.') from e
    report={'archive':Path(path).name,'mode':session['mode'],'referenceFrame':len(frames)//2,'roi':roi,'backgroundRoi':background_roi,'originalSize':original_size,'analysisSize':size,'analysisScale':scale,'accepted':len(accepted),'total':len(frames),'featureCount':count,'registrationQuality':{'retainedFraction':retention,'scope':'local-focus-region-only','warning':'Die Ausrichtung ist nur lokal geprüft; weiter entfernte Bildteile können Perspektivfehler enthalten.'},'frames':records,'trajectory':trajectory}
    (out/'analysis.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    progress('Vorschaubilder vorbereiten …')
    preview_scale=min(1,640/max(size)); preview_size=tuple(round(v*preview_scale) for v in size)
    values=[]; valid=np.ones((preview_size[1],preview_size[0]),bool)
    for r in accepted:
        c=np.array(r['transform']);c[2:]*=preview_scale
        warped,ok=warp_linear(frames[r['frame']].resize(preview_size),c);values.append(warped);valid&=ok
    crop=full_coverage_crop(valid); x,y,right,bottom=crop
    array=np.stack([v[y:bottom,x:right] for v in values]).astype(np.float32)
    np.save(out/'preview.npy',array)
    frames[report['referenceFrame']].resize(preview_size).crop(crop).save(out/'reference.jpg',quality=96)
    report['previewCrop']=crop;(out/'analysis.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report


def render(path,out,aperture,taper,area,full=False):
    out=Path(out); report=json.loads((out/'analysis.json').read_text()); accepted=[r for r in report['frames'] if 'transform' in r]
    weights,info=spatial_weights(report['trajectory']['alignedBackgroundOffsets'],aperture,taper,area)
    if full:
        size=report['originalSize'];total=np.zeros((size[1],size[0],3),np.float32); valid=np.ones(total.shape[:2],bool)
        with zipfile.ZipFile(path) as z:
            session=json.loads(z.read('session.json'))
            for r,w in zip(accepted,weights):
                if w==0:continue
                image=Image.open(io.BytesIO(z.read(session['frames'][r['frame']]['name']))).convert('RGB')
                c=np.array(r['transform']);c[2:]/=report['analysisScale'];warped,ok=warp_linear(image,c);total+=warped*w;valid&=ok
        crop=full_coverage_crop(valid);result=srgb(total).crop(crop);filename='synthese.jpg'
    else:
        values=np.load(out/'preview.npy',mmap_mode='r'); total=np.zeros(values.shape[1:],np.float32)
        for value,w in zip(values,weights):
            if w:total+=value*w
        result=srgb(total);filename='preview.jpg'
    result.save(out/filename,quality=96)
    recipe={'apertureFraction':aperture,'taper':taper,'areaRequested':area,'fullResolution':full,'weights':weights.tolist(),**info}
    (out/('export-settings.json' if full else 'preview-settings.json')).write_text(json.dumps(recipe,indent=2),encoding='utf-8')
    return {'file':filename,'width':result.width,'height':result.height,**info}
