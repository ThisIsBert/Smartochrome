const CACHE='smartochrome-0.1.0';
const FILES=['./','./index.html','./style.css','./app.js','./core.js','./storage.js','./manifest.webmanifest','./icons/mark.svg','./icons/icon-192.png','./icons/icon-512.png'];
self.addEventListener('install',event=>event.waitUntil(caches.open(CACHE).then(c=>c.addAll(FILES))));
self.addEventListener('activate',event=>event.waitUntil((async()=>{for(const k of await caches.keys())if(k.startsWith('smartochrome-')&&k!==CACHE)await caches.delete(k);await self.clients.claim();})()));
self.addEventListener('message',event=>{if(event.data==='ACTIVATE')self.skipWaiting();});
self.addEventListener('fetch',event=>{if(event.request.method!=='GET'||new URL(event.request.url).origin!==self.location.origin)return;event.respondWith((async()=>{const c=await caches.open(CACHE),cached=await c.match(event.request);if(cached)return cached;return fetch(event.request);})());});
