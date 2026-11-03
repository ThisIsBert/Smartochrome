import {test} from 'node:test';
import assert from 'node:assert/strict';
import {crc32,makeZip,summarize,assessment,cleanSettings,imageMetrics} from '../core.js';
test('ZIP entries have correct CRCs, bytes, UTF-8 flags and directory offsets',async()=>{
 const entries=[{name:'session.json',blob:new Blob(['{"note":"Grüße"}'])},{name:'frames/0000.jpg',blob:new Blob([new Uint8Array([255,216,0,255,217])])}];
 const b=new Uint8Array(await(await makeZip(entries)).arrayBuffer()),v=new DataView(b.buffer);let at=0;
 for(const e of entries){assert.equal(v.getUint32(at,true),0x04034b50);assert.equal(v.getUint16(at+6,true),0x800);assert.equal(v.getUint16(at+8,true),0);const n=v.getUint16(at+26,true),size=v.getUint32(at+18,true);assert.equal(new TextDecoder().decode(b.slice(at+30,at+30+n)),e.name);assert.equal(v.getUint32(at+14,true),crc32(b.slice(at+30+n,at+30+n+size)));assert.deepEqual(b.slice(at+30+n,at+30+n+size),new Uint8Array(await e.blob.arrayBuffer()));at+=30+n+size;}
 assert.equal(v.getUint32(at,true),0x02014b50);const end=b.length-22;assert.equal(v.getUint32(end,true),0x06054b50);assert.equal(v.getUint16(end+10,true),2);assert.equal(v.getUint32(end+16,true),at);
});
test('CRC32 matches standard check value',()=>assert.equal(crc32(new TextEncoder().encode('123456789')),0xcbf43926));
const frames=times=>times.map((t,i)=>({elapsedMs:t,bytes:100,metrics:{meanLuma:100+i,laplacianEnergy:10,thumbnailHash:String(i)}}));
test('rate uses saved frame timestamps and reports gaps',()=>{const s=summarize(frames([0,100,200,500]),20);assert.equal(s.savedFps,6);assert.equal(s.maxIntervalMs,300);assert.equal(s.totalBytes,400);});
test('empty, interrupted and poorly sampled captures cannot pass',()=>{for(const s of [{state:'complete',summary:summarize([],12)},{state:'interrupted',summary:summarize(frames(Array.from({length:36},(_,i)=>i*85)),12)},{state:'complete',summary:summarize(frames(Array.from({length:36},(_,i)=>i*500)),12)}])assert.equal(assessment(s).label,'EINGESCHRÄNKT');const good={state:'complete',summary:summarize(frames(Array.from({length:36},(_,i)=>i*85)),12)};assert.equal(assessment(good).label,'AUFNAHME MÖGLICH');assert.match(assessment(good).checks.at(-1),/noch nicht bestätigt/);});
test('diagnostics omit device IDs but preserve optical settings',()=>assert.deepEqual(cleanSettings({deviceId:'secret',groupId:'secret',focusDistance:3,width:1920}),{focusDistance:3,width:1920}));
test('image metrics distinguish flat from detailed content',()=>{const w=20,h=20,flat=new Uint8ClampedArray(w*h*4),detail=new Uint8ClampedArray(w*h*4);for(let i=0;i<w*h;i++){flat.set([120,120,120,255],i*4);const k=(i%w+Math.floor(i/w))%2?220:20;detail.set([k,k,k,255],i*4);}const a=imageMetrics(flat,w,h),b=imageMetrics(detail,w,h);assert.ok(a.laplacianEnergy<1e-5);assert.ok(b.laplacianEnergy>100);assert.ok(b.contrast>a.contrast);assert.equal(a.thumbnailHash,imageMetrics(flat,w,h).thumbnailHash);});
