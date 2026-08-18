/*
 * Push handling, imported into the generated Workbox service worker (see
 * vite.config.ts). Kept as a plain file in public/ so the generateSW strategy
 * stays untouched. Paths are relative to the SW scope, so they resolve under
 * the /gym/ base in production and / in dev.
 */
self.addEventListener("push", (event) => {
  let payload = {};
  try {
    payload = event.data ? event.data.json() : {};
  } catch {
    payload = {};
  }
  const title = payload.title || "hoy toca entrenar";
  event.waitUntil(
    self.registration.showNotification(title, {
      body: payload.body || "",
      icon: "icon-192.png",
      badge: "icon-192.png",
      lang: "es",
      // One reminder at a time: a new one replaces yesterday's leftover.
      tag: "gym-daily",
      renotify: true,
    }),
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  event.waitUntil(
    self.clients
      .matchAll({ type: "window", includeUncontrolled: true })
      .then((windows) => {
        // Focus the app if it's already open rather than stacking new tabs.
        for (const client of windows) {
          if (client.url.includes(self.registration.scope) && "focus" in client) {
            return client.focus();
          }
        }
        return self.clients.openWindow(self.registration.scope);
      }),
  );
});
