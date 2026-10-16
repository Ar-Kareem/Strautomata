import type { StatusTone } from '@main/arena.constants';

export interface OpenSpielUpdate {
  status: StatusTone;
  message: string;
  errorLines: string[];
  logLines: string[];
}

export interface PyodideUiCallbacks {
  setStatus: (tone: StatusTone, message: string) => void;
  updateOpenSpiel: (update: OpenSpielUpdate) => void;
  appendLogs: (lines: string[]) => void;
}

type PyodideMatchInit = {
  gameId: string;
  worldId: string;
  config: Record<string, unknown>;
  botA: string;
  botB: string;
};

export type PyodideReplayRequest = {
  gameId: string;
  worldId: string;
  config: Record<string, unknown>;
  seed: number | null;
  moves: unknown[];
};

export type PyodideFullMatchRequest = {
  gameId: string;
  worldId: string;
  config: Record<string, unknown>;
  botA: string;
  botB: string;
  seed: number;
  moveTimeout: number;
};

export type WorkerRequestPayload =
  | { type: 'ensureRunner' }
  | { type: 'replayMoves'; payload: PyodideReplayRequest }
  | { type: 'getGamePrompt'; gameId: string; worldId: string; config: Record<string, unknown> }
  | { type: 'setUserPolicy'; gameId: string; worldId: string; code: string; config: Record<string, unknown> | null; smoke?: boolean }
  | { type: 'smokeTestUserPolicy'; gameId: string; worldId: string; config: Record<string, unknown> | null; moveTimeout: number }
  | { type: 'playFullMatch'; payload: PyodideFullMatchRequest }
  | { type: 'loadBots'; gameId: string; worldId: string }
  | { type: 'initMatch'; payload: PyodideMatchInit }
  | { type: 'stepMatch' }
  | { type: 'submitHumanMove'; action: string; forceApply?: boolean }
  | { type: 'capturePyspielError' }
  | { type: 'retryOpenSpielInstall' };

type WorkerRequest = WorkerRequestPayload & { id: number };

type WorkerResponse =
  | { kind: 'response'; id: number; ok: true; data: unknown }
  | { kind: 'response'; id: number; ok: false; error: string };

type WorkerEvent =
  | { kind: 'status'; tone: StatusTone; message: string }
  | { kind: 'openSpiel'; update: OpenSpielUpdate }
  | { kind: 'appendLogs'; lines: string[] }
  | { kind: 'matchProgress'; id: number; moves: number; player: number; last: [number, unknown, number] | null };

type WorkerMessage = WorkerResponse | WorkerEvent;
type PendingRequest = {
  resolve: (value: unknown) => void;
  reject: (error: Error) => void;
  masterToken: number;
  workerSlot: number;
  internal: boolean;
  requestType: WorkerRequestPayload['type'];
};
type WorkerSlot = { worker: Worker; ready: boolean; warming: boolean };

/** small touch screen, or a browser that reports itself as mobile */
const isPhone = (): boolean => {
  const uaMobile = (navigator as Navigator & { userAgentData?: { mobile?: boolean } }).userAgentData?.mobile;
  return Boolean(uaMobile) || window.matchMedia('(pointer: coarse) and (max-width: 900px)').matches;
};

export class ArenaPyodideClient {
  private requestId = 0;
  private pending = new Map<number, PendingRequest>();
  private masterToken = 0;
  private DEBUG_LOGS: [string, unknown][] = [];
  /**
   * Runtimes kept alive: one active plus warm standbys that take over instantly on a restart.
   * Phones get a single runtime: three Python engines booting at once (~46 MB, a few hundred MB of
   * memory, one CPU core each) made the whole site lag there. A restart then reboots in place.
   */
  private readonly workerPoolSize = isPhone() ? 1 : 3;
  private workers: WorkerSlot[] = [];
  private activeWorkerSlot = 0;
  /**
   * Resolves once any runtime has finished loading, i.e. the engine files are in the browser cache.
   * Standbys wait for it and then load one at a time: started together they each downloaded the
   * 10 MB scipy package again because none had finished caching it yet.
   */
  private markFirstReady!: () => void;
  private readonly firstReady = new Promise<void>((resolve) => {
    this.markFirstReady = resolve;
    window.setTimeout(resolve, 20000); // fallback if nothing asks the active runtime to load
  });
  private standbyChain: Promise<void> = Promise.resolve();

  constructor(private readonly ui: PyodideUiCallbacks) {
    for (let slot = 0; slot < this.workerPoolSize; slot += 1) {
      this.workers.push({ worker: this.createWorker(slot), ready: false, warming: false });
    }
    this.warmStandbyWorkers();
    (window as any).PYODIDE_DEBUG_LOGS = this.DEBUG_LOGS;
    (window as any).PYODIDE_PRINT_DEBUG_LOGS = () => {
      this.DEBUG_LOGS.forEach(([timestamp, data]) => { console.log(`${timestamp}`, data); });
    }
  }

  private createWorker(slot: number): Worker {
    const worker = new Worker(new URL('./arena-pyodide.worker', import.meta.url), {
      type: 'module'
    });
    worker.onmessage = (event: MessageEvent<WorkerMessage>) => {
      this.handleMessage(slot, event.data);
    };
    worker.onerror = () => {
      if (slot === this.activeWorkerSlot) {
        this.ui.setStatus('error', 'Pyodide worker error');
      }
    };
    return worker;
  }

  private debugLogs(message: string, id: number, data: unknown): void {
    const d = new Date();
    const timestamp = `${d.getMinutes()}:${d.getSeconds()}.${d.getMilliseconds()}`;
    this.DEBUG_LOGS.push([`${timestamp} ${message} ${id}`, data]);
    // console.log(`${timestamp} ${message} ${id}`, data);
  }

  private logDebug(message: string, data?: unknown): void {
    const d = new Date();
    const mm = String(d.getMinutes()).padStart(2, '0');
    const ss = String(d.getSeconds()).padStart(2, '0');
    const ms = String(d.getMilliseconds()).padStart(3, '0');
    console.debug(`[${mm}:${ss}.${ms}] [ArenaPyodideClient] ${message}`, data ?? '');
  }

  private sendRequest<T>(
    workerSlot: number,
    request: WorkerRequestPayload,
    internal = false
  ): Promise<T> {
    const id = ++this.requestId;
    const requestMasterToken = this.masterToken;
    this.debugLogs('request', id, { ...request, workerSlot, internal });
    return new Promise((resolve, reject) => {
      const resolveWithCast = (value: unknown) => resolve(value as T);
      this.pending.set(id, {
        resolve: resolveWithCast,
        reject,
        masterToken: requestMasterToken,
        workerSlot,
        internal,
        requestType: request.type
      });
      this.workers[workerSlot].worker.postMessage({ ...request, id } as WorkerRequest);
    });
  }

  request<T>(request: WorkerRequestPayload): Promise<T> {
    return this.sendRequest<T>(this.activeWorkerSlot, request, false);
  }

  /** Warm-up work (preloading the runtime or a game): never counts as pending match work. */
  requestInBackground<T>(request: WorkerRequestPayload): Promise<T> {
    return this.sendRequest<T>(this.activeWorkerSlot, request, true);
  }

  hasPendingRequests(): boolean {
    for (const entry of this.pending.values()) {
      if (!entry.internal) {
        return true;
      }
    }
    return false;
  }

  setMasterToken(masterToken: number): boolean {
    if (this.masterToken === masterToken) {
      return false;
    }
    this.ui.setStatus('loading', 'Restarting Pyodide worker');
    this.masterToken = masterToken;
    for (const [id, pendingRequest] of this.pending) {
      if (pendingRequest.masterToken !== this.masterToken) {
        pendingRequest.reject(new Error('Dropped stale Pyodide request'));
        this.pending.delete(id);
      }
    }
    const previousActiveSlot = this.activeWorkerSlot;
    const readyStandbySlot = this.pickReadyStandbySlot(previousActiveSlot);
    if (readyStandbySlot !== null) {
      this.activeWorkerSlot = readyStandbySlot;
      this.logDebug('new active slot', {
        fromSlot: previousActiveSlot,
        toSlot: readyStandbySlot
      });
    }
    this.replaceWorker(previousActiveSlot);
    if (readyStandbySlot === null) {
      this.activeWorkerSlot = previousActiveSlot;
      this.logDebug('worker fallback: no warm standby ready, replacing active slot in place', {
        activeSlot: previousActiveSlot
      });
    }
    this.warmStandbyWorkers();
    this.ui.setStatus('loading', 'Reinitializing Pyodide runtime');
    return true;
  }

  private pickReadyStandbySlot(excludeSlot: number): number | null {
    for (let slot = 0; slot < this.workers.length; slot += 1) {
      if (slot === excludeSlot) {
        continue;
      }
      const worker = this.workers[slot];
      if (worker.ready && !worker.warming) {
        return slot;
      }
    }
    return null;
  }

  private replaceWorker(slot: number): void {
    this.logDebug('recreating worker', { slot });
    this.workers[slot].worker.terminate();
    this.workers[slot] = { worker: this.createWorker(slot), ready: false, warming: false };
  }

  /** Load the standby runtimes one after another, once the first runtime has filled the cache. */
  private warmStandbyWorkers(): void {
    for (let slot = 0; slot < this.workers.length; slot += 1) {
      if (slot === this.activeWorkerSlot) {
        continue;
      }
      const worker = this.workers[slot].worker;
      this.standbyChain = this.standbyChain
        .then(() => this.firstReady)
        .then(() => (this.workers[slot].worker === worker ? this.warmWorker(slot) : undefined));
    }
  }

  private warmWorker(slot: number): Promise<void> {
    const workerObj = this.workers[slot];
    if (workerObj.ready || workerObj.warming) {
      return Promise.resolve();
    }
    const workerRef = workerObj.worker;
    workerObj.warming = true;
    return this.sendRequest<void>(slot, { type: 'ensureRunner' }, true)
      .then(() => {
        const current = this.workers[slot];
        if (current.worker !== workerRef) {
          return;
        }
        current.ready = true;
        current.warming = false;
      })
      .catch(() => {
        const current = this.workers[slot];
        if (current.worker !== workerRef) {
          return;
        }
        current.ready = false;
        current.warming = false;
      });
  }

  private handleMessage(slot: number, message: WorkerMessage): void {
    this.debugLogs('response', (message as WorkerResponse).id ?? -999, message);
    if (message.kind === 'response') {
      const entry = this.pending.get(message.id);
      if (!entry) {
        return;
      }
      if (entry.workerSlot !== slot) {
        return;
      }
      this.pending.delete(message.id);
      if (message.ok && entry.requestType === 'ensureRunner') {
        this.workers[slot].ready = true;
        this.workers[slot].warming = false;
        this.markFirstReady();
      }
      if (entry.masterToken !== this.masterToken) {
        return;
      }
      if (message.ok) {
        entry.resolve(message.data);
      } else {
        if (!entry.internal && slot === this.activeWorkerSlot) {
          this.ui.setStatus('error', "Pyodide worker error");
        }
        entry.reject(new Error(message.error));
      }
      return;
    }

    if (slot !== this.activeWorkerSlot) {
      return;
    }

    if (message.kind === 'status') {
      this.ui.setStatus(message.tone, message.message);
      return;
    }

    if (message.kind === 'openSpiel') {
      this.ui.updateOpenSpiel(message.update);
      return;
    }

    if (message.kind === 'appendLogs') {
      this.ui.appendLogs(message.lines);
    }
  }
}
