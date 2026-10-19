import type { StatusTone } from '@main/arena.constants';

type WorkerRequestPayload =
  | { type: 'ensureRunner' }
  | { type: 'listFileWarriors' }
  | { type: 'loadWarriorCode'; payload: { path: string } }
  | { type: 'compileWarrior'; payload: { code: string; config?: Record<string, unknown> } }
  | { type: 'initMatch'; payload: { config?: Record<string, unknown>; warriorSpecs?: Record<string, unknown>[] } }
  | { type: 'stepMatch'; payload: { matchId: number; steps?: number; view?: string; centerAddr?: number | null; window?: number | null } }
  | { type: 'getProcesses'; matchId: number }
  | { type: 'nextRound'; matchId: number }
  | { type: 'reloadRound'; matchId: number }
  | { type: 'destroyMatch'; matchId: number };

type WorkerRequest = WorkerRequestPayload & { id: number };

export interface CorewarUiCallbacks {
  setStatus: (tone: StatusTone, message: string) => void;
}

type WorkerResponse =
  | { kind: 'response'; id: number; ok: true; data: unknown }
  | { kind: 'response'; id: number; ok: false; error: string };

type WorkerEvent = { kind: 'status'; tone: StatusTone; message: string };

type WorkerMessage = WorkerResponse | WorkerEvent;

export class CorewarPyodideClient {
  private worker: Worker;
  private requestId = 0;
  private pending = new Map<
    number,
    { resolve: (value: unknown) => void; reject: (error: Error) => void }
  >();
  private debugLogs: [string, unknown][] = [];

  constructor(private readonly ui?: CorewarUiCallbacks) {
    this.worker = new Worker(new URL('./corewar-pyodide.worker', import.meta.url), {
      type: 'module'
    });
    this.worker.onmessage = (event: MessageEvent<WorkerMessage>) => {
      this.handleMessage(event.data);
    };
    this.worker.onerror = () => {
      const error = new Error('Corewar worker error');
      this.ui?.setStatus?.('error', 'Pyodide worker error');
      this.pending.forEach((entry) => entry.reject(error));
      this.pending.clear();
    };
    (window as any).COREWAR_DEBUG_LOGS = this.debugLogs;
    (window as any).COREWAR_PRINT_DEBUG_LOGS = () => {
      this.debugLogs.forEach(([timestamp, data]) => { console.debug(`${timestamp}`, data); });
    };
  }

  private logDebug(message: string, id: number, data: unknown): void {
    const now = new Date();
    const mm = String(now.getMinutes()).padStart(2, '0');
    const ss = String(now.getSeconds()).padStart(2, '0');
    const ms = String(now.getMilliseconds()).padStart(3, '0');
    const stamp = `[${mm}:${ss}.${ms}] [CorewarClient] ${message} ${id}`;
    this.debugLogs.push([stamp, data]);
    console.debug(stamp, data);
  }

  request<T>(request: WorkerRequestPayload): Promise<T> {
    const id = ++this.requestId;
    this.logDebug('send', id, request);
    return new Promise((resolve, reject) => {
      const resolveWithCast = (value: unknown) => resolve(value as T);
      this.pending.set(id, { resolve: resolveWithCast, reject });
      this.worker.postMessage({ ...request, id } as WorkerRequest);
    });
  }

  private handleMessage(message: WorkerMessage): void {
    const responseId = (message as WorkerResponse).id ?? -1;
    this.logDebug('recv', responseId, message);
    if (message.kind === 'status') {
      this.ui?.setStatus?.(message.tone, message.message);
      return;
    }
    if (message.kind !== 'response') {
      return;
    }
    const entry = this.pending.get(message.id);
    if (!entry) {
      return;
    }
    this.pending.delete(message.id);
    if (message.ok) {
      entry.resolve(message.data);
    } else {
      this.ui?.setStatus?.('error', 'Pyodide error');
      entry.reject(new Error(message.error));
    }
  }
}
