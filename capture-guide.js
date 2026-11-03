export const GUIDE_VERSION='raster-1';
export const PLANS={
 stationary:{title:'A · Stillhalten',duration:8,help:'Während der gesamten Aufnahme Handy und Motiv ruhig halten. Das ist die Vergleichsaufnahme.',start:'Bequemen Stand einnehmen. Nach dem Countdown bis zum Ende der Aufnahme stillhalten.'},
 horizontal:{title:'B · Seitlich bewegen',duration:8,help:'Erst nach dem Countdown während der Aufnahme insgesamt etwa 3 cm nach rechts bewegen. Handy parallel halten; nicht zum Motiv schwenken.',start:'Am linken Ende des kleinen Wegs beginnen. Bis zum Ende des Countdowns stillhalten.'},
 disk:{title:'C · Fläche abtasten',duration:8,help:'Während der Aufnahme fünf Bahnen durch ein etwa 3 × 3 cm großes Quadrat fahren: rechts, ein Stück nach unten, links, nach unten … Handy dabei parallel halten.',start:'Oben links im gedachten Quadrat beginnen. Erst bei „Aufnahme läuft“ dem Punkt folgen.'}
};
export const RASTER=[[0,0],[1,0],[1,.25],[0,.25],[0,.5],[1,.5],[1,.75],[0,.75],[0,1],[1,1]];
export function pathFor(mode){return mode==='disk'?RASTER:mode==='horizontal'?[[0,.5],[1,.5]]:[[.5,.5],[.5,.5]];}
export function guideCue(mode,progress){
 const t=Math.max(0,Math.min(1,progress));
 if(mode==='stationary'||mode==='diagnostic')return{x:.5,y:.5,text:'Stillhalten',segment:0};
 const path=pathFor(mode),lengths=path.slice(1).map((p,i)=>Math.hypot(p[0]-path[i][0],p[1]-path[i][1]));
 let distance=t*lengths.reduce((a,b)=>a+b,0),segment=0;
 while(segment<lengths.length-1&&distance>lengths[segment])distance-=lengths[segment++];
 const a=path[segment],b=path[segment+1],u=lengths[segment]?distance/lengths[segment]:0;
 return{x:a[0]+(b[0]-a[0])*u,y:a[1]+(b[1]-a[1])*u,segment,text:b[1]>a[1]?'Ein kleines Stück nach unten ↓':b[0]>a[0]?'Langsam nach rechts →':'Langsam nach links ←'};
}
export function normalizedRegion(point,percent,width,height){
 if(!(width>0&&height>0&&Number.isFinite(point.x)&&Number.isFinite(point.y)))throw new Error('Ungültiges Bildformat oder Referenzpunkt');
 const side=Math.min(width,height)*Math.max(.06,Math.min(.24,percent/100)),w=side/width,h=side/height;
 return{x:Math.max(0,Math.min(1-w,point.x-w/2)),y:Math.max(0,Math.min(1-h,point.y-h/2)),width:w,height:h};
}
