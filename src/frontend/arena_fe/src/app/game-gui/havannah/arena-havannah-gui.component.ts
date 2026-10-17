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
import type { MatchResultSummary, StatusTone } from '@main/arena.constants';
import { ArenaBannerComponent } from '../../components/arena-gui-helpers/arena-banner.component';
import { ArenaGuiAlertComponent } from '../../components/arena-gui-helpers/arena-gui-alert.component';
import { ArenaGuiEmptyComponent } from '../../components/arena-gui-helpers/arena-gui-empty.component';
import { ArenaGuiLegendComponent } from '../../components/arena-gui-helpers/arena-gui-legend.component';

type HavannahPoint = [number, number];

type HavannahCell = {
  key: string;
  row: number;
  col: number;
  playable: boolean;
  token: string;
  notation: string;
  owner: 'black' | 'white' | null;
  legal: boolean;
  illegal: boolean;
  winning: boolean;
};

type HavannahRow = {
  key: string;
  rowIndex: number;
  indent: number;
  cells: HavannahCell[];
};

@Component({
  selector: 'arena-havannah-gui',
  standalone: true,
  templateUrl: './arena-havannah-gui.component.html',
  styleUrl: './arena-havannah-gui.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    ArenaBannerComponent,
    ArenaGuiAlertComponent,
    ArenaGuiEmptyComponent,
    ArenaGuiLegendComponent
  ]
})
export class ArenaHavannahGuiComponent implements AfterViewInit, OnDestroy {
  boardSpan = 0;
  radius = 0;
  cellSize = 24;
  rows: HavannahRow[] = [];
  blackCount = 0;
  whiteCount = 0;
  currentPlayer: number | null = null;
  matchBannerMessage: string | null = null;
  illegalClickMessage: string | null = null;
  illegalClickToken = 0;
  hasWinner = false;
  showScrollLeft = false;
  showScrollRight = false;

  @Input() botA = 'Automaton A';
  @Input() botB = 'Automaton B';
  @Input() statusTone: StatusTone = 'idle';
  @Input() statusMessage = '';
  @Input() showHumanControls = false;
  @Input() awaitingHumanMove = false;
  @Input() submitHumanMove?: (move: string) => void;

  private blackPoints: HavannahPoint[] = [];
  private whitePoints: HavannahPoint[] = [];
  private validMask: boolean[][] | null = null;
  private currentLegalMoves: string[] = [];
  private legalMovesByKey = new Map<string, string>();
  private illegalKey: string | null = null;
  private bannerTimer: number | null = null;
  private lastMatchStamp: number | null = null;
  private matchWinner: number | null = null;
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
    this.rebuildLegalMoves();
    this.refreshBoard();
  }

  get legalMoves(): string[] {
    return this.currentLegalMoves;
  }

  @Input() set illegalAction(value: string | null) {
    const point = value ? this.parseMovePoint(value, this.boardSpan, this.radius) : null;
    this.illegalKey = point ? this.coordKey(point[0], point[1]) : null;
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
      this.boardSpan = 0;
      this.radius = 0;
      this.rows = [];
      this.blackPoints = [];
      this.whitePoints = [];
      this.validMask = null;
      this.blackCount = 0;
      this.whiteCount = 0;
      this.currentPlayer = null;
      this.setScrollHints(false, false);
      return;
    }
    this.blackPoints = parsed.black;
    this.whitePoints = parsed.white;
    this.blackCount = this.blackPoints.length;
    this.whiteCount = this.whitePoints.length;
    this.currentPlayer = parsed.player;
    this.boardSpan = parsed.boardSpan;
    this.radius = Math.floor((this.boardSpan - 1) / 2);
    this.validMask = parsed.validMask;
    this.cellSize = this.resolveCellSize(this.boardSpan);
    this.rebuildLegalMoves();
    this.refreshBoard();
  }

  onCellClick(cell: HavannahCell): void {
    if (!cell.playable) {
      return;
    }
    if (!this.awaitingHumanMove || !this.submitHumanMove) {
      return;
    }
    const move = this.legalMovesByKey.get(cell.key);
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
    black: HavannahPoint[];
    white: HavannahPoint[];
    player: number | null;
    boardSpan: number;
    validMask: boolean[][] | null;
  } | null {
    if (!value || typeof value !== 'object') {
      return null;
    }
    const statePlayer = value as { state?: unknown; player?: unknown };
    const record = (statePlayer.state ?? value) as Record<string, unknown>;
    const player =
      typeof statePlayer.player === 'number'
        ? statePlayer.player
        : typeof record['turn'] === 'number'
          ? (record['turn'] as number)
          : typeof record['player'] === 'number'
            ? (record['player'] as number)
            : null;
    const explicitSpan = this.parseBoardSpan(record['board_size'] ?? record['boardSize']);
    const blackDirect = this.parsePoints(record['black']);
    const whiteDirect = this.parsePoints(record['white']);
    let black = blackDirect;
    let white = whiteDirect;
    if (!black || !white) {
      const me = this.parsePoints(record['me']);
      const opponent = this.parsePoints(record['opp'] ?? record['opponent']);
      const color = record['color'];
      if (!me || !opponent) {
        return null;
      }
      const isMeBlack = color === 'w' ? false : true;
      black = isMeBlack ? me : opponent;
      white = isMeBlack ? opponent : me;
    }
    const validMask = this.parseValidMask(record['valid_mask'] ?? record['validMask']);
    const boardSpan = this.resolveBoardSpan(explicitSpan, [...black, ...white], validMask);
    return { black, white, player, boardSpan, validMask };
  }

  private parsePoints(value: unknown): HavannahPoint[] | null {
    if (!Array.isArray(value)) {
      return null;
    }
    const points: HavannahPoint[] = [];
    for (const entry of value) {
      if (!Array.isArray(entry) || entry.length < 2) {
        continue;
      }
      const row = Number(entry[0]);
      const col = Number(entry[1]);
      if (!Number.isFinite(row) || !Number.isFinite(col)) {
        continue;
      }
      points.push([Math.floor(row), Math.floor(col)]);
    }
    return points;
  }

  private parseBoardSpan(value: unknown): number | null {
    if (typeof value === 'number' && Number.isFinite(value) && value > 0) {
      return Math.floor(value);
    }
    if (Array.isArray(value) && value.length > 0) {
      const first = Number(value[0]);
      if (Number.isFinite(first) && first > 0) {
        return Math.floor(first);
      }
    }
    return null;
  }

  private parseValidMask(value: unknown): boolean[][] | null {
    if (!Array.isArray(value) || value.length === 0) {
      return null;
    }
    const parsed: boolean[][] = [];
    let width = 0;
    for (const row of value) {
      if (!Array.isArray(row)) {
        return null;
      }
      const parsedRow = row.map((entry) => Boolean(entry));
      width = Math.max(width, parsedRow.length);
      parsed.push(parsedRow);
    }
    if (width <= 0) {
      return null;
    }
    return parsed.map((row) => {
      if (row.length === width) {
        return row;
      }
      return [...row, ...new Array(width - row.length).fill(false)];
    });
  }

  private resolveBoardSpan(
    explicitSpan: number | null,
    points: HavannahPoint[],
    validMask: boolean[][] | null
  ): number {
    let maxCoord = -1;
    for (const [row, col] of points) {
      maxCoord = Math.max(maxCoord, row, col);
    }
    let inferred = maxCoord >= 0 ? maxCoord + 1 : 0;
    if (validMask && validMask.length > 0) {
      const maskWidth = validMask.reduce((acc, row) => Math.max(acc, row.length), 0);
      inferred = Math.max(inferred, validMask.length, maskWidth);
    }
    let span = Math.max(explicitSpan ?? 0, inferred, 15);
    if (span % 2 === 0) {
      span += 1;
    }
    return span;
  }

  private resolveCellSize(span: number): number {
    if (span <= 0) {
      return 30;
    }
    return Math.max(22, Math.min(42, Math.floor(560 / (span + 2))));
  }

  private rebuildLegalMoves(): void {
    this.legalMovesByKey.clear();
    for (const move of this.currentLegalMoves) {
      const point = this.parseMovePoint(move, this.boardSpan, this.radius);
      if (!point) {
        continue;
      }
      const key = this.coordKey(point[0], point[1]);
      if (!this.legalMovesByKey.has(key)) {
        this.legalMovesByKey.set(key, move);
      }
    }
  }

  private refreshBoard(): void {
    const legalKeys =
      this.awaitingHumanMove && this.showHumanControls
        ? new Set(this.legalMovesByKey.keys())
        : new Set<string>();
    this.rows = this.buildRows(
      this.blackPoints,
      this.whitePoints,
      this.boardSpan,
      this.radius,
      this.validMask,
      legalKeys,
      this.illegalKey
    );
    this.cdr.markForCheck();
    this.scheduleScrollHintUpdate();
  }

  private buildRows(
    blackPoints: HavannahPoint[],
    whitePoints: HavannahPoint[],
    span: number,
    radius: number,
    validMask: boolean[][] | null,
    legalKeys: Set<string>,
    illegalKey: string | null
  ): HavannahRow[] {
    if (span <= 0) {
      return [];
    }
    const blackSet = new Set(blackPoints.map(([row, col]) => this.coordKey(row, col)));
    const whiteSet = new Set(whitePoints.map(([row, col]) => this.coordKey(row, col)));
    const rows: HavannahRow[] = [];
    const half = Math.floor(span / 2);

    for (let row = 0; row < span; row += 1) {
      let firstPlayable = -1;
      let lastPlayable = -1;
      for (let col = 0; col < span; col += 1) {
        if (!this.isPlayableCell(row, col, span, radius, validMask)) {
          continue;
        }
        if (firstPlayable < 0) {
          firstPlayable = col;
        }
        lastPlayable = col;
      }
      if (firstPlayable < 0 || lastPlayable < 0) {
        continue;
      }

      const cells: HavannahCell[] = [];
      for (let col = firstPlayable; col <= lastPlayable; col += 1) {
        const playable = this.isPlayableCell(row, col, span, radius, validMask);
        if (!playable) {
          cells.push({
            key: `gap-${row}-${col}`,
            row,
            col,
            playable: false,
            token: ' ',
            notation: '',
            owner: null,
            legal: false,
            illegal: false,
            winning: false
          });
          continue;
        }

        const key = this.coordKey(row, col);
        let owner: HavannahCell['owner'] = null;
        if (blackSet.has(key)) {
          owner = 'black';
        } else if (whiteSet.has(key)) {
          owner = 'white';
        }
        const winning =
          this.matchWinner !== null &&
          ((this.matchWinner === 0 && owner === 'black') ||
            (this.matchWinner === 1 && owner === 'white'));
        const token = owner === 'black' ? 'b' : owner === 'white' ? 'w' : '.';
        cells.push({
          key,
          row,
          col,
          playable: true,
          token,
          notation: this.toNotation(row, col),
          owner,
          legal: legalKeys.has(key),
          illegal: Boolean(illegalKey && illegalKey === key),
          winning
        });
      }

      rows.push({
        key: `row-${row}`,
        rowIndex: row,
        indent: Math.abs(half - row),
        cells
      });
    }

    return rows;
  }

  private parseMovePoint(value: string, span: number, radius: number): HavannahPoint | null {
    const trimmed = String(value ?? '').trim();
    if (!trimmed) {
      return null;
    }
    const numbers = trimmed.match(/-?\d+/g);
    if (numbers && numbers.length >= 2) {
      const first = Number(numbers[0]);
      const second = Number(numbers[1]);
      if (Number.isFinite(first) && Number.isFinite(second)) {
        if (span > 0 && this.isValidCell(first, second, span, radius)) {
          return [first, second];
        }
        if (span > 0 && this.isValidCell(first - 1, second - 1, span, radius)) {
          return [first - 1, second - 1];
        }
      }
    }
    const algebraic = trimmed.match(/^([a-zA-Z])\s*([0-9]{1,2})$/);
    if (!algebraic) {
      return null;
    }
    const row = Number(algebraic[2]) - 1;
    if (!Number.isFinite(row) || row < 0) {
      return null;
    }
    const globalCol = algebraic[1].toLowerCase().charCodeAt(0) - 97;
    if (span > 0 && this.isValidCell(row, globalCol, span, radius)) {
      return [row, globalCol];
    }
    const effectiveRadius = span > 0 ? radius : 7;
    const startCol = Math.max(0, row - effectiveRadius);
    const localCol = algebraic[1].toLowerCase().charCodeAt(0) - 97;
    const col = startCol + localCol;
    if (span > 0) {
      if (!this.isValidCell(row, col, span, effectiveRadius)) {
        return null;
      }
    }
    return [row, col];
  }

  private toNotation(row: number, col: number): string {
    const letter = String.fromCharCode(97 + col);
    return `${letter}${row + 1}`;
  }

  private isValidCell(row: number, col: number, span: number, radius: number): boolean {
    if (
      !Number.isFinite(row) ||
      !Number.isFinite(col) ||
      row < 0 ||
      col < 0 ||
      row >= span ||
      col >= span
    ) {
      return false;
    }
    return this.isPlayableCell(row, col, span, radius, this.validMask);
  }

  private isPlayableCell(
    row: number,
    col: number,
    span: number,
    radius: number,
    validMask: boolean[][] | null
  ): boolean {
    if (validMask && validMask.length > 0) {
      const rowMask = validMask[row];
      if (!rowMask || col >= rowMask.length) {
        return false;
      }
      return Boolean(rowMask[col]);
    }
    return Math.abs(row - col) <= radius;
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

  private coordKey(row: number, col: number): string {
    return `${row},${col}`;
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
