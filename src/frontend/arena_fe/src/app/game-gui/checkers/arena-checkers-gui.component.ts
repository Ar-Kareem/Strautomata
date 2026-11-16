import { ChangeDetectionStrategy, ChangeDetectorRef, Component, Input, OnDestroy } from '@angular/core';
import { ArenaBannerComponent } from '../../components/arena-gui-helpers/arena-banner.component';
import { ArenaGuiAlertComponent } from '../../components/arena-gui-helpers/arena-gui-alert.component';
import { ArenaGuiEmptyComponent } from '../../components/arena-gui-helpers/arena-gui-empty.component';
import { ArenaGuiLegendComponent } from '../../components/arena-gui-helpers/arena-gui-legend.component';
import { kbdSquare } from '../../components/arena-gui-helpers/arena-kbd-keys';
import type { MatchResultSummary, StatusTone } from '@main/arena.constants';

type CheckersPoint = [number, number];

type CheckersCell = {
  key: string;
  row: number;
  col: number;
  isDark: boolean;
  owner: 'black' | 'white' | null;
  king: boolean;
  legalFrom: boolean;
  legalTo: boolean;
  selected: boolean;
  illegal: boolean;
  winning: boolean;
};

type ParsedMove = {
  fromRow: number;
  fromCol: number;
  toRow: number;
  toCol: number;
};

@Component({
  selector: 'arena-checkers-gui',
  standalone: true,
  templateUrl: './arena-checkers-gui.component.html',
  styleUrl: './arena-checkers-gui.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    ArenaBannerComponent,
    ArenaGuiAlertComponent,
    ArenaGuiEmptyComponent,
    ArenaGuiLegendComponent
  ]
})
export class ArenaCheckersGuiComponent implements OnDestroy {
  boardSize = 0;
  cells: CheckersCell[] = [];
  blackCount = 0;
  whiteCount = 0;
  currentPlayer: number | null = null;
  matchBannerMessage: string | null = null;
  @Input() botA = 'Automaton A';
  @Input() botB = 'Automaton B';
  @Input() statusTone: StatusTone = 'idle';
  @Input() statusMessage = '';
  @Input() showHumanControls = false;
  get activePlayerLabel(): string {
    return this.resolveLabelForPlayer(this.currentPlayer);
  }
  private awaitingHuman = false;
  @Input() set awaitingHumanMove(value: boolean) {
    this.awaitingHuman = value;
    if (!value) {
      this.selectedFromKey = null;
    } else {
      this.suppressLegalHighlights = false;
    }
    this.refreshCells();
  }
  get awaitingHumanMove(): boolean {
    return this.awaitingHuman;
  }
  @Input() submitHumanMove?: (move: string) => void;

  private bannerTimer: number | null = null;
  private lastMatchStamp: number | null = null;
  private matchWinner: number | null = null;
  hasWinner = false;
  private currentLegalMoves: string[] = [];
  private movesByKey = new Map<string, string>();
  private fromKeys = new Set<string>();
  private toKeysByFrom = new Map<string, Set<string>>();
  private illegalMoveKey: string | null = null;
  private suppressLegalHighlights = false;
  // Fixed observation: player 0 is white, player 1 is black.
  private playerColorByIndex: Record<0 | 1, 'white' | 'black'> = {
    0: 'white',
    1: 'black'
  };
  illegalClickMessage: string | null = null;
  illegalClickToken = 0;
  selectedFromKey: string | null = null;
  private blackMen: CheckersPoint[] = [];
  private blackKings: CheckersPoint[] = [];
  private whiteMen: CheckersPoint[] = [];
  private whiteKings: CheckersPoint[] = [];

  constructor(private readonly cdr: ChangeDetectorRef) {
    (window as any).GUI_COMPONENT = this;
  }

  @Input() set legalMoves(value: string[] | null) {
    this.currentLegalMoves = Array.isArray(value) ? value : [];
    this.movesByKey.clear();
    this.fromKeys.clear();
    this.toKeysByFrom.clear();
    this.selectedFromKey = null;
    if (this.awaitingHumanMove) {
      this.suppressLegalHighlights = false;
    }
    for (const move of this.currentLegalMoves) {
      const parsed = this.parseMove(move);
      if (!parsed) {
        continue;
      }
      const fromKey = this.coordKey(parsed.fromRow, parsed.fromCol);
      const toKey = this.coordKey(parsed.toRow, parsed.toCol);
      const moveKey = `${fromKey}|${toKey}`;
      if (!this.movesByKey.has(moveKey)) {
        this.movesByKey.set(moveKey, move);
      }
      this.fromKeys.add(fromKey);
      const targets = this.toKeysByFrom.get(fromKey) ?? new Set<string>();
      targets.add(toKey);
      this.toKeysByFrom.set(fromKey, targets);
    }
    this.refreshCells();
  }

  get legalMoves(): string[] {
    return this.currentLegalMoves;
  }

  @Input() set illegalAction(value: string | null) {
    const parsed = value ? this.parseMove(value) : null;
    this.illegalMoveKey = parsed ? this.coordKey(parsed.toRow, parsed.toCol) : null;
    this.refreshCells();
  }

  @Input() set matchResult(value: MatchResultSummary | null) {
    if (!value) {
      this.lastMatchStamp = null;
      this.matchWinner = null;
      this.hasWinner = false;
      this.clearBanner();
      this.refreshCells();
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
      this.refreshCells();
      return;
    }
    this.matchBannerMessage = this.resolveResultMessage(value.winner);
    this.resetBannerTimer();
    this.refreshCells();
  }

  @Input() set observation(value: unknown | null) {
    const parsed = this.parseObservation(value);
    if (!parsed) {
      this.boardSize = 0;
      this.cells = [];
      this.blackCount = 0;
      this.whiteCount = 0;
      this.currentPlayer = null;
      this.blackMen = [];
      this.blackKings = [];
      this.whiteMen = [];
      this.whiteKings = [];
      this.refreshCells();
      return;
    }
    this.whiteMen = parsed.whiteMen;
    this.whiteKings = parsed.whiteKings;
    this.blackMen = parsed.blackMen;
    this.blackKings = parsed.blackKings;
    this.currentPlayer = parsed.player;
    this.blackCount = this.blackMen.length + this.blackKings.length;
    this.whiteCount = this.whiteMen.length + this.whiteKings.length;
    this.boardSize = this.resolveBoardSize(
      [...this.blackMen, ...this.blackKings, ...this.whiteMen, ...this.whiteKings],
      parsed.boardSize
    );
    this.refreshCells();
  }

  /** keyboard hint: movable pieces, then the selected piece's landing squares */
  kbdLabel(cell: CheckersCell): string | null {
    const target = this.selectedFromKey ? cell.legalTo : cell.legalFrom;
    return target ? kbdSquare(cell.col, cell.row, this.boardSize) : null;
  }

  onCellClick(cell: CheckersCell): void {
    if (!this.awaitingHumanMove || !this.submitHumanMove) {
      return;
    }
    if (!this.selectedFromKey) {
      if (!cell.legalFrom) {
        this.showIllegalClick('Select a movable piece.');
        return;
      }
      this.selectedFromKey = cell.key;
      this.refreshCells();
      return;
    }
    if (this.selectedFromKey === cell.key) {
      this.selectedFromKey = null;
      this.refreshCells();
      return;
    }
    if (cell.legalFrom) {
      this.selectedFromKey = cell.key;
      this.refreshCells();
      return;
    }
    const move = this.movesByKey.get(`${this.selectedFromKey}|${cell.key}`);
    this.selectedFromKey = null;
    if (!move) {
      this.showIllegalClick('Illegal move.');
      this.refreshCells();
      return;
    }
    this.suppressLegalHighlights = true;
    this.refreshCells();
    this.submitHumanMove(move);
  }


  ngOnDestroy(): void {
    this.clearBannerTimer();
  }

  resolveLabelForColor(color: 'black' | 'white'): string {
    return color === 'white' ? this.botA : this.botB;
  }

  private parseObservation(value: unknown | null): {
    whiteMen: CheckersPoint[];
    whiteKings: CheckersPoint[];
    blackMen: CheckersPoint[];
    blackKings: CheckersPoint[];
    player: number | null;
    boardSize: number | null;
  } | null {
    if (!value || typeof value !== 'object') {
      return null;
    }
    const statePlayer = value as { state?: unknown; player?: unknown };
    const record = (statePlayer.state ?? value) as Record<string, unknown>;
    const player =
      typeof statePlayer.player === 'number'
        ? statePlayer.player
        : typeof record['player'] === 'number'
          ? (record['player'] as number)
          : typeof record['turn'] === 'number'
            ? (record['turn'] as number)
            : null;
    const boardSize = typeof record['board_size'] === 'number' ? (record['board_size'] as number) : null;
    const whiteMen = this.parsePoints(record['white_men']);
    const whiteKings = this.parsePoints(record['white_kings']);
    const blackMen = this.parsePoints(record['black_men']);
    const blackKings = this.parsePoints(record['black_kings']);
    if (!whiteMen || !whiteKings || !blackMen || !blackKings) {
      return null;
    }
    return { whiteMen, whiteKings, blackMen, blackKings, player, boardSize };
  }

  private parsePoints(value: unknown): CheckersPoint[] | null {
    if (!Array.isArray(value)) {
      return null;
    }
    const points: CheckersPoint[] = [];
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

  private resolveBoardSize(points: CheckersPoint[], fallback: number | null): number {
    if (fallback && Number.isFinite(fallback) && fallback > 0) {
      return Math.floor(fallback);
    }
    let maxCoord = 0;
    for (const [row, col] of points) {
      maxCoord = Math.max(maxCoord, row, col);
    }
    return Math.max(8, maxCoord + 1);
  }

  private refreshCells(): void {
    this.cells = this.buildCells(
      this.blackMen,
      this.blackKings,
      this.whiteMen,
      this.whiteKings,
      this.boardSize,
      this.fromKeys,
      this.selectedFromKey,
      this.illegalMoveKey,
      this.awaitingHumanMove && !this.suppressLegalHighlights
    );
    this.cdr.markForCheck();
  }

  private buildCells(
    blackMen: CheckersPoint[],
    blackKings: CheckersPoint[],
    whiteMen: CheckersPoint[],
    whiteKings: CheckersPoint[],
    size: number,
    legalFrom: Set<string>,
    selectedFrom: string | null,
    illegalKey: string | null,
    allowLegal: boolean
  ): CheckersCell[] {
    if (size <= 0) {
      return [];
    }
    const blackMenSet = new Set(blackMen.map(([row, col]) => this.coordKey(row, col)));
    const blackKingsSet = new Set(blackKings.map(([row, col]) => this.coordKey(row, col)));
    const whiteMenSet = new Set(whiteMen.map(([row, col]) => this.coordKey(row, col)));
    const whiteKingsSet = new Set(whiteKings.map(([row, col]) => this.coordKey(row, col)));
    const legalTargets =
      selectedFrom && allowLegal ? this.toKeysByFrom.get(selectedFrom) ?? new Set<string>() : new Set<string>();
    const winnerColor = this.resolveWinnerColor();
    const cells: CheckersCell[] = [];
    for (let row = size - 1; row >= 0; row -= 1) {
      for (let col = 0; col < size; col += 1) {
        const key = this.coordKey(row, col);
        const isDark = (row + col) % 2 === 0;
        let owner: CheckersCell['owner'] = null;
        let king = false;
        if (blackMenSet.has(key)) {
          owner = 'black';
        } else if (blackKingsSet.has(key)) {
          owner = 'black';
          king = true;
        } else if (whiteMenSet.has(key)) {
          owner = 'white';
        } else if (whiteKingsSet.has(key)) {
          owner = 'white';
          king = true;
        }
        cells.push({
          key,
          row,
          col,
          isDark,
          owner,
          king,
          legalFrom: allowLegal && legalFrom.has(key),
          legalTo: allowLegal && Boolean(selectedFrom && legalTargets.has(key)),
          selected: selectedFrom === key,
          illegal: Boolean(illegalKey && illegalKey === key),
          winning: Boolean(winnerColor && owner === winnerColor)
        });
      }
    }
    return cells;
  }

  private resolveWinnerColor(): 'black' | 'white' | null {
    if (this.matchWinner !== 0 && this.matchWinner !== 1) {
      return null;
    }
    return this.playerColorByIndex[this.matchWinner];
  }

  private resolveResultMessage(winner: number | null): string {
    if (winner === 0) {
      return `${this.resolveLabelForColor('white')} won`;
    }
    if (winner === 1) {
      return `${this.resolveLabelForColor('black')} won`;
    }
    return 'Draw';
  }

  private resolveLabelForPlayer(playerIndex: number | null): string {
    if (playerIndex !== 0 && playerIndex !== 1) {
      return '';
    }
    return this.resolveLabelForColor(this.playerColorByIndex[playerIndex]);
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

  private parseMove(value: string): ParsedMove | null {
    const trimmed = String(value ?? '').trim();
    if (!trimmed) {
      return null;
    }
    const squares = trimmed.match(/[a-h][1-8]/gi);
    if (squares && squares.length >= 2) {
      const from = this.squareToCoord(squares[0]);
      const to = this.squareToCoord(squares[squares.length - 1]);
      if (from && to) {
        return { fromRow: from.row, fromCol: from.col, toRow: to.row, toCol: to.col };
      }
    }
    const numbers = trimmed.match(/-?\d+/g);
    if (numbers && numbers.length >= 4) {
      const fromRow = Number(numbers[0]);
      const fromCol = Number(numbers[1]);
      const toRow = Number(numbers[numbers.length - 2]);
      const toCol = Number(numbers[numbers.length - 1]);
      if ([fromRow, fromCol, toRow, toCol].every((entry) => Number.isFinite(entry))) {
        return { fromRow, fromCol, toRow, toCol };
      }
    }
    return null;
  }

  private squareToCoord(square: string): { row: number; col: number } | null {
    if (!square || square.length < 2) {
      return null;
    }
    const col = square.charCodeAt(0) - 97;
    const row = Number(square[1]) - 1;
    if (!Number.isFinite(row) || col < 0 || col > 7 || row < 0 || row > 7) {
      return null;
    }
    return { row, col };
  }
}
