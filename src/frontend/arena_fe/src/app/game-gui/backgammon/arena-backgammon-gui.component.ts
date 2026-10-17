import { ChangeDetectionStrategy, ChangeDetectorRef, Component, Input, OnDestroy } from '@angular/core';
import { HumanMovePanelComponent } from '@arena/human-move-panel.component';
import type { MatchResultSummary, StatusTone } from '@main/arena.constants';
import { ArenaBannerComponent } from '../../components/arena-gui-helpers/arena-banner.component';
import { ArenaGuiAlertComponent } from '../../components/arena-gui-helpers/arena-gui-alert.component';
import { ArenaGuiEmptyComponent } from '../../components/arena-gui-helpers/arena-gui-empty.component';
import { ArenaGuiLegendComponent } from '../../components/arena-gui-helpers/arena-gui-legend.component';

type BackgammonPointCell = {
  key: string;
  point: number;
  row: 'top' | 'bottom';
  owner: 'black' | 'white' | null;
  count: number;
  tokens: number[];
  overflow: number;
  legalFrom: boolean;
  legalTo: boolean;
  selected: boolean;
  illegal: boolean;
  winning: boolean;
};

type BackgammonMoveStep = {
  from: string;
  to: string;
  hit: boolean;
};

type ParsedBackgammonMove = {
  id: string;
  raw: string;
  label: string;
  steps: BackgammonMoveStep[];
  primaryFromKey: string | null;
  primaryToKey: string | null;
};

@Component({
  selector: 'arena-backgammon-gui',
  standalone: true,
  templateUrl: './arena-backgammon-gui.component.html',
  styleUrl: './arena-backgammon-gui.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    HumanMovePanelComponent,
    ArenaBannerComponent,
    ArenaGuiAlertComponent,
    ArenaGuiEmptyComponent,
    ArenaGuiLegendComponent
  ]
})
export class ArenaBackgammonGuiComponent implements OnDestroy {
  readonly topOrder = [12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23];
  readonly bottomOrder = [11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0];

  topPoints: BackgammonPointCell[] = [];
  bottomPoints: BackgammonPointCell[] = [];
  diceValues: number[] = [];
  blackBar = 0;
  whiteBar = 0;
  blackOff = 0;
  whiteOff = 0;
  blackBarTokens: number[] = [];
  whiteBarTokens: number[] = [];
  blackBarOverflow = 0;
  whiteBarOverflow = 0;
  currentPlayer: number | null = null;
  boardReady = false;
  matchBannerMessage: string | null = null;
  illegalClickMessage: string | null = null;
  illegalClickToken = 0;
  hasWinner = false;

  @Input() botA = 'Automaton A';
  @Input() botB = 'Automaton B';
  @Input() statusTone: StatusTone = 'idle';
  @Input() statusMessage = '';
  @Input() showHumanControls = false;
  @Input() submitHumanMove?: (move: string) => void;

  private awaitingHuman = false;
  @Input() set awaitingHumanMove(value: boolean) {
    this.awaitingHuman = value;
    if (!value) {
      this.selectedSourceKey = null;
    }
    this.refreshBoard();
  }
  get awaitingHumanMove(): boolean {
    return this.awaitingHuman;
  }

  private ptsBlack: number[] = new Array(24).fill(0);
  private ptsWhite: number[] = new Array(24).fill(0);
  private currentLegalMoves: string[] = [];
  private moveEntries: ParsedBackgammonMove[] = [];
  private fromKeys = new Set<string>();
  private toKeysByFrom = new Map<string, Set<string>>();
  private movesByFromTo = new Map<string, string[]>();
  private selectedSourceKey: string | null = null;
  private illegalKey: string | null = null;
  private pts1Mode: 'identity' | 'reversed' = 'reversed';
  private movePointMode: 'ascending' | 'descending' = 'descending';
  private bannerTimer: number | null = null;
  private lastMatchStamp: number | null = null;
  private matchWinner: number | null = null;

  constructor(private readonly cdr: ChangeDetectorRef) {}

  get activePlayerLabel(): string {
    if (this.currentPlayer === 0) {
      return this.blackPlayerName;
    }
    if (this.currentPlayer === 1) {
      return this.whitePlayerName;
    }
    return '';
  }

  get blackPlayerName(): string {
    return this.botA;
  }

  get whitePlayerName(): string {
    return this.botB;
  }

  get humanHint(): string {
    if (!this.showHumanControls) {
      return '';
    }
    if (!this.awaitingHumanMove) {
      return 'AI\'s turn...';
    }
    if (this.selectedSourceKey) {
      return 'Select a destination, or choose a move from the legal list.';
    }
    return 'Select a source point (0..23), bar, or pick a move from the legal list.';
  }

  get activeColor(): 'black' | 'white' | null {
    if (this.currentPlayer === 0) {
      return 'black';
    }
    if (this.currentPlayer === 1) {
      return 'white';
    }
    return null;
  }

  get availableMoves(): ParsedBackgammonMove[] {
    if (!this.selectedSourceKey) {
      return this.moveEntries;
    }
    const filtered = this.moveEntries.filter((move) => move.primaryFromKey === this.selectedSourceKey);
    return filtered.length > 0 ? filtered : this.moveEntries;
  }

  get selectedFromKey(): string | null {
    return this.selectedSourceKey;
  }

  @Input() set legalMoves(value: string[] | null) {
    this.currentLegalMoves = Array.isArray(value) ? value : [];
    this.rebuildMoveMaps();
    this.refreshBoard();
  }

  get legalMoves(): string[] {
    return this.currentLegalMoves;
  }

  @Input() set illegalAction(value: string | null) {
    const parsed = value ? this.parseBackgammonMove(value, 'illegal') : null;
    this.illegalKey = parsed?.primaryToKey ?? null;
    this.refreshBoard();
  }

  @Input() set matchResult(value: MatchResultSummary | null) {
    if (!value) {
      this.lastMatchStamp = null;
      this.matchWinner = null;
      this.hasWinner = false;
      this.clearBanner();
      this.refreshBoard();
      return;
    }
    if (this.lastMatchStamp === value.finishedAt) {
      return;
    }
    this.lastMatchStamp = value.finishedAt;
    this.matchWinner = value.illegal ? null : value.winner;
    this.hasWinner = this.matchWinner !== null;
    if (value.illegal) {
      this.clearBanner();
      this.refreshBoard();
      return;
    }
    this.matchBannerMessage = this.resolveResultMessage(value.winner);
    this.resetBannerTimer();
    this.refreshBoard();
  }

  @Input() set observation(value: unknown | null) {
    const parsed = this.parseObservation(value);
    if (!parsed) {
      this.boardReady = false;
      this.currentPlayer = null;
      this.ptsBlack = new Array(24).fill(0);
      this.ptsWhite = new Array(24).fill(0);
      this.blackBar = 0;
      this.whiteBar = 0;
      this.blackOff = 0;
      this.whiteOff = 0;
      this.blackBarTokens = [];
      this.whiteBarTokens = [];
      this.blackBarOverflow = 0;
      this.whiteBarOverflow = 0;
      this.diceValues = [];
      this.topPoints = [];
      this.bottomPoints = [];
      return;
    }
    this.boardReady = true;
    this.currentPlayer = parsed.player;
    this.ptsBlack = parsed.pts0;
    this.ptsWhite = parsed.pts1;
    this.blackBar = parsed.p0Bar;
    this.whiteBar = parsed.p1Bar;
    this.blackOff = parsed.p0Off;
    this.whiteOff = parsed.p1Off;
    this.refreshBarTokens();
    this.diceValues = parsed.dice;
    this.pts1Mode = this.resolvePts1Mode(this.ptsBlack, this.ptsWhite);
    this.rebuildMoveMaps();
    this.refreshBoard();
  }

  onPointClick(point: BackgammonPointCell): void {
    if (!this.awaitingHumanMove || !this.submitHumanMove) {
      return;
    }
    const key = point.key;
    if (!this.selectedSourceKey) {
      if (!point.legalFrom) {
        this.showIllegalClick('Select a movable source.');
        return;
      }
      this.selectedSourceKey = key;
      this.refreshBoard();
      return;
    }
    if (this.selectedSourceKey === key) {
      this.selectedSourceKey = null;
      this.refreshBoard();
      return;
    }
    if (point.legalFrom) {
      this.selectedSourceKey = key;
      this.refreshBoard();
      return;
    }
    this.trySubmitFromTo(this.selectedSourceKey, key);
  }

  onBarClick(): void {
    if (!this.awaitingHumanMove || !this.submitHumanMove) {
      return;
    }
    const key = 'bar';
    if (!this.selectedSourceKey) {
      if (!this.fromKeys.has(key)) {
        this.showIllegalClick('No legal entry from bar.');
        return;
      }
      this.selectedSourceKey = key;
      this.refreshBoard();
      return;
    }
    if (this.selectedSourceKey === key) {
      this.selectedSourceKey = null;
      this.refreshBoard();
      return;
    }
    if (this.fromKeys.has(key)) {
      this.selectedSourceKey = key;
      this.refreshBoard();
      return;
    }
    this.trySubmitFromTo(this.selectedSourceKey, key);
  }

  onOffClick(): void {
    if (!this.awaitingHumanMove || !this.submitHumanMove || !this.selectedSourceKey) {
      return;
    }
    this.trySubmitFromTo(this.selectedSourceKey, 'off');
  }

  onMoveClick(move: ParsedBackgammonMove): void {
    if (!this.awaitingHumanMove || !this.submitHumanMove) {
      return;
    }
    this.selectedSourceKey = null;
    this.refreshBoard();
    this.submitHumanMove(move.raw);
  }

  isBarSelected(): boolean {
    return this.selectedSourceKey === 'bar';
  }

  isBarLegalFrom(): boolean {
    return this.awaitingHumanMove && this.fromKeys.has('bar');
  }

  isBarLegalTo(): boolean {
    if (!this.awaitingHumanMove || !this.selectedSourceKey) {
      return false;
    }
    return this.toKeysByFrom.get(this.selectedSourceKey)?.has('bar') ?? false;
  }

  isOffLegalTo(side: 'black' | 'white'): boolean {
    if (!this.awaitingHumanMove || !this.selectedSourceKey) {
      return false;
    }
    const active = this.activeColor;
    if (active !== side) {
      return false;
    }
    return this.toKeysByFrom.get(this.selectedSourceKey)?.has('off') ?? false;
  }

  isOffWinning(side: 'black' | 'white'): boolean {
    if (this.matchWinner === null) {
      return false;
    }
    return (this.matchWinner === 0 && side === 'black') || (this.matchWinner === 1 && side === 'white');
  }

  isBarIllegal(): boolean {
    return this.illegalKey === 'bar';
  }

  isOffIllegal(side: 'black' | 'white'): boolean {
    if (this.illegalKey !== 'off') {
      return false;
    }
    const active = this.activeColor;
    return active === side;
  }

  ngOnDestroy(): void {
    this.clearBannerTimer();
  }

  private parseObservation(value: unknown | null): {
    pts0: number[];
    pts1: number[];
    p0Bar: number;
    p1Bar: number;
    p0Off: number;
    p1Off: number;
    dice: number[];
    player: number | null;
  } | null {
    if (!value || typeof value !== 'object') {
      return null;
    }
    const statePlayer = value as { state?: unknown; player?: unknown };
    const record = (statePlayer.state ?? value) as Record<string, unknown>;
    const pts0 = this.parsePointList(record['pts0']);
    const pts1 = this.parsePointList(record['pts1']);
    if (!pts0 || !pts1) {
      return null;
    }
    const p0Bar = this.parseCounter(record['p0_bar']);
    const p1Bar = this.parseCounter(record['p1_bar']);
    const p0Off = this.parseCounter(record['p0_off']);
    const p1Off = this.parseCounter(record['p1_off']);
    const dice = this.parseDice(record['dice']);
    const player =
      typeof statePlayer.player === 'number'
        ? statePlayer.player
        : typeof record['turn'] === 'number'
          ? (record['turn'] as number)
          : typeof record['player'] === 'number'
            ? (record['player'] as number)
            : null;
    return {
      pts0,
      pts1,
      p0Bar,
      p1Bar,
      p0Off,
      p1Off,
      dice,
      player
    };
  }

  private parsePointList(value: unknown): number[] | null {
    let entries: unknown[] | null = null;
    if (Array.isArray(value) || ArrayBuffer.isView(value)) {
      entries = Array.from(value as Iterable<unknown>);
    } else if (value && typeof value === 'object') {
      const sorted = Object.entries(value as Record<string, unknown>)
        .map(([key, cell]) => ({ index: Number(key), cell }))
        .filter(({ index }) => Number.isInteger(index) && index >= 0)
        .sort((a, b) => a.index - b.index);
      if (sorted.length === 0) {
        return null;
      }
      entries = sorted.map((entry) => entry.cell);
    }
    if (!entries || entries.length < 24) {
      return null;
    }
    const parsed: number[] = [];
    for (const entry of entries.slice(0, 24)) {
      const num = Number(entry);
      if (!Number.isFinite(num)) {
        return null;
      }
      parsed.push(Math.max(0, Math.floor(num)));
    }
    return parsed;
  }

  private parseCounter(value: unknown): number {
    const num = Number(value);
    if (!Number.isFinite(num)) {
      return 0;
    }
    return Math.max(0, Math.floor(num));
  }

  private parseDice(value: unknown): number[] {
    if (!Array.isArray(value) && !ArrayBuffer.isView(value)) {
      return [];
    }
    return Array.from(value as Iterable<unknown>)
      .map((entry) => Number(entry))
      .filter((num) => Number.isFinite(num) && num > 0)
      .map((num) => Math.floor(num));
  }

  private rebuildMoveMaps(): void {
    this.moveEntries = [];
    this.fromKeys.clear();
    this.toKeysByFrom.clear();
    this.movesByFromTo.clear();
    const seenMoveSignatures = new Set<string>();
    this.movePointMode = this.resolveMovePointMode();
    for (let index = 0; index < this.currentLegalMoves.length; index += 1) {
      const raw = this.currentLegalMoves[index];
      const parsed = this.parseBackgammonMove(raw, `mv-${index}`, this.movePointMode);
      if (!parsed) {
        continue;
      }
      const signature = this.moveSignature(parsed.steps);
      if (seenMoveSignatures.has(signature)) {
        continue;
      }
      seenMoveSignatures.add(signature);
      this.moveEntries.push(parsed);
      if (!parsed.primaryFromKey || !parsed.primaryToKey) {
        continue;
      }
      this.fromKeys.add(parsed.primaryFromKey);
      const existingTargets = this.toKeysByFrom.get(parsed.primaryFromKey) ?? new Set<string>();
      existingTargets.add(parsed.primaryToKey);
      this.toKeysByFrom.set(parsed.primaryFromKey, existingTargets);
      const edgeKey = `${parsed.primaryFromKey}|${parsed.primaryToKey}`;
      const moves = this.movesByFromTo.get(edgeKey) ?? [];
      if (!moves.includes(parsed.raw)) {
        moves.push(parsed.raw);
      }
      this.movesByFromTo.set(edgeKey, moves);
    }
    if (this.selectedSourceKey && !this.fromKeys.has(this.selectedSourceKey)) {
      this.selectedSourceKey = null;
    }
  }

  private moveSignature(steps: BackgammonMoveStep[]): string {
    return steps.map((step) => `${step.from}/${step.to}`).join(' ');
  }

  private refreshBoard(): void {
    const canHighlight = this.awaitingHumanMove && this.showHumanControls;
    this.topPoints = this.topOrder.map((point) =>
      this.buildPointCell(point, 'top', canHighlight, this.selectedSourceKey, this.illegalKey)
    );
    this.bottomPoints = this.bottomOrder.map((point) =>
      this.buildPointCell(point, 'bottom', canHighlight, this.selectedSourceKey, this.illegalKey)
    );
    this.cdr.markForCheck();
  }

  private refreshBarTokens(): void {
    const visiblePerSide = 3;
    const whiteVisible = Math.min(visiblePerSide, this.whiteBar);
    const blackVisible = Math.min(visiblePerSide, this.blackBar);
    this.whiteBarTokens = Array.from({ length: whiteVisible }, (_, index) => index);
    this.blackBarTokens = Array.from({ length: blackVisible }, (_, index) => index);
    this.whiteBarOverflow = Math.max(0, this.whiteBar - whiteVisible);
    this.blackBarOverflow = Math.max(0, this.blackBar - blackVisible);
  }

  private buildPointCell(
    point: number,
    row: 'top' | 'bottom',
    canHighlight: boolean,
    selectedSourceKey: string | null,
    illegalKey: string | null
  ): BackgammonPointCell {
    const key = `p${point}`;
    // Backgammon observation layout:
    // - pts0[i] corresponds to absolute point (23 - i)
    // - pts1 may be absolute or mirrored depending on runtime; resolve per-state.
    const pts0Index = 23 - point;
    const pts1Index = this.pts1Mode === 'identity' ? point : 23 - point;
    const blackCount = this.ptsBlack[pts0Index] ?? 0;
    const whiteCount = this.ptsWhite[pts1Index] ?? 0;
    let owner: 'black' | 'white' | null = null;
    let count = 0;
    if (blackCount > 0 && whiteCount === 0) {
      owner = 'black';
      count = blackCount;
    } else if (whiteCount > 0 && blackCount === 0) {
      owner = 'white';
      count = whiteCount;
    } else if (blackCount > 0 && whiteCount > 0) {
      // This should be impossible in valid states; prefer the side to move for stable interactivity.
      if (this.activeColor === 'white') {
        owner = 'white';
        count = whiteCount;
      } else {
        owner = 'black';
        count = blackCount;
      }
    }
    const displayCount = Math.min(5, count);
    const overflow = Math.max(0, count - displayCount);
    const tokens = Array.from({ length: displayCount }, (_, tokenIndex) => tokenIndex);
    const legalTargets =
      selectedSourceKey && canHighlight
        ? this.toKeysByFrom.get(selectedSourceKey) ?? new Set<string>()
        : new Set<string>();
    const activeColor = this.activeColor;
    const activeCheckerCount =
      activeColor === 'black' ? blackCount : activeColor === 'white' ? whiteCount : 0;
    const hasActiveChecker = activeCheckerCount > 0;
    const legalFrom = canHighlight && hasActiveChecker && this.fromKeys.has(key);
    const legalTo = canHighlight && Boolean(selectedSourceKey && legalTargets.has(key));
    const selected = selectedSourceKey === key;
    const illegal = Boolean(illegalKey && illegalKey === key);
    const winning =
      this.matchWinner !== null &&
      ((this.matchWinner === 0 && owner === 'black') || (this.matchWinner === 1 && owner === 'white'));
    return {
      key,
      point,
      row,
      owner,
      count,
      tokens,
      overflow,
      legalFrom,
      legalTo,
      selected,
      illegal,
      winning
    };
  }

  private trySubmitFromTo(fromKey: string, toKey: string): void {
    const candidates = this.movesByFromTo.get(`${fromKey}|${toKey}`) ?? [];
    if (candidates.length === 1 && this.submitHumanMove) {
      const move = candidates[0];
      const parsed = this.moveEntries.find((entry) => entry.raw === move) ?? null;
      if (
        parsed &&
        parsed.steps.length > 1 &&
        parsed.steps[0] &&
        parsed.steps[1] &&
        parsed.steps[1].from === parsed.steps[0].to
      ) {
        this.showIllegalClick('That checker continues with die two. Pick the full move from the list.');
        return;
      }
      this.selectedSourceKey = null;
      this.refreshBoard();
      this.submitHumanMove(move);
      return;
    }
    if (candidates.length > 1) {
      this.showIllegalClick('Multiple continuations. Choose from the legal move list.');
      return;
    }
    this.showIllegalClick('Illegal move.');
  }

  private parseBackgammonMove(
    rawMove: string,
    id: string,
    movePointMode: 'ascending' | 'descending' = this.movePointMode
  ): ParsedBackgammonMove | null {
    const raw = String(rawMove ?? '').trim();
    if (!raw) {
      return null;
    }
    const dashIndex = raw.indexOf(' - ');
    let canonical = dashIndex >= 0 ? raw.slice(dashIndex + 3).trim() : raw;
    canonical = canonical.toUpperCase();
    if (canonical.endsWith('(2)')) {
      const base = canonical.slice(0, -3);
      canonical = `${base} ${base}`;
    }
    if (canonical === 'PASS') {
      return {
        id,
        raw,
        label: 'PASS',
        steps: [],
        primaryFromKey: null,
        primaryToKey: null
      };
    }
    if (canonical !== 'PASS' && canonical.split('/').length - 1 === 2 && !canonical.includes(' ')) {
      const [first, second, third] = canonical.split('/');
      if (first && second && third) {
        canonical = `${first}/${second} ${second}/${third}`;
      }
    }

    const pairs = canonical.split(/\s+/).filter((entry) => entry.length > 0);
    const steps: BackgammonMoveStep[] = [];
    for (const pair of pairs) {
      if (pair === 'PASS') {
        continue;
      }
      const segments = pair.split('/');
      if (segments.length !== 2) {
        continue;
      }
      const fromToken = segments[0];
      const toTokenRaw = segments[1];
      const hit = /\*+$/.test(toTokenRaw);
      const toToken = toTokenRaw.replace(/\*+$/g, '');
      const from = this.normalizeToken(fromToken, movePointMode);
      const to = this.normalizeToken(toToken, movePointMode);
      if (!from || !to) {
        continue;
      }
      steps.push({ from, to, hit });
    }
    if (steps.length === 0) {
      return null;
    }
    const primary = steps[0];
    const primaryFromKey = this.moveTokenToKey(primary.from);
    const primaryToKey = this.moveTokenToKey(primary.to);
    const label = steps
      .map((step) => `${this.displayToken(step.from)}/${this.displayToken(step.to)}${step.hit ? '*' : ''}`)
      .join(' ');
    return {
      id,
      raw,
      label,
      steps,
      primaryFromKey,
      primaryToKey
    };
  }

  private normalizeToken(value: string, movePointMode: 'ascending' | 'descending'): string {
    const cleaned = value.replace(/[^a-zA-Z0-9]/g, '').toLowerCase();
    if (!cleaned) {
      return '';
    }
    if (cleaned === 'bar') {
      return 'Bar';
    }
    if (cleaned === 'off') {
      return 'Off';
    }
    if (/^a?\d+$/.test(cleaned)) {
      const point = this.parseAbsoluteIndex(cleaned, movePointMode);
      return point === null ? '' : `A${point}`;
    }
    return cleaned;
  }

  private moveTokenToKey(token: string): string | null {
    if (!token) {
      return null;
    }
    if (token === 'Bar') {
      return 'bar';
    }
    if (token === 'Off') {
      return 'off';
    }
    const point = this.parseAbsoluteIndex(token, this.movePointMode);
    if (point === null) {
      return null;
    }
    return `p${point}`;
  }

  private displayToken(token: string): string {
    if (token === 'Bar' || token === 'Off') {
      return token;
    }
    const point = this.parseAbsoluteIndex(token, this.movePointMode);
    return point === null ? token : String(point);
  }

  private parseAbsoluteIndex(
    token: string,
    movePointMode: 'ascending' | 'descending'
  ): number | null {
    const raw = String(token ?? '').trim();
    if (!raw) {
      return null;
    }
    const absMatch = raw.match(/^A(\d{1,2})$/i);
    if (absMatch) {
      const point = Number(absMatch[1]);
      if (Number.isInteger(point) && point >= 0 && point <= 23) {
        return point;
      }
      return null;
    }
    const point = Number(raw);
    if (!Number.isInteger(point)) {
      return null;
    }
    // OpenSpiel move strings use 1..24 point notation; map to absolute 0..23.
    if (point >= 1 && point <= 24) {
      return movePointMode === 'ascending' ? point - 1 : 24 - point;
    }
    if (point === 0) {
      return 0;
    }
    return null;
  }

  private resolveMovePointMode(): 'ascending' | 'descending' {
    const candidates: Array<'ascending' | 'descending'> = ['descending', 'ascending'];
    let bestMode: 'ascending' | 'descending' = this.movePointMode;
    let bestScore = Number.NEGATIVE_INFINITY;
    for (const mode of candidates) {
      let score = 0;
      for (let index = 0; index < this.currentLegalMoves.length; index += 1) {
        const parsed = this.parseBackgammonMove(this.currentLegalMoves[index], `probe-${index}`, mode);
        if (!parsed?.primaryFromKey) {
          continue;
        }
        if (parsed.primaryFromKey === 'bar' || parsed.primaryFromKey === 'off') {
          score += 1;
          continue;
        }
        const point = Number(parsed.primaryFromKey.slice(1));
        if (!Number.isInteger(point) || point < 0 || point > 23) {
          continue;
        }
        if (this.activeColor === 'black' && (this.ptsBlack[23 - point] ?? 0) > 0) {
          score += 1;
          continue;
        }
        if (this.activeColor === 'white' && this.getWhiteCountAtPoint(point, this.pts1Mode) > 0) {
          score += 1;
        }
      }
      if (score > bestScore || (score === bestScore && mode === this.movePointMode)) {
        bestScore = score;
        bestMode = mode;
      }
    }
    return bestMode;
  }

  private getWhiteCountAtPoint(point: number, mode: 'identity' | 'reversed'): number {
    const index = mode === 'identity' ? point : 23 - point;
    return this.ptsWhite[index] ?? 0;
  }

  private resolvePts1Mode(pts0: number[], pts1: number[]): 'identity' | 'reversed' {
    const overlapIdentity = this.measureOverlap(pts0, pts1, 'identity');
    const overlapReversed = this.measureOverlap(pts0, pts1, 'reversed');
    if (overlapReversed < overlapIdentity) {
      return 'reversed';
    }
    if (overlapIdentity < overlapReversed) {
      return 'identity';
    }
    // No evidence either way (e.g. terminal state with one side fully borne off): keep the current mode.
    return this.pts1Mode;
  }

  private measureOverlap(
    pts0: number[],
    pts1: number[],
    mode: 'identity' | 'reversed'
  ): number {
    let overlap = 0;
    for (let point = 0; point < 24; point += 1) {
      const blackCount = pts0[23 - point] ?? 0;
      const whiteIndex = mode === 'identity' ? point : 23 - point;
      const whiteCount = pts1[whiteIndex] ?? 0;
      if (blackCount > 0 && whiteCount > 0) {
        overlap += Math.min(blackCount, whiteCount);
      }
    }
    return overlap;
  }

  private resolveResultMessage(winner: number | null): string {
    if (winner === 0) {
      return `${this.botA} won`;
    }
    if (winner === 1) {
      return `${this.botB} won`;
    }
    return 'Draw';
  }

  private resetBannerTimer(): void {
    this.clearBannerTimer();
    this.bannerTimer = window.setTimeout(() => {
      this.matchBannerMessage = null;
      this.cdr.markForCheck();
    }, 3000);
  }

  private clearBanner(): void {
    this.clearBannerTimer();
    this.matchBannerMessage = null;
  }

  private clearBannerTimer(): void {
    if (this.bannerTimer !== null) {
      window.clearTimeout(this.bannerTimer);
      this.bannerTimer = null;
    }
  }

  private showIllegalClick(message: string): void {
    this.illegalClickMessage = message;
    this.illegalClickToken += 1;
    this.cdr.markForCheck();
  }
}
