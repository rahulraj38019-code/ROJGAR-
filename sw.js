const CACHE_NAME = "vidyajobs-ai-v2";

// sirf basic safe files (over-cache mat karo)
const urlsToCache = [
  "/",
  "/index.html",
  "/style.css",
  "/script.js",
  "/api.js",
  "/manifest.json"
];

// INSTALL
self.addEventListener("install", (event) => {
  self.skipWaiting(); // force update
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(urlsToCache);
    })
  );
});

// ACTIVATE (purana cache hata do)
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// FETCH (safe fallback)
self.addEventListener("fetch", (event) => {
  event.respondWith(
    fetch(event.request).catch(() => {
      return caches.match(event.request);
    })
  );
});