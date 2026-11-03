"""Offline synthetic aperture experiment v2: sparse tracking and parallax weights.

Only ONE similarity transform is used to resample each image. Sparse flow finds
correspondences; it does not independently align the background or alter depths.
The background trajectory is an image-space proxy, not a metric camera pose.
"""
import argparse
import io
import json
from pathlib import Path
import zipfile
import numpy as np
from PIL import Image
from synthetic_aperture import points, pyramid, design, fit, warp_linear, srgb


def sample(a, xy):
    h,w=a.shape
    x=np.clip(xy[...,0],0,w-1.001); y=np.clip(xy[...,1],0,h-1.001)
    ix=x.astype(int); iy=y.astype(int); fx=x-ix; fy=y-iy
    return (a[iy,ix]*(1-fx)+a[iy,ix+1]*fx)*(1-fy)+(a[iy+1,ix]*(1-fx)+a[iy+1,ix+1]*fx)*fy


def track(ref, target, p, initial=None, shape=None):
    """Pyramidal patch Lucas-Kanade; one translation per feature, subpixel samples."""
    q=p.copy() if initial is None else initial.copy()
    mat=np.eye(2) if shape is None else np.asarray(shape)
    oy,ox=np.mgrid[-6:7,-6:7]; offsets=np.column_stack((ox.ravel(),oy.ravel()))
    target_offsets=offsets@mat.T
    for level in (2,1,0):
        scale=2**level; a=ref[level]; b=target[level]; gy,gx=np.gradient(b)
        template=sample(a,p[:,None,:]/scale+offsets); template-=template.mean(axis=1,keepdims=True)
        q/=scale
        for _ in range(15):
            coords=q[:,None,:]+target_offsets
            values=sample(b,coords); values-=values.mean(axis=1,keepdims=True)
            dx=sample(gx,coords); dx-=dx.mean(axis=1,keepdims=True)
            dy=sample(gy,coords); dy-=dy.mean(axis=1,keepdims=True)
            residual=template-values
            hxx=np.sum(dx*dx,axis=1)+1e-6; hyy=np.sum(dy*dy,axis=1)+1e-6; hxy=np.sum(dx*dy,axis=1)
            bx=np.sum(dx*residual,axis=1); by=np.sum(dy*residual,axis=1); det=hxx*hyy-hxy*hxy+1e-6
            step=np.column_stack(((hyy*bx-hxy*by)/det,(hxx*by-hxy*bx)/det))
            step=np.clip(step,-2,2); q+=step
            if np.max(np.linalg.norm(step,axis=1))<.015: break
        q*=scale
    values=sample(target[0],q[:,None,:]+target_offsets); values-=values.mean(axis=1,keepdims=True)
    ncc=np.sum(template*values,axis=1)/(np.linalg.norm(template,axis=1)*np.linalg.norm(values,axis=1)+1e-9)
    h,w=target[0].shape
    ncc[(q[:,0]<8)|(q[:,0]>w-9)|(q[:,1]<8)|(q[:,1]>h-9)]=-1
    return q,ncc


def transform_points(p,c):
    return (design(p)@c).reshape(-1,2)


def track_sequence(pyramids,p,mid):
    """Track outward from the middle, with adjacent forward/backward checks."""
    n=len(pyramids); positions=np.full((n,len(p),2),np.nan); confidence=np.zeros((n,len(p)))
    positions[mid]=p; confidence[mid]=1
    for direction in (-1,1):
        for i in range(mid+direction,-1 if direction<0 else n,direction):
            previous=i-direction; before=positions[previous]
            q,score=track(pyramids[previous],pyramids[i],before)
            back,backscore=track(pyramids[i],pyramids[previous],q,initial=before)
            good=(score>.85)&(backscore>.85)&(np.linalg.norm(back-before,axis=1)<.65)&(confidence[previous]>0)
            positions[i]=q; confidence[i]=np.where(good,score,0)
    return positions,confidence


def register(pyramids,roi):
    mid=len(pyramids)//2
    compact=min(roi[2:])<90
    p=points(pyramids[mid][0],roi,spacing=7 if compact else 14,step=4 if compact else 9)
    if len(p)<12: raise ValueError('Focus region needs at least 12 textured features')
    tracked,confidence=track_sequence(pyramids,p,mid); records=[]
    for i in range(len(pyramids)):
        try:
            c,quality=fit(p,tracked[i],confidence[i])
            a,b=c[:2]; shape=np.array([[a,-b],[b,a]])
            # Re-anchor patches directly to the middle frame to limit accumulated drift.
            direct,score=track(pyramids[mid],pyramids[i],p,transform_points(p,c),shape)
            back,backscore=track(pyramids[i],pyramids[mid],direct,initial=p,shape=np.linalg.inv(shape))
            fb=np.linalg.norm(back-p,axis=1)
            score=np.where((fb<.8)&(backscore>.8),score,0)
            c,quality=fit(p,direct,score)
            err=np.linalg.norm(transform_points(p,c)-direct,axis=1)
            valid=(score>.8)&(err<1.8)
            if valid.sum()<max(10,len(p)*.45): raise ValueError('Insufficient reliable focus-plane support')
            spread=np.std(p[valid],axis=0)
            if min(spread)<(8 if compact else 12): raise ValueError('Focus correspondences are too concentrated')
            if not .85<np.hypot(*c[:2])<1.15: raise ValueError('Implausible scale for this short sweep')
            # Held-out feature locations test prediction within the ROI.
            train=np.arange(len(p))%3!=0; test=~train
            holdout=None
            try:
                hc,_=fit(p[train],direct[train],score[train])
                test&=score>.8
                if test.sum()>=3: holdout=float(np.median(np.linalg.norm(transform_points(p[test],hc)-direct[test],axis=1)))
            except ValueError: pass
            records.append({'frame':i,'transform':c.tolist(),**quality,'support':int(valid.sum()),'forwardBackwardMedianPx':float(np.median(fb[valid])),'holdoutMedianPx':holdout})
        except ValueError as e:
            records.append({'frame':i,'rejected':str(e)})
    return records,len(p)


def parallax_positions(pyramids,background_roi,records,min_span=3):
    mid=len(pyramids)//2; p=points(pyramids[mid][0],background_roi)
    if len(p)<6: raise ValueError('Background region has too few features')
    tracked,confidence=track_sequence(pyramids,p,mid)
    accepted=[r['frame'] for r in records if 'transform' in r]
    # A fixed set of landmarks prevents changing depths from masquerading as motion.
    stable=np.all(confidence[accepted]>.8,axis=0)
    if stable.sum()<6: raise ValueError('Too few background landmarks survive the whole accepted sweep')
    residual=[]
    for r in records:
        if 'transform' not in r: continue
        a,b,tx,ty=r['transform']; inv=np.linalg.inv([[a,-b],[b,a]])
        aligned=(tracked[r['frame'],stable]-[tx,ty])@inv.T
        residual.append(np.median(aligned-p[stable],axis=0))
    residual=np.array(residual); centered=residual-residual.mean(axis=0)
    _,s,axes=np.linalg.svd(centered,full_matrices=False); axis=axes[0]
    if axis[0]<0: axis=-axis
    coordinate=centered@axis
    span=float(np.ptp(coordinate))
    if span<min_span: raise ValueError('Insufficient measured relative parallax for spatial weighting')
    return coordinate,{'stableBackgroundFeatures':int(stable.sum()),'backgroundFeatureCount':len(p),'axis':axis.tolist(),'parallaxSpanPx':span,'secondaryToPrimaryRatio':float(s[1]/max(s[0],1e-8)),'alignedBackgroundOffsets':residual.tolist()}


def aperture_weights(coordinate,spacing=1.):
    """Integrate a 1D pupil over Voronoi cells; repeated locations share a cell.

    Near-duplicate positions are grouped within `spacing` image-space pixels.
    Provides a flat pupil and a cosine-tapered pupil; neither is a circular pupil.
    """
    coordinate=np.asarray(coordinate,float)
    if coordinate.ndim!=1 or not np.isfinite(coordinate).all() or spacing<0:
        raise ValueError('Finite one-dimensional coordinates and nonnegative spacing required')
    order=np.argsort(coordinate); groups=[]
    for i in order:
        if not groups or coordinate[i]-coordinate[groups[-1][0]]>spacing: groups.append([int(i)])
        else: groups[-1].append(int(i))
    if len(groups)<3: raise ValueError('Not enough distinct aperture positions')
    centers=np.array([np.mean(coordinate[g]) for g in groups]); left,right=centers[0],centers[-1]
    edges=np.r_[left,(centers[:-1]+centers[1:])/2,right]; span=right-left
    flat=np.diff(edges)/span
    def integral(x):
        t=(x-left)/span
        return .5*t-np.sin(2*np.pi*t)/(4*np.pi)
    taper=np.diff(integral(edges)); taper/=taper.sum()
    weights=np.zeros(len(coordinate)); uniform=weights.copy()
    for j,g in enumerate(groups): weights[g]=taper[j]/len(g); uniform[g]=flat[j]/len(g)
    return weights,uniform,{'groups':len(groups),'mergeTolerancePx':spacing,'effectiveFramesTapered':float(1/np.sum(weights**2)),'maxPositionGapPx':float(np.max(np.diff(centers)))}


def full_coverage_crop(valid):
    h,w=valid.shape
    for margin in range(min(w,h)//2):
        if valid[margin:h-margin,margin:w-margin].all(): return (margin,margin,w-margin,h-margin)
    raise ValueError('No common rectangular image area')


def run(archive,out,roi,background_roi,baseline):
    out.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        session=json.loads(z.read('session.json'))
        frames=[Image.open(io.BytesIO(z.read(f['name']))).convert('RGB') for f in session['frames']]
    pyramids=[pyramid(f) for f in frames]; mid=len(frames)//2
    old=json.loads(baseline.read_text())
    if old['archive']!=archive.name or old['referenceFrame']!=mid:
        raise ValueError('Baseline must use the same capture and reference frame')
    records,count=register(pyramids,roi)
    (out/'registration.json').write_text(json.dumps({'roi':roi,'featureCount':count,'frames':records},indent=2),encoding='utf-8')
    accepted=[r for r in records if 'transform' in r]
    print(f'Registration: {len(accepted)}/{len(frames)}',flush=True)
    if len(accepted)<5: raise ValueError('Insufficient registered frames')
    coordinate,trajectory=parallax_positions(pyramids,background_roi,records)
    tapered,uniform,weight_summary=aperture_weights(coordinate)
    old_by_index={r['frame']:r for r in old['frames'] if 'transform' in r}
    shape=(frames[mid].height,frames[mid].width,3)
    accum={name:np.zeros(shape,np.float32) for name in ('equal','uniform','tapered','baseline','matched')}
    all_valid=np.ones(shape[:2],bool); matched_count=0
    for j,r in enumerate(accepted):
        warped,valid=warp_linear(frames[r['frame']],r['transform']); all_valid&=valid
        accum['equal']+=warped/len(accepted); accum['uniform']+=warped*uniform[j]; accum['tapered']+=warped*tapered[j]
        if r['frame'] in old_by_index: accum['matched']+=warped; matched_count+=1
        r.update({'parallaxCoordinatePx':float(coordinate[j]),'uniformWeight':float(uniform[j]),'taperedWeight':float(tapered[j])})
    if not matched_count: raise ValueError('No common frames for alignment comparison')
    accum['matched']/=matched_count
    # Same contributing frames for old/new registration comparison.
    for r in accepted:
        if r['frame'] not in old_by_index: continue
        warped,valid=warp_linear(frames[r['frame']],old_by_index[r['frame']]['transform'])
        all_valid&=valid; accum['baseline']+=warped/matched_count
    crop=full_coverage_crop(all_valid)
    for name,arr in accum.items(): srgb(arr).crop(crop).save(out/f'{name}.jpg',quality=96)
    frames[mid].crop(crop).save(out/'reference.jpg',quality=96)
    report={'version':2,'archive':archive.name,'referenceFrame':mid,'roi':roi,'backgroundRoi':background_roi,'featureCount':count,'accepted':len(accepted),'total':len(frames),'sameFramesComparisonCount':matched_count,'crop':crop,'trajectory':trajectory,'weighting':weight_summary,'frames':records,'limitations':['Relative background parallax is a proxy, not a calibrated camera position.','One similarity per image is an approximation; depth within the focus ROI and projective changes remain.','Cosine taper reduces effective aperture width as well as edge contributions.','Horizontal sampling cannot reproduce a filled circular aperture.']}
    (out/'analysis.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('frames','trajectory')}),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('archive',type=Path); parser.add_argument('output',type=Path)
    parser.add_argument('--roi',type=int,nargs=4,required=True); parser.add_argument('--background-roi',type=int,nargs=4,required=True)
    parser.add_argument('--baseline',type=Path,required=True)
    args=parser.parse_args(); run(args.archive,args.output,args.roi,args.background_roi,args.baseline)
