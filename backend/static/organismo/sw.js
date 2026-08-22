const CACHE = 'organismo-ia-shell-v3';
const SHELL = [
  '/organismo-app/', '/organismo-app/index.html', '/organismo-app/manifest.json',
  '/organismo-app/icon.svg', '/organismo-app/icon-180.png', '/organismo-app/icon-192.png', '/organismo-app/icon-512.png',
];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)));
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
  );
  self.clients.claim();
});

self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);
  // Solo mismo origen: las descargas del núcleo IA local (WebLLM, CDN +
  // pesos del modelo) son de otro origen y manejan su propio cacheo
  // (Cache API / IndexedDB) — no hay que interceptarlas acá.
  if (url.origin !== self.location.origin) return;
  if (url.pathname.startsWith('/organismo/')) return; // API real, nunca cacheada
  if (e.request.method !== 'GET') return;
  e.respondWith(
    caches.match(e.request).then((cached) => cached || fetch(e.request).catch(() => cached))
  );
});
