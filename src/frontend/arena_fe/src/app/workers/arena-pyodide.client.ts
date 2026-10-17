import type { StatusTone } from '@main/arena.constants';
import { PythonInterrupt } from './python-interrupt';

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
  | { type: 'resolveHungAutomaton'; choice: 'random' | 'forfeit' }
  | { type: 'capturePyspielError' }
  | { type: 'retryOpenSpielInstall' }
  | { type: 'ping' };

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
  /** survives a master token change: the ping that tells when an interrupted worker is free again */
  persistent: boolean;
  request: WorkerRequestPayload;
};
type WorkerSlot = {
  worker: Worker;
  ready: boolean;
  warming: boolean;
  interrupt: PythonInterrupt | null;
  /** the stop in progress on this worker, if any; later stops wait for it */
  stopping: Promise<void> | null;
};

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
   * When Python can be interrupted in place, a restart is rare (code stuck in C, or one that keeps
   * catching KeyboardInterrupt), so one standby is enough.
   */
  private readonly workerPoolSize = isPhone() ? 1 : PythonInterrupt.supported ? 2 : 3;
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
      this.workers.push(this.createSlot(slot));
    }
    this.warmStandbyWorkers();
    (window as any).PYODIDE_DEBUG_LOGS = this.DEBUG_LOGS;
    (window as any).PYODIDE_PRINT_DEBUG_LOGS = () => {
      this.DEBUG_LOGS.forEach(([timestamp, data]) => { console.log(`${timestamp}`, data); });
    }
  }

  private createSlot(slot: number): WorkerSlot {
    const worker = this.createWorker(slot);
    const interrupt = PythonInterrupt.supported ? new PythonInterrupt() : null;
    interrupt?.attach(worker);
    return { worker, ready: false, warming: false, interrupt, stopping: null };
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
    internal = false,
    persistent = false
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
        persistent,
        request
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

  /**
   * Drop every request of the previous token and stop whatever the active worker is running.
   * Python is interrupted in place when possible; the worker is only replaced (by a warm standby if
   * one is ready) when the page cannot interrupt it or the interrupt does not take effect.
   */
  /** this page can stop Python without losing the runtime's state (see python-interrupt.ts) */
  get canInterrupt(): boolean {
    return PythonInterrupt.supported;
  }

  /**
   * Interrupt the active worker's Python but keep every request and the runtime's state (e.g. a
   * live match). Resolves false if it could not be interrupted; the caller then restarts it.
   */
  async interruptActive(): Promise<boolean> {
    const slotIndex = this.activeWorkerSlot;
    const slot = this.workers[slotIndex];
    if (!slot.interrupt || !slot.ready) {
      return false;
    }
    return slot.interrupt.stop(() => this.sendRequest<void>(slotIndex, { type: 'ping' }, true, true));
  }

  /** `replace`: skip the interrupt and replace the worker right away (it is known to be stuck) */
  setMasterToken(masterToken: number, replace = false): boolean {
    if (this.masterToken === masterToken) {
      return false;
    }
    this.masterToken = masterToken;
    const stoppedSlot = this.activeWorkerSlot;
    let busy = false;
    for (const [id, pendingRequest] of this.pending) {
      if (pendingRequest.workerSlot === stoppedSlot) {
        busy = true;
      }
      if (pendingRequest.masterToken !== this.masterToken && !pendingRequest.persistent) {
        pendingRequest.reject(new Error('Dropped stale Pyodide request'));
        this.pending.delete(id);
      }
    }
    if (!busy) {
      return true; // nothing is running there
    }
    const slot = this.workers[stoppedSlot];
    if (replace || !slot.interrupt || (!slot.ready && !slot.stopping)) {
      // cannot interrupt, or the runtime is still booting (an interrupt would break the boot)
      this.swapOutWorker(stoppedSlot);
      return true;
    }
    const workerRef = slot.worker;
    this.ui.setStatus('loading', 'Stopping Python');
    const stopping = (slot.stopping ?? Promise.resolve()).then(() => this.interruptWorker(stoppedSlot, workerRef));
    slot.stopping = stopping;
    void stopping.finally(() => {
      if (this.workers[stoppedSlot].stopping === stopping) {
        this.workers[stoppedSlot].stopping = null;
      }
    });
    return true;
  }

  private async interruptWorker(slot: number, workerRef: Worker): Promise<void> {
    const current = this.workers[slot];
    if (current.worker !== workerRef || !current.interrupt) {
      return; // already replaced
    }
    const stopped = await current.interrupt.stop(() => this.sendRequest<void>(slot, { type: 'ping' }, true, true));
    if (this.workers[slot].worker !== workerRef) {
      return;
    }
    if (stopped) {
      this.logDebug('interrupted python in place', { slot });
      if (slot === this.activeWorkerSlot) {
        this.ui.setStatus('ready', 'Pyodide ready');
      }
      return;
    }
    this.logDebug('interrupt did not take effect, replacing worker', { slot });
    this.swapOutWorker(slot);
  }

  /** Kill a worker; if it was the active one, move to a warm standby (or reboot it in place). */
  private swapOutWorker(stoppedSlot: number): void {
    this.ui.setStatus('loading', 'Restarting Pyodide worker');
    const wasActive = stoppedSlot === this.activeWorkerSlot;
    if (wasActive) {
      const readyStandbySlot = this.pickReadyStandbySlot(stoppedSlot);
      if (readyStandbySlot !== null) {
        this.activeWorkerSlot = readyStandbySlot;
        this.logDebug('new active slot', { fromSlot: stoppedSlot, toSlot: readyStandbySlot });
      } else {
        this.logDebug('worker fallback: no warm standby ready, replacing active slot in place', {
          activeSlot: stoppedSlot
        });
      }
    }
    this.replaceWorker(stoppedSlot);
    // requests sent after the stop are waiting in the killed worker's queue: send them again
    for (const [id, entry] of this.pending) {
      if (entry.workerSlot !== stoppedSlot) {
        continue;
      }
      if (entry.persistent || entry.masterToken !== this.masterToken) {
        entry.reject(new Error('Pyodide worker restarted'));
        this.pending.delete(id);
        continue;
      }
      entry.workerSlot = this.activeWorkerSlot;
      this.workers[entry.workerSlot].worker.postMessage({ ...entry.request, id } as WorkerRequest);
    }
    this.warmStandbyWorkers();
    this.ui.setStatus('loading', 'Reinitializing Pyodide runtime');
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
    this.workers[slot] = this.createSlot(slot);
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
      if (message.ok && entry.request.type === 'ensureRunner') {
        this.workers[slot].ready = true;
        this.workers[slot].warming = false;
        this.markFirstReady();
      }
      if (entry.masterToken !== this.masterToken && !entry.persistent) {
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
