import { api, type SyncPush, type SyncResult } from "./api";

/**
 * Thin sync client for phase 4: pushes events straight to the server and tracks
 * the pull cursor. Phase 8 replaces this with a Dexie-backed queue that survives
 * being offline; screens already call through here so that swap is contained.
 */
let cursor = 0;

type PushInput = Omit<Partial<SyncPush>, "cursor">;

export async function pushEvents(events: PushInput): Promise<SyncResult> {
  const result = await api.sync({
    cursor,
    sessions: events.sessions ?? [],
    set_logs: events.set_logs ?? [],
    body_weights: events.body_weights ?? [],
    treadmill_sessions: events.treadmill_sessions ?? [],
  });
  cursor = result.cursor;
  return result;
}

export function resetCursor(): void {
  cursor = 0;
}
