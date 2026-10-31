const C='dp-v5';const SHELL=['./','index.html','manifest.json','icons/icon-192.png','icons/icon-512.png'];
self.addEventListener('install',e=>{self.skipWaiting();e.waitUntil(caches.open(C).then(c=>c.addAll(SHELL)))});
self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(k=>Promise.all(k.filter(x=>x!==C).map(x=>caches.delete(x)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',e=>{const u=new URL(e.request.url);if(e.request.method!=='GET'||u.origin!==location.origin)return;
 if(/\/(data|x)\.json$/.test(u.pathname)){e.respondWith(fetch(e.request,{cache:'no-store'}).catch(()=>new Response('{"updated":"offline","sections":[],"items":[]}',{headers:{'Content-Type':'application/json'}})));return}
 e.respondWith(fetch(e.request).then(r=>{const cl=r.clone();caches.open(C).then(c=>c.put(e.request,cl));return r}).catch(()=>caches.match(e.request,{ignoreSearch:true})))});
