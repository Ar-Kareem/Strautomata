import { ModelLogoComponent } from '../shared/model-logo.component';
import { ChangeDetectionStrategy, Component, DestroyRef, OnInit, computed, effect, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Store } from '@ngrx/store';
import { type ArenaState } from '@main/arena.store';
import { getHashRouteState, setHashRouteState } from '@main/arena.utils';
import type { HistoryIndexGame, MatchDetail, MatchReason, PlayerResult } from '@main/history.types';
import { HistoryService } from '../matches/history.service';
import { botLabel, familyColor, formatRating, formatSecs } from '../matches/history-format';
import { AutomataService, USER_BOT, type CompileResult, type FullMatchResult, type Opponent } from '../create/automata.service';
import { estimateRating, spreadOrder, type RatedResult, type RatingEstimate } from '../create/automata-rating';
import { ArenaCodeEditorComponent } from '../create/code-editor.component';
import { CreateDraftService } from '../create/create-draft.service';
import { MatchesReplayComponent } from '../matches/matches-replay.component';
import type { MatchLane } from '../create/match-lane-pool';

type Step = 'edit' | 'qualify' | 'evaluate';
/** 'error' is a runtime/setup failure that is nobody's fault: shown, but never scored */
type Outcome = 'pending' | 'running' | 'win' | 'loss' | 'draw' | 'fault' | 'gift' | 'error';

interface QualRow {
  index: number;
  seed: number;
  side: 0 | 1;
  outcome: Outcome;
  result: FullMatchResult | null;
}

interface EvalRow {
  key: string;
  opponent: Opponent;
  round: number;
  side: 0 | 1;
  seed: number;
  outcome: Outcome;
  result: FullMatchResult | null;
  /** wall-clock start of the match, for the "now playing" elapsed time */
  startedAt?: number;
}

/** the states a heatmap square can be in ('gift' folds into win, 'fault' into loss) */
type HeatState = 'pending' | 'running' | 'win' | 'loss' | 'draw' | 'error';

interface HeatTip {
  /** position inside the heatmap wrapper, in px */
  x: number;
  y: number;
  /** show below the square instead of above it, for squares on the first rows */
  below: boolean;
  title: string;
  lines: string[];
}

/** one match to play: who sits where and which seed */
interface MatchSpec {
  botA: string;
  botB: string;
  seed: number;
}

const QUAL_SEEDS = [42, 43, 44, 45, 46, 47, 48, 49, 50, 51];
const MAX_ROUNDS = 4;
const MAX_LANES = 32;
const DEFAULT_LANES = 10;
const DEFAULT_CODE = `# Define a function called \`policy\`.
# Its arguments are the observation fields described in the prompt (click "Show prompt"),
# and it must return one legal move.
# \`np\` (numpy) and \`random\` are available.

def policy(**kwargs):
    raise NotImplementedError("write your automaton here")
`;

const defaultLanes = (): number => DEFAULT_LANES;

const isSettled = (outcome: Outcome): boolean => outcome !== 'pending' && outcome !== 'running';
/** settled and counted: runtime errors are left out of every score */
const isScored = (outcome: Outcome): boolean => isSettled(outcome) && outcome !== 'error';

@Component({
  selector: 'arena-entrypoint-create',
  standalone: true,
  imports: [ModelLogoComponent, FormsModule, ArenaCodeEditorComponent, MatchesReplayComponent],
  templateUrl: './entrypoints-create.component.html',
  styleUrl: './entrypoints-create.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class ArenaEntrypointCreateComponent implements OnInit {
  private readonly store = inject(Store<{ arena: ArenaState }>);
  private readonly history = inject(HistoryService);
  private readonly automata = inject(AutomataService);
  private readonly destroyRef = inject(DestroyRef);
  private readonly drafts = inject(CreateDraftService);

  readonly botLabel = botLabel;
  readonly familyColor = familyColor;
  readonly formatRating = formatRating;
  readonly formatSecs = formatSecs;
  readonly maxLanes = MAX_LANES;

  // ---- setup ---------------------------------------------------------------------------
  readonly games = signal<HistoryIndexGame[]>([]);
  readonly gameKey = signal<string | null>(null);
  readonly game = computed(() => this.games().find((g) => g.id === this.gameKey()) ?? null);
  readonly code = signal(DEFAULT_CODE);
  readonly prompt = signal<string | null>(null);
  readonly promptOpen = signal(false);
  readonly promptLoading = signal(false);
  readonly opponents = signal<Opponent[]>([]);
  readonly exampleBot = signal('');
  /** code of the template as loaded (the starter for Blank), to tell whether the editor holds unsaved edits */
  readonly exampleCode = signal<string | null>(DEFAULT_CODE);
  readonly isEdited = computed(() => this.code() !== (this.exampleCode() ?? DEFAULT_CODE));
  readonly isPristine = computed(() => this.code() === DEFAULT_CODE && !this.exampleBot());
  readonly moveTimeout = signal(5);
  readonly lanes = signal(defaultLanes());
  readonly setupError = signal<string | null>(null);
  /** first runtime/setup failure of the current run (those matches are shown but not scored) */
  readonly runtimeError = signal<string | null>(null);
  readonly compiling = signal(false);
  readonly compileError = signal<string | null>(null);
  /** 1-based line of the compile/smoke error inside the user's code, when the runtime could tell */
  readonly compileErrorLine = signal<number | null>(null);
  readonly compileErrorSource = computed(() => {
    const line = this.compileErrorLine();
    if (line === null) {
      return null;
    }
    return this.code().split('\n')[line - 1] ?? null;
  });
  /** set by a successful Compile; cleared whenever the code or game changes */
  readonly compiled = signal<CompileResult | null>(null);
  /** bumped by every compile and every change that makes a pending compile obsolete */
  private compileGen = 0;
  /** settles when the runtime is done with the previous compile; the next one waits for it so a stale
   *  compile still running in the worker does not eat into the new one's time limit */
  private compileQueue: Promise<void> = Promise.resolve();

  // ---- flow ------------------------------------------------------------------------------
  readonly step = signal<Step>('edit');
  readonly qualRows = signal<QualRow[]>([]);
  readonly qualFault = signal<FullMatchResult | null>(null);
  readonly qualDone = signal(false);
  readonly evalRows = signal<EvalRow[]>([]);
  readonly evalRunning = signal(false);
  readonly paused = signal(false);
  readonly evalFinished = signal(false);
  readonly estimate = signal<RatingEstimate | null>(null);
  /** "starting runtimes" style message while lanes come up */
  readonly poolStatus = signal<string | null>(null);
  /** a section shows a spinner while its runtimes start or any of its matches is being played */
  private readonly startingRuntimes = computed(() => this.poolStatus()?.startsWith('starting runtimes') ?? false);
  readonly qualBusy = computed(
    () => !this.paused() && (this.qualRows().some((r) => r.outcome === 'running') || (this.step() === 'qualify' && this.startingRuntimes()))
  );
  readonly evalBusy = computed(
    () => !this.paused() && (this.evalRows().some((r) => r.outcome === 'running') || (this.step() === 'evaluate' && this.startingRuntimes()))
  );
  /** ticks once a second while matches run so elapsed times in the "now playing" cards update */
  readonly clock = signal(Date.now());
  private clockTimer: number | null = null;
  private runToken = 0;
  private pauseWaiters: (() => void)[] = [];

  readonly qualWins = computed(() => this.qualRows().filter((r) => r.outcome === 'win' || r.outcome === 'gift').length);
  readonly qualPlayed = computed(() => this.qualRows().filter((r) => isScored(r.outcome)).length);
  readonly qualFaultCount = computed(() => this.qualRows().filter((r) => r.outcome === 'fault').length);
  /** matches that actually reached an end, whatever the result */
  readonly qualFinished = computed(() => this.qualRows().filter((r) => isScored(r.outcome) && r.outcome !== 'fault').length);
  /** every game against random ended in a fault: nothing to rate, back to the editor */
  readonly qualAllCrashed = computed(() => this.qualDone() && this.qualPlayed() > 0 && this.qualFinished() === 0);
  /** waiting for the user to decide whether a sub-50% automaton should still go to the tournament */
  readonly qualConfirm = signal(false);

  readonly evalStats = computed(() => {
    const t = { played: 0, win: 0, loss: 0, draw: 0, fault: 0, gift: 0 };
    for (const row of this.evalRows()) {
      if (!isScored(row.outcome)) {
        continue;
      }
      t.played += 1;
      if (row.outcome === 'win') t.win += 1;
      else if (row.outcome === 'loss') t.loss += 1;
      else if (row.outcome === 'draw') t.draw += 1;
      else if (row.outcome === 'fault') t.fault += 1;
      else if (row.outcome === 'gift') t.gift += 1;
    }
    return t;
  });

  readonly evalProgress = computed(() => {
    const rows = this.evalRows();
    const done = rows.filter((r) => isSettled(r.outcome)).length;
    return { done, total: rows.length, pct: rows.length ? Math.round((done / rows.length) * 100) : 0 };
  });

  /** every match currently in flight (one per busy lane) */
  readonly currentRows = computed(() => this.evalRows().filter((r) => r.outcome === 'running'));

  readonly currentLabel = computed(() => {
    const rows = this.currentRows();
    const shown = rows.slice(0, 3).map((r) => `${botLabel(r.opponent.id)} (r${r.round + 1}, ${this.sideLabel(r.side)})`);
    const more = rows.length - shown.length;
    return more > 0 ? `${shown.join(', ')} +${more} more` : shown.join(', ');
  });

  /**
   * Where the estimate would sit in the tournament ranking, using the tournament's own rule:
   * rank = 1 + number of bots whose interval lower bound is above your interval upper bound.
   * (Ties are common, which is why the leaderboard shows several bots at the same rank.)
   */
  readonly projectedRank = computed(() => {
    const est = this.estimate();
    if (!est) {
      return null;
    }
    const clearlyAbove = this.opponents().filter((o) => o.low > est.high).length;
    return { rank: clearlyAbove + 1, of: this.opponents().length + 1 };
  });

  readonly faults = computed(() =>
    this.evalRows().filter((r) => r.outcome === 'fault' && r.result?.error).map((r) => ({ row: r, error: r.result!.error! }))
  );

  /** results table grouped by opponent (one column per round) */
  readonly evalByOpponent = computed(() => {
    const groups = new Map<string, { opponent: Opponent; rounds: (EvalRow | null)[]; running: boolean }>();
    for (const opp of this.opponents()) {
      groups.set(opp.id, { opponent: opp, rounds: [], running: false });
    }
    for (const row of this.evalRows()) {
      const g = groups.get(row.opponent.id);
      if (g) {
        g.rounds[row.round] = row;
        if (row.outcome === 'running') {
          g.running = true;
        }
      }
    }
    return [...groups.values()];
  });

  readonly roundsPlanned = computed(() => Math.max(1, ...this.evalRows().map((r) => r.round + 1)));

  // ---- match heatmap ---------------------------------------------------------------------
  readonly heatLegend: { state: HeatState; label: string }[] = [
    { state: 'pending', label: 'Not started' },
    { state: 'running', label: 'Playing' },
    { state: 'win', label: 'Won' },
    { state: 'loss', label: 'Lost' },
    { state: 'draw', label: 'Draw' }
  ];

  /** details of the square under the cursor, positioned relative to the heatmap wrapper */
  readonly heatTip = signal<HeatTip | null>(null);
  /** key of the heatmap square pinned by a click; its full detail (moves, fault, board replay) shows below */
  readonly pinnedKey = signal<string | null>(null);
  readonly pinned = computed(() => {
    const key = this.pinnedKey();
    return key === null ? null : this.evalRows().find((r) => r.key === key) ?? null;
  });
  /** the pinned match in the Match Viewer's detail format, so the replay component can drive the board */
  readonly pinnedDetail = computed<MatchDetail | null>(() => {
    const row = this.pinned();
    const result = row?.result;
    if (!row || !result || !isSettled(row.outcome)) {
      return null;
    }
    return this.toMatchDetail(row, result);
  });
  readonly pinnedLabels = computed<[string, string]>(() => {
    const row = this.pinned();
    if (!row) {
      return ['', ''];
    }
    const opp = botLabel(row.opponent.id);
    return row.side === 0 ? ['You', opp] : [opp, 'You'];
  });

  /** one heatmap line per round, so a round never shares a line with the next one */
  readonly heatRounds = computed(() => {
    const byRound = new Map<number, EvalRow[]>();
    for (const row of this.evalRows()) {
      const rows = byRound.get(row.round);
      if (rows) {
        rows.push(row);
      } else {
        byRound.set(row.round, [row]);
      }
    }
    return [...byRound.entries()].sort((a, b) => a[0] - b[0]).map(([round, rows]) => ({ round, rows }));
  });

  heatState(outcome: Outcome): HeatState {
    if (outcome === 'gift') {
      return 'win';
    }
    if (outcome === 'fault') {
      return 'loss';
    }
    return outcome;
  }

  showHeatTip(row: EvalRow, event: Event): void {
    const cell = event.currentTarget as HTMLElement | null;
    const wrap = cell?.closest('.cr-heat') as HTMLElement | null;
    if (!cell || !wrap) {
      return;
    }
    const cellBox = cell.getBoundingClientRect();
    const wrapBox = wrap.getBoundingClientRect();
    const centre = cellBox.left - wrapBox.left + cellBox.width / 2;
    const margin = 130;
    const top = cellBox.top - wrapBox.top;
    const below = top < 90;
    this.heatTip.set({
      x: Math.min(Math.max(centre, margin), Math.max(margin, wrapBox.width - margin)),
      y: below ? cellBox.bottom - wrapBox.top + 8 : top - 8,
      below,
      title: botLabel(row.opponent.id),
      lines: this.heatTipLines(row)
    });
  }

  hideHeatTip(): void {
    this.heatTip.set(null);
  }

  toggleHeatPin(row: EvalRow): void {
    this.heatTip.set(null);
    this.pinnedKey.set(this.pinnedKey() === row.key ? null : row.key);
  }

  unpin(): void {
    this.pinnedKey.set(null);
  }

  /** who faulted, from the pinned match's point of view */
  pinnedFaultSide(): 'you' | 'opponent' | null {
    const row = this.pinned();
    if (!row || row.outcome === 'fault') {
      return row ? 'you' : null;
    }
    return row.outcome === 'gift' ? 'opponent' : null;
  }

  private toMatchDetail(row: EvalRow, result: FullMatchResult): MatchDetail {
    const reason: MatchReason =
      result.reason === 'win' || result.reason === 'draw'
        ? result.reason
        : result.reason === 'error' || result.reason === 'illegal'
          ? 'error'
          : result.reason === 'timeout' || result.reason === 'hung'
            ? 'timeout'
            : 'unknown';
    const culprit = result.culprit;
    const per = (player: 0 | 1): PlayerResult => {
      if (reason === 'win') {
        return result.winner === player ? 'win' : 'loss';
      }
      if (reason === 'draw') {
        return 'draw';
      }
      if (reason === 'error') {
        return culprit === player ? 'error' : 'enemy_error';
      }
      if (reason === 'timeout') {
        return culprit === player ? 'timeout' : 'enemy_timeout';
      }
      return 'unknown';
    };
    const history = result.history ?? [];
    return {
      i: 0,
      a: row.side === 0 ? USER_BOT : row.opponent.id,
      b: row.side === 0 ? row.opponent.id : USER_BOT,
      seed: row.seed,
      reason,
      winner: result.winner,
      result: [per(0), per(1)],
      move_count: result.moves,
      secs: result.secs,
      moves: history.map(([player, move]) => [player, move] as [number, unknown]),
      think: history.map(([, , secs]) => (typeof secs === 'number' ? secs : null)),
      exception: result.traceback ?? result.error ?? null,
      timeout_hit: null,
      returns: null,
      other: null,
      started: null
    };
  }

  private heatTipLines(row: EvalRow): string[] {
    const lines = [
      `#${row.opponent.rank} · ${formatRating(row.opponent.rating)}`,
      `round ${row.round + 1} · you play ${this.sideLabel(row.side)} · seed ${row.seed}`
    ];
    if (row.outcome === 'pending') {
      lines.push('Not started');
      return lines;
    }
    if (row.outcome === 'running') {
      lines.push('Playing…');
      return lines;
    }
    const result = row.result;
    const detail = result ? `${result.moves} mv · ${formatSecs(result.secs)}` : '';
    const label = this.outcomeLabel(row.outcome);
    lines.push(detail ? `${label} · ${detail}` : label);
    if (row.outcome === 'fault' || row.outcome === 'gift' || row.outcome === 'error') {
      const reason = this.describeFault(result);
      if (reason) {
        lines.push(row.outcome === 'fault' ? `Your fault: ${reason}` : row.outcome === 'gift' ? `Opponent fault: ${reason}` : `${reason} · not scored`);
      }
    }
    if (result?.error) {
      lines.push(result.error.length > 160 ? `${result.error.slice(0, 160)}…` : result.error);
    }
    return lines;
  }

  constructor() {
    effect(() => {
      const key = this.gameKey();
      this.drafts.gameKey = key;
      this.drafts.moveTimeout = this.moveTimeout();
      this.drafts.lanes = this.lanes();
      this.drafts.save(key, { code: this.code(), exampleBot: this.exampleBot(), exampleCode: this.exampleCode() });
    });
  }

  ngOnInit(): void {
    const { path, params } = getHashRouteState();
    const game = path === '/create' ? params.get('game') : null;
    this.gameKey.set(game || this.drafts.gameKey);
    this.restoreDraft(this.gameKey());
    this.moveTimeout.set(this.drafts.moveTimeout ?? this.moveTimeout());
    this.lanes.set(this.drafts.lanes ?? this.lanes());
    setHashRouteState('/create', this.gameKey() ? new URLSearchParams({ game: this.gameKey()! }) : undefined);
    this.automata.warmRuntime();
    this.history
      .loadIndex()
      .then((index) => {
        this.games.set([...index.games].sort((a, b) => a.label.localeCompare(b.label)));
        if (this.gameKey()) {
          void this.loadGameAssets();
        }
      })
      .catch((err) => this.setupError.set(err instanceof Error ? err.message : String(err)));
    this.destroyRef.onDestroy(() => {
      this.runToken += 1;
      this.resumeAll();
      this.stopClock();
      this.automata.disposeLanes();
    });
  }

  // ---- setup actions ----------------------------------------------------------------------
  /** load the saved draft of a game; without one the editor keeps its code */
  private restoreDraft(key: string | null): void {
    const draft = this.drafts.get(key);
    if (draft) {
      this.code.set(draft.code);
      this.exampleBot.set(draft.exampleBot);
      this.exampleCode.set(draft.exampleCode);
    } else {
      this.exampleBot.set('');
      this.exampleCode.set(null);
    }
  }

  /** a pending compile no longer matches the editor: drop its result whenever it arrives */
  private invalidateCompile(): void {
    this.compileGen += 1;
    this.compiling.set(false);
    this.compiled.set(null);
    this.compileError.set(null);
    this.compileErrorLine.set(null);
  }

  private confirmDiscard(): boolean {
    return !this.isEdited() || window.confirm('Discard your changes to the code?');
  }

  selectGame(key: string | null): void {
    this.gameKey.set(key || null);
    this.prompt.set(null);
    this.opponents.set([]);
    this.restoreDraft(this.gameKey());
    this.invalidateCompile();
    this.resetRuns();
    setHashRouteState('/create', key ? new URLSearchParams({ game: key }) : undefined);
    this.promptLoading.set(false);
    if (key) {
      void this.loadGameAssets();
      void this.loadPrompt();
    }
  }

  private async loadGameAssets(): Promise<void> {
    const game = this.game();
    if (!game) {
      return;
    }
    this.setupError.set(null);
    try {
      const opponents = await this.automata.loadOpponents(game.id);
      if (this.game() === game) {
        this.opponents.set(opponents);
      }
    } catch (err) {
      if (this.game() === game) {
        this.setupError.set(err instanceof Error ? err.message : String(err));
      }
    }
  }

  togglePrompt(): void {
    this.promptOpen.set(!this.promptOpen());
    void this.loadPrompt();
  }

  /** load the open prompt for the current game; a response for a game no longer selected is dropped */
  private async loadPrompt(): Promise<void> {
    const game = this.game();
    if (!this.promptOpen() || !game || this.prompt() !== null) {
      return;
    }
    this.promptLoading.set(true);
    let text: string;
    try {
      text = await this.automata.loadPrompt(game.game, game.world);
    } catch (err) {
      text = `Could not load the prompt: ${err instanceof Error ? err.message : String(err)}`;
    }
    if (this.game() !== game) {
      return;
    }
    this.prompt.set(text);
    this.promptLoading.set(false);
  }

  async loadExample(botId: string): Promise<void> {
    const previous = this.exampleBot();
    if (!this.confirmDiscard()) {
      // the <select> already shows the new choice: bounce the model so it shows the old one again
      this.exampleBot.set(botId);
      queueMicrotask(() => this.exampleBot.set(previous));
      return;
    }
    this.exampleBot.set(botId);
    const game = this.game();
    if (!botId) {
      this.applyTemplate(DEFAULT_CODE);
      return;
    }
    if (!game) {
      return;
    }
    this.invalidateCompile();
    try {
      const code = await this.automata.loadBotCode(game.game, game.world, botId);
      if (this.exampleBot() === botId && this.game() === game) {
        this.applyTemplate(code);
      }
    } catch (err) {
      this.setupError.set(err instanceof Error ? err.message : String(err));
    }
  }

  /** back to the blank starter for this game; the saved draft is dropped */
  resetDraft(): void {
    if (!this.confirmDiscard()) {
      return;
    }
    this.drafts.clear(this.gameKey());
    this.exampleBot.set('');
    this.applyTemplate(DEFAULT_CODE);
  }

  private applyTemplate(code: string): void {
    this.exampleCode.set(code);
    this.code.set(code);
    this.invalidateCompile();
  }

  setCode(value: string): void {
    if (value === this.code()) {
      return;
    }
    this.code.set(value);
    this.invalidateCompile();
  }

  onTimeoutChange(value: string): void {
    const n = Number(value);
    if (Number.isFinite(n) && n > 0) {
      this.moveTimeout.set(n);
    }
  }

  onLanesChange(value: string): void {
    const n = Math.round(Number(value));
    if (Number.isFinite(n) && n >= 1) {
      this.lanes.set(Math.min(MAX_LANES, n));
    }
  }

  backToEditor(): void {
    this.stop();
    this.step.set('edit');
  }

  private resetRuns(): void {
    this.runToken += 1;
    this.resumeAll();
    this.qualRows.set([]);
    this.qualFault.set(null);
    this.runtimeError.set(null);
    this.qualDone.set(false);
    this.qualConfirm.set(false);
    this.evalRows.set([]);
    this.heatTip.set(null);
    this.pinnedKey.set(null);
    this.evalRunning.set(false);
    this.evalFinished.set(false);
    this.paused.set(false);
    this.estimate.set(null);
    this.poolStatus.set(null);
    this.step.set('edit');
  }

  // ---- compile ---------------------------------------------------------------------------
  /** Compile the code and call the policy once on the initial board; Run stays disabled until this passes. */
  async compile(): Promise<boolean> {
    const game = this.game();
    if (!game || this.compiling()) {
      return false;
    }
    this.resetRuns();
    this.invalidateCompile();
    const gen = this.compileGen;
    this.compiling.set(true);
    const code = this.code();
    // a result only counts for the exact game and code it was compiled for
    const current = () => gen === this.compileGen && this.game() === game && this.code() === code;
    const previous = this.compileQueue;
    let release = () => {};
    this.compileQueue = new Promise<void>((resolve) => (release = resolve));
    try {
      await previous;
      if (!current()) {
        return false;
      }
      const result = await this.automata.compile(game.game, game.world, code, this.moveTimeout());
      if (!current()) {
        return false;
      }
      if (!result.ok) {
        this.compileError.set([result.error, result.traceback].filter(Boolean).join('\n\n') || 'Compile failed');
        this.compileErrorLine.set(typeof result.line === 'number' ? result.line : null);
        return false;
      }
      this.compiled.set(result);
      return true;
    } catch (err) {
      if (current()) {
        this.compileError.set(err instanceof Error ? err.message : String(err));
      }
      return false;
    } finally {
      release();
      if (gen === this.compileGen) {
        this.compiling.set(false);
      }
    }
  }

  // ---- run -------------------------------------------------------------------------------
  async run(): Promise<void> {
    const game = this.game();
    if (!game || this.compiling() || !this.compiled()) {
      return;
    }
    this.resetRuns();
    const token = ++this.runToken;
    this.step.set('qualify');
    const verdict = await this.qualify(game, token);
    if (token !== this.runToken) {
      return;
    }
    if (verdict === 'go') {
      this.step.set('evaluate');
      await this.evaluate(game, token);
    } else if (verdict === 'ask') {
      this.qualConfirm.set(true);
    }
  }

  /** the user chose to take a sub-50% automaton to the tournament anyway */
  async proceedToTournament(): Promise<void> {
    const game = this.game();
    if (!game || !this.qualConfirm()) {
      return;
    }
    this.qualConfirm.set(false);
    this.step.set('evaluate');
    await this.evaluate(game, this.runToken);
  }

  private userOutcome(result: FullMatchResult, side: 0 | 1): Outcome {
    if (result.reason === 'win') {
      return result.winner === side ? 'win' : 'loss';
    }
    if (result.reason === 'draw') {
      return 'draw';
    }
    if (result.reason === 'setup') {
      return 'error';
    }
    if (result.culprit === null) {
      return 'fault';
    }
    return result.culprit === side ? 'fault' : 'gift';
  }

  private noteRuntimeError(outcome: Outcome, result: FullMatchResult): void {
    if (outcome === 'error' && !this.runtimeError()) {
      this.runtimeError.set(`Runtime error, match not counted: ${result.error ?? 'unknown'}`);
    }
  }

  private userScore(outcome: Outcome): number {
    return outcome === 'win' || outcome === 'gift' ? 1 : outcome === 'draw' ? 0.5 : 0;
  }

  /**
   * Play `count` matches spread over the parallel lanes. Each lane loads the user's code, then
   * pulls the next unplayed index until the queue is empty, the run is stopped, or `onResult`
   * asks to abort. Resolves to true only when every match was played.
   */
  private async runInParallel(
    game: HistoryIndexGame,
    token: number,
    count: number,
    spec: (index: number) => MatchSpec,
    onStart: (index: number) => void,
    onResult: (index: number, result: FullMatchResult) => boolean
  ): Promise<boolean> {
    const lanes = this.automata.ensureLanes(this.lanes());
    const code = this.code();
    let next = 0;
    let aborted = false;
    let ready = 0;
    let failed = 0;
    let skipped = 0;
    let lastPrepareError: string | null = null;
    const alive = () => token === this.runToken && !aborted;
    const setPoolStatus = () => {
      if (token !== this.runToken) {
        return;
      }
      if (ready + failed + skipped < lanes.length) {
        this.poolStatus.set(`starting runtimes · ${ready} of ${lanes.length} ready${failed ? ` · ${failed} failed` : ''}`);
      } else if (failed > 0) {
        this.poolStatus.set(`Running on ${ready} of ${lanes.length} parallel runtimes (${failed} couldn't start)`);
      } else {
        this.poolStatus.set(null);
      }
    };
    setPoolStatus();

    // bring runtimes up a few at a time: starting many at once can make some fail to load OpenSpiel
    const startingLimit = 3;
    let starting = 0;
    const startQueue: (() => void)[] = [];
    const acquireStart = () =>
      new Promise<void>((resolve) => {
        if (starting < startingLimit) {
          starting += 1;
          resolve();
        } else {
          startQueue.push(() => {
            starting += 1;
            resolve();
          });
        }
      });
    const releaseStart = () => {
      starting -= 1;
      startQueue.shift()?.();
    };

    const drive = async (lane: MatchLane): Promise<void> => {
      await acquireStart();
      if (next >= count || !alive()) {
        // the other runtimes already took every match: no need to load this one
        releaseStart();
        skipped += 1;
        setPoolStatus();
        return;
      }
      try {
        await this.automata.prepareLane(lane, game.game, game.world, code);
      } catch (err) {
        releaseStart();
        lastPrepareError = err instanceof Error ? err.message : String(err);
        console.error(`Match runtime ${lane.index + 1} could not start:`, lastPrepareError);
        failed += 1;
        setPoolStatus();
        return;
      }
      releaseStart();
      ready += 1;
      setPoolStatus();
      while (alive()) {
        if (this.paused()) {
          await this.waitWhilePaused();
          if (!alive()) {
            return;
          }
        }
        if (lane.prepared === null) {
          // the runtime was restarted after a hang: load the code again before using it
          try {
            await this.automata.prepareLane(lane, game.game, game.world, code);
          } catch (err) {
            lastPrepareError = err instanceof Error ? err.message : String(err);
            ready -= 1;
            failed += 1;
            setPoolStatus();
            return;
          }
        }
        const index = next++;
        if (index >= count) {
          return;
        }
        onStart(index);
        const { botA, botB, seed } = spec(index);
        let result: FullMatchResult;
        try {
          result = await this.automata.playOnLane(lane, game.game, game.world, botA, botB, seed, this.moveTimeout());
        } catch (err) {
          result = { winner: null, reason: 'setup', culprit: null, error: err instanceof Error ? err.message : String(err), moves: 0, secs: 0 };
        }
        if (!alive()) {
          return;
        }
        if (!onResult(index, result)) {
          aborted = true;
          return;
        }
      }
    };

    await Promise.all(lanes.map(drive));
    if (token !== this.runToken) {
      return false;
    }
    if (failed === 0) {
      this.poolStatus.set(null);
    }
    if (ready === 0 && failed > 0) {
      this.setupError.set(`Could not start any match runtime: ${lastPrepareError ?? 'unknown error'}`);
      return false;
    }
    if (aborted) {
      // kill matches still in flight on other lanes and show their rows as not played
      this.automata.disposeLanes();
      this.clearRunning();
      return false;
    }
    return true;
  }

  /**
   * Play every game against random. Only a total crash blocks the run: if a single game reached an
   * end the automaton can go on, and a win rate below half asks the user first.
   */
  private async qualify(game: HistoryIndexGame, token: number): Promise<'go' | 'ask' | 'stop'> {
    this.qualRows.set(QUAL_SEEDS.map((seed, index) => ({ index, seed, side: (index % 2) as 0 | 1, outcome: 'pending', result: null })));
    const completed = await this.runInParallel(
      game,
      token,
      QUAL_SEEDS.length,
      (i) => {
        const side = (i % 2) as 0 | 1;
        return { botA: side === 0 ? USER_BOT : 'random', botB: side === 0 ? 'random' : USER_BOT, seed: QUAL_SEEDS[i] };
      },
      (i) => this.patchQual(i, { outcome: 'running' }),
      (i, result) => {
        const outcome = this.userOutcome(result, (i % 2) as 0 | 1);
        this.patchQual(i, { outcome, result });
        this.noteRuntimeError(outcome, result);
        if (outcome === 'fault' && !this.qualFault()) {
          this.qualFault.set(result);
        }
        return true;
      }
    );
    if (token !== this.runToken) {
      return 'stop';
    }
    this.qualDone.set(true);
    if (!completed || this.qualFinished() === 0) {
      return 'stop';
    }
    return this.qualWins() * 2 >= this.qualPlayed() ? 'go' : 'ask';
  }

  private patchQual(index: number, patch: Partial<QualRow>): void {
    this.qualRows.update((rows) => rows.map((r, i) => (i === index ? { ...r, ...patch } : r)));
  }

  private async evaluate(game: HistoryIndexGame, token: number): Promise<void> {
    const order = spreadOrder(this.opponents());
    if (order.length === 0) {
      this.setupError.set('No tournament opponents are available for this game.');
      return;
    }
    const rows: EvalRow[] = [];
    for (let round = 0; round < MAX_ROUNDS; round += 1) {
      order.forEach((opponent, i) => {
        rows.push({
          key: `${opponent.id}|${round}`,
          opponent,
          round,
          side: ((i + round) % 2) as 0 | 1,
          seed: 1000 + round * 1000 + i,
          outcome: 'pending',
          result: null
        });
      });
    }
    this.evalRows.set(rows);
    this.evalRunning.set(true);
    this.evalFinished.set(false);
    this.startClock();
    const rated: RatedResult[] = [];
    const completed = await this.runInParallel(
      game,
      token,
      rows.length,
      (i) => {
        const row = rows[i];
        return {
          botA: row.side === 0 ? USER_BOT : row.opponent.id,
          botB: row.side === 0 ? row.opponent.id : USER_BOT,
          seed: row.seed
        };
      },
      (i) => this.patchEval(rows[i].key, { outcome: 'running', startedAt: Date.now() }),
      (i, result) => {
        const row = rows[i];
        const outcome = this.userOutcome(result, row.side);
        this.patchEval(row.key, { outcome, result });
        this.noteRuntimeError(outcome, result);
        if (outcome !== 'error') {
          rated.push({ opponentRating: row.opponent.rating, score: this.userScore(outcome) });
          this.estimate.set(estimateRating(rated));
        }
        return true; // a hung match is a loss like any other fault; its lane restarts and reloads the code by itself
      }
    );
    if (token !== this.runToken) {
      return;
    }
    this.stopClock();
    this.evalRunning.set(false);
    this.evalFinished.set(completed);
  }

  private startClock(): void {
    if (this.clockTimer === null) {
      this.clockTimer = window.setInterval(() => this.clock.set(Date.now()), 1000);
    }
  }

  private stopClock(): void {
    if (this.clockTimer !== null) {
      window.clearInterval(this.clockTimer);
      this.clockTimer = null;
    }
  }

  elapsedLabel(row: EvalRow): string {
    if (!row.startedAt) {
      return '';
    }
    const secs = Math.max(0, Math.floor((this.clock() - row.startedAt) / 1000));
    return secs >= 60 ? `${Math.floor(secs / 60)}m ${String(secs % 60).padStart(2, '0')}s` : `${secs}s`;
  }

  private patchEval(key: string, patch: Partial<EvalRow>): void {
    this.evalRows.update((rows) => rows.map((r) => (r.key === key ? { ...r, ...patch } : r)));
  }

  private clearRunning(): void {
    this.qualRows.update((rows) => rows.map((r) => (r.outcome === 'running' ? { ...r, outcome: 'pending' } : r)));
    this.evalRows.update((rows) => rows.map((r) => (r.outcome === 'running' ? { ...r, outcome: 'pending' } : r)));
  }

  private hasRunning(): boolean {
    return this.qualRows().some((r) => r.outcome === 'running') || this.evalRows().some((r) => r.outcome === 'running');
  }

  togglePause(): void {
    if (this.paused()) {
      this.paused.set(false);
      this.resumeAll();
      return;
    }
    this.paused.set(true); // lanes finish their current match, then wait
  }

  stop(): void {
    this.runToken += 1;
    this.resumeAll();
    this.paused.set(false);
    this.poolStatus.set(null);
    if (this.hasRunning()) {
      this.automata.disposeLanes(); // matches cannot be interrupted inside Python; kill the runtimes
    }
    this.stopClock();
    this.evalRunning.set(false);
    this.clearRunning();
  }

  private waitWhilePaused(): Promise<void> {
    return new Promise<void>((resolve) => {
      this.pauseWaiters.push(resolve);
    });
  }

  private resumeAll(): void {
    const waiters = this.pauseWaiters;
    this.pauseWaiters = [];
    for (const resume of waiters) {
      resume();
    }
  }

  outcomeLabel(outcome: Outcome): string {
    switch (outcome) {
      case 'win':
        return 'Win';
      case 'loss':
        return 'Loss';
      case 'draw':
        return 'Draw';
      case 'fault':
        return 'Your fault';
      case 'gift':
        return 'Opp. fault';
      case 'error':
        return 'Error';
      case 'running':
        return 'Playing…';
      default:
        return '';
    }
  }

  describeFault(result: FullMatchResult | null): string {
    if (!result) {
      return '';
    }
    switch (result.reason) {
      case 'illegal':
        return 'Illegal move';
      case 'timeout':
        return 'Move timeout';
      case 'error':
        return 'Exception';
      case 'hung':
        return 'Runtime hung';
      case 'setup':
        return 'Setup error';
      default:
        return '';
    }
  }

  sideLabel(side: 0 | 1): string {
    return side === 0 ? 'first' : 'second';
  }
}
