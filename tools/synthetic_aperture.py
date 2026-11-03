"""Local, experimental plane-aligned averaging. Requires numpy and Pillow.

Fits one similarity transform per image from patch correspondences in a chosen
foreground ROI. Does not use dense optical flow or artificially blur the image.
Equal temporal weights are a first experiment, NOT a calibrated circular pupil.
The ROI must contain a static, textured object at roughly one depth.
"""
import argparse
import io
import json
from pathlib import Path
import zipfile
import numpy as np
from PIL import Image, ImageDraw


def pyramid(image):
    return [np.asarray(image.convert('L').resize((image.width//s, image.height//s)), dtype=np.float32) for s in (1, 2, 4)]


def points(gray, roi, spacing=14, step=9):
    x, y, w, h = roi
    if x<0 or y<0 or w<24 or h<24 or x+w>gray.shape[1] or y+h>gray.shape[0]:
        raise ValueError('ROI must be inside the image and at least 24 pixels wide and high')
    gy, gx = np.gradient(gray)
    candidates = []
    for py in range(y+10, y+h-10, step):
        for px in range(x+10, x+w-10, step):
            a = gx[py-4:py+5, px-4:px+5]; b = gy[py-4:py+5, px-4:px+5]
            mat = np.array([[np.mean(a*a), np.mean(a*b)], [np.mean(a*b), np.mean(b*b)]])
            candidates.append((np.linalg.eigvalsh(mat)[0], px, py))
    chosen = []
    for score, px, py in sorted(candidates, reverse=True):
        if score < 8: break
        if all((px-q[0])**2+(py-q[1])**2 > spacing**2 for q in chosen): chosen.append((px, py))
        if len(chosen) == 55: break
    return np.array(chosen, dtype=float)


def match(ref, target, pts):
    result = []; scores = []
    for px, py in pts:
        dx = dy = 0.; best_score = -1.
        for level in (2, 1, 0):
            scale = 2**level; a = ref[level]; b = target[level]
            cx, cy = round(px/scale), round(py/scale)
            radius = 22 if level == 2 else 3
            ox, oy = round(dx/scale), round(dy/scale)
            r = 5
            patch = a[cy-r:cy+r+1, cx-r:cx+r+1]
            if patch.shape != (11, 11): break
            patch = patch-patch.mean(); norm = np.sqrt(np.sum(patch*patch))
            xs = np.arange(cx+ox-radius, cx+ox+radius+1)
            ys = np.arange(cy+oy-radius, cy+oy+radius+1)
            xs = xs[(xs>=r)&(xs<b.shape[1]-r)]; ys = ys[(ys>=r)&(ys<b.shape[0]-r)]
            if not len(xs) or not len(ys): break
            xx, yy = np.meshgrid(xs, ys)
            patches = b[yy[...,None,None]+np.arange(-r,r+1)[None,None,:,None], xx[...,None,None]+np.arange(-r,r+1)[None,None,None,:]]
            patches = patches-patches.mean(axis=(-2,-1), keepdims=True)
            ncc = np.sum(patches*patch, axis=(-2,-1))/(norm*np.sqrt(np.sum(patches*patches, axis=(-2,-1)))+1e-8)
            iy, ix = np.unravel_index(np.argmax(ncc), ncc.shape)
            # Parabolic subpixel refinement around the correlation peak.
            def sub(v, i):
                if i == 0 or i == len(v)-1: return 0.
                den = v[i-1]-2*v[i]+v[i+1]
                return float(np.clip(.5*(v[i-1]-v[i+1])/den, -.5, .5)) if abs(den)>1e-8 else 0.
            dx = (xs[ix]-cx+sub(ncc[iy,:], ix))*scale
            dy = (ys[iy]-cy+sub(ncc[:,ix], iy))*scale
            best_score = float(ncc[iy,ix])
        result.append((px+dx, py+dy)); scores.append(best_score)
    return np.array(result), np.array(scores)


def design(p):
    x,y=p.T
    a=np.zeros((len(p)*2,4)); a[::2]=np.column_stack((x,-y,np.ones(len(p)),np.zeros(len(p))))
    a[1::2]=np.column_stack((y,x,np.zeros(len(p)),np.ones(len(p))))
    return a


def fit(p,q,scores):
    keep=scores>.80; p=p[keep]; q=q[keep]
    if len(p)<6: raise ValueError('Too few reliable patch correspondences')
    a=design(p); rng=np.random.default_rng(42); best=np.zeros(len(p),bool)
    for _ in range(180):
        pick=rng.choice(len(p),2,replace=False)
        if np.linalg.norm(p[pick[0]]-p[pick[1]])<25: continue
        coeff=np.linalg.lstsq(design(p[pick]),q[pick].ravel(),rcond=None)[0]
        err=np.linalg.norm((a@coeff).reshape(-1,2)-q,axis=1); mask=err<1.8
        if mask.sum()>best.sum(): best=mask
    if best.sum()<6: raise ValueError('No consistent focus-plane transform')
    coeff=np.linalg.lstsq(design(p[best]),q[best].ravel(),rcond=None)[0]
    residual=np.linalg.norm((a@coeff).reshape(-1,2)-q,axis=1)
    return coeff, {'matches':len(p),'inliers':int(best.sum()),'medianResidualPx':float(np.median(residual[best]))}


def warp_linear(image, coeff):
    arr=np.asarray(image,dtype=np.float32)/255
    arr=np.where(arr<=.04045,arr/12.92,((arr+.055)/1.055)**2.4)
    h,w=arr.shape[:2]; yy,xx=np.mgrid[:h,:w]; a,b,tx,ty=coeff
    sx=a*xx-b*yy+tx; sy=b*xx+a*yy+ty
    valid=(sx>=0)&(sy>=0)&(sx<w-1)&(sy<h-1)
    sx=np.clip(sx,0,w-1.001); sy=np.clip(sy,0,h-1.001)
    ix=sx.astype(int); iy=sy.astype(int); fx=(sx-ix)[...,None]; fy=(sy-iy)[...,None]
    out=(arr[iy,ix]*(1-fx)+arr[iy,ix+1]*fx)*(1-fy)+(arr[iy+1,ix]*(1-fx)+arr[iy+1,ix+1]*fx)*fy
    return out.astype(np.float32),valid


def srgb(arr):
    out=np.where(arr<=.0031308,arr*12.92,1.055*np.maximum(arr,0)**(1/2.4)-.055)
    return Image.fromarray(np.uint8(np.clip(out*255+.5,0,255)))


def run(archive, out, roi):
    out.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        s=json.loads(z.read('session.json'))
        frames=[Image.open(io.BytesIO(z.read(f['name']))).convert('RGB') for f in s['frames']]
    mid=len(frames)//2; ref=frames[mid]; pyr=pyramid(ref); pts=points(pyr[0],roi)
    if len(pts)<6: raise ValueError('ROI has insufficient texture')
    total=np.zeros((ref.height,ref.width,3),np.float32); coverage=np.zeros((ref.height,ref.width),np.float32)
    records=[]
    for i,img in enumerate(frames):
        try:
            q,score=match(pyr,pyramid(img),pts); coeff,quality=fit(pts,q,score)
            if quality['inliers']<max(8,len(pts)*.3): raise ValueError('Too few inliers')
            warped,valid=warp_linear(img,coeff); total+=warped*valid[...,None]; coverage+=valid
            records.append({'frame':i,'transform':coeff.tolist(),**quality})
            if i in (0,mid,len(frames)-1): srgb(warped).save(out/f'aligned-{i:03d}.jpg',quality=95)
        except ValueError as e: records.append({'frame':i,'rejected':str(e)})
    accepted=sum('transform' in r for r in records)
    if accepted<3: raise ValueError('Insufficient accepted frames')
    result=srgb(total/np.maximum(coverage,1)[...,None])
    # Fixed central crop, then tighten until every output pixel has full coverage.
    margin=0
    while margin<min(ref.size)//3 and np.any(coverage[margin:ref.height-margin or None,margin:ref.width-margin or None]<accepted): margin+=1
    crop=(margin,margin,ref.width-margin,ref.height-margin)
    result.crop(crop).save(out/'synthetic-aperture.jpg',quality=96)
    ref.crop(crop).save(out/'reference.jpg',quality=96)
    comparison=Image.new('RGB',(ref.width*2,ref.height+48),'#191919')
    comparison.paste(ref,(0,48)); comparison.paste(result,(ref.width,48)); d=ImageDraw.Draw(comparison)
    d.text((15,15),'Single reference frame',fill='white'); d.text((ref.width+15,15),f'Synthetic horizontal aperture - {accepted} frames',fill='white')
    comparison.save(out/'comparison.jpg',quality=94)
    report={'archive':archive.name,'referenceFrame':mid,'roi':roi,'featureCount':len(pts),'accepted':accepted,'total':len(frames),'crop':crop,'method':'ROI patch matching, robust similarity alignment, equal-time linear-light mean','limitations':['Not a calibrated pupil; variable speed changes spatial weights.','Similarity transform approximates one focus plane; not a full projective camera calibration.','Horizontal sweep produces directional blur.','No metric depth or physical aperture inferred.'],'frames':records}
    (out/'analysis.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='frames'}),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('archive',type=Path); parser.add_argument('output',type=Path)
    parser.add_argument('--roi',type=int,nargs=4,required=True,metavar=('X','Y','WIDTH','HEIGHT'))
    args=parser.parse_args(); run(args.archive,args.output,args.roi)
