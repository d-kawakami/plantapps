/**
 * Service Worker
 * - アプリシェル（HTML/CSS/JS）をキャッシュ → オフラインでも開ける
 * - API: Network First（失敗時は空レスポンスを返す）
 * - Background Sync: オンライン復帰時に未同期データをサーバーへ送信
 */

const CACHE_NAME    = "tenken-v1";
const SYNC_TAG      = "sync-results";

const APP_SHELL = [
  "/",
  "/inspect/1",
  "/inspect/2",
  "/inspect/3",
  "/inspect/4",
  "/inspect/5",
  "/static/css/style.css",
  "/static/js/app.js",
  "/static/js/db.js",
  "/static/manifest.json",
  "/static/icons/icon-192.png",
  "/static/icons/icon-512.png",
];

/* ─── install: アプリシェルをキャッシュ ─── */
self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(APP_SHELL))
  );
  self.skipWaiting();
});

/* ─── activate: 古いキャッシュを削除 ──── */
self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

/* ─── fetch: リクエスト戦略 ──────────── */
self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);

  // API は Network First
  if (url.pathname.startsWith("/api/")) {
    e.respondWith(networkFirst(e.request));
    return;
  }

  // その他（アプリシェル）は Cache First
  e.respondWith(cacheFirst(e.request));
});

async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) return cached;
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    return new Response("オフライン: リソースが見つかりません", { status: 503 });
  }
}

async function networkFirst(request) {
  try {
    const response = await fetch(request);
    return response;
  } catch {
    // オフライン時 — GETは空配列、POSTは受付済みを返す
    if (request.method === "GET") {
      return new Response("[]", {
        headers: { "Content-Type": "application/json" }
      });
    }
    // POST はクライアント側IndexedDBで処理済みなので202を返す
    return new Response(JSON.stringify({ queued: true }), {
      status: 202,
      headers: { "Content-Type": "application/json" }
    });
  }
}

/* ─── Background Sync ────────────────── */
self.addEventListener("sync", (e) => {
  if (e.tag === SYNC_TAG) {
    e.waitUntil(doSync());
  }
});

async function doSync() {
  // クライアントへ同期指示を送る（app.js側で実処理）
  const clients = await self.clients.matchAll();
  clients.forEach(client => client.postMessage({ type: "SYNC_NOW" }));
}

/* ─── クライアントからのメッセージ ────── */
self.addEventListener("message", (e) => {
  if (e.data?.type === "SKIP_WAITING") self.skipWaiting();
});
