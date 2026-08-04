import Dexie, { type Table } from "dexie";

import type { BodyWeightIn, SessionIn, SetLogIn, TreadmillIn } from "./api";

/** SyncPush keys — the entity buckets an event belongs to. */
export type QueueEntity =
  | "sessions"
  | "set_logs"
  | "body_weights"
  | "treadmill_sessions";

export type QueuePayload = SessionIn | SetLogIn | BodyWeightIn | TreadmillIn;

export interface QueuedEvent {
  id?: number;
  entity: QueueEntity;
  payload: QueuePayload;
}

export interface MetaRow {
  key: string;
  value: number;
}

/**
 * Durable client store (spec §2, hard requirement: the gym basement has no
 * signal). Writes are queued here first and flushed to POST /sync when a
 * connection is available; the queue survives reloads and logout.
 */
class GymDB extends Dexie {
  queue!: Table<QueuedEvent, number>;
  meta!: Table<MetaRow, string>;

  constructor() {
    super("gym");
    this.version(1).stores({
      queue: "++id",
      meta: "key",
    });
  }
}

export const db = new GymDB();
