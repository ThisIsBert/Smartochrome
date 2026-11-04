"""Coverage-aware pupil integration. Thresholds are experimental, not calibration."""
import numpy as np


def capped_weights(raw,cap=.12):
    raw=np.asarray(raw,float); positive=raw>0
    if positive.sum()*cap<1-1e-9:raise ValueError('Zu wenige unabhängige Positionen für eine ausgewogene Öffnung.')
    weights=np.zeros(len(raw));free=positive.copy();remaining=1.
    while free.any():
        proposal=raw[free]/raw[free].sum()*remaining;indices=np.flatnonzero(free);over=proposal>cap+1e-12
        if not over.any():weights[indices]=proposal;break
        fixed=indices[over];weights[fixed]=cap;free[fixed]=False;remaining=1-weights.sum()
    return weights


def spatial_weights(offsets,aperture=1.,taper=1.,area=False):
    xy=np.asarray(offsets,float)
    if xy.ndim!=2 or xy.shape[1]!=2 or len(xy)<3 or not np.isfinite(xy).all():raise ValueError('Zu wenige gültige Positionen.')
    if not .2<=aperture<=1 or not 0<=taper<=1:raise ValueError('Ungültige Öffnung oder Randgewichtung.')
    mean=xy.mean(axis=0);_,s,axes=np.linalg.svd(xy-mean,full_matrices=False);coords=(xy-mean)@axes.T
    ratio=float(s[1]/max(s[0],1e-9));dimensions=2 if area else 1
    if area and ratio<=.2:raise ValueError('Der Weg ist zu schmal für eine Flächenöffnung. Linienöffnung wählen.')
    low=coords.min(axis=0);high=coords.max(axis=0);origin=(low+high)/2
    radius=float((min(high-low) if area else high[0]-low[0])*.5*aperture)
    if radius<1:raise ValueError('Zu wenig Parallaxe für diese Öffnung.')
    # Search nearby pupil centers, without adding views or changing registration.
    shifts=[np.zeros(2)]
    if area:shifts += [np.array([x,y])*radius*.3 for x,y in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,-1),(1,-1),(-1,1)]]
    else:shifts += [np.array([x*radius*.3,0]) for x in [-1,1]]
    if area:
        yy,xx=np.mgrid[-1:1:64j,-1:1:64j];grid=np.column_stack((xx.ravel(),yy.ravel()));grid=grid[np.linalg.norm(grid,axis=1)<=1]*radius
    else:grid=np.linspace(-radius,radius,512)[:,None]
    candidates=[]
    for shift in shifts:
        centered=coords-origin-shift;distance=np.linalg.norm(centered[:,:dimensions],axis=1)
        groups=[]
        for i in np.flatnonzero(distance<=radius+1e-7):
            found=next((g for g in groups if np.linalg.norm(coords[i,:dimensions]-np.mean(coords[g,:dimensions],axis=0))<=1),None)
            if found is None:groups.append([int(i)])
            else:found.append(int(i))
        if len(groups)<9:continue
        centers=np.array([np.mean(centered[g,:dimensions],axis=0) for g in groups])
        sq=np.sum((grid[:,None,:]-centers[None,:,:])**2,axis=-1);nearest=sq.argmin(axis=1);dist=np.sqrt(sq.min(axis=1))
        supported=dist<=max(1.,radius*.30);coverage=float(supported.mean());hole=float(dist.max()/radius)
        if coverage<.85 or hole>.55:continue
        rho=np.linalg.norm(grid,axis=1)/radius;pupil=((1-taper)+taper*(.5+.5*np.cos(np.pi*rho)))*supported
        cell=np.bincount(nearest,weights=pupil,minlength=len(groups))
        try:group_weights=capped_weights(cell)
        except ValueError:continue
        effective=float(1/np.sum(group_weights**2))
        if effective<9:continue
        weights=np.zeros(len(xy))
        for g,w in zip(groups,group_weights):weights[g]=w/len(g)
        center_original=(origin+shift)@axes+mean
        info={'algorithm':'coverage-capped-v1','kind':'area' if area else 'line','axisRatio':ratio,'groups':len(groups),'usedFrames':int(np.count_nonzero(weights)),'radiusPx':radius,'coverageFraction':coverage,'maxUnsampledDistancePx':float(dist.max()),'maxHoleRadiusFraction':hole,'maxGroupWeight':float(group_weights.max()),'maxFrameWeight':float(weights.max()),'effectivePositions':effective,'effectiveFrames':float(1/np.sum(weights**2)),'centerOffsetPx':center_original.tolist(),'missingCellsExcluded':True}
        candidates.append((coverage-hole*.1-np.linalg.norm(shift)/radius*.01,weights,info))
    if not candidates:raise ValueError('Öffnung unzureichend abgedeckt oder von zu wenigen Positionen getragen. „Geeignete Öffnung suchen“ verwenden. Kleinere Öffnungen sind nicht automatisch besser.')
    _,weights,info=max(candidates,key=lambda c:c[0]);return weights,info


def recommend(offsets,taper=1.,area=False):
    valid=[]
    for fraction in [1.,.9,.8,.7,.6,.5,.4,.3,.2]:
        try:
            _,info=spatial_weights(offsets,fraction,taper,area)
            valid.append({'apertureFraction':fraction,**info})
        except ValueError:pass
    if not valid:raise ValueError('Keine ausreichend abgedeckte Öffnung gefunden. Schärfebereich verbessern oder eine dichter abgetastete Folge verwenden; die Qualitätsgrenzen werden nicht abgesenkt.')
    return valid[0]
