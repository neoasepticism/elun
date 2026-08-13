/* Elun PWA service worker — 보수적 캐시 전략 (라이브 결제 사이트) */
const VERSION = 'elun-v1';
const CORE = [
  '/ko/', '/en/',
  '/icon-192.png', '/icon-512.png',
  '/manifest.webmanifest', '/manifest-en.webmanifest'
];
/* 개인 리포트·결제 결과는 캐시하지 않음 */
const NO_CACHE = /\/(result|report|couple)\.html/;

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(VERSION).then((c) => c.addAll(CORE)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== VERSION).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;                 // 결제 POST 등은 통과
  const url = new URL(req.url);
  if (url.origin !== location.origin) return;        // Paddle 등 크로스오리진 통과

  // 페이지 이동: 네트워크 우선 → 오프라인 시 캐시 → 최후에 /ko/
  if (req.mode === 'navigate') {
    if (NO_CACHE.test(url.pathname)) return;          // 개인 리포트는 기본 네트워크(캐시 X)
    e.respondWith(
      fetch(req)
        .then((res) => { const cp = res.clone(); caches.open(VERSION).then((c) => c.put(req, cp)); return res; })
        .catch(() => caches.match(req).then((r) => r || caches.match('/ko/')))
    );
    return;
  }

  // 정적 자산: 캐시 우선 + 백그라운드 갱신
  e.respondWith(
    caches.match(req).then((cached) => {
      const net = fetch(req)
        .then((res) => { if (res && res.ok) { const cp = res.clone(); caches.open(VERSION).then((c) => c.put(req, cp)); } return res; })
        .catch(() => cached);
      return cached || net;
    })
  );
});
