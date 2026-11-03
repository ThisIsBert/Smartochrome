import {test} from 'node:test';
import assert from 'node:assert/strict';
import {guideCue,pathFor,normalizedRegion,RASTER} from '../capture-guide.js';
test('raster crosses the interior in five alternating rows, not only the perimeter',()=>{
 assert.deepEqual(RASTER[0],[0,0]);assert.deepEqual(RASTER.at(-1),[1,1]);
 const rows=RASTER.slice(1).flatMap((p,i)=>p[1]===RASTER[i][1]?[p[1]]:[]);
 assert.deepEqual(rows,[0,.25,.5,.75,1]);
 for(let i=1;i<RASTER.length;i++)assert.ok(RASTER[i][0]===RASTER[i-1][0]||RASTER[i][1]===RASTER[i-1][1]);
});
test('guide follows path at bounded constant speed and stops at the final point',()=>{
 let last=guideCue('disk',0);
 for(let k=1;k<=1000;k++){const q=guideCue('disk',k/1000);assert.ok(q.x>=0&&q.x<=1&&q.y>=0&&q.y<=1);assert.ok(Math.hypot(q.x-last.x,q.y-last.y)<=.006001);last=q;}
 assert.equal(last.x,1);assert.equal(last.y,1);assert.equal(guideCue('horizontal',.5).x,.5);assert.equal(guideCue('stationary',.8).x,.5);
 assert.deepEqual(pathFor('diagnostic'),[[.5,.5],[.5,.5]]);
});
test('selected region stays square in image pixels and clamps to all image edges',()=>{
 for(const [w,h]of [[720,1280],[1280,720]])for(const p of [{x:0,y:0},{x:1,y:1},{x:.5,y:.5}]){
  const r=normalizedRegion(p,10,w,h);assert.ok(r.x>=0&&r.y>=0&&r.x+r.width<=1&&r.y+r.height<=1);assert.ok(Math.abs(r.width*w-r.height*h)<1e-8);
 }
 assert.throws(()=>normalizedRegion({x:0,y:0},10,0,1280));
});
