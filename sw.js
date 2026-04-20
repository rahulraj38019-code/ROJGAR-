const CACHE_NAME = "vidyajobs-ai-v3";

// ONLY essential files (safe for AppCreator24)
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
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(urlsToCache);
    })
  );
});

// ACTIVATE → FORCE OLD CACHE DELETE
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

// FETCH → NETWORK FIRST (VERY IMPORTANT FOR LIVE APP)
self.addEventListener("fetch", (event) => {
  event.respondWith(
    fetch(event.request)
      .then((res) => {
        return res;
      })
      .catch(() => {
        return caches.match(event.request);
      })
  );
});