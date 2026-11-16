/// <reference lib="webworker" />

import { toJsValue } from '@main/arena.utils';
import type { PyodideRuntime, StatusTone } from '@main/arena.constants';

type CorewarMatchInit = {
  config?: Record<string, unknown>;
  warriorSpecs?: Record<string, unknown>[];
};

type CorewarCompilePayload = {
  code: string;
  config?: Record<string, unknown>;
};

type CorewarLoadWarriorCodePayload = {
  path: string;
};

type CorewarStepPayload = {
  matchId: number;
  steps?: number;
  view?: string;
  centerAddr?: number | null;
  window?: number | null;
};

type WorkerRequest =
  | { id: number; type: 'ensureRunner' }
  | { id: number; type: 'listFileWarriors' }
  | { id: number; type: 'loadWarriorCode'; payload: CorewarLoadWarriorCodePayload }
  | { id: number; type: 'compileWarrior'; payload: CorewarCompilePayload }
  | { id: number; type: 'initMatch'; payload: CorewarMatchInit }
  | { id: number; type: 'stepMatch'; payload: CorewarStepPayload }
  | { id: number; type: 'getProcesses'; matchId: number }
  | { id: number; type: 'nextRound'; matchId: number }
  | { id: number; type: 'reloadRound'; matchId: number }
  | { id: number; type: 'destroyMatch'; matchId: number };

type WorkerResponse =
  | { kind: 'response'; id: number; ok: true; data: unknown }
  | { kind: 'response'; id: number; ok: false; error: string };

type WorkerEvent = { kind: 'status'; tone: StatusTone; message: string };

type CloneWarsCachePayload = {
  files: string[];
};

type WarriorListing = {
  name: string;
  value: string;
  source: 'inline';
  code: string;
  path: string;
  codeLoaded: boolean;
};

const ctx = self as DedicatedWorkerGlobalScope;

class CorewarPyodideWorker {
  private pyodidePromise: Promise<PyodideRuntime> | null = null;
  private runnerReady = false;
  private runnerCode: string | null = null;
  private cacheLoaded = false;
  private cloneWarsFiles: string[] = [];
  private cloneWarsFileSet = new Set<string>();
  private cloneWarsLoaded = false;

  private toWorkerUrl(path: string): string {
    return new URL(path.replace(/^\/+/, ''), self.location.href).toString();
  }

  private logDebug(...args: unknown[]): void {
    const now = new Date();
    const mm = String(now.getMinutes()).padStart(2, '0');
    const ss = String(now.getSeconds()).padStart(2, '0');
    const ms = String(now.getMilliseconds()).padStart(3, '0');
    console.debug(`[${mm}:${ss}.${ms}] [CorewarPyodideWorker]`, ...args);
  }

  private emitStatus(tone: StatusTone, message: string): void {
    const payload: WorkerEvent = { kind: 'status', tone, message };
    ctx.postMessage(payload);
  }

  private async getPyodide(): Promise<PyodideRuntime> {
    if (!this.pyodidePromise) {
      this.pyodidePromise = this.initPyodide();
    }
    return this.pyodidePromise;
  }

  private async initPyodide(): Promise<PyodideRuntime> {
    this.emitStatus('loading', 'Loading Pyodide runtime');
    await this.ensurePyodideScript();
    const loader = (self as { loadPyodide?: (config: { indexURL: string }) => Promise<unknown> })
      .loadPyodide;
    if (!loader) {
      throw new Error('Pyodide loader not available');
    }
    const pyodide = (await loader({
      indexURL: 'https://cdn.jsdelivr.net/pyodide/v0.26.2/full/'
    })) as PyodideRuntime;
    this.emitStatus('loading', 'Loading numpy');
    await pyodide.loadPackage(['numpy']);
    this.emitStatus('ready', '');
    return pyodide;
  }

  private async ensurePyodideScript(): Promise<void> {
    if ((self as { loadPyodide?: unknown }).loadPyodide) {
      return;
    }
    try {
      const module = await import('https://cdn.jsdelivr.net/pyodide/v0.26.2/full/pyodide.mjs');
      (self as { loadPyodide?: unknown }).loadPyodide = module.loadPyodide ?? module.default;
      if ((self as { loadPyodide?: unknown }).loadPyodide) {
        return;
      }
    } catch {
      // fall through to importScripts
    }
    if (typeof importScripts === 'function') {
      try {
        importScripts('https://cdn.jsdelivr.net/pyodide/v0.26.2/full/pyodide.js');
        return;
      } catch {
        throw new Error('Failed to load Pyodide script');
      }
    }
    throw new Error('Pyodide loader not available');
  }

  private async ensureCloneWarsCache(): Promise<void> {
    if (this.cacheLoaded) {
      return;
    }
    const cacheUrl = this.toWorkerUrl('py/game_arena_cache/clone_wars.json');
    this.logDebug('fetch cache', cacheUrl);
    const response = await fetch(cacheUrl, { cache: 'no-store' });
    if (!response.ok) {
      throw new Error('Failed to load clone_wars cache');
    }
    const cache = (await response.json()) as CloneWarsCachePayload;
    if (!Array.isArray(cache.files)) {
      throw new Error('clone_wars cache payload is invalid');
    }
    this.cloneWarsFiles = cache.files.filter((file) => typeof file === 'string');
    this.cloneWarsFileSet = new Set(this.cloneWarsFiles);
    this.cacheLoaded = true;
  }

  private shouldLoadRuntimeCloneWarsFile(file: string): boolean {
    if (!file.startsWith('game_arena/clone_wars/drq/')) {
      return false;
    }
    if (file.includes('/tests/') || file.endsWith('/tests.py')) {
      return false;
    }

    if (file === 'game_arena/clone_wars/drq/src/corewar_util.py') {
      return true;
    }
    if (file.startsWith('game_arena/clone_wars/drq/corewar/corewar/') && file.endsWith('.py')) {
      return true;
    }
    return false;
  }

  private toWarriorListing(file: string): WarriorListing | null {
    if (!file.endsWith('.red')) {
      return null;
    }
    let prefix: 'orig' | 'drq' | 'gw' | null = null;
    if (file.startsWith('game_arena/clone_wars/drq/corewar/warriors/')) {
      prefix = 'orig';
    } else if (file.startsWith('game_arena/clone_wars/drq/human_warriors/')) {
      prefix = 'drq';
    } else if (file.startsWith('game_arena/clone_wars/drq/corewar/gpt_warriors/')) {
      prefix = 'gw';
    }
    if (!prefix) {
      return null;
    }
    const fileName = file.split('/').pop();
    if (!fileName) {
      return null;
    }
    const name = `${prefix}:${fileName}`;
    return {
      name,
      value: name,
      source: 'inline',
      code: '',
      path: file,
      codeLoaded: false
    };
  }

  private async readCloneWarsFile(file: string): Promise<string> {
    const fileUrl = this.toWorkerUrl(`py/${file}`);
    this.logDebug('fetch file', fileUrl);
    const response = await fetch(fileUrl, { cache: 'no-store' });
    if (!response.ok) {
      throw new Error(`Failed to load clone_wars file: ${file}`);
    }
    const text = await response.text();
    const contentType = response.headers.get('content-type') ?? '';
    const htmlFallback = contentType.includes('text/html') || text.trimStart().startsWith('<!doctype html');
    if (htmlFallback) {
      throw new Error(`clone_wars file resolved to HTML fallback: ${file}`);
    }
    return text;
  }

  private ensureDir(pyodide: { FS: { mkdir: (path: string) => void } }, path: string): void {
    const parts = path.split('/').filter(Boolean);
    let current = '';
    for (const part of parts) {
      current += `/${part}`;
      try {
        pyodide.FS.mkdir(current);
      } catch {
        // already exists
      }
    }
  }

  private writePyFile(
    pyodide: { FS: { mkdir: (path: string) => void; writeFile: (path: string, data: string) => void } },
    targetPath: string,
    content: string
  ): void {
    const dir = targetPath.split('/').slice(0, -1).join('/');
    if (dir) {
      this.ensureDir(pyodide, dir);
    }
    pyodide.FS.writeFile(targetPath, content);
  }

  private async ensureCloneWars(pyodide: PyodideRuntime): Promise<void> {
    if (this.cloneWarsLoaded) {
      return;
    }
    await this.ensureCloneWarsCache();
    const filesToLoad = this.cloneWarsFiles.filter((file) => this.shouldLoadRuntimeCloneWarsFile(file));
    if (filesToLoad.length === 0) {
      throw new Error('clone_wars cache did not contain required Corewar files');
    }

    const basePath = '/home/src';
    this.ensureDir(pyodide, basePath);
    for (const file of filesToLoad) {
      const content = await this.readCloneWarsFile(file);
      this.writePyFile(pyodide, `${basePath}/${file}`, content);
    }
    this.cloneWarsLoaded = true;
  }

  async ensureRunner(): Promise<void> {
    if (this.runnerReady) {
      return;
    }
    this.emitStatus('loading', 'Loading Core Wars');
    const pyodide = await this.getPyodide();
    await this.ensureCloneWars(pyodide);
    if (!this.runnerCode) {
      const runnerUrl = this.toWorkerUrl('corewar.runner.py');
      this.logDebug('fetch runner', runnerUrl);
      const response = await fetch(runnerUrl, { cache: 'no-store' });
      if (!response.ok) {
        throw new Error('Failed to load corewar runner');
      }
      this.runnerCode = await response.text();
    }
    const code = `__file__ = '/home/src/corewar.runner.py'\n${this.runnerCode}`;
    await pyodide.runPythonAsync(code);
    this.runnerReady = true;
    this.emitStatus('ready', '');
  }

  async listFileWarriors(): Promise<unknown> {
    await this.ensureCloneWarsCache();
    const warriors = this.cloneWarsFiles
      .map((file) => this.toWarriorListing(file))
      .filter((warrior): warrior is WarriorListing => warrior !== null)
      .sort((a, b) => a.name.localeCompare(b.name));
    if (warriors.length === 0) {
      return { warriors: [], error: 'warriors directories not found' };
    }
    return { warriors, error: null };
  }

  async loadWarriorCode(payload: CorewarLoadWarriorCodePayload): Promise<unknown> {
    await this.ensureCloneWarsCache();
    const file = payload.path;
    if (!this.cloneWarsFileSet.has(file)) {
      throw new Error(`Unknown warrior path: ${file}`);
    }
    if (!this.toWarriorListing(file)) {
      throw new Error(`Unsupported warrior path: ${file}`);
    }
    const code = await this.readCloneWarsFile(file);
    return { code };
  }

  async initMatch(payload: CorewarMatchInit): Promise<unknown> {
    const pyodide = await this.getPyodide();
    await this.ensureRunner();
    pyodide.globals.set('CW_CONFIG', pyodide.toPy(payload.config ?? {}));
    pyodide.globals.set('CW_WARRIOR_SPECS', pyodide.toPy(payload.warriorSpecs ?? []));
    const result = await pyodide.runPythonAsync('init_match(config=CW_CONFIG, warrior_specs=CW_WARRIOR_SPECS)');
    return toJsValue(result) ?? {};
  }

  async compileWarrior(payload: CorewarCompilePayload): Promise<unknown> {
    const pyodide = await this.getPyodide();
    await this.ensureRunner();
    pyodide.globals.set('CW_CODE', payload.code ?? '');
    pyodide.globals.set('CW_CONFIG', pyodide.toPy(payload.config ?? {}));
    const result = await pyodide.runPythonAsync('compile_warrior(CW_CODE, config=CW_CONFIG)');
    return toJsValue(result) ?? {};
  }

  async stepMatch(payload: CorewarStepPayload): Promise<unknown> {
    const pyodide = await this.getPyodide();
    await this.ensureRunner();
    pyodide.globals.set('CW_MATCH_ID', payload.matchId);
    pyodide.globals.set('CW_STEPS', payload.steps ?? 1);
    pyodide.globals.set('CW_VIEW', payload.view ?? 'summary');
    pyodide.globals.set('CW_CENTER', payload.centerAddr ?? null);
    pyodide.globals.set('CW_WINDOW', payload.window ?? null);
    const result = await pyodide.runPythonAsync(
      'step_match(CW_MATCH_ID, steps=CW_STEPS, view=CW_VIEW, center_addr=CW_CENTER, window=CW_WINDOW)'
    );
    return toJsValue(result) ?? {};
  }

  async getProcesses(matchId: number): Promise<unknown> {
    const pyodide = await this.getPyodide();
    await this.ensureRunner();
    pyodide.globals.set('CW_MATCH_ID', matchId);
    const result = await pyodide.runPythonAsync('get_processes(CW_MATCH_ID)');
    return toJsValue(result) ?? {};
  }

  async nextRound(matchId: number): Promise<unknown> {
    const pyodide = await this.getPyodide();
    await this.ensureRunner();
    pyodide.globals.set('CW_MATCH_ID', matchId);
    const result = await pyodide.runPythonAsync('next_round(CW_MATCH_ID)');
    return toJsValue(result) ?? {};
  }

  async reloadRound(matchId: number): Promise<unknown> {
    const pyodide = await this.getPyodide();
    await this.ensureRunner();
    pyodide.globals.set('CW_MATCH_ID', matchId);
    const result = await pyodide.runPythonAsync('reload_round(CW_MATCH_ID)');
    return toJsValue(result) ?? {};
  }

  async destroyMatch(matchId: number): Promise<unknown> {
    const pyodide = await this.getPyodide();
    await this.ensureRunner();
    pyodide.globals.set('CW_MATCH_ID', matchId);
    const result = await pyodide.runPythonAsync('destroy_match(CW_MATCH_ID)');
    return toJsValue(result) ?? {};
  }
}

const worker = new CorewarPyodideWorker();

const sendResponse = (response: WorkerResponse): void => {
  ctx.postMessage(response);
};

const handleRequest = async (request: WorkerRequest): Promise<void> => {
  try {
    switch (request.type) {
      case 'ensureRunner':
        await worker.ensureRunner();
        sendResponse({ kind: 'response', id: request.id, ok: true, data: { ok: true } });
        return;
      case 'listFileWarriors': {
        const data = await worker.listFileWarriors();
        sendResponse({ kind: 'response', id: request.id, ok: true, data });
        return;
      }
      case 'loadWarriorCode': {
        const data = await worker.loadWarriorCode(request.payload);
        sendResponse({ kind: 'response', id: request.id, ok: true, data });
        return;
      }
      case 'compileWarrior': {
        const data = await worker.compileWarrior(request.payload);
        sendResponse({ kind: 'response', id: request.id, ok: true, data });
        return;
      }
      case 'initMatch': {
        const data = await worker.initMatch(request.payload);
        sendResponse({ kind: 'response', id: request.id, ok: true, data });
        return;
      }
      case 'stepMatch': {
        const data = await worker.stepMatch(request.payload);
        sendResponse({ kind: 'response', id: request.id, ok: true, data });
        return;
      }
      case 'getProcesses': {
        const data = await worker.getProcesses(request.matchId);
        sendResponse({ kind: 'response', id: request.id, ok: true, data });
        return;
      }
      case 'nextRound': {
        const data = await worker.nextRound(request.matchId);
        sendResponse({ kind: 'response', id: request.id, ok: true, data });
        return;
      }
      case 'reloadRound': {
        const data = await worker.reloadRound(request.matchId);
        sendResponse({ kind: 'response', id: request.id, ok: true, data });
        return;
      }
      case 'destroyMatch': {
        const data = await worker.destroyMatch(request.matchId);
        sendResponse({ kind: 'response', id: request.id, ok: true, data });
        return;
      }
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    sendResponse({ kind: 'response', id: request.id, ok: false, error: message });
  }
};

ctx.onmessage = (event: MessageEvent<WorkerRequest>) => {
  void handleRequest(event.data);
};
