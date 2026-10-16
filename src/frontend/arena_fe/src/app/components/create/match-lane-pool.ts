/**
 * A pool of independent Pyodide workers ("lanes") used to play evaluation matches in parallel.
 *
 * Each lane is a full Python runtime with its own copy of the game engines and the user's code,
 * so matches on different lanes never share state. Lanes are separate from the main
 * ArenaPyodideClient pool (which serves the Game Arena page and the Compile button).
 */
import type { WorkerRequestPayload } from '../../workers/arena-pyodide.client';

export type ProgressHandler = (moves: number, player: number, last: [number, unknown, number] | null) => void;
type Pending = { resolve: (value: unknown) => void; reject: (error: Error) => void; onProgress?: ProgressHandler };
type LaneMessage =
  | { kind: 'response'; id: number; ok: boolean; data?: unknown; error?: string }
  | { kind: 'matchProgress'; id: number; moves: number; player: number; last: [number, unknown, number] | null }
  | { kind: string };

export class MatchLane {
  private worker!: Worker;
  private pending = new Map<number, Pending>();
  private nextId = 0;
  /** identifies the (game, code) loaded into this runtime; null until prepared or after a restart */
  prepared: string | null = null;

  constructor(readonly index: number) {
    this.spawn();
  }

  private spawn(): void {
    this.worker = new Worker(new URL('../../workers/arena-pyodide.worker', import.meta.url), { type: 'module' });
    this.worker.onmessage = (event: MessageEvent<LaneMessage>) => {
      const message = event.data;
      if (message.kind === 'matchProgress') {
        const progress = message as { id: number; moves: number; player: number; last: [number, unknown, number] | null };
        this.pending.get(progress.id)?.onProgress?.(progress.moves, progress.player, progress.last ?? null);
        return;
      }
      if (message.kind !== 'response') {
        return; // status/log events are only meaningful for the main runtime's UI
      }
      const response = message as { id: number; ok: boolean; data?: unknown; error?: string };
      const entry = this.pending.get(response.id);
      if (!entry) {
        return;
      }
      this.pending.delete(response.id);
      if (response.ok) {
        entry.resolve(response.data);
      } else {
        entry.reject(new Error(response.error ?? 'Match runtime error'));
      }
    };
    this.worker.onerror = (event) => {
      this.failAll(new Error(event.message || 'Match runtime crashed'));
    };
  }

  request<T>(payload: WorkerRequestPayload, onProgress?: ProgressHandler): Promise<T> {
    const id = ++this.nextId;
    return new Promise<T>((resolve, reject) => {
      this.pending.set(id, { resolve: (value) => resolve(value as T), reject, onProgress });
      this.worker.postMessage({ ...payload, id });
    });
  }

  /** Kill the runtime (e.g. it is stuck in the user's loop) and start a fresh, unprepared one. */
  restart(): void {
    this.worker.terminate();
    this.failAll(new Error('Match runtime restarted'));
    this.prepared = null;
    this.spawn();
  }

  terminate(): void {
    this.worker.terminate();
    this.failAll(new Error('Match runtime stopped'));
    this.prepared = null;
  }

  private failAll(error: Error): void {
    for (const entry of this.pending.values()) {
      entry.reject(error);
    }
    this.pending.clear();
  }
}

export class MatchLanePool {
  private lanes: MatchLane[] = [];

  /** Grow or shrink the pool to exactly `size` lanes and return them. */
  setSize(size: number): MatchLane[] {
    const target = Math.max(1, Math.floor(size));
    while (this.lanes.length < target) {
      this.lanes.push(new MatchLane(this.lanes.length));
    }
    while (this.lanes.length > target) {
      this.lanes.pop()!.terminate();
    }
    return [...this.lanes];
  }

  get size(): number {
    return this.lanes.length;
  }

  /** Terminate every lane; in-flight matches are killed. Lanes are recreated lazily by setSize. */
  dispose(): void {
    for (const lane of this.lanes) {
      lane.terminate();
    }
    this.lanes = [];
  }
}
