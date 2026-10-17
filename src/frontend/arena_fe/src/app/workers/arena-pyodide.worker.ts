/// <reference lib="webworker" />

import { OPEN_SPIEL_ARCHIVE } from '@main/arena.constants';
import { formatErrorLines, toJsValue } from '@main/arena.utils';
import type { MatchPayload, PyodideRuntime, StatusTone } from '@main/arena.constants';
import { INTERRUPT_PENDING_SLOT, INTERRUPT_SIGNAL_SLOT } from './python-interrupt';

type HungAutomatonChoice = 'random' | 'forfeit';

type PyodideMatchInit = {
  gameId: string;
  worldId: string;
  config: Record<string, unknown>;
  botA: string;
  botB: string;
};

type PyodideReplayRequest = {
  gameId: string;
  worldId: string;
  config: Record<string, unknown>;
  seed: number | null;
  moves: unknown[];
};

type PyodideFullMatchRequest = {
  gameId: string;
  worldId: string;
  config: Record<string, unknown>;
  botA: string;
  botB: string;
  seed: number;
  moveTimeout: number;
};

type WorkerRequest =
  | { id: number; type: 'ensureRunner' }
  | { id: number; type: 'replayMoves'; payload: PyodideReplayRequest }
  | { id: number; type: 'getGamePrompt'; gameId: string; worldId: string; config: Record<string, unknown> }
  | { id: number; type: 'setUserPolicy'; gameId: string; worldId: string; code: string; config: Record<string, unknown> | null; smoke?: boolean }
  | { id: number; type: 'smokeTestUserPolicy'; gameId: string; worldId: string; config: Record<string, unknown> | null; moveTimeout: number }
  | { id: number; type: 'playFullMatch'; payload: PyodideFullMatchRequest }
  | { id: number; type: 'loadBots'; gameId: string; worldId: string }
  | { id: number; type: 'initMatch'; payload: PyodideMatchInit }
  | { id: number; type: 'stepMatch' }
  | { id: number; type: 'submitHumanMove'; action: string; forceApply?: boolean }
  | { id: number; type: 'resolveHungAutomaton'; choice: HungAutomatonChoice }
  | { id: number; type: 'capturePyspielError' }
  | { id: number; type: 'retryOpenSpielInstall' }
  | { id: number; type: 'ping' };

/** sent once, right after the worker is created, when the page can share memory with it */
type InterruptBufferMessage = { type: 'setInterruptBuffer'; buffer: Int32Array };

type WorkerResponse =
  | { kind: 'response'; id: number; ok: true; data: unknown }
  | { kind: 'response'; id: number; ok: false; error: string };

type OpenSpielUpdate = {
  status: StatusTone;
  message: string;
  errorLines: string[];
  logLines: string[];
};

type WorkerEvent =
  | { kind: 'status'; tone: StatusTone; message: string }
  | { kind: 'openSpiel'; update: OpenSpielUpdate }
  | { kind: 'appendLogs'; lines: string[] }
  | { kind: 'matchProgress'; id: number; moves: number; player: number; last: [number, unknown, number] | null };

type GameCachePayload = {
  files?: string[];
};

const SHARED_ARENA_FILES = [
  'game_arena/base.py',
  'game_arena/prompt_render.py',
  'game_arena/typing.py',
  'game_arena/utils.py'
  // not needed
  // 'game_arena/live_play.py',
  // 'game_arena/prompter.py',
  // 'game_arena/run_leaderboard.py',
];

const ctx = self as DedicatedWorkerGlobalScope;

/** shared with the host (see python-interrupt.ts); null when the page is not cross-origin isolated */
let interruptBuffer: Int32Array | null = null;

class ArenaPyodideWorker {
  private static readonly BOT_CODE_FILE_SUFFIX = '/2.python_code.py';
  private static readonly BUILTIN_BOTS = new Set(['human', 'random', 'first', 'last', 'user']);

  private pyodidePromise: Promise<PyodideRuntime> | null = null;
  private sharedArenaLoaded = false;
  private gameArenaLoaded = new Set<string>();
  private runnerReady = false;
  private runnerCode: string | null = null;
  private openSpielLoaded = false;
  /** why the OpenSpiel install failed, so requests that need pyspiel fail loudly instead of at import time */
  private openSpielError: string | null = null;
  private gameCacheFiles = new Map<string, string[]>();
  private loadedFiles = new Set<string>();

  private toWorkerUrl(path: string): string {
    return new URL(path.replace(/^\/+/, ''), self.location.href).toString();
  }

  private logDebug(...args: unknown[]): void {
    const now = new Date();
    const mm = String(now.getMinutes()).padStart(2, '0');
    const ss = String(now.getSeconds()).padStart(2, '0');
    const ms = String(now.getMilliseconds()).padStart(3, '0');
    console.debug(`[${mm}:${ss}.${ms}] [ArenaPyodideWorker]`, ...args);
  }

  private async ensureGameCacheFiles(gameId: string): Promise<string[]> {
    const existing = this.gameCacheFiles.get(gameId);
    if (existing) {
      return existing;
    }
    const safeGameId = encodeURIComponent(gameId);
    const url = this.toWorkerUrl(`py/game_arena_cache/${safeGameId}.json`);
    this.logDebug('fetch start 6', url);
    const response = await fetch(url, { cache: 'no-store' });
    if (!response.ok) {
      throw new Error(`Failed to load game cache for ${gameId}`);
    }
    const cache = (await response.json()) as GameCachePayload;
    const files = Array.isArray(cache.files)
      ? cache.files.filter((file): file is string => typeof file === 'string')
      : [];
    this.gameCacheFiles.set(gameId, files);
    return files;
  }

  private async readArenaFile(file: string): Promise<string | null> {
    const url = this.toWorkerUrl(`py/${file}`);
    this.logDebug('fetch start 7', url);
    const response = await fetch(url, { cache: 'no-store' });
    if (!response.ok) {
      return null;
    }
    return await response.text();
  }

  async ensureBotCode(gameId: string, worldId: string, botId: string): Promise<void> {
    if (!botId || ArenaPyodideWorker.BUILTIN_BOTS.has(botId)) {
      return;
    }
    const path = `game_arena/${gameId}/examples/${worldId}/${botId}${ArenaPyodideWorker.BOT_CODE_FILE_SUFFIX}`;
    if (this.loadedFiles.has(path)) {
      return;
    }
    const gameFiles = await this.ensureGameCacheFiles(gameId);
    if (!gameFiles.includes(path)) {
      throw new Error(`Automaton code file not found for ${botId}`);
    }
    const pyodide = await this.getPyodide();
    const content = await this.readArenaFile(path);
    if (content === null) {
      throw new Error(`Failed to load automaton code for ${botId}`);
    }
    await this.loadImportsOf(pyodide, content);
    this.writePyFile(pyodide, `/home/src/${path}`, content);
    this.loadedFiles.add(path);
  }

  /** Fetch the Pyodide packages a piece of automaton code imports (e.g. scipy) before it runs. */
  private async loadImportsOf(pyodide: PyodideRuntime, code: string): Promise<void> {
    try {
      await pyodide.loadPackagesFromImports(code);
    } catch (error) {
      this.logDebug('could not load imports of automaton code', error);
    }
  }

  async ensureRunner(): Promise<void> {
    if (this.runnerReady) {
      return;
    }
    const pyodide = await this.getPyodide();
    if (!this.runnerCode) {
      const runnerUrl = this.toWorkerUrl('arena.runner.py');
      this.logDebug('fetch start 8', runnerUrl);
      const response = await fetch(runnerUrl);
      if (!response.ok) {
        throw new Error('Failed to load arena runner');
      }
      this.runnerCode = await response.text();
    }
    await pyodide.runPythonAsync(this.runnerCode);
    this.runnerReady = true;
  }

  async loadBots(gameId: string, worldId: string): Promise<{ bots?: string[]; error?: string }> {
    await this.ensureRunner();
    await this.ensureGameArena(gameId);
    const gameFiles = await this.ensureGameCacheFiles(gameId);
    const prefix = `game_arena/${gameId}/examples/${worldId}/`;
    const suffix = ArenaPyodideWorker.BOT_CODE_FILE_SUFFIX;
    const ids = new Set<string>();
    for (const file of gameFiles) {
      if (!file.startsWith(prefix) || !file.endsWith(suffix)) {
        continue;
      }
      const id = file.slice(prefix.length, file.length - suffix.length);
      if (!id) {
        continue;
      }
      ids.add(id);
    }
    return { bots: [...ids].sort() };
  }

  async initMatch(payload: PyodideMatchInit): Promise<MatchPayload> {
    const pyodide = await this.getPyodide();
    await this.ensureRunner();
    await this.ensureGameArena(payload.gameId, pyodide);
    await this.ensureBotCode(payload.gameId, payload.worldId, payload.botA);
    if (payload.botB !== payload.botA) {
      await this.ensureBotCode(payload.gameId, payload.worldId, payload.botB);
    }
    pyodide.globals.set('GAME_NAME', payload.gameId);
    pyodide.globals.set('WORLD_NAME', payload.worldId);
    pyodide.globals.set('GAME_CONFIG', pyodide.toPy(payload.config ?? {}));
    pyodide.globals.set('BOT_A', payload.botA);
    pyodide.globals.set('BOT_B', payload.botB);
    const result = await pyodide.runPythonAsync('init_match()');
    return this.toMatchPayload(result);
  }

  async stepMatch(): Promise<MatchPayload> {
    const pyodide = await this.getPyodide();
    const result = await pyodide.runPythonAsync('step_match()');
    return this.toMatchPayload(result);
  }

  async getGamePrompt(gameId: string, worldId: string, config: Record<string, unknown>): Promise<unknown> {
    const pyodide = await this.getPyodide();
    await this.ensureRunner();
    await this.ensureGameArena(gameId, pyodide);
    pyodide.globals.set('PROMPT_GAME', gameId);
    pyodide.globals.set('PROMPT_CONFIG', pyodide.toPy(config ?? {}));
    return toJsValue<unknown>(await pyodide.runPythonAsync('get_game_prompt(PROMPT_GAME, PROMPT_CONFIG)'));
  }

  async setUserPolicy(gameId: string, worldId: string, code: string, config: Record<string, unknown> | null, smoke = false): Promise<unknown> {
    const pyodide = await this.getPyodide();
    this.assertOpenSpiel();
    await this.ensureRunner();
    await this.ensureGameArena(gameId, pyodide);
    await this.loadImportsOf(pyodide, code);
    pyodide.globals.set('USER_GAME', gameId);
    pyodide.globals.set('USER_WORLD', worldId);
    pyodide.globals.set('USER_CODE', code);
    pyodide.globals.set('USER_CONFIG', pyodide.toPy(config ?? {}));
    pyodide.globals.set('USER_SMOKE', smoke);
    return toJsValue<unknown>(await pyodide.runPythonAsync('set_user_policy(USER_GAME, USER_WORLD, USER_CODE, USER_CONFIG, USER_SMOKE)'));
  }

  async smokeTestUserPolicy(gameId: string, worldId: string, config: Record<string, unknown> | null, moveTimeout: number): Promise<unknown> {
    const pyodide = await this.getPyodide();
    this.assertOpenSpiel();
    await this.ensureRunner();
    await this.ensureGameArena(gameId, pyodide);
    pyodide.globals.set('SMOKE_GAME', gameId);
    pyodide.globals.set('SMOKE_WORLD', worldId);
    pyodide.globals.set('SMOKE_CONFIG', pyodide.toPy(config ?? {}));
    pyodide.globals.set('SMOKE_TIMEOUT', moveTimeout);
    return toJsValue<unknown>(await pyodide.runPythonAsync('smoke_test_user_policy(SMOKE_GAME, SMOKE_WORLD, SMOKE_CONFIG, SMOKE_TIMEOUT)'));
  }

  async playFullMatch(payload: PyodideFullMatchRequest, requestId: number): Promise<unknown> {
    const pyodide = await this.getPyodide();
    this.assertOpenSpiel();
    await this.ensureRunner();
    await this.ensureGameArena(payload.gameId, pyodide);
    await this.ensureBotCode(payload.gameId, payload.worldId, payload.botA);
    if (payload.botB !== payload.botA) {
      await this.ensureBotCode(payload.gameId, payload.worldId, payload.botB);
    }
    pyodide.globals.set('FM_GAME', payload.gameId);
    pyodide.globals.set('FM_WORLD', payload.worldId);
    pyodide.globals.set('FM_CONFIG', pyodide.toPy(payload.config ?? {}));
    pyodide.globals.set('FM_A', payload.botA);
    pyodide.globals.set('FM_B', payload.botB);
    pyodide.globals.set('FM_SEED', payload.seed);
    pyodide.globals.set('FM_TIMEOUT', payload.moveTimeout);
    // heartbeat before every move; postMessage from a busy worker is queued and delivered normally
    pyodide.globals.set('FM_PROGRESS', (moves: number, player: number, lastJson: string | null | undefined) => {
      const last = typeof lastJson === 'string' ? (JSON.parse(lastJson) as [number, unknown, number]) : null;
      ctx.postMessage({ kind: 'matchProgress', id: requestId, moves: Number(moves), player: Number(player), last } satisfies WorkerEvent);
    });
    return toJsValue<unknown>(
      await pyodide.runPythonAsync('play_full_match(FM_GAME, FM_WORLD, FM_CONFIG, FM_A, FM_B, FM_SEED, FM_TIMEOUT, FM_PROGRESS)')
    );
  }

  async replayMoves(payload: PyodideReplayRequest): Promise<unknown> {
    const pyodide = await this.getPyodide();
    this.assertOpenSpiel();
    await this.ensureRunner();
    await this.ensureGameArena(payload.gameId, pyodide);
    pyodide.globals.set('REPLAY_GAME', payload.gameId);
    pyodide.globals.set('REPLAY_WORLD', payload.worldId);
    pyodide.globals.set('REPLAY_CONFIG', pyodide.toPy(payload.config ?? {}));
    pyodide.globals.set('REPLAY_SEED', payload.seed ?? null);
    pyodide.globals.set('REPLAY_MOVES', pyodide.toPy(payload.moves ?? []));
    const result = await pyodide.runPythonAsync(
      'replay_moves(REPLAY_GAME, REPLAY_WORLD, REPLAY_CONFIG, REPLAY_SEED, REPLAY_MOVES)'
    );
    return toJsValue<unknown>(result);
  }

  async resolveHungAutomaton(choice: HungAutomatonChoice): Promise<MatchPayload> {
    const pyodide = await this.getPyodide();
    pyodide.globals.set('HUNG_CHOICE', choice);
    return this.toMatchPayload(await pyodide.runPythonAsync('resolve_hung_automaton(HUNG_CHOICE)'));
  }

  async submitHumanMove(action: string, forceApply = false): Promise<MatchPayload> {
    const pyodide = await this.getPyodide();
    await this.ensureRunner();
    pyodide.globals.set('HUMAN_ACTION', action);
    pyodide.globals.set('HUMAN_ACTION_FORCE_APPLY', forceApply);
    const result = await pyodide.runPythonAsync(
      'submit_human_move(HUMAN_ACTION, HUMAN_ACTION_FORCE_APPLY)'
    );
    return this.toMatchPayload(result);
  }

  async capturePyspielError(): Promise<string[]> {
    try {
      const pyodide = await this.getPyodide();
      const script = [
        'import traceback',
        'result = {"ok": True, "error": ""}',
        'try:',
        '    import pyspiel',
        'except Exception:',
        '    result["ok"] = False',
        '    result["error"] = traceback.format_exc()',
        'result'
      ].join('\n');
      const rawResult = await pyodide.runPythonAsync(script);
      const result = toJsValue<{ ok?: boolean; error?: string }>(rawResult) ?? {};
      if (result.ok) {
        return [];
      }
      return formatErrorLines(result.error ?? 'Unknown error');
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      return formatErrorLines(message);
    }
  }

  async retryOpenSpielInstall(): Promise<void> {
    try {
      const pyodide = await this.getPyodide();
      await this.ensureOpenSpiel(pyodide, true);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      const logLines = ['OpenSpiel retry failed:', ...formatErrorLines(message)];
      this.emitLogs(logLines);
      this.emitOpenSpiel({
        status: 'error',
        message: 'OpenSpiel install failed',
        errorLines: formatErrorLines(message),
        logLines
      });
    }
  }

  private async getPyodide(): Promise<PyodideRuntime> {
    if (!this.pyodidePromise) {
      this.pyodidePromise = this.initPyodide();
    }
    return this.pyodidePromise;
  }

  private async initPyodide(): Promise<PyodideRuntime> {
    this.emitStatus('loading', 'Loading Pyodide runtime');
    if (!(self as { loadPyodide?: unknown }).loadPyodide) {
      try {
        const module = await import('https://cdn.jsdelivr.net/pyodide/v0.26.2/full/pyodide.mjs');
        (self as { loadPyodide?: unknown }).loadPyodide = module.loadPyodide ?? module.default;
      } catch {
        // Fall back to importScripts when module import fails.
      }
      if (!(self as { loadPyodide?: unknown }).loadPyodide) {
        if (typeof importScripts !== 'function') {
          throw new Error('Pyodide loader not available');
        }
        try {
          importScripts('https://cdn.jsdelivr.net/pyodide/v0.26.2/full/pyodide.js');
        } catch {
          throw new Error('Failed to load Pyodide script');
        }
      }
    }
    const loader = (self as {
      loadPyodide?: (config: { indexURL: string }) => Promise<unknown>;
    }).loadPyodide;
    if (!loader) {
      throw new Error('Pyodide loader not available');
    }
    const pyodide = (await loader({
      indexURL: 'https://cdn.jsdelivr.net/pyodide/v0.26.2/full/'
    })) as PyodideRuntime;
    if (interruptBuffer) {
      pyodide.setInterruptBuffer(interruptBuffer);
    }
    this.emitStatus('loading', 'Loading numpy');
    await pyodide.loadPackage(['numpy']);
    this.emitStatus('loading', 'Loading game arena');
    await this.ensureOpenSpiel(pyodide);
    await this.ensureSharedArena(pyodide);
    this.emitStatus('ready', 'Pyodide ready');
    return pyodide;
  }

  private async ensureOpenSpiel(pyodide: PyodideRuntime, force = false): Promise<void> {
    if (this.openSpielLoaded && !force) {
      return;
    }
    const archiveUrl = new URL(OPEN_SPIEL_ARCHIVE, self.location.href).toString();
    this.emitOpenSpiel({
      status: 'loading',
      message: 'Installing OpenSpiel',
      errorLines: [],
      logLines: [`OpenSpiel install started: ${archiveUrl}`]
    });
    let detail: string | null = null;
    // one automatic retry: a transient fetch or memory hiccup should not leave this runtime without pyspiel
    for (let attempt = 0; attempt < 2; attempt += 1) {
      detail = await this.installOpenSpiel(pyodide, archiveUrl);
      if (detail === null) {
        break;
      }
      this.emitLogs([`OpenSpiel install attempt ${attempt + 1} failed:`, ...formatErrorLines(detail)]);
    }
    this.openSpielLoaded = true;
    this.openSpielError = detail;
    if (detail === null) {
      const logLines = [`OpenSpiel loaded from ${archiveUrl}`];
      this.emitLogs(logLines);
      this.emitOpenSpiel({ status: 'ready', message: 'OpenSpiel ready', errorLines: [], logLines });
      return;
    }
    const logLines = ['OpenSpiel install failed:', ...formatErrorLines(detail)];
    this.emitLogs(logLines);
    this.emitOpenSpiel({ status: 'error', message: 'OpenSpiel install failed', errorLines: formatErrorLines(detail), logLines });
  }

  /** one install attempt; resolves to null on success or the error text */
  private async installOpenSpiel(pyodide: PyodideRuntime, archiveUrl: string): Promise<string | null> {
    try {
      await pyodide.loadPackage(['micropip']);
      const script = [
        'import micropip',
        'import traceback',
        'result = {"ok": False, "error": ""}',
        'try:',
        // open_spiel lists scipy (10 MB, ~47 MB in memory) and pip as requirements, but the game
        // engines never import them: install it without its listed requirements, add the small ones
        // that are used, and load scipy only for code that imports it (see loadImportsOf)
        `    await micropip.install(${JSON.stringify(archiveUrl)}, deps=False)`,
        "    await micropip.install(['attrs', 'absl-py', 'ml-collections'])",
        '    import pyspiel  # fail here, not at the first game import',
        '    result["ok"] = True',
        'except Exception:',
        '    result["error"] = traceback.format_exc()',
        'result'
      ].join('\n');
      const rawResult = await pyodide.runPythonAsync(script);
      const result = toJsValue<{ ok?: boolean; error?: string }>(rawResult) ?? {};
      return result.ok ? null : result.error?.trim() || 'Unknown error';
    } catch (error) {
      return error instanceof Error ? error.message : String(error);
    }
  }

  /** throw if this runtime has no working pyspiel; used by every request that plays or replays a game */
  private assertOpenSpiel(): void {
    if (this.openSpielError) {
      throw new Error(`OpenSpiel is not available in this runtime: ${this.openSpielError.split('\n').slice(-1)[0]}`);
    }
  }

  private async ensureSharedArena(pyodide?: PyodideRuntime): Promise<void> {
    if (this.sharedArenaLoaded) {
      return;
    }
    const basePath = '/home/src';
    const pyRuntime = pyodide ?? (await this.getPyodide());
    this.ensureDir(pyRuntime, basePath);
    for (const file of SHARED_ARENA_FILES) {
      if (this.loadedFiles.has(file)) {
        continue;
      }
      const content = await this.readArenaFile(file);
      if (content === null) {
        continue;
      }
      this.writePyFile(pyRuntime, `${basePath}/${file}`, content);
      this.loadedFiles.add(file);
    }
    pyRuntime.runPython(
      "import sys\nsys.path.append('/home/src') if '/home/src' not in sys.path else None"
    );
    this.sharedArenaLoaded = true;
  }

  private async ensureGameArena(gameId: string, pyodide?: PyodideRuntime): Promise<void> {
    if (this.gameArenaLoaded.has(gameId)) {
      return;
    }
    const pyRuntime = pyodide ?? (await this.getPyodide());
    await this.ensureSharedArena(pyRuntime);
    const gameFiles = await this.ensureGameCacheFiles(gameId);
    const baseFiles = gameFiles.filter(
      (file) =>
        file.startsWith(`game_arena/${gameId}/`) &&
        file.endsWith('.py') &&
        !file.includes('/examples/')
    );
    const basePath = '/home/src';
    this.ensureDir(pyRuntime, basePath);
    for (const file of baseFiles) {
      if (this.loadedFiles.has(file)) {
        continue;
      }
      const content = await this.readArenaFile(file);
      if (content === null) {
        continue;
      }
      this.writePyFile(pyRuntime, `${basePath}/${file}`, content);
      this.loadedFiles.add(file);
    }
    this.gameArenaLoaded.add(gameId);
  }

  private ensureDir(pyodide: { FS: { mkdir: (path: string) => void } }, path: string): void {
    const parts = path.split('/').filter(Boolean);
    let current = '';
    for (const part of parts) {
      current += `/${part}`;
      try {
        pyodide.FS.mkdir(current);
      } catch {
        // Ignore if the directory already exists.
      }
    }
  }

  private writePyFile(
    pyodide: { FS: { mkdir: (path: string) => void; writeFile: (path: string, data: string) => void } },
    targetPath: string,
    content: string
  ): void {
    const dir = targetPath.slice(0, Math.max(0, targetPath.lastIndexOf('/')));
    if (dir) {
      this.ensureDir(pyodide, dir);
    }
    pyodide.FS.writeFile(targetPath, content);
  }

  private toMatchPayload(value: unknown): MatchPayload {
    return toJsValue<MatchPayload>(value) ?? {};
  }

  private emitStatus(tone: StatusTone, message: string): void {
    const payload: WorkerEvent = { kind: 'status', tone, message };
    ctx.postMessage(payload);
  }

  private emitOpenSpiel(update: OpenSpielUpdate): void {
    const payload: WorkerEvent = { kind: 'openSpiel', update };
    ctx.postMessage(payload);
  }

  private emitLogs(lines: string[]): void {
    const payload: WorkerEvent = { kind: 'appendLogs', lines };
    ctx.postMessage(payload);
  }
}

const worker = new ArenaPyodideWorker();

const sendResponse = (response: WorkerResponse): void => {
  ctx.postMessage(response);
};

const handleRequest = async (request: WorkerRequest): Promise<void> => {
  const { id } = request;
  if (interruptBuffer) {
    if (request.type === 'ping') {
      // everything queued before the host's interrupt has run: stop interrupting
      Atomics.store(interruptBuffer, INTERRUPT_PENDING_SLOT, 0);
      Atomics.store(interruptBuffer, INTERRUPT_SIGNAL_SLOT, 0);
    } else if (Atomics.load(interruptBuffer, INTERRUPT_PENDING_SLOT) === 0) {
      // drop an interrupt that arrived after the Python it was meant for had already returned
      Atomics.store(interruptBuffer, INTERRUPT_SIGNAL_SLOT, 0);
    }
  }
  try {
    switch (request.type) {
      case 'ping': {
        sendResponse({ kind: 'response', id, ok: true, data: null });
        break;
      }
      case 'ensureRunner': {
        await worker.ensureRunner();
        sendResponse({ kind: 'response', id, ok: true, data: null });
        break;
      }
      case 'loadBots': {
        const data = await worker.loadBots(request.gameId, request.worldId);
        sendResponse({ kind: 'response', id, ok: true, data });
        break;
      }
      case 'initMatch': {
        const data = await worker.initMatch(request.payload);
        sendResponse({ kind: 'response', id, ok: true, data });
        break;
      }
      case 'stepMatch': {
        const data = await worker.stepMatch();
        sendResponse({ kind: 'response', id, ok: true, data });
        break;
      }
      case 'replayMoves': {
        const data = await worker.replayMoves(request.payload);
        sendResponse({ kind: 'response', id, ok: true, data });
        break;
      }
      case 'getGamePrompt': {
        const data = await worker.getGamePrompt(request.gameId, request.worldId, request.config);
        sendResponse({ kind: 'response', id, ok: true, data });
        break;
      }
      case 'setUserPolicy': {
        const data = await worker.setUserPolicy(request.gameId, request.worldId, request.code, request.config, request.smoke ?? false);
        sendResponse({ kind: 'response', id, ok: true, data });
        break;
      }
      case 'smokeTestUserPolicy': {
        const data = await worker.smokeTestUserPolicy(request.gameId, request.worldId, request.config, request.moveTimeout);
        sendResponse({ kind: 'response', id, ok: true, data });
        break;
      }
      case 'playFullMatch': {
        const data = await worker.playFullMatch(request.payload, id);
        sendResponse({ kind: 'response', id, ok: true, data });
        break;
      }
      case 'resolveHungAutomaton': {
        const data = await worker.resolveHungAutomaton(request.choice);
        sendResponse({ kind: 'response', id, ok: true, data });
        break;
      }
      case 'submitHumanMove': {
        const data = await worker.submitHumanMove(request.action, Boolean(request.forceApply));
        sendResponse({ kind: 'response', id, ok: true, data });
        break;
      }
      case 'capturePyspielError': {
        const data = await worker.capturePyspielError();
        sendResponse({ kind: 'response', id, ok: true, data });
        break;
      }
      case 'retryOpenSpielInstall': {
        await worker.retryOpenSpielInstall();
        sendResponse({ kind: 'response', id, ok: true, data: null });
        break;
      }
      default: {
        sendResponse({ kind: 'response', id, ok: false, error: 'Unknown request type' });
        break;
      }
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    sendResponse({ kind: 'response', id, ok: false, error: message });
  }
};

ctx.onmessage = (event: MessageEvent<WorkerRequest | InterruptBufferMessage>) => {
  const message = event.data;
  if (message.type === 'setInterruptBuffer') {
    interruptBuffer = message.buffer;
    return;
  }
  void handleRequest(message);
};
