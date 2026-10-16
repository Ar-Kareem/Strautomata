import { Injectable, NgZone, Signal } from '@angular/core';
import { ActionsSubject, type Action, Store } from '@ngrx/store';
import { ArenaPyodideClient, type PyodideFullMatchRequest, type PyodideReplayRequest } from '../workers/arena-pyodide.client';
import {
  buildBotOptions,
  formatGameDescription,
  formatGameLabel,
  getActiveGame,
  getHashRouteState,
  includeGameInDropdown,
  normalizeLogs,
  parseEloCsv,
  resolveEloColumn,
  setHashRouteState
} from '@main/arena.utils';
import type {
  BotOption,
  GameWorldOption,
  MatchPayload,
  MatchResultSummary
} from '@main/arena.constants';
import { DEFAULT_GAME_ID, GAME_GUI_IDS } from '@main/arena.constants';
import type { ArenaState, MatchupMode } from '@main/arena.store';
import { arenaActions } from '@main/arena.store';

@Injectable({ providedIn: 'root' })
export class ArenaMatchRunner {
  private isPlaying = false;
  private matchReady = false;
  private outputLines: string[] = [];
  private moveSpeed = 20;
  private readonly maxMoveSpeed = 20;
  private readonly repeatMatches = true;
  private readonly swapEveryMatch = true;
  private readonly state: Signal<ArenaState>;

  private readonly pyodideClient: ArenaPyodideClient;
  private openSpielLogLines: string[] = [];
  private botsLoadToken = 0;
  private botsLoadKey = '';
  private eloLoad: Promise<void> | null = null;
  private botStrategyCache = new Map<string, string>();
  private botStrategyLoadTokenA = 0;
  private botStrategyLoadTokenB = 0;
  private initStarted = false;

  private lastRunKey = '';
  private stepTimer: number | null = null;
  private stepInFlight = false;
  private pyodideMasterToken = 0;
  private pendingSingleStep = false;
  private matchToken = 0;
  private readonly maxOutputLines = 300;
  private readonly restartDelayMs = 3000;
  private seriesMatchIndex = 0;
  private currentBotAId: string | null = null;
  private currentBotBId: string | null = null;
  private matchObservation: unknown | null = null;
  private illegalAction: string | null = null;
  private awaitingHumanMove = false;
  private legalMoves: string[] = [];
  private readonly PYODIDE_GRACE_PERIOD_MS = 1000;

  private toAppUrl(path: string): string {
    return new URL(path.replace(/^\/+/, ''), document.baseURI).toString();
  }

  constructor(
    private readonly store: Store<{ arena: ArenaState }>,
    private readonly zone: NgZone,
    private readonly actions: ActionsSubject
  ) {
    (window as any).arenaMatchRunner = this;
    this.state = this.store.selectSignal((root: { arena: ArenaState }) => root.arena);
    this.moveSpeed = this.state().match.moveSpeed;
    this.pyodideClient = new ArenaPyodideClient({
      setStatus: (tone, message) => this.patchStatus({ tone, message }),
      appendLogs: (lines) => this.appendLogs(lines),
      updateOpenSpiel: (update) => {
        this.openSpielLogLines = update.logLines;
        this.patchState({
          openSpiel: { ...this.state().openSpiel, 
            tone: update.status,
            message: update.message,
            errorLines: update.errorLines
          }
        });
      }
    });
    this.registerActionHandlers();
    // this.store.select((root: { arena: ArenaState }) => root.arena.match.matchObservation)
    //   .subscribe((obs) => {
    //     console.log('store select:', obs);
    //   });
  }

  /** Match Viewer: replay a recorded move list through the game engine in the Pyodide worker. */
  replayMoves<T>(request: PyodideReplayRequest): Promise<T> {
    return this.pyodideClient.request<T>({ type: 'replayMoves', payload: request });
  }

  /** Create your own Automata: the prompt the LLMs received for this game. */
  getGamePrompt<T>(gameId: string, worldId: string, config: Record<string, unknown>): Promise<T> {
    return this.pyodideClient.request<T>({ type: 'getGamePrompt', gameId, worldId, config });
  }

  /** Create your own Automata: compile the user's policy code inside the worker. */
  setUserPolicy<T>(gameId: string, worldId: string, code: string, config: Record<string, unknown> | null): Promise<T> {
    return this.pyodideClient.request<T>({ type: 'setUserPolicy', gameId, worldId, code, config });
  }

  smokeTestUserPolicy<T>(gameId: string, worldId: string, config: Record<string, unknown> | null, moveTimeout: number): Promise<T> {
    return this.pyodideClient.request<T>({ type: 'smokeTestUserPolicy', gameId, worldId, config, moveTimeout });
  }

  /** Create your own Automata: play one whole match in the worker and return its outcome. */
  playFullMatch<T>(request: PyodideFullMatchRequest): Promise<T> {
    return this.pyodideClient.request<T>({ type: 'playFullMatch', payload: request });
  }

  /** Drop every pending request and swap to a fresh worker (used when user code hangs). */
  restartRuntime(): void {
    this.pyodideMasterToken += 1;
    this.matchToken += 1;
    this.pyodideClient.setMasterToken(this.pyodideMasterToken);
  }

  /** Match Viewer: start loading the Python runtime without touching live-match state. */
  warmRuntime(): void {
    void this.pyodideClient.requestInBackground<void>({ type: 'ensureRunner' }).catch(() => undefined);
  }

  /** Load a game's engine files and bot list ahead of time (the worker caches both per game). */
  prefetchGame(gameId: string, worldId: string): void {
    void this.pyodideClient
      .requestInBackground<unknown>({ type: 'loadBots', gameId, worldId })
      .catch(() => undefined);
  }

  private registerActionHandlers(): void {
    this.actions.subscribe((action) => {
      // console.debug('[action]', action);
      try {
        switch (action.type) {
          case arenaActions.initRequested.type:
            this.runAsync(this.init());
            return;
          case arenaActions.selectEntry.type: {
            const { entryId } = action as ReturnType<typeof arenaActions.selectEntry>;
            this.runAsync(this.selectEntry(entryId));
            return;
          }
          case arenaActions.resetEntry.type:
            this.runAsync(this.resetEntry());
            return;
          case arenaActions.gameChangeRequested.type: {
            const { id, gameId, worldId } = action as ReturnType<typeof arenaActions.gameChangeRequested>;
            this.runAsync(this.onGameChange(id, gameId, worldId));
            return;
          }
          case arenaActions.matchupChangeRequested.type: {
            const { mode } = action as ReturnType<typeof arenaActions.matchupChangeRequested>;
            this.runAsync(this.onMatchupChange(mode));
            return;
          }
          case arenaActions.botChangeRequested.type: {
            const { slot, botId } = action as ReturnType<typeof arenaActions.botChangeRequested>;
            this.runAsync(this.onBotChange(slot, botId));
            return;
          }
          case arenaActions.randomBotRequested.type: {
            const { slot } = action as ReturnType<typeof arenaActions.randomBotRequested>;
            this.selectRandomBot(slot);
            return;
          }
          case arenaActions.togglePlayRequested.type:
            this.togglePlay();
            return;
          case arenaActions.stepRequested.type:
            this.stepOnce();
            return;
          case arenaActions.restartSeriesRequested.type:
            this.runAsync(this.restartSeries());
            return;
          case arenaActions.speedChangeRequested.type: {
            const { speed } = action as ReturnType<typeof arenaActions.speedChangeRequested>;
            this.setMoveSpeed(speed);
            return;
          }
          case arenaActions.humanMoveSubmitted.type: {
            const { action: move, forceApply } = action as ReturnType<
              typeof arenaActions.humanMoveSubmitted
            >;
            this.submitHumanMove(move, forceApply);
          }
        }
      } catch (error) {
        this.reportAsyncError(error);
      }
    });
  }

  private async init(): Promise<void> {
    if (this.initStarted) {
      return;
    }
    this.initStarted = true;
    this.patchStatus({ tone: 'loading', message: 'Preparing arena runtime' });
    void this.pyodideClient.request<void>({ type: 'ensureRunner' }).catch(() => undefined);
    this.runAsync(this.loadEloTable());
    await this.applyDefaults();
  }

  private async selectEntry(entryId: string): Promise<void> {
    const entry = this.state().catalog.entrypoints.find((option) => option.id === entryId);
    if (!entry || !entry.available) {
      return;
    }
    this.patchSelection({ entryId: entry.id });
    await this.applySelectionReset({
      id: null,
      gameId: null,
      worldId: null,
      botAId: null,
      botBId: null
    });
  }

  private async resetEntry(): Promise<void> {
    setHashRouteState('/');
    this.patchSelection({ entryId: null });
    await this.applySelectionReset({
      id: null,
      gameId: null,
      worldId: null,
      botAId: null,
      botBId: null
    });
  }

  private async restartIfNeeded(): Promise<void> {
    if (!this.pyodideClient.hasPendingRequests()) {
      return;
    }
    await new Promise<void>((resolve) => {
      window.setTimeout(resolve, this.PYODIDE_GRACE_PERIOD_MS);
    });
    if (!this.pyodideClient.hasPendingRequests()) {
      return;
    }
    this.pyodideMasterToken += 1;
    this.matchToken += 1;
    this.pyodideClient.setMasterToken(this.pyodideMasterToken);
  }

  private async onGameChange(id: string, gameId: string | null, worldId: string | null): Promise<void> {
    await this.applySelectionReset({
        id: id,
        gameId: gameId,
        worldId: worldId,
        botAId: null,
        botBId: null
      });
    this.runAsync(this.refreshBots(true));
  }

  private async onBotChange(slot: 'a' | 'b', value: string | null): Promise<void> {
    const selection = this.state().selection;
    let botA = slot === 'a' ? value : selection.botAId;
    let botB = slot === 'b' ? value : selection.botBId;
    // a lone human always takes slot A (sides still alternate between games)
    if (botB === 'human' && botA !== 'human') {
      [botA, botB] = [botB, botA];
    }
    const humans = [botA, botB].filter((id) => id === 'human').length;
    const matchup: MatchupMode = humans === 2 ? 'human-vs-human' : humans === 1 ? 'human-vs-ai' : 'ai-vs-ai';
    this.patchSelection({ botAId: botA, botBId: botB, matchup });
    await this.stopMatch();
    this.maybeRunMatch();
    this.runAsync(this.refreshBotStrategies());
  }

  private selectRandomBot(slot: 'a' | 'b'): void {
    const state = this.state();
    let pool = this.getRandomBotPool(state.catalog.bots);
    const otherId = slot === 'a' ? state.selection.botBId : state.selection.botAId;
    if (otherId && pool.length > 1) {
      const filtered = pool.filter((bot) => bot.id !== otherId);
      if (filtered.length > 0) {
        pool = filtered;
      }
    }
    if (pool.length === 0) {
      return;
    }
    const nextId = this.pickRandomBotId(pool);
    this.runAsync(this.onBotChange(slot, nextId));
  }

  private setMoveSpeed(speed: number): void {
    if (!Number.isFinite(speed)) {
      return;
    }
    this.moveSpeed = speed;
    this.dispatchAction(arenaActions.updateMatchSpeed({ speed }));
  }

  private async applySelectionReset(selection: Partial<ArenaState['selection']>): Promise<void> {
    this.patchSelection(selection);
    await this.stopMatch();
    this.resetBotStrategies();
  }

  maybeRunMatch(): void {
    const setup = this.getActiveSetup();
    if (!setup) {
      return;
    }
    const runKey = [setup.game.id, setup.game.worldId, setup.botA, setup.botB].join('|');
    if (runKey !== this.lastRunKey) {
      this.lastRunKey = runKey;
      this.startMatch(true);
      return;
    }
    if (!this.matchReady) {
      this.startMatch(false);
      return;
    }
  }

  togglePlay(): void {
    if (!this.canControlMatch()) {
      return;
    }
    if (this.isPlaying) {
      this.isPlaying = false;
      this.pendingSingleStep = false;
      this.clearStepTimer();
      this.emitState();
      if (!this.illegalAction) {
        this.patchStatus({ tone: 'idle', message: 'Paused' });
      }
      return;
    }
    if (!this.matchReady) {
      this.startMatch(false);
      return;
    }
    this.isPlaying = true;
    this.patchStatus({ tone: 'ready', message: 'Match running' });
    this.emitState();
    this.scheduleNextStep(0);
  }

  async restartSeries(): Promise<void> {
    if (!this.canControlMatch()) {
      return;
    }
    await this.restartIfNeeded();
    this.startMatch(true);
  }

  async stopMatch(): Promise<void> {
    this.matchToken += 1;
    this.isPlaying = false;
    this.setStepInFlight(false);
    this.pendingSingleStep = false;
    this.outputLines = [];
    this.matchReady = false;
    this.lastRunKey = '';
    this.seriesMatchIndex = 0;
    this.currentBotAId = null;
    this.currentBotBId = null;
    this.clearStepTimer();
    this.matchObservation = null;
    this.clearMatchFlags();
    await this.restartIfNeeded();
    this.isPlaying = false;
    this.matchReady = false;
    this.patchStatus({ tone: 'idle', message: 'Pyodide idle' });
    this.resetScoreboard();
    this.emitState();
  }

  appendLogs(lines: string[]): void {
    if (lines.length === 0) {
      return;
    }
    // fix order; last line should be first
    lines = lines.reverse();
    const next = [...lines, ...this.outputLines];
    if (next.length > this.maxOutputLines) {
      this.outputLines = next.slice(0, this.maxOutputLines);
    } else {
      this.outputLines = next;
    }
    this.emitState();
  }

  submitHumanMove(action: string, forceApply?: boolean): void {
    if (!this.isPlaying || !this.matchReady || !this.awaitingHumanMove) {
      return;
    }
    if (this.stepInFlight) {
      return;
    }
    const token = this.matchToken;
    this.clearAwaiting();
    this.emitState();
    this.setStepInFlight(true);
    this.runAsync(this.dispatchHumanMove(action, token, forceApply));
  }

  private clearAwaiting(): void {
    this.awaitingHumanMove = false;
    this.legalMoves = [];
  }

  private setStepInFlight(stepInFlight: boolean): void {
    if (this.stepInFlight === stepInFlight) {
      return;
    }
    this.stepInFlight = stepInFlight;
    this.dispatchAction(arenaActions.updateStepInFlight({ stepInFlight }));
  }

  private clearMatchFlags(): void {
    this.illegalAction = null;
    this.dispatchAction(arenaActions.updateLastMatchResult({ lastMatchResult: null }));
    this.clearAwaiting();
  }

  private canControlMatch(): boolean {
    return Boolean(this.getActiveSetup());
  }

  private getActiveSetup(): {
    game: GameWorldOption;
    botA: string;
    botB: string;
  } | null {
    const game = getActiveGame(this.state());
    const botA = this.state().selection.botAId;
    const botB = this.state().selection.botBId;
    if (!game || !botA || !botB || this.state().selection.matchup === null) {
      return null;
    }
    return { game, botA, botB };
  }

  private clearStepTimer(): void {
    if (this.stepTimer !== null) {
      window.clearTimeout(this.stepTimer);
      this.stepTimer = null;
    }
  }

  private startMatch(resetScoreboard: boolean): void {
    if (!this.getActiveSetup()) {
      return;
    }
    if (resetScoreboard) {
      this.resetScoreboard();
    }
    this.clearStepTimer();
    this.setStepInFlight(false);
    this.pendingSingleStep = false;
    this.matchReady = false;
    this.isPlaying = true;
    this.clearMatchFlags();
    this.matchToken += 1;
    const token = this.matchToken;

    this.outputLines = this.openSpielLogLines.length ? [...this.openSpielLogLines] : [];
    this.emitState();
    this.patchStatus({ tone: 'loading', message: 'Starting match' });

    this.runAsync(this.initAndKickoff(token));
  }

  private async initAndKickoff(token: number): Promise<void> {
    const initPayload = await this.initMatch();
    if (token !== this.matchToken) {
      return;
    }
    if (initPayload.error) {
      let openSpielLines = this.openSpielLogLines;
      if (String(initPayload.error).includes('pyspiel')) {
        const pyspielLines = await this.pyodideClient.request<string[]>({
          type: 'capturePyspielError'
        });
        if (pyspielLines.length > 0) {
          openSpielLines = [...openSpielLines, 'OpenSpiel import error:', ...pyspielLines];
        }
        await this.pyodideClient.request<void>({ type: 'retryOpenSpielInstall' });
        const refreshedLogs = this.openSpielLogLines;
        if (refreshedLogs.length > 0) {
          openSpielLines = [...openSpielLines, ...refreshedLogs];
        }
      }
      const errorLogs = normalizeLogs(initPayload.logs);
      const errorLines = String(initPayload.error)
        .split('\n')
        .map((line) => line.trimEnd())
        .filter((line) => line.length > 0);
      this.outputLines = [...errorLines, ...errorLogs, ...openSpielLines];
      this.isPlaying = false;
      this.matchReady = false;
      this.emitState();
      this.patchStatus({ tone: 'error', message: 'Pyodide error' });
      return;
    }
    this.appendLogs(normalizeLogs(initPayload.logs));
    this.matchReady = true;
    this.emitState();
    this.patchStatus({ tone: 'ready', message: 'Match running' });
    this.processPayload(initPayload, token);
  }

  private scheduleNextStep(delayMs: number): void {
    if (!this.isPlaying) {
      return;
    }
    this.clearStepTimer();
    this.stepTimer = window.setTimeout(() => {
      this.runAsync(this.tickMatch(this.matchToken));
    }, delayMs);
  }

  private scheduleRestart(token: number): void {
    if (!this.isPlaying) {
      return;
    }
    this.clearStepTimer();
    this.stepTimer = window.setTimeout(() => {
      this.runAsync(this.restartMatch(token));
    }, this.restartDelayMs);
  }

  private async restartMatch(token: number): Promise<void> {
    if (!this.isPlaying || token !== this.matchToken) {
      return;
    }
    this.clearMatchFlags();
    const initPayload = await this.initMatch();
    if (token !== this.matchToken) {
      return;
    }
    if (initPayload.error) {
      this.appendLogs([`Match failed: ${initPayload.error}`]);
      this.isPlaying = false;
      this.matchReady = false;
      this.emitState();
      this.patchStatus({ tone: 'error', message: 'Pyodide error' });
      return;
    }
    this.appendLogs(['-- restarting match --']);
    this.appendLogs(normalizeLogs(initPayload.logs));
    this.matchReady = true;
    this.emitState();
    this.patchStatus({ tone: 'ready', message: 'Match running' });
    this.processPayload(initPayload, token);
  }

  private async dispatchHumanMove(
    action: string,
    token: number,
    forceApply?: boolean
  ): Promise<void> {
    let payload: MatchPayload = {};
    try {
      payload = await this.pyodideClient.request<MatchPayload>({
        type: 'submitHumanMove',
        action,
        forceApply
      });
    } catch (error) {
      payload = { error: error instanceof Error ? error.message : String(error) };
    } finally {
      this.setStepInFlight(false);
    }
    this.processPayload(payload, token);
  }

  private async tickMatch(token: number): Promise<void> {
    if (!this.isPlaying || !this.matchReady || token !== this.matchToken) {
      return;
    }
    if (this.stepInFlight) {
      this.scheduleNextStep(this.nextDelayMs());
      return;
    }
    this.setStepInFlight(true);
    let payload: MatchPayload = {};
    try {
      payload = await this.pyodideClient.request<MatchPayload>({ type: 'stepMatch' });
    } catch (error) {
      payload = { error: error instanceof Error ? error.message : String(error) };
    } finally {
      this.setStepInFlight(false);
    }

    this.processPayload(payload, token);

    if (this.pendingSingleStep && !this.isPlaying && token === this.matchToken) {
      this.pendingSingleStep = false;
      if (this.matchReady && !this.stepInFlight) {
        this.runAsync(this.runSingleStep(token));
      }
    }
  }

  stepOnce(): void {
    if (!this.canControlMatch()) {
      return;
    }
    const wasPlaying = this.isPlaying;
    if (this.isPlaying) {
      this.isPlaying = false;
      this.clearStepTimer();
      this.emitState();
      if (!this.illegalAction) {
        this.patchStatus({ tone: 'idle', message: 'Paused' });
      }
    }
    if (!this.matchReady) {
      return;
    }
    const token = this.matchToken;
    if (this.stepInFlight) {
      this.pendingSingleStep = !wasPlaying;
      return;
    }
    this.runAsync(this.runSingleStep(token));
  }

  private async runSingleStep(token: number): Promise<void> {
    if (!this.matchReady || token !== this.matchToken || this.stepInFlight) {
      return;
    }
    this.setStepInFlight(true);
    let payload: MatchPayload = {};
    try {
      payload = await this.pyodideClient.request<MatchPayload>({ type: 'stepMatch' });
    } catch (error) {
      payload = { error: error instanceof Error ? error.message : String(error) };
    } finally {
      this.setStepInFlight(false);
    }
    this.processPayload(payload, token);
  }

  private processPayload(payload: MatchPayload, token: number): void {
    // console.log('processPayload', payload);
    if (token !== this.matchToken) {
      return;
    }

    if (payload.error) {
      this.appendLogs([`Match failed: ${payload.error}`]);
      this.isPlaying = false;
      this.matchReady = false;
      this.clearAwaiting();
      this.emitState();
      this.patchStatus({ tone: 'error', message: 'Pyodide error' });
      return;
    }

    let observationUpdated = false;
    if (payload.state_player !== undefined) {
      this.matchObservation = payload.state_player ? JSON.parse(JSON.stringify(payload.state_player)) : null;
      observationUpdated = true;
    }
    const normalizedLogs = normalizeLogs(payload.logs);
    if (normalizedLogs.length > 0) {
      this.appendLogs(normalizedLogs);
    } else if (observationUpdated) {
      this.emitState();
    }

    if (payload.awaiting_input) {
      this.awaitingHumanMove = true;
      this.legalMoves = Array.isArray(payload.legal_moves)
        ? payload.legal_moves.map((move) => String(move))
        : [];
      this.matchReady = true;
      this.emitState();
      this.patchStatus({ tone: 'ready', message: 'Waiting for human move' });
      return;
    }

    if (this.awaitingHumanMove || this.legalMoves.length > 0) {
      this.clearAwaiting();
      this.emitState();
    }

    if (payload.done) {
      const isIllegal = Boolean(payload.illegal);
      this.illegalAction = isIllegal
        ? payload.illegal_action
          ? String(payload.illegal_action)
          : null
        : null;
      this.dispatchAction(arenaActions.updateLastMatchResult({lastMatchResult: {
        winner: payload.final?.winner ?? null,
        illegal: isIllegal,
        finishedAt: Date.now()
      }}));
      this.updateScoreboard(payload.final);
      const illegalBot = isIllegal
        ? payload.illegal_bot
          ? String(payload.illegal_bot)
          : 'Unknown automaton'
        : null;
      if (this.repeatMatches && this.isHumanMatchActive()) {
        this.isPlaying = false;
        this.clearStepTimer();
        this.matchReady = false;
        this.emitState();
        if (isIllegal) {
          this.patchStatus({ tone: 'error', message: `Illegal move by ${illegalBot}` });
        } else {
          this.patchStatus({ tone: 'ready', message: 'Round finished' });
        }
        return;
      }
      if (!this.repeatMatches) {
        this.isPlaying = false;
        this.matchReady = false;
        this.clearAwaiting();
        this.emitState();
        if (isIllegal) {
          this.patchStatus({ tone: 'error', message: `Illegal move by ${illegalBot}` });
        } else {
          this.patchStatus({ tone: 'ready', message: 'Match finished' });
        }
        return;
      }
      this.matchReady = false;
      this.emitState();
      if (isIllegal) {
        this.patchStatus({ tone: 'error', message: `Illegal move by ${illegalBot}` });
      }
      this.scheduleRestart(token);
      return;
    }

    this.scheduleNextStep(this.nextDelayMs());
  }

  private nextDelayMs(): number {
    if (this.isHumanMatchActive()) {
      return 0;
    }
    if (this.moveSpeed >= this.maxMoveSpeed) {
      return 0;
    }
    return Math.max(0, Math.round(1000 / Math.max(1, this.moveSpeed)));
  }

  private isHumanMatchActive(): boolean {
    if (this.currentBotAId === 'human' || this.currentBotBId === 'human') {
      return true;
    }
    const selection = this.state().selection;
    return selection.botAId === 'human' || selection.botBId === 'human';
  }

  private async initMatch(): Promise<MatchPayload> {
    const setup = this.getActiveSetup();
    if (!setup) {
      return { error: 'Match setup missing.' };
    }
    const swap = this.swapEveryMatch && this.seriesMatchIndex % 2 === 1;
    const resolvedBotA = swap ? setup.botB : setup.botA;
    const resolvedBotB = swap ? setup.botA : setup.botB;
    this.currentBotAId = resolvedBotA;
    this.currentBotBId = resolvedBotB;
    let config = {};
    try {
      config = setup.game.config ? JSON.parse(setup.game.config) : {};
    } catch {
      config = {};
    }
    const payload = await this.pyodideClient.request<MatchPayload>({
      type: 'initMatch',
      payload: {
        gameId: setup.game.gameId,
        worldId: setup.game.worldId,
        config: config,
        botA: resolvedBotA,
        botB: resolvedBotB
      }
    });
    if (!payload.error) {
      this.seriesMatchIndex += 1;
    }
    return payload;
  }

  private resetScoreboard(): void {
    this.dispatchAction(arenaActions.resetScoreboard());
  }

  private updateScoreboard(finalStats?: { winner?: number | null }): void {
    const state = this.state();
    const selectedBotA = state.selection.botAId;
    const selectedBotB = state.selection.botBId;
    const next = { games: 0, botAWins: 0, botBWins: 0, draws: 0 };
    next.games += 1;
    if (finalStats?.winner === 0) {
      if (this.currentBotAId === selectedBotA) {
        next.botAWins += 1;
      } else if (this.currentBotAId === selectedBotB) {
        next.botBWins += 1;
      } else {
        next.draws += 1;
      }
    } else if (finalStats?.winner === 1) {
      if (this.currentBotBId === selectedBotA) {
        next.botAWins += 1;
      } else if (this.currentBotBId === selectedBotB) {
        next.botBWins += 1;
      } else {
        next.draws += 1;
      }
    } else {
      next.draws += 1;
    }
    this.dispatchAction(arenaActions.updateScoreboard({ delta: next }));
  }

  private emitState(): void {
    this.dispatchAction(arenaActions.updateIsPlaying({ isPlaying: this.isPlaying }));
    this.dispatchAction(arenaActions.updateMatchReady({ matchReady: this.matchReady }));
    this.dispatchAction(arenaActions.updateOutputLines({ outputLines: this.outputLines }));
    if (this.matchObservation !== this.state().match.matchObservation) {
      // console.log('matchObservation changed:', this.matchObservation);
    }
    this.dispatchAction(arenaActions.updateMatchObservation({ matchObservation: this.matchObservation }));
    this.dispatchAction(arenaActions.updateAwaitingHumanMove({ awaitingHumanMove: this.awaitingHumanMove }));
    this.dispatchAction(arenaActions.updateLegalMoves({ legalMoves: this.legalMoves }));
    this.dispatchAction(arenaActions.updateActiveBotAId({ activeBotAId: this.currentBotAId }));
    this.dispatchAction(arenaActions.updateActiveBotBId({ activeBotBId: this.currentBotBId }));
    this.dispatchAction(arenaActions.updateIllegalAction({ illegalAction: this.illegalAction }));
  }

  private logDebug(...args: unknown[]): void {
    const now = new Date();
    const mm = String(now.getMinutes()).padStart(2, '0');
    const ss = String(now.getSeconds()).padStart(2, '0');
    const ms = String(now.getMilliseconds()).padStart(3, '0');
    console.debug(`[${mm}:${ss}.${ms}] [ArenaMatchRunner]`, ...args);
  }

  private isStalePyodideRequestError(error: unknown): boolean {
    return error instanceof Error && error.message === 'Dropped stale Pyodide request';
  }

  private reportAsyncError(error: unknown): void {
    if (this.isStalePyodideRequestError(error)) {
      return;
    }
    this.patchStatus({ tone: 'error', message: 'Unexpected error. More details in the logs.' });
    this.appendLogs([`Unexpected error: ${error instanceof Error ? error.message : String(error)}`]);
    this.emitState();
  }

  private runAsync(task: Promise<void>): void {
    void task.catch((error) => this.reportAsyncError(error));
  }

  private loadEloTable(): Promise<void> {
    this.eloLoad ??= this.fetchEloTable();
    return this.eloLoad;
  }

  private async fetchEloTable(): Promise<void> {
    let parsed = null as ReturnType<typeof parseEloCsv>;
    try {
      const eloUrl = this.toAppUrl('elos_all_bots.csv');
      this.logDebug('fetch start 3', eloUrl);
      const response = await fetch(eloUrl);
      if (response.ok) {
        const csv = await response.text();
        parsed = parseEloCsv(csv);
      }
    } catch {
      parsed = null;
    }
    if (parsed) {
      this.patchCatalog({ eloByColumn: parsed });
    }
  }

  private async applyDefaults(): Promise<void> {
    try {
      const worldsUrl = this.toAppUrl('py/game_worlds.json');
      this.logDebug('fetch start 4', worldsUrl);
      const gameWorlds = await fetch(worldsUrl);
      if (gameWorlds.ok) {
        const json = await gameWorlds.json();
        const configs: Record<string, { gameId: string; worldId: string; config: string | null }> = json.configs;
        const games = Object.values(configs)
        .filter((config) => includeGameInDropdown(config.gameId, config.worldId))
        .sort((a, b) => a.gameId.localeCompare(b.gameId) || a.worldId.localeCompare(b.worldId))
        .map((config) => ({
          id: `${config.gameId}/${config.worldId}`,
          gameId: config.gameId,
          worldId: config.worldId,
          config: config.config,
          label: formatGameLabel(config.gameId, config.worldId),
          description: formatGameDescription(config.gameId, config.worldId),
          hasGui: GAME_GUI_IDS.some((gameId) => gameId === config.gameId)
        }));
        this.patchCatalog({ games });
      }
    } catch (error) {
      console.error('Failed to load game arena manifest', error);
      this.patchStatus({ tone: 'error', message: 'Failed to load game arena manifest' });
    }
    const state = this.state();
    const entry = state.catalog.entrypoints.find((option) => option.available) ?? null;
    const game =
      this.readArenaGameFromUrl(state.catalog.games) ??
      state.catalog.games.find((candidate) => candidate.id === DEFAULT_GAME_ID) ??
      null;
    if (!game) {
      return;
    }
    const defaultBot =
      state.catalog.bots.find((bot) => bot.id === 'random')?.id ??
      state.catalog.bots[0]?.id ??
      null;
    this.patchSelection({
      entryId: entry?.id ?? null,
      id: game.id,
      gameId: game.gameId,
      worldId: game.worldId,
      botAId: defaultBot,
      botBId: defaultBot
    });

    await this.refreshBots(true);
  }

  private readArenaGameFromUrl(games: GameWorldOption[]): GameWorldOption | null {
    try {
      const route = getHashRouteState();
      if (route.path !== '/arena') {
        return null;
      }
      const gameId = route.params.get('game');
      const worldId = route.params.get('sub');
      if (!gameId || !worldId) {
        return null;
      }
      return games.find((game) => game.gameId === gameId && game.worldId === worldId) ?? null;
    } catch {
      return null;
    }
  }

  private async refreshBots(autoStart: boolean): Promise<void> {
    const activeGame = getActiveGame(this.state());
    if (!activeGame) {
      return;
    }
    const key = activeGame.id;
    if (this.botsLoadKey === key && this.state().match.botsStatus === 'ready') {
      if (autoStart) {
        this.maybeRunMatch();
      }
      return;
    }
    const token = ++this.botsLoadToken;
    this.dispatchAction(arenaActions.botsLoadLoading());
    this.patchStatus({ tone: 'loading', message: 'Loading automata' });

    try {
      const result = await this.pyodideClient.request<{ bots?: string[]; error?: string }>({
        type: 'loadBots',
        gameId: activeGame.gameId,
        worldId: activeGame.worldId
      });
      if (token !== this.botsLoadToken) {
        return;
      }
      if (result?.error) {
        this.dispatchAction(arenaActions.botsLoadFailed());
        this.patchStatus({ tone: 'error', message: 'Pyodide error' });
        this.botsLoadKey = '';
        return;
      }
      const options = buildBotOptions(result?.bots ?? [], activeGame.hasGui);
      await this.loadEloTable(); // default picks are by rating
      if (token !== this.botsLoadToken) {
        return;
      }
      this.patchCatalog({ bots: options });
      this.selectDefaultBots(options);
      this.applyMatchupConstraints(options);
      this.botsLoadKey = key;
      this.patchStatus({ tone: 'ready', message: 'Automata ready' });
      this.runAsync(this.refreshBotStrategies());
      this.dispatchAction(arenaActions.botsLoadSuccessful());
    } catch (error) {
      if (token !== this.botsLoadToken) {
        return;
      }
      this.patchStatus({ tone: 'error', message: 'Automata load failed' });
      this.botsLoadKey = '';
      const message = error instanceof Error ? error.message : String(error);
      this.appendLogs([`Automata load failed: ${message}`]);
    }

    if (autoStart) {
      this.maybeRunMatch();
    }
  }

  /**
   * Runner-up as A (left) and the strongest as B (right), so a human taking slot A faces the
   * strongest; random picks when the game has no ratings.
   */
  private selectDefaultBots(options: BotOption[]): void {
    if (options.length === 0) {
      this.patchSelection({ botAId: null, botBId: null });
      return;
    }
    const ranked = this.rankBotsByElo(options);
    if (ranked.length >= 2) {
      const [first, second] = ranked;
      this.patchSelection({ botAId: second, botBId: first });
      return;
    }
    const pool = this.getRandomBotPool(options);
    const first = this.pickRandomBotId(pool);
    let second = first;
    if (pool.length > 1) {
      const remaining = pool.filter((bot) => bot.id !== first);
      const secondPool = remaining.length > 0 ? remaining : pool;
      second = this.pickRandomBotId(secondPool);
    }
    this.patchSelection({ botAId: first, botBId: second });
  }

  private pickRandomBotId(options: BotOption[]): string {
    const index = Math.floor(Math.random() * options.length);
    return options[Math.max(0, Math.min(options.length - 1, index))]?.id ?? options[0].id;
  }

  private getRandomBotPool(options: BotOption[]): BotOption[] {
    const preferred = options.filter((bot) => bot.id !== 'random' && bot.id !== 'human');
    return preferred.length > 0 ? preferred : options;
  }

  private async onMatchupChange(mode: MatchupMode): Promise<void> {
    const patch = this.buildMatchupSelectionPatch(mode, this.state().catalog.bots);
    if (Object.keys(patch).length === 0) {
      return;
    }
    this.patchSelection(patch);
    await this.stopMatch();
    this.maybeRunMatch();
    this.runAsync(this.refreshBotStrategies());
  }

  private applyMatchupConstraints(options: BotOption[]): void {
    const mode = this.state().selection.matchup;
    if (mode === null) {
      return;
    }
    const patch = this.buildMatchupSelectionPatch(mode, options);
    if (Object.keys(patch).length === 0) {
      return;
    }
    this.patchSelection(patch);
  }

  private buildMatchupSelectionPatch(
    requestedMode: MatchupMode,
    options: BotOption[]
  ): Partial<ArenaState['selection']> {
    const selection = this.state().selection;
    const hasHuman = options.some((bot) => bot.id === 'human');
    const patch: Partial<ArenaState['selection']> = {};
    let mode = requestedMode;
    if (!hasHuman && mode !== 'ai-vs-ai') {
      mode = 'ai-vs-ai';
    }
    if (mode !== selection.matchup) {
      patch.matchup = mode;
    }
    if (mode === 'human-vs-human') {
      if (selection.botAId !== 'human') {
        patch.botAId = 'human';
      }
      if (selection.botBId !== 'human') {
        patch.botBId = 'human';
      }
      return patch;
    }
    if (mode === 'human-vs-ai') {
      if (selection.botAId !== 'human') {
        patch.botAId = 'human';
      }
      // first choice after entering: face the strongest automaton
      if (selection.matchup === null || !selection.botBId || selection.botBId === 'human') {
        const nextBotB = this.pickAiBot(options, null);
        if (nextBotB) {
          patch.botBId = nextBotB;
        } else if (selection.botBId !== null) {
          patch.botBId = null;
        }
      }
      return patch;
    }
    // fill human slots with automata; B avoids A's new pick so the two sides differ
    let botA = selection.botAId;
    if (botA === 'human') {
      botA = this.pickAiBot(options, selection.botBId);
      patch.botAId = botA;
    }
    if (selection.botBId === 'human') {
      patch.botBId = this.pickAiBot(options, botA);
    }
    return patch;
  }

  private pickAiBot(options: BotOption[], excludeId: string | null): string | null {
    const strongest = this.rankBotsByElo(options).find((id) => id !== excludeId);
    if (strongest) {
      return strongest;
    }
    const pool = options.filter((bot) => bot.id !== 'human' && bot.id !== excludeId);
    if (pool.length === 0) {
      return null;
    }
    return this.pickRandomBotId(pool);
  }

  /**
   * Best rated bot of each model for the active game, highest Elo first (unrated bots are left
   * out). One per model so the picks stay visible in the setup's default "best bot per model" list.
   */
  private rankBotsByElo(options: BotOption[]): string[] {
    const selection = this.state().selection;
    const column = resolveEloColumn(selection.gameId, selection.worldId);
    const elo = column ? this.state().catalog.eloByColumn?.[column] : undefined;
    if (!elo) {
      return [];
    }
    const seenModels = new Set<string>();
    return options
      .filter((bot) => bot.id !== 'human' && elo[bot.id] !== undefined)
      .sort((a, b) => elo[b.id] - elo[a.id])
      .map((bot) => bot.id)
      .filter((id) => {
        const model = id.split('/')[0];
        if (seenModels.has(model)) {
          return false;
        }
        seenModels.add(model);
        return true;
      });
  }

  private async refreshBotStrategies(slot?: 'a' | 'b'): Promise<void> {
    const selection = this.state().selection;
    const gameId = selection.gameId;
    const worldId = selection.worldId;
    if (!gameId || !worldId) {
      if (slot) {
        this.resetBotStrategy(slot);
      } else {
        this.resetBotStrategies();
      }
      return;
    }

    const refreshSlot = (currentSlot: 'a' | 'b', botId: string | null): void => {
      if (!botId) {
        this.resetBotStrategy(currentSlot);
        return;
      }
      this.runAsync(this.loadBotStrategy(currentSlot, botId, gameId, worldId));
    };

    if (slot) {
      refreshSlot(slot, slot === 'a' ? selection.botAId : selection.botBId);
      return;
    }

    refreshSlot('a', selection.botAId);
    refreshSlot('b', selection.botBId);
  }

  private patchBotStrategy(
    slot: 'a' | 'b',
    next: Partial<ArenaState['botStrategies']['a']>
  ): void {
    const strategies = this.state().botStrategies;
    this.patchState({
      botStrategies: {
        ...strategies,
        [slot]: { ...strategies[slot], ...next }
      }
    });
  }

  private patchBotStrategyIfCurrent(
    slot: 'a' | 'b',
    token: number,
    next: Partial<ArenaState['botStrategies']['a']>
  ): void {
    if (slot === 'a' ? token === this.botStrategyLoadTokenA : token === this.botStrategyLoadTokenB) {
      this.patchBotStrategy(slot, next);
    }
  }

  private async loadBotStrategy(
    slot: 'a' | 'b',
    botId: string,
    gameId: string,
    worldId: string
  ): Promise<void> {
    const token = slot === 'a' ? ++this.botStrategyLoadTokenA : ++this.botStrategyLoadTokenB;
    this.patchBotStrategy(slot, { text: null, loading: true, error: null });

    if (botId === 'human' || botId === 'random' || botId === 'first' || botId === 'last') {
      this.patchBotStrategyIfCurrent(slot, token, {
        text: null,
        loading: false,
        error: null
      });
      return;
    }

    const cacheKey = `${gameId}|${worldId}|${botId}`;
    if (this.botStrategyCache.has(cacheKey)) {
      const cached = this.botStrategyCache.get(cacheKey) ?? '';
      this.patchBotStrategyIfCurrent(slot, token, {
        text: cached,
        loading: false,
        error: null
      });
      return;
    }
    if (!gameId || !worldId || !botId) {
      this.patchBotStrategyIfCurrent(slot, token, {
        text: null,
        loading: false,
        error: 'Strategy file not found.'
      });
      return;
    }
    const prefix = `game_arena/${gameId}/examples/${worldId}/`;
    const path = `${prefix}${botId}/1.output.txt`;
    try {
      const strategyUrl = this.toAppUrl(`py/${path}`);
      this.logDebug('fetch start 5', strategyUrl);
      const response = await fetch(strategyUrl);
      if (!response.ok) {
        throw new Error('Strategy file not found.');
      }
      const text = (await response.text()).trimEnd();
      this.botStrategyCache.set(cacheKey, text);
      this.patchBotStrategyIfCurrent(slot, token, {
        text,
        loading: false,
        error: null
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Strategy load failed.';
      this.patchBotStrategyIfCurrent(slot, token, {
        text: null,
        loading: false,
        error: message
      });
    }
  }

  private resetBotStrategies(): void {
    this.botStrategyLoadTokenA += 1;
    this.botStrategyLoadTokenB += 1;
    this.patchState({
      botStrategies: {
        a: { text: null, loading: false, error: null },
        b: { text: null, loading: false, error: null }
      }
    });
  }

  private resetBotStrategy(slot: 'a' | 'b'): void {
    if (slot === 'a') {
      this.botStrategyLoadTokenA += 1;
    } else {
      this.botStrategyLoadTokenB += 1;
    }
    this.patchBotStrategy(slot, { text: null, loading: false, error: null });
  }

  private dispatchAction(action: Action): void {
    this.zone.run(() => {
      this.store.dispatch(action);
    });
  }

  private patchState(patch: Partial<ArenaState>): void {
    this.dispatchAction(arenaActions.patchState(patch));
  }

  private patchSelection(next: Partial<ArenaState['selection']>): void {
    this.patchState({
      selection: { ...this.state().selection, ...next }
    });
  }

  private patchCatalog(next: Partial<ArenaState['catalog']>): void {
    this.patchState({
      catalog: { ...this.state().catalog, ...next }
    });
  }

  private patchStatus(next: Partial<ArenaState['status']>): void {
    this.patchState({
      status: { ...this.state().status, ...next }
    });
  }

}
