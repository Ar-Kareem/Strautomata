import { Injectable, inject } from '@angular/core';
import { Store } from '@ngrx/store';

import { CorewarConsoleRunner } from '../../controllers/corewar-console-runner';
import {
  CorewarFrame,
  CorewarInitMatchPayload,
  CorewarMetrics,
  CorewarNextRoundPayload,
  CorewarProcessState,
  CorewarSimConfig,
  CorewarStepPayload,
  CorewarStepState,
  CorewarWarriorSpec,
  CorewarWarriorState,
  ScoreboardRow,
  OWNER_COLORS,
  getCorewarMatchWinner,
} from '../corewar/corewar.constants';
import { arenaActions, ArenaState } from '@main/arena.store';
import { CorewarBotSetupComponent } from '../corewar/corewar-bot-setup.component';
import { CorewarViewerComponent } from '../corewar/corewar-viewer.component';

type CorewarMatchState = {
  matchId: number | null;
  cycle: number;
  totalCycles: number | null;
  perWarrior: CorewarWarriorState[];
  processQueues: number[][];
  roundIndex: number | null;
  roundsTotal: number | null;
  nAlive: number | null;
  roundDone: boolean;
  matchDone: boolean;
  metrics: CorewarMetrics | null;
  coreSize: number | null;
  latestFrame: CorewarFrame | null;
};

type MatchSessionHooks = {
  getBotSetup: () => CorewarBotSetupComponent | undefined;
  getViewer: () => CorewarViewerComponent | undefined;
  flush: () => void;
};

@Injectable()
export class CorewarMatchSessionService {
  private readonly runner = inject(CorewarConsoleRunner);
  private readonly store = inject(Store<{ arena: ArenaState }>);

  private hooks: MatchSessionHooks | null = null;

  matchState: CorewarMatchState = {
    matchId: null,
    cycle: 0,
    totalCycles: null,
    perWarrior: [],
    processQueues: [],
    roundIndex: null,
    roundsTotal: null,
    nAlive: null,
    roundDone: false,
    matchDone: false,
    metrics: null,
    coreSize: null,
    latestFrame: null
  };
  error: string | null = null;
  running = false;
  moveSpeed = 1;
  matchBannerMessage: string | null = null;
  matchSummaryDismissed = false;
  roundWins: number[] = [];
  roundSummaryDismissed = false;
  activeWarriorCodes: string[] = [];
  selectedWarriorIndex: number | null = null;
  selectedProcessQueue: number[] = [];
  rosterResetToken = 0;

  private lastRoundResultIndex: number | null = null;
  private inFlight = false;
  private stepCarry = 0;
  private runToken = 0;
  private destroyed = false;
  private tickHandle: number | null = null;
  private nextTickTime = 0;
  private readonly fps = 30;

  bindHooks(hooks: MatchSessionHooks): void {
    this.hooks = hooks;
  }

  destroy(): void {
    this.destroyed = true;
    this.running = false;
    this.matchBannerMessage = null;
    this.stopTickLoop();
    this.updateCorewarMatchInProgress(false);
    this.flush();
  }

  isMatchInProgress(): boolean {
    return Boolean(this.matchState.matchId) && !this.matchState.matchDone;
  }

  setError(value: string | null): void {
    this.error = value;
    this.flush();
  }

  setProcessSelection(selection: { warriorIndex: number | null; queue: number[] }): void {
    this.selectedWarriorIndex = selection.warriorIndex;
    this.selectedProcessQueue = selection.queue;
    this.flush();
  }

  onMoveSpeedChange(value: number): void {
    const normalized = this.normalizeMoveSpeed(value);
    this.moveSpeed = normalized;
    if (this.moveSpeed === 0 && this.running) {
      this.toggleRunning(false);
      return;
    }
    this.flush();
  }

  dismissRoundSummary(): void {
    this.roundSummaryDismissed = true;
    this.flush();
  }

  dismissMatchSummary(): void {
    this.matchSummaryDismissed = true;
    this.flush();
  }

  async startMatch(simConfig: CorewarSimConfig, loading: boolean): Promise<void> {
    if (loading) {
      return;
    }
    this.error = null;
    this.hooks?.getBotSetup()?.setErrorIndices(null);
    this.running = false;
    this.runToken += 1;
    this.clearBanner();
    this.matchState.roundIndex = null;
    this.matchState.roundsTotal = null;
    this.matchState.nAlive = null;
    this.matchState.roundDone = false;
    this.roundSummaryDismissed = false;
    this.matchState.matchDone = false;
    this.matchSummaryDismissed = false;
    this.roundWins = [];
    this.lastRoundResultIndex = null;
    this.activeWarriorCodes = [];
    this.matchState.latestFrame = null;
    this.matchState.coreSize = null;
    this.matchState.processQueues = [];
    this.selectedProcessQueue = [];
    this.selectedWarriorIndex = null;
    this.rosterResetToken += 1;
    this.hooks?.getViewer()?.clear();
    this.flush();

    try {
      const botSetup = this.hooks?.getBotSetup();
      if (!botSetup) {
        throw new Error('Bot selector not ready.');
      }
      const warriorSpecs = await botSetup.getSelectedWarriorSpecs() as CorewarWarriorSpec[];
      if (warriorSpecs.length < 2) {
        throw new Error('Select at least two warriors.');
      }

      const payload = await this.runner.initMatch({
        warriorSpecs,
        config: simConfig
      }) as CorewarInitMatchPayload;

      if (payload.error) {
        botSetup.setErrorIndices(payload.error_indices ?? null);
        throw new Error(payload.error);
      }

      this.matchState.matchId = payload.match_id ?? null;
      this.applyState(payload.state);
      this.matchState.roundDone = false;
      this.roundSummaryDismissed = false;
      this.matchState.matchDone = false;
      this.matchSummaryDismissed = false;
      this.activeWarriorCodes = warriorSpecs.map((spec) => spec.code);
      this.roundWins = new Array(this.matchState.perWarrior.length).fill(0);
      this.lastRoundResultIndex = null;
      this.updateCorewarMatchInProgress(true);
      this.matchState.latestFrame = this.frameFromPayload(payload.frame);
      this.selectedProcessQueue = [];
      this.selectedWarriorIndex = null;
      this.rosterResetToken += 1;
      this.flush();

      const normalized = this.normalizeMoveSpeed(this.moveSpeed);
      if (normalized !== this.moveSpeed) {
        this.moveSpeed = normalized;
      }
      this.toggleRunning(true);
    } catch (error) {
      this.error = error instanceof Error ? error.message : String(error);
      this.flush();
    }
  }

  toggleRunning(force?: boolean): void {
    const shouldRun = force ?? !this.running;
    if (shouldRun === this.running) {
      return;
    }
    if (shouldRun && this.moveSpeed === 0) {
      this.moveSpeed = 1;
    }
    this.running = shouldRun;
    this.flush();
    if (!this.running) {
      this.hooks?.getViewer()?.forceFullRedraw();
      this.stopTickLoop();
    }
    if (this.running) {
      this.runToken += 1;
      this.stepCarry = 0;
      this.startTickLoop(this.runToken);
    }
  }

  async stepOnce(loading: boolean): Promise<void> {
    if (!this.matchState.matchId || loading) {
      return;
    }
    if (this.running) {
      this.running = false;
      this.runToken += 1;
      this.stepCarry = 0;
      this.stopTickLoop();
      this.flush();
    }
    await this.stepMatch();
  }

  async nextRound(): Promise<void> {
    if (!this.matchState.matchId || this.matchState.matchDone || !this.matchState.roundDone) {
      return;
    }
    const payload = await this.runner.nextRound(this.matchState.matchId) as CorewarNextRoundPayload;
    if (payload.error) {
      this.error = payload.error;
      this.flush();
      return;
    }
    this.matchState.roundDone = false;
    this.roundSummaryDismissed = false;
    this.matchState.matchDone = false;
    this.applyState(payload.state);
    this.selectedProcessQueue = [];
    this.selectedWarriorIndex = null;
    this.rosterResetToken += 1;
    this.clearBanner();
    this.hooks?.getViewer()?.clear();
    this.matchState.latestFrame = this.frameFromPayload(payload.frame);
    this.flush();
    this.toggleRunning(true);
  }

  async resetMatch(): Promise<void> {
    if (!this.matchState.matchId) {
      return;
    }
    const matchId = this.matchState.matchId;
    this.running = false;
    this.runToken += 1;
    this.matchState.matchId = null;
    this.clearBanner();
    this.matchState.cycle = 0;
    this.matchState.totalCycles = null;
    this.matchState.perWarrior = [];
    this.matchState.metrics = null;
    this.matchState.coreSize = null;
    this.matchState.latestFrame = null;
    this.matchState.roundIndex = null;
    this.matchState.roundsTotal = null;
    this.matchState.nAlive = null;
    this.matchState.roundDone = false;
    this.roundSummaryDismissed = false;
    this.matchState.matchDone = false;
    this.roundWins = [];
    this.lastRoundResultIndex = null;
    this.moveSpeed = 1;
    this.selectedProcessQueue = [];
    this.selectedWarriorIndex = null;
    this.matchState.processQueues = [];
    this.rosterResetToken += 1;
    this.updateCorewarMatchInProgress(false);
    this.flush();
    await this.runner.destroyMatch(matchId);
    this.hooks?.getViewer()?.clear();
    this.flush();
  }

  async reloadRound(): Promise<void> {
    if (!this.matchState.matchId) {
      return;
    }
    this.running = false;
    this.runToken += 1;
    this.stepCarry = 0;
    this.inFlight = false;
    this.stopTickLoop();
    this.clearBanner();
    this.matchState.roundDone = false;
    this.roundSummaryDismissed = false;
    this.matchState.matchDone = false;
    this.matchSummaryDismissed = false;
    this.selectedProcessQueue = [];
    this.selectedWarriorIndex = null;
    this.rosterResetToken += 1;
    this.hooks?.getViewer()?.clear();
    this.flush();

    try {
      const result = await this.runner.reloadRound(this.matchState.matchId);
      const payload = result as CorewarStepPayload;
      if (payload.error) {
        this.error = payload.error;
        this.flush();
        return;
      }

      this.matchState.cycle = payload.state?.cycle ?? 0;
      this.matchState.totalCycles = payload.state?.total_cycles ?? this.matchState.totalCycles;
      this.matchState.perWarrior = payload.state?.per_warrior ?? this.matchState.perWarrior;
      this.applyProcessQueues(payload.state?.processes);
      this.matchState.metrics = payload.state?.metrics ?? this.matchState.metrics;
      this.matchState.coreSize = payload.state?.core_size ?? this.matchState.coreSize;
      this.matchState.roundIndex = payload.state?.round_index ?? this.matchState.roundIndex;
      this.matchState.roundsTotal = payload.state?.rounds ?? this.matchState.roundsTotal;
      this.matchState.nAlive = payload.state?.n_alive ?? this.matchState.nAlive;
      this.matchState.roundDone = Boolean(payload.done);
      this.matchState.matchDone = Boolean(payload.match_done ?? false);
      this.lastRoundResultIndex = null;
      this.matchState.latestFrame = this.frameFromPayload(payload.frame);
      this.updateCorewarMatchInProgress(!this.matchState.matchDone);
      this.flush();
    } catch (error) {
      this.error = error instanceof Error ? error.message : String(error);
      this.flush();
    }
  }

  get cycleLabel(): string {
    const total = this.matchState.totalCycles;
    if (total === null || total === undefined) {
      return String(this.matchState.cycle ?? 0);
    }
    return `${this.matchState.cycle}/${total}`;
  }

  get roundLabel(): string {
    if (this.matchState.roundIndex === null || this.matchState.roundsTotal === null) {
      return '-';
    }
    return `${this.matchState.roundIndex + 1}/${this.matchState.roundsTotal}`;
  }

  get aliveLabel(): string {
    if (this.matchState.nAlive === null) {
      return '-';
    }
    const total = this.matchState.perWarrior.length;
    return total ? `${this.matchState.nAlive}/${total}` : `${this.matchState.nAlive}`;
  }

  get lastExecutedByWarrior(): Array<number | null> {
    return this.matchState.perWarrior.map((warrior) => (warrior.alive ? (warrior.last_executed ?? null) : null));
  }

  get scoreboardRows(): ScoreboardRow[] {
    return this.matchState.perWarrior.map((warrior, index) => ({
      id: warrior.id,
      label: warrior.name || `Warrior ${index + 1}`,
      color: OWNER_COLORS[index % OWNER_COLORS.length],
      alive: warrior.alive,
      isLastAlive: this.matchState.nAlive === 1 && warrior.alive,
      processes: warrior.n_processes,
      lastExecutedLabel: warrior.last_executed !== null && warrior.last_executed !== undefined
        ? `#${warrior.last_executed}`
        : '-',
      roundsWon: this.roundWins[index] ?? 0,
      score: this.matchState.metrics?.score?.[index] ?? null,
      aliveScore: this.matchState.metrics?.alive_score?.[index] ?? null,
      spawned: this.matchState.metrics?.total_spawned_procs?.[index] ?? 0,
      coverage: this.matchState.metrics?.memory_coverage?.[index] ?? 0
    }));
  }

  private async stepMatch(steps = 1): Promise<void> {
    if (!this.matchState.matchId) {
      return;
    }
    try {
      const batchSize = Math.max(1, steps | 0);
      const payload = await this.runner.stepMatch({
        matchId: this.matchState.matchId,
        steps: batchSize,
        view: 'full'
      }) as CorewarStepPayload;
      if (payload.error) {
        throw new Error(payload.error);
      }
      this.applyState(payload.state);
      this.matchState.roundDone = Boolean(payload.done);
      this.matchState.matchDone = Boolean(payload.match_done ?? this.matchState.matchDone);
      this.matchState.latestFrame = payload.frame?.instructions
        ? this.frameFromPayload(payload.frame)
        : this.matchState.latestFrame;
      if (payload.done) {
        this.running = false;
        this.moveSpeed = 1;
        this.setWinnerFromState(payload.state);
      }
      if (this.matchState.matchDone) {
        this.matchSummaryDismissed = false;
        this.showMatchWinnerBanner();
        this.updateCorewarMatchInProgress(false);
      }
      this.flush();
    } catch (error) {
      this.error = error instanceof Error ? error.message : String(error);
      this.running = false;
      this.flush();
    }
  }

  private startTickLoop(token: number): void {
    this.stopTickLoop();
    this.nextTickTime = performance.now();
    this.nextTickTime += 1000 / this.fps;
    void this.requestNextFrame(token);
  }

  private scheduleTick(token: number): void {
    if (this.tickHandle !== null) {
      return;
    }
    const now = performance.now();
    const delay = Math.max(0, this.nextTickTime - now);
    this.tickHandle = window.setTimeout(() => {
      this.tickHandle = null;
      if (!this.running || token !== this.runToken || this.destroyed) {
        return;
      }
      this.nextTickTime += 1000 / this.fps;
      void this.requestNextFrame(token);
    }, delay);
  }

  private async requestNextFrame(token: number): Promise<void> {
    if (!this.matchState.matchId || !this.running || token !== this.runToken || this.destroyed) {
      return;
    }
    if (this.inFlight) {
      this.scheduleTick(token);
      return;
    }
    this.stepCarry += this.moveSpeed / this.fps;
    const stepsToRun = Math.floor(this.stepCarry);
    if (stepsToRun < 1) {
      this.scheduleTick(token);
      return;
    }
    this.inFlight = true;
    let payload: CorewarStepPayload | null = null;
    try {
      payload = await this.runner.stepMatch({
        matchId: this.matchState.matchId,
        steps: stepsToRun,
        view: 'full'
      }) as CorewarStepPayload;
    } catch (error) {
      this.error = error instanceof Error ? error.message : String(error);
      this.running = false;
      this.stopTickLoop();
      this.flush();
    } finally {
      this.inFlight = false;
    }

    if (!payload || token !== this.runToken || this.destroyed) {
      return;
    }
    if (payload.error) {
      this.error = payload.error;
      this.running = false;
      this.stopTickLoop();
      this.flush();
      return;
    }

    const done = Boolean(payload.done);
    const matchDone = Boolean(payload.match_done ?? this.matchState.matchDone);
    this.stepCarry = Math.max(0, this.stepCarry - stepsToRun);
    let dispatchedImmediate = false;
    if (this.running && !done && token === this.runToken) {
      const now = performance.now();
      if (this.nextTickTime <= now) {
        this.nextTickTime += 1000 / this.fps;
        dispatchedImmediate = true;
        void this.requestNextFrame(token);
      }
    }

    this.applyState(payload.state);
    this.matchState.roundDone = done;
    this.matchState.matchDone = matchDone;
    if (payload.frame?.instructions) {
      this.matchState.latestFrame = this.frameFromPayload(payload.frame);
    }
    if (done) {
      this.running = false;
      this.moveSpeed = 1;
      this.stopTickLoop();
      this.roundSummaryDismissed = false;
      this.setWinnerFromState(payload.state);
    }
    if (this.matchState.matchDone) {
      this.matchSummaryDismissed = false;
      this.showMatchWinnerBanner();
      this.updateCorewarMatchInProgress(false);
    }
    if (this.running && !done && token === this.runToken && !dispatchedImmediate) {
      const now = performance.now();
      if (this.nextTickTime <= now) {
        this.nextTickTime += 1000 / this.fps;
        void this.requestNextFrame(token);
      } else {
        this.scheduleTick(token);
      }
    }
    this.flush();
  }

  private setWinnerFromState(state: Pick<CorewarStepState, 'per_warrior' | 'round_index'> | undefined): void {
    const roster = state?.per_warrior ?? this.matchState.perWarrior;
    if (!roster || roster.length === 0) {
      return;
    }
    const roundIndex = state?.round_index ?? this.matchState.roundIndex;
    if (roundIndex !== null && roundIndex !== undefined) {
      if (this.lastRoundResultIndex === roundIndex) {
        return;
      }
      this.lastRoundResultIndex = roundIndex;
    }
    const alive = roster.filter((warrior) => warrior.alive);
    if (alive.length === 1) {
      const winner = alive[0];
      const winnerIndex = roster.indexOf(winner);
      if (winnerIndex >= 0) {
        if (!this.roundWins[winnerIndex]) {
          this.roundWins[winnerIndex] = 0;
        }
        this.roundWins[winnerIndex] += 1;
      }
      const name = winner?.name?.trim() || 'Unknown warrior';
      this.showWinnerBanner(`${name} wins the round`);
      return;
    }
    if (alive.length === 0) {
      this.showWinnerBanner('All warriors terminated - round tie.');
      return;
    }
    const names = alive
      .map((warrior) => warrior?.name?.trim())
      .filter((name): name is string => Boolean(name));
    const label = names.length > 0 ? names.join(', ') : 'multiple warriors';
    this.showWinnerBanner(`Cycle limit reached - round tie between ${label}`);
  }

  private stopTickLoop(): void {
    if (this.tickHandle === null) {
      return;
    }
    window.clearTimeout(this.tickHandle);
    this.tickHandle = null;
  }

  private updateCorewarMatchInProgress(inProgress: boolean): void {
    this.store.dispatch(arenaActions.updateCorewarMatchInProgress({ inProgress }));
  }

  private showWinnerBanner(message: string): void {
    this.matchBannerMessage = message;
  }

  private showMatchWinnerBanner(): void {
    const winner = getCorewarMatchWinner(this.matchState.perWarrior, this.roundWins, this.matchState.matchDone);
    if (winner) {
      this.showWinnerBanner(`${winner.name} wins the match`);
      return;
    }
    this.showWinnerBanner('Match ended in a draw.');
  }

  private clearBanner(): void {
    this.matchBannerMessage = null;
  }

  private normalizeMoveSpeed(value: number): number {
    const numeric = Number.isFinite(value) ? Math.floor(value) : 0;
    return Math.max(0, Math.min(2000, numeric));
  }

  private applyState(state: CorewarStepState | undefined): void {
    if (!state) {
      return;
    }
    this.matchState.totalCycles = state.total_cycles ?? this.matchState.totalCycles;
    this.matchState.cycle = state.cycle ?? this.matchState.cycle;
    this.matchState.coreSize = state.core_size ?? this.matchState.coreSize;
    this.matchState.perWarrior = state.per_warrior ?? this.matchState.perWarrior;
    this.applyProcessQueues(state.processes);
    this.matchState.metrics = state.metrics ?? this.matchState.metrics;
    this.matchState.roundIndex = state.round_index ?? this.matchState.roundIndex;
    this.matchState.roundsTotal = state.rounds ?? this.matchState.roundsTotal;
    this.matchState.nAlive = state.n_alive ?? this.matchState.nAlive;
  }

  private frameFromPayload(frame: CorewarFrame | undefined): CorewarFrame | null {
    if (!frame?.instructions) {
      return null;
    }
    return {
      instructions: frame.instructions,
      owners: frame.owners ?? [],
      addresses: frame.addresses ?? undefined
    };
  }

  private applyProcessQueues(processes: CorewarProcessState[] | null | undefined): void {
    if (!processes || processes.length === 0) {
      this.matchState.processQueues = [];
      if (this.selectedWarriorIndex !== null) {
        this.selectedProcessQueue = [];
      }
      return;
    }
    if (!this.matchState.perWarrior.length) {
      this.matchState.processQueues = processes.map((entry) => entry?.queue ?? []);
      if (this.selectedWarriorIndex !== null) {
        this.selectedProcessQueue = this.matchState.processQueues[this.selectedWarriorIndex] ?? [];
      }
      return;
    }
    const map = new Map<number, number[]>();
    processes.forEach((entry) => {
      const id = entry?.id;
      if (Number.isFinite(id)) {
        map.set(id as number, entry?.queue ?? []);
      }
    });
    this.matchState.processQueues = this.matchState.perWarrior.map((warrior) => map.get(warrior.id) ?? []);
    if (this.selectedWarriorIndex !== null) {
      this.selectedProcessQueue = this.matchState.processQueues[this.selectedWarriorIndex] ?? [];
    }
  }

  private flush(): void {
    this.hooks?.flush();
  }
}
