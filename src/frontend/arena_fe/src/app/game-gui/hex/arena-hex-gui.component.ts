import {
  AfterViewInit,
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  ElementRef,
  Input,
  OnDestroy,
  ViewChild
} from '@angular/core';
import { ArenaBannerComponent } from '../../components/arena-gui-helpers/arena-banner.component';
import { ArenaGuiAlertComponent } from '../../components/arena-gui-helpers/arena-gui-alert.component';
import { ArenaGuiEmptyComponent } from '../../components/arena-gui-helpers/arena-gui-empty.component';
import { ArenaGuiLegendComponent } from '../../components/arena-gui-helpers/arena-gui-legend.component';
import type { MatchResultSummary, StatusTone } from '@main/arena.constants';
import { kbdFile, kbdRankLetter } from '../../components/arena-gui-helpers/arena-kbd-keys';

type HexPoint = [number, number];

type HexCell = {
  key: string;
  row: number;
  col: number;
  owner: 'black' | 'white' | null;
  legal: boolean;
  illegal: boolean;
};

type HexRow = {
  key: string;
  rowIndex: number;
  cells: HexCell[];
};

@Component({
  selector: 'arena-hex-gui',
  standalone: true,
  templateUrl: './arena-hex-gui.component.html',
  styleUrl: './arena-hex-gui.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    ArenaBannerComponent,
    ArenaGuiAlertComponent,
    ArenaGuiEmptyComponent,
    ArenaGuiLegendComponent
  ]
})
export class ArenaHexGuiComponent implements AfterViewInit, OnDestroy {
  boardSize = 0;
  /** column picked by keyboard, whose cells then get row hints */
  kbdColumn: number | null = null;
  rows: HexRow[] = [];
  blackCount = 0;
  whiteCount = 0;
  cellSize = 34;
  currentPlayer: number | null = null;
  matchBannerMessage: string | null = null;
  @Input() botA = 'Automaton A';
  @Input() botB = 'Automaton B';
  @Input() statusTone: StatusTone = 'idle';
  @Input() statusMessage = '';
  @Input() showHumanControls = false;
  @Input() awaitingHumanMove = false;
  @Input() submitHumanMove?: (move: string) => void;
  illegalClickMessage: string | null = null;
  illegalClickToken = 0;
  showScrollLeft = false;
  showScrollRight = false;

  private blackPoints: HexPoint[] = [];
  private whitePoints: HexPoint[] = [];
  private illegalMove: HexPoint | null = null;
  private bannerTimer: number | null = null;
  private lastMatchStamp: number | null = null;
  private currentLegalMoves: string[] = [];
  private legalMovesByPoint = new Map<string, string>();
  private scrollHintFrame: number | null = null;
  private readonly handleWindowResize = () => this.scheduleScrollHintUpdate();

  @ViewChild('boardScroller') private boardScrollerRef?: ElementRef<HTMLDivElement>;

  constructor(private readonly cdr: ChangeDetectorRef) {}

  get activePlayerLabel(): string {
    if (this.currentPlayer === 0) {
      return this.botA;
    }
    if (this.currentPlayer === 1) {
      return this.botB;
    }
    return '';
  }

  @Input() set legalMoves(value: string[] | null) {
    this.currentLegalMoves = Array.isArray(value) ? value : [];
    this.legalMovesByPoint.clear();
    for (const move of this.currentLegalMoves) {
      const point = this.parseMovePoint(move);
      if (!point) {
        continue;
      }
      const key = `${point[0]},${point[1]}`;
      if (!this.legalMovesByPoint.has(key)) {
        this.legalMovesByPoint.set(key, move);
      }
    }
    this.kbdColumn = null;
    this.refreshRows();
  }

  get legalMoves(): string[] {
    return this.currentLegalMoves;
  }

  @Input() set illegalAction(value: string | null) {
    this.illegalMove = this.parseIllegalAction(value);
    this.refreshRows();
  }

  @Input() set matchResult(value: MatchResultSummary | null) {
    if (!value) {
      this.lastMatchStamp = null;
      this.clearBanner();
      return;
    }
    if (this.lastMatchStamp === value.finishedAt) {
      return;
    }
    this.lastMatchStamp = value.finishedAt;
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
      this.rows = [];
      this.blackCount = 0;
      this.whiteCount = 0;
      this.currentPlayer = null;
      this.blackPoints = [];
      this.whitePoints = [];
      this.setScrollHints(false, false);
      return;
    }
    if (parsed.black && parsed.white) {
      this.blackPoints = parsed.black;
      this.whitePoints = parsed.white;
    } else {
      const isMeBlack =
        parsed.color ? parsed.color === 'b' : parsed.player !== 1;
      this.blackPoints = isMeBlack ? parsed.me : parsed.opponent;
      this.whitePoints = isMeBlack ? parsed.opponent : parsed.me;
    }
    this.blackCount = this.blackPoints.length;
    this.whiteCount = this.whitePoints.length;
    this.currentPlayer = parsed.player;
    this.boardSize = this.resolveBoardSize(parsed.boardSize, [
      ...this.blackPoints,
      ...this.whitePoints
    ]);
    this.cellSize = this.resolveCellSize(this.boardSize);
    this.refreshRows();
  }

  /** Square name for a legal cell, a1 is the bottom-left cell as drawn. */
  /** keyboard hint on a cell: its row letter (a at the bottom), on the picked column only */
  kbdLabel(cell: HexCell): string | null {
    const target = this.awaitingHumanMove && cell.legal && cell.col === this.kbdColumn;
    return target ? kbdRankLetter(this.boardSize - 1 - cell.row) : null;
  }

  /** keyboard hint on a column's top cell: its letter while no column is picked, if it has a legal cell */
  kbdColumnLabel(col: number): string | null {
    const open = this.rows.some((row) => row.cells[col]?.legal);
    return this.awaitingHumanMove && this.kbdColumn === null && open ? kbdFile(col) : null;
  }

  /** picking the picked column again goes back to the column pick */
  onKbdColumn(col: number): void {
    this.kbdColumn = this.kbdColumn === col ? null : col;
    this.cdr.markForCheck();
  }

  cellLabel(cell: HexCell): string {
    return `${String.fromCharCode(97 + cell.col)}${cell.row + 1}: ${cell.owner ?? 'empty'}`;
  }

  onCellClick(cell: HexCell): void {
    if (!this.awaitingHumanMove || !this.submitHumanMove) {
      return;
    }
    const key = `${cell.row},${cell.col}`;
    const move = this.legalMovesByPoint.get(key);
    if (!move) {
      this.showIllegalClick('Illegal move.');
      return;
    }
    this.submitHumanMove(move);
  }

  /** Edge strips: scroll the board by most of its visible width. */
  scrollBoard(container: HTMLDivElement, direction: -1 | 1): void {
    container.scrollBy({ left: direction * container.clientWidth * 0.65, behavior: 'smooth' });
  }

  onBoardScroll(container: HTMLDivElement): void {
    this.updateScrollHints(container);
  }

  ngAfterViewInit(): void {
    window.addEventListener('resize', this.handleWindowResize);
    this.scheduleScrollHintUpdate();
  }


  ngOnDestroy(): void {
    window.removeEventListener('resize', this.handleWindowResize);
    this.clearScrollHintFrame();
    this.clearBannerTimer();
  }

  private parseObservation(value: unknown | null): {
    me: HexPoint[];
    opponent: HexPoint[];
    black: HexPoint[] | null;
    white: HexPoint[] | null;
    player: number | null;
    color: 'b' | 'w' | null;
    boardSize: number | null;
  } | null {
    if (!value || typeof value !== 'object') {
      return null;
    }
    const statePlayer = value as { state?: unknown; player?: unknown };
    const record = (statePlayer.state ?? value) as {
      me?: unknown;
      opp?: unknown;
      opponent?: unknown;
      black?: unknown;
      white?: unknown;
      color?: unknown;
      turn?: unknown;
      board_size?: unknown;
      boardSize?: unknown;
    };
    const player =
      typeof record.turn === 'number'
        ? record.turn
        : (statePlayer.player as number | null);
    const color = record.color === 'b' || record.color === 'w' ? record.color : null;
    const black = this.parsePoints(record.black);
    const white = this.parsePoints(record.white);
    const boardSize = this.parseBoardSize(record.board_size ?? record.boardSize);
    if (black && white) {
      return { black, white, me: [], opponent: [], player, color, boardSize };
    }
    const me = this.parsePoints(record.me);
    const opponent = this.parsePoints(record.opp ?? record.opponent);
    if (!me || !opponent) {
      return null;
    }
    return { me, opponent, black: null, white: null, player, color, boardSize };
  }

  private parsePoints(value: unknown): HexPoint[] | null {
    if (!Array.isArray(value)) {
      return null;
    }
    const points: HexPoint[] = [];
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

  private parseBoardSize(value: unknown): number | null {
    if (typeof value === 'number' && Number.isFinite(value)) {
      return value;
    }
    if (Array.isArray(value) && value.length > 0) {
      const first = Number(value[0]);
      if (Number.isFinite(first)) {
        return first;
      }
    }
    return null;
  }

  private resolveBoardSize(boardSize: number | null, points: HexPoint[]): number {
    let maxCoord = -1;
    for (const [row, col] of points) {
      maxCoord = Math.max(maxCoord, row, col);
    }
    if (this.currentLegalMoves.length > 0) {
      for (const move of this.currentLegalMoves) {
        const point = this.parseMovePoint(move);
        if (!point) {
          continue;
        }
        maxCoord = Math.max(maxCoord, point[0], point[1]);
      }
    }
    const inferred = maxCoord >= 0 ? maxCoord + 1 : 0;
    if (boardSize && boardSize > 0) {
      return Math.max(boardSize, inferred);
    }
    return inferred;
  }

  private resolveCellSize(boardSize: number): number {
    if (boardSize <= 0) {
      return 34;
    }
    return Math.max(18, Math.min(42, Math.floor(420 / boardSize)));
  }

  private buildRows(
    blackPoints: HexPoint[],
    whitePoints: HexPoint[],
    size: number,
    legalKeys: Set<string>,
    illegalMove: HexPoint | null
  ): HexRow[] {
    if (size <= 0) {
      return [];
    }
    const blackSet = new Set(blackPoints.map(([row, col]) => `${row},${col}`));
    const whiteSet = new Set(whitePoints.map(([row, col]) => `${row},${col}`));
    const illegalKey = illegalMove ? `${illegalMove[0]},${illegalMove[1]}` : null;
    const rows: HexRow[] = [];
    for (let row = 0; row < size; row += 1) {
      const cells: HexCell[] = [];
      for (let col = 0; col < size; col += 1) {
        const key = `${row},${col}`;
        let owner: HexCell['owner'] = null;
        if (blackSet.has(key)) {
          owner = 'black';
        } else if (whiteSet.has(key)) {
          owner = 'white';
        }
        const legal = legalKeys.has(key);
        const illegal = Boolean(illegalKey && illegalKey === key);
        cells.push({ key, row, col, owner, legal, illegal });
      }
      rows.push({ key: `row-${row}`, rowIndex: row, cells });
    }
    return rows;
  }

  private refreshRows(): void {
    const allowLegal = this.awaitingHumanMove;
    const legalKeys = allowLegal ? new Set(this.legalMovesByPoint.keys()) : new Set<string>();
    this.rows = this.buildRows(
      this.blackPoints,
      this.whitePoints,
      this.boardSize,
      legalKeys,
      this.illegalMove
    );
    this.cdr.markForCheck();
    this.scheduleScrollHintUpdate();
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

  private parseIllegalAction(value: string | null): HexPoint | null {
    return value ? this.parseMovePoint(value) : null;
  }

  private parseMovePoint(value: string): HexPoint | null {
    const trimmed = String(value ?? '').trim();
    if (!trimmed) {
      return null;
    }
    const numbers = trimmed.match(/-?\d+/g);
    if (numbers && numbers.length >= 2) {
      const row = Number(numbers[0]);
      const col = Number(numbers[1]);
      if (Number.isFinite(row) && Number.isFinite(col)) {
        return [row, col];
      }
    }
    const alphaMatch = trimmed.match(/([A-Za-z])\s*([0-9]+)/);
    if (alphaMatch) {
      const col = alphaMatch[1].toLowerCase().charCodeAt(0) - 97;
      const row = Number(alphaMatch[2]) - 1;
      if (Number.isFinite(row) && Number.isFinite(col)) {
        return [row, col];
      }
    }
    return null;
  }

  private scheduleScrollHintUpdate(): void {
    this.clearScrollHintFrame();
    this.scrollHintFrame = window.requestAnimationFrame(() => {
      this.scrollHintFrame = null;
      this.updateScrollHints();
    });
  }

  private clearScrollHintFrame(): void {
    if (this.scrollHintFrame !== null) {
      window.cancelAnimationFrame(this.scrollHintFrame);
      this.scrollHintFrame = null;
    }
  }

  private updateScrollHints(container?: HTMLDivElement | null): void {
    const target = container ?? this.boardScrollerRef?.nativeElement ?? null;
    if (!target) {
      this.setScrollHints(false, false);
      return;
    }
    const maxScrollLeft = target.scrollWidth - target.clientWidth;
    if (maxScrollLeft <= 1) {
      this.setScrollHints(false, false);
      return;
    }
    const nextShowLeft = target.scrollLeft > 1;
    const nextShowRight = target.scrollLeft < maxScrollLeft - 1;
    this.setScrollHints(nextShowLeft, nextShowRight);
  }

  private setScrollHints(showLeft: boolean, showRight: boolean): void {
    if (this.showScrollLeft === showLeft && this.showScrollRight === showRight) {
      return;
    }
    this.showScrollLeft = showLeft;
    this.showScrollRight = showRight;
    this.cdr.markForCheck();
  }
}
