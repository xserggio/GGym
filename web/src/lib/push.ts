import { api, type PushSubscriptionBody } from "./api";

/**
 * Browser side of the daily reminder (spec §7.6). The schedule lives on the
 * server — here we only obtain permission and hand the push endpoint over.
 */

/** Web push needs a service worker, the Push API and Notification API. On iOS
 * these only exist once the app is installed to the home screen. */
export const pushSupported = (): boolean =>
  "serviceWorker" in navigator && "PushManager" in window && "Notification" in window;

/** iOS exposes the APIs only in standalone mode, so we can tell the user why. */
export const isStandalone = (): boolean =>
  window.matchMedia("(display-mode: standalone)").matches ||
  (navigator as { standalone?: boolean }).standalone === true;

/** The VAPID key travels as base64url; the Push API wants raw bytes. Returns an
 * ArrayBuffer (a valid BufferSource) to sidestep Uint8Array's buffer generic. */
function vapidKeyToBytes(base64: string): ArrayBuffer {
  const padded = base64.padEnd(base64.length + ((4 - (base64.length % 4)) % 4), "=");
  const raw = atob(padded.replace(/-/g, "+").replace(/_/g, "/"));
  const buffer = new ArrayBuffer(raw.length);
  const view = new Uint8Array(buffer);
  for (let i = 0; i < raw.length; i += 1) view[i] = raw.charCodeAt(i);
  return buffer;
}

function toBody(sub: PushSubscription): PushSubscriptionBody {
  const json = sub.toJSON();
  const keys = json.keys ?? {};
  if (!keys.p256dh || !keys.auth) throw new Error("subscripción push incompleta");
  return { endpoint: sub.endpoint, keys: { p256dh: keys.p256dh, auth: keys.auth } };
}

/**
 * Ask for permission and register this device. Returns false when the user
 * denies the prompt, so the caller can leave the switch off instead of
 * pretending reminders are on.
 */
export async function enablePush(vapidPublicKey: string): Promise<boolean> {
  if (!pushSupported() || !vapidPublicKey) return false;
  if ((await Notification.requestPermission()) !== "granted") return false;

  const reg = await navigator.serviceWorker.ready;
  const sub =
    (await reg.pushManager.getSubscription()) ??
    (await reg.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: vapidKeyToBytes(vapidPublicKey),
    }));
  await api.subscribePush(toBody(sub));
  return true;
}

/** Unregister this device, both in the browser and on the server. */
export async function disablePush(): Promise<void> {
  if (!pushSupported()) return;
  const reg = await navigator.serviceWorker.ready;
  const sub = await reg.pushManager.getSubscription();
  if (!sub) return;
  await api.unsubscribePush(sub.endpoint).catch(() => undefined);
  await sub.unsubscribe();
}
