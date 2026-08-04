import { api, type SyncPush } from "./api";
import { db, type QueueEntity, type QueuedEvent, type QueuePayload } from "./db";

/**
 * Offline-first sync (spec §2, §3). Events are enqueued in IndexedDB and flushed
 * to POST /sync — idempotent by client UUID, so retries are safe. The pull
 * cursor is persisted so it survives reloads. This replaces phase 4's direct
 * push; screens keep calling enqueue() and read the pending count for the UI.
 */
const CURSOR_KEY = "cursor";
const BATCH = 200;
const FLUSH_INTERVAL_MS = 15_000;
const ENTITIES: QueueEntity[] = [
  "sessions",
  "set_logs",
  "body_weights",
  "treadmill_sessions",
];

const listeners = new Set<(pending: number) => void>();

async function notify(): Promise<void> {
  const pending = await db.queue.count();
  for (const l of listeners) l(pending);
}

export function subscribePending(cb: (pending: number) => void): () => void {
  listeners.add(cb);
  void notify();
  return () => listeners.delete(cb);
}

async function getCursor(): Promise<number> {
  return (await db.meta.get(CURSOR_KEY))?.value ?? 0;
}

async function setCursor(value: number): Promise<void> {
  await db.meta.put({ key: CURSOR_KEY, value });
}

type EnqueueInput = Partial<Record<QueueEntity, QueuePayload[]>>;

export async function enqueue(events: EnqueueInput): Promise<void> {
  const rows: QueuedEvent[] = [];
  for (const entity of ENTITIES) {
    for (const payload of events[entity] ?? []) rows.push({ entity, payload });
  }
  if (rows.length) await db.queue.bulkAdd(rows);
  await notify();
  void flush();
}

let flushPromise: Promise<void> | null = null;

/** Flush the queue. Concurrent callers share the in-flight run, so awaiting it
 * guarantees the queue was drained (or a network error stopped it). */
export function flush(): Promise<void> {
  if (!navigator.onLine) return Promise.resolve();
  if (flushPromise) return flushPromise;
  flushPromise = drain().finally(() => {
    flushPromise = null;
  });
  return flushPromise;
}

async function drain(): Promise<void> {
  try {
    for (;;) {
      const batch = await db.queue.orderBy("id").limit(BATCH).toArray();
      if (batch.length === 0) break;

      const push: SyncPush = {
        cursor: await getCursor(),
        sessions: [],
        set_logs: [],
        body_weights: [],
        treadmill_sessions: [],
      };
      for (const row of batch) {
        (push[row.entity] as QueuePayload[]).push(row.payload);
      }

      const result = await api.sync(push);
      await db.queue.bulkDelete(batch.map((b) => b.id as number));
      await setCursor(result.cursor);
      await notify();
    }
  } catch {
    // Network/auth error: leave the queue intact and retry on the next
    // `online` event or interval tick. Idempotency makes replays safe.
  }
}

let started = false;

export function startSync(): void {
  if (started) return;
  started = true;
  window.addEventListener("online", () => void flush());
  window.setInterval(() => void flush(), FLUSH_INTERVAL_MS);
  void flush();
}
