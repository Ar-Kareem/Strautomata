import { ChangeDetectionStrategy, ChangeDetectorRef, Component, Input, OnDestroy } from '@angular/core';
import { ArenaBannerComponent } from '../../components/arena-gui-helpers/arena-banner.component';
import { ArenaGuiAlertComponent } from '../../components/arena-gui-helpers/arena-gui-alert.component';
import { ArenaGuiEmptyComponent } from '../../components/arena-gui-helpers/arena-gui-empty.component';
import { ArenaGuiLegendComponent } from '../../components/arena-gui-helpers/arena-gui-legend.component';
import { HumanMovePanelComponent } from '@arena/human-move-panel.component';
import type { MatchResultSummary, StatusTone } from '@main/arena.constants';

type BreakthroughPoint = [number, number];

type BreakthroughCell = {
  key: string;
  row: number;
  col: number;
  coordKey: string;
  owner: 'black' | 'white' | null;
  legalFrom: boolean;
  legalTo: boolean;
  illegal: boolean;
  winning: boolean;
};

@Component({
  selector: 'arena-breakthrough-gui',
  standalone: true,
  templateUrl: './arena-breakthrough-gui.component.html',
  styleUrl: './arena-breakthrough-gui.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    HumanMovePanelComponent,
    ArenaBannerComponent,
    ArenaGuiAlertComponent,
    ArenaGuiEmptyComponent,
    ArenaGuiLegendComponent
  ]
})
export class ArenaBreakthroughGuiComponent implements OnDestroy {
  boardSize = 0;
  cells: BreakthroughCell[] = [];
  blackCount = 0;
  whiteCount = 0;
  currentPlayer: number | null = null;
  matchBannerMessage: string | null = null;
  @Input() botA = 'Automaton A';
  @Input() botB = 'Automaton B';
  @Input() statusTone: StatusTone = 'idle';
  @Input() statusMessage = '';
  @Input() showHumanControls = false;
  private awaitingHuman = false;
  @Input() set awaitingHumanMove(value: boolean) {
    this.awaitingHuman = value;
    if (!value) {
      this.selectedFromKey = null;
    }
    this.refreshCells();
  }
  get awaitingHumanMove(): boolean {
    return this.awaitingHuman;
  }
  get activePlayerLabel(): string {
    if (this.currentPlayer === 0) {
      return this.botA;
    }
    if (this.currentPlayer === 1) {
      return this.botB;
    }
    return '';
  }
  get displaybotB(): string {
    return this.botB;
  }
  get displaybotA(): string {
    return this.botA;
  }
  @Input() submitHumanMove?: (move: string) => void;
  private blackPoints: BreakthroughPoint[] = [];
  private whitePoints: BreakthroughPoint[] = [];
  private illegalMove: BreakthroughPoint | null = null;
  private bannerTimer: number | null = null;
  private lastMatchStamp: number | null = null;
  private matchWinner: number | null = null;
  private matchIllegal = false;
  private currentLegalMoves: string[] = [];
  private movesByKey = new Map<string, string>();
  private legalToByFrom = new Map<string, Set<string>>();
  private suppressLegalHighlights = false;
  private fromKeys = new Set<string>();
  illegalClickMessage: string | null = null;
  illegalClickToken = 0;
  selectedFromKey: string | null = null;
  hasWinningLine = false;
  private winningCells = new Set<string>();

  @Input() set legalMoves(value: string[] | null) {
    this.currentLegalMoves = Array.isArray(value) ? value : [];
    this.movesByKey.clear();
    this.fromKeys.clear();
    this.legalToByFrom.clear();
    this.selectedFromKey = null;
    if (this.awaitingHumanMove) {
      this.suppressLegalHighlights = false;
    }
    for (const move of this.currentLegalMoves) {
      const parsed = this.parseMoveKeys(move);
      if (!parsed) {
        continue;
      }
      const key = `${parsed.from}|${parsed.to}`;
      if (!this.movesByKey.has(key)) {
        this.movesByKey.set(key, move);
      }
      this.fromKeys.add(parsed.from);
      let toKeys = this.legalToByFrom.get(parsed.from);
      if (!toKeys) {
        toKeys = new Set<string>();
        this.legalToByFrom.set(parsed.from, toKeys);
      }
      toKeys.add(parsed.to);
    }
    this.refreshCells();
  }

  get legalMoves(): string[] {
    return this.currentLegalMoves;
  }

  constructor(private readonly cdr: ChangeDetectorRef) {
    (window as any).GUI_COMPONENT = this;
  }

  @Input() set illegalAction(value: string | null) {
    this.illegalMove = this.parseIllegalAction(value);
    this.refreshCells();
  }

  @Input() set matchResult(value: MatchResultSummary | null) {
    if (!value) {
      this.lastMatchStamp = null;
      this.matchWinner = null;
      this.matchIllegal = false;
      this.winningCells = new Set<string>();
      this.hasWinningLine = false;
      this.refreshCells();
      this.clearBanner();
      return;
    }
    if (this.lastMatchStamp === value.finishedAt) {
      return;
    }
    this.lastMatchStamp = value.finishedAt;
    this.matchIllegal = value.illegal;
    this.matchWinner = value.illegal ? null : value.winner;
    this.updateWinningCells();
    if (value.illegal) {
      this.clearBanner();
      return;
    }
    this.matchBannerMessage = this.resolveResultMessage(value.winner);
    this.resetBannerTimer();
  }

  @Input() set observation(value: unknown | null) {
    const parsed = this.parseObservation(value);
    if (!parsed) {
      this.boardSize = 0;
      this.cells = [];
      this.blackCount = 0;
      this.whiteCount = 0;
      this.currentPlayer = null;
      this.blackPoints = [];
      this.whitePoints = [];
      this.winningCells = new Set<string>();
      this.hasWinningLine = false;
      return;
    }
    if (parsed.black && parsed.white) {
      this.blackPoints = parsed.black;
      this.whitePoints = parsed.white;
    } else {
      const isMeBlack = parsed.color ? parsed.color === 'b' : parsed.player !== 1;
      this.blackPoints = isMeBlack ? parsed.me : parsed.opponent;
      this.whitePoints = isMeBlack ? parsed.opponent : parsed.me;
    }
    this.blackCount = this.blackPoints.length;
    this.whiteCount = this.whitePoints.length;
    this.currentPlayer = parsed.player;
    this.boardSize = this.resolveBoardSize([...this.blackPoints, ...this.whitePoints]);
    this.updateWinningCells();
  }

  onCellClick(cell: BreakthroughCell): void {
    if (!this.awaitingHumanMove || !this.submitHumanMove) {
      return;
    }
    const key = cell.coordKey;
    if (!this.selectedFromKey) {
      if (!this.fromKeys.has(key)) {
        this.showIllegalClick('Select a movable piece.');
        return;
      }
      this.selectedFromKey = key;
      this.refreshCells();
      return;
    }
    if (this.selectedFromKey === key) {
      this.selectedFromKey = null;
      this.refreshCells();
      return;
    }
    if (this.fromKeys.has(key)) {
      this.selectedFromKey = key;
      this.refreshCells();
      return;
    }
    const fromKey = this.selectedFromKey;
    this.selectedFromKey = null;
    this.refreshCells();
    const move = this.movesByKey.get(`${fromKey}|${key}`);
    if (!move) {
      this.showIllegalClick('Illegal move.');
      return;
    }
    this.suppressLegalHighlights = true;
    this.refreshCells();
    this.submitHumanMove(move);
  }

  private parseObservation(value: unknown | null): {
    me: BreakthroughPoint[];
    opponent: BreakthroughPoint[];
    black: BreakthroughPoint[] | null;
    white: BreakthroughPoint[] | null;
    player: number | null;
    color: 'b' | 'w' | null;
  } | null {
    if (!value || typeof value !== 'object') {
      return null;
    }
    const statePlayer = value as { state?: unknown; player?: unknown };
    const record = (statePlayer.state ?? value) as {
      me?: unknown;
      opp?: unknown;
      black?: unknown;
      white?: unknown;
      color?: unknown;
      turn?: unknown;
    };
    const player =
      typeof record.turn === 'number' && record.turn >= 0
        ? record.turn
        : (statePlayer.player as number | null);
    const color = record.color === 'b' || record.color === 'w' ? record.color : null;
    const black = this.parsePoints(record.black);
    const white = this.parsePoints(record.white);
    if (black && white) {
      return { black, white, me: [], opponent: [], player, color };
    }
    const me = this.parsePoints(record.me);
    const opponent = this.parsePoints(record.opp);
    if (!me || !opponent) {
      return null;
    }
    return { me, opponent, black: null, white: null, player, color };
  }

  private parsePoints(value: unknown): BreakthroughPoint[] | null {
    if (!Array.isArray(value)) {
      return null;
    }
    const points: BreakthroughPoint[] = [];
    for (const entry of value) {
      if (!Array.isArray(entry) || entry.length < 2) {
        continue;
      }
      const row = Number(entry[0]);
      const col = Number(entry[1]);
      if (!Number.isFinite(row) || !Number.isFinite(col)) {
        continue;
      }
      points.push([row, col]);
    }
    return points;
  }

  private resolveBoardSize(points: BreakthroughPoint[]): number {
    let maxCoord = 0;
    for (const [row, col] of points) {
      maxCoord = Math.max(maxCoord, row, col);
    }
    return Math.max(8, maxCoord + 1);
  }

  private buildCells(
    blackPoints: BreakthroughPoint[],
    whitePoints: BreakthroughPoint[],
    size: number,
    legalFromKeys: Set<string>,
    legalToKeys: Set<string>,
    illegalMove: BreakthroughPoint | null
  ): BreakthroughCell[] {
    if (size <= 0) {
      return [];
    }
    const blackSet = new Set(blackPoints.map(([row, col]) => `${row},${col}`));
    const whiteSet = new Set(whitePoints.map(([row, col]) => `${row},${col}`));
    const illegalKey = illegalMove ? `${illegalMove[0]},${illegalMove[1]}` : null;
    const cells: BreakthroughCell[] = [];
    for (let row = size - 1; row >= 0; row -= 1) {
      for (let col = 0; col < size; col += 1) {
        const key = `${row},${col}`;
        const coordKey = this.coordToKey(row, col);
        let owner: BreakthroughCell['owner'] = null;
        if (blackSet.has(key)) {
          owner = 'black';
        } else if (whiteSet.has(key)) {
          owner = 'white';
        }
        const illegal = Boolean(illegalKey && illegalKey === key);
        cells.push({
          key,
          row,
          col,
          coordKey,
          owner,
          legalFrom: legalFromKeys.has(coordKey),
          legalTo: legalToKeys.has(coordKey),
          illegal,
          winning: this.winningCells.has(key)
        });
      }
    }
    return cells;
  }

  ngOnDestroy(): void {
    this.clearBannerTimer();
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

  private parseIllegalAction(value: string | null): BreakthroughPoint | null {
    if (!value) {
      return null;
    }
    const trimmed = String(value).trim();
    if (!trimmed) {
      return null;
    }
    const match = trimmed.match(/^([a-h])([1-8])([a-h])([1-8])\*?$/i);
    if (!match) {
      return null;
    }
    const toCol = match[3].toLowerCase().charCodeAt(0) - 97;
    const toRow = Number(match[4]) - 1;
    if (!Number.isFinite(toRow) || !Number.isFinite(toCol)) {
      return null;
    }
    return [toRow, toCol];
  }

  private parseMoveKeys(value: string): { from: string; to: string } | null {
    const trimmed = String(value ?? '').trim();
    if (!trimmed) {
      return null;
    }
    const match = trimmed.match(/^([a-h])([1-8])([a-h])([1-8])\*?$/i);
    if (!match) {
      return null;
    }
    return { from: `${match[1].toLowerCase()}${match[2]}`, to: `${match[3].toLowerCase()}${match[4]}` };
  }

  private coordToKey(row: number, col: number): string {
    const file = String.fromCharCode(97 + col);
    return `${file}${row + 1}`;
  }

  private refreshCells(): void {
    const allowLegal = this.awaitingHumanMove && !this.suppressLegalHighlights;
    const legalFromKeys = allowLegal ? this.fromKeys : new Set<string>();
    const legalToKeys =
      allowLegal && this.selectedFromKey
        ? this.legalToByFrom.get(this.selectedFromKey) ?? new Set<string>()
        : new Set<string>();
    this.cells = this.buildCells(
      this.blackPoints,
      this.whitePoints,
      this.boardSize,
      legalFromKeys,
      legalToKeys,
      this.illegalMove
    );
    this.cdr.markForCheck();
  }

  private updateWinningCells(): void {
    this.winningCells = this.findWinningCells();
    this.hasWinningLine = this.winningCells.size > 0;
    this.refreshCells();
  }

  private findWinningCells(): Set<string> {
    if (this.matchWinner === null || this.matchIllegal || this.boardSize <= 0) {
      return new Set<string>();
    }
    if (this.matchWinner === 0) {
      return new Set(
        this.blackPoints.filter(([row]) => row === 0).map(([row, col]) => `${row},${col}`)
      );
    }
    if (this.matchWinner === 1) {
      const lastRow = this.boardSize - 1;
      return new Set(
        this.whitePoints.filter(([row]) => row === lastRow).map(([row, col]) => `${row},${col}`)
      );
    }
    return new Set<string>();
  }
}
