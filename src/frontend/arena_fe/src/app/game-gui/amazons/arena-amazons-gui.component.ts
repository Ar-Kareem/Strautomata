import { ChangeDetectionStrategy, ChangeDetectorRef, Component, Input, OnDestroy } from '@angular/core';
import type { MatchResultSummary, StatusTone } from '@main/arena.constants';

type AmazonsCell = {
  key: string;
  row: number;
  col: number;
  isDark: boolean;
  owner: 'white' | 'black' | null;
  arrow: boolean;
  legalFrom: boolean;
  legalTo: boolean;
  legalArrow: boolean;
  selectedFrom: boolean;
  selectedTo: boolean;
  lastMovedQueen: boolean;
  lastPlacedArrow: boolean;
  illegal: boolean;
  winning: boolean;
};

type ParsedAmazonsMove = {
  fromRow: number;
  fromCol: number;
  toRow: number;
  toCol: number;
  arrowRow: number;
  arrowCol: number;
};

@Component({
  selector: 'arena-amazons-gui',
  standalone: true,
  templateUrl: './arena-amazons-gui.component.html',
  styleUrl: './arena-amazons-gui.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ArenaAmazonsGuiComponent implements OnDestroy {
  boardRows = 0;
  boardCols = 0;
  cells: AmazonsCell[] = [];
  arrowCount = 0;
  whiteCount = 0;
  blackCount = 0;
  currentPlayer: number | null = null;
  matchBannerMessage: string | null = null;
  @Input() botA = 'Automaton A';
  @Input() botB = 'Automaton B';
  @Input() statusTone: StatusTone = 'idle';
  @Input() statusMessage = '';
  @Input() showHumanControls = false;
  get activePlayerLabel(): string {
    if (this.currentPlayer === 0) {
      return this.botA;
    }
    if (this.currentPlayer === 1) {
      return this.botB;
    }
    return '';
  }

  get arrowCountDisplay(): number {
    return Number.isFinite(this.arrowCount) ? this.arrowCount : 0;
  }
  private awaitingHuman = false;
  @Input() set awaitingHumanMove(value: boolean) {
    this.awaitingHuman = value;
    if (!value) {
      this.selectedFromKey = null;
      this.selectedToKey = null;
      this.suppressLegalHighlights = false;
    }
    this.refreshCells();
  }
  get awaitingHumanMove(): boolean {
    return this.awaitingHuman;
  }
  @Input() submitHumanMove?: (move: string, forceApply?: boolean) => void;

  private board: number[][] = [];
  private bannerTimer: number | null = null;
  private lastMatchStamp: number | null = null;
  private matchWinner: number | null = null;
  hasWinner = false;

  private dynamicLegalFrom = new Set<string>();
  private dynamicLegalTo = new Set<string>();
  private dynamicLegalArrow = new Set<string>();
  private illegalMoveKey: string | null = null;
  private suppressLegalHighlights = false;
  selectedFromKey: string | null = null;
  selectedToKey: string | null = null;
  private lastMovedQueenKey: string | null = null;
  private lastPlacedArrowKey: string | null = null;
  illegalClickMessage: string | null = null;
  illegalClickToken = 0;

  private whitePieceValue: number | null = null;
  private blackPieceValue: number | null = null;
  private arrowValue: number | null = null;

  constructor(private readonly cdr: ChangeDetectorRef) {
    (window as { GUI_COMPONENT?: unknown }).GUI_COMPONENT = this;
  }

  @Input() set legalMoves(_value: string[] | null) {
    // Amazons legal_moves currently only identifies movable pieces, not full 3-phase moves.
    // Ignore it for geometry, but use this update as a turn-boundary reset signal.
    this.selectedFromKey = null;
    this.selectedToKey = null;
    this.suppressLegalHighlights = false;
    this.refreshCells();
  }

  get legalMoves(): string[] {
    return [];
  }

  @Input() set illegalAction(value: string | null) {
    const parsed = value ? this.parseMove(value) : null;
    this.illegalMoveKey = parsed ? this.coordKey(parsed.arrowRow, parsed.arrowCol) : null;
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
      this.board = [];
      this.boardRows = 0;
      this.boardCols = 0;
      this.cells = [];
      this.arrowCount = 0;
      this.whiteCount = 0;
      this.blackCount = 0;
      this.currentPlayer = null;
      this.whitePieceValue = null;
      this.blackPieceValue = null;
      this.arrowValue = null;
      this.lastMovedQueenKey = null;
      this.lastPlacedArrowKey = null;
      return;
    }
    const boardChanged = this.hasBoardChanged(this.board, parsed.board, this.boardRows, this.boardCols, parsed.rows, parsed.cols);
    const latestMove = this.resolveLatestMove(this.board, parsed.board, this.boardRows, this.boardCols);
    if (latestMove) {
      this.lastMovedQueenKey = latestMove.queenToKey;
      this.lastPlacedArrowKey = latestMove.arrowKey;
    } else if (boardChanged) {
      this.lastMovedQueenKey = null;
      this.lastPlacedArrowKey = null;
    }
    this.board = parsed.board;
    this.boardRows = parsed.rows;
    this.boardCols = parsed.cols;
    this.currentPlayer = parsed.player;
    this.selectedFromKey = null;
    this.selectedToKey = null;
    this.suppressLegalHighlights = false;
    this.whitePieceValue = 1;
    this.blackPieceValue = 2;
    this.arrowValue = -1;
    const counts = this.countPieces(parsed.board);
    this.arrowCount = this.countArrows(parsed.board);
    this.whiteCount = counts.whiteCount;
    this.blackCount = counts.blackCount;
    this.refreshCells();
  }


  onCellClick(cell: AmazonsCell): void {
    if (!this.awaitingHumanMove || !this.submitHumanMove) {
      return;
    }
    const key = cell.key;
    if (!this.selectedFromKey) {
      if (!cell.legalFrom) {
        this.showIllegalClick('Select a movable queen.');
        return;
      }
      this.selectedFromKey = key;
      this.selectedToKey = null;
      this.refreshCells();
      return;
    }

    if (!this.selectedToKey) {
      if (key === this.selectedFromKey) {
        this.selectedFromKey = null;
        this.refreshCells();
        return;
      }
      if (this.dynamicLegalFrom.has(key)) {
        this.selectedFromKey = key;
        this.refreshCells();
        return;
      }
      if (!this.dynamicLegalTo.has(key)) {
        this.showIllegalClick('Select a legal destination.');
        return;
      }
      this.selectedToKey = key;
      this.refreshCells();
      return;
    }

    if (this.dynamicLegalArrow.has(key)) {
      this.submitPendingMove(key);
      return;
    }
    this.cancelPendingMoveSelection();
  }

  private submitPendingMove(arrowKey: string): void {
    if (!this.submitHumanMove || !this.selectedFromKey || !this.selectedToKey) {
      return;
    }
    const move = `${this.selectedFromKey}:${this.selectedToKey}:${arrowKey}`;
    this.suppressLegalHighlights = true;
    this.selectedFromKey = null;
    this.selectedToKey = null;
    this.refreshCells();
    const forceApply = true;
    this.submitHumanMove(move, forceApply);
  }

  private cancelPendingMoveSelection(): void {
    this.selectedFromKey = null;
    this.selectedToKey = null;
    this.refreshCells();
  }

  resolveLabelForColor(color: 'white' | 'black'): string {
    return color === 'white' ? this.botA : this.botB;
  }

  ngOnDestroy(): void {
    this.clearBannerTimer();
  }

  private parseObservation(value: unknown | null): {
    board: number[][];
    rows: number;
    cols: number;
    player: number | null;
  } | null {
    if (!value || typeof value !== 'object') {
      return null;
    }
    const statePlayer = value as { state?: unknown; player?: unknown };
    const record = (statePlayer.state ?? value) as Record<string, unknown>;
    const board = this.parseBoard(record['board'] ?? (value as { board?: unknown }).board);
    if (!board) {
      return null;
    }
    const player =
      typeof statePlayer.player === 'number'
        ? statePlayer.player
        : typeof record['player'] === 'number'
          ? (record['player'] as number)
          : typeof record['turn'] === 'number'
            ? (record['turn'] as number)
            : null;
    return {
      board,
      rows: board.length,
      cols: board[0]?.length ?? 0,
      player
    };
  }

  private parseBoard(value: unknown): number[][] | null {
    if (!Array.isArray(value) || value.length === 0) {
      return null;
    }
    const rows: number[][] = [];
    let width = 0;
    for (const row of value) {
      const parsed = this.parseRow(row);
      if (!parsed) {
        return null;
      }
      if (!width) {
        width = parsed.length;
      }
      if (parsed.length !== width) {
        return null;
      }
      rows.push(parsed);
    }
    return rows.length > 0 && width > 0 ? rows : null;
  }

  private parseRow(value: unknown): number[] | null {
    if (Array.isArray(value) || ArrayBuffer.isView(value)) {
      return Array.from(value as Iterable<unknown>, (entry) => this.normalizeCell(entry));
    }
    if (!value || typeof value !== 'object') {
      return null;
    }
    const keys = Object.keys(value);
    if (keys.length === 0) {
      return null;
    }
    const sortedKeys = keys.sort((a, b) => Number(a) - Number(b));
    const entries = sortedKeys.map((key) => (value as Record<string, unknown>)[key]);
    return entries.map((entry) => this.normalizeCell(entry));
  }

  private normalizeCell(value: unknown): number {
    const num = Number(value);
    if (!Number.isFinite(num) || Object.is(num, -0)) {
      return 0;
    }
    return num;
  }

  private parseMove(value: string): ParsedAmazonsMove | null {
    const trimmed = String(value ?? '').trim();
    const match = trimmed.match(/^(\d+),(\d+):(\d+),(\d+):(\d+),(\d+)$/);
    if (!match) {
      return null;
    }
    return {
      fromRow: Number(match[1]),
      fromCol: Number(match[2]),
      toRow: Number(match[3]),
      toCol: Number(match[4]),
      arrowRow: Number(match[5]),
      arrowCol: Number(match[6])
    };
  }

  private coordKey(row: number, col: number): string {
    return `${row},${col}`;
  }

  private parseCoordKey(key: string): { row: number; col: number } | null {
    const [rowToken, colToken] = key.split(',');
    const row = Number(rowToken);
    const col = Number(colToken);
    if (!Number.isInteger(row) || !Number.isInteger(col)) {
      return null;
    }
    if (!this.inBounds(row, col)) {
      return null;
    }
    return { row, col };
  }

  private inBounds(row: number, col: number): boolean {
    return row >= 0 && col >= 0 && row < this.boardRows && col < this.boardCols;
  }

  private isEmptyForPath(row: number, col: number, sourceKey: string | null, targetKey: string | null): boolean {
    const key = this.coordKey(row, col);
    if (sourceKey && key === sourceKey) {
      return true;
    }
    if (targetKey && key === targetKey) {
      return false;
    }
    return (this.board[row]?.[col] ?? 0) === 0;
  }

  private collectRayMoves(originKey: string, sourceKey: string | null, targetKey: string | null): Set<string> {
    const origin = this.parseCoordKey(originKey);
    if (!origin) {
      return new Set<string>();
    }
    const moves = new Set<string>();
    const directions = [
      [-1, -1], [-1, 0], [-1, 1],
      [0, -1],           [0, 1],
      [1, -1],  [1, 0],  [1, 1]
    ];
    for (const [dr, dc] of directions) {
      let row = origin.row + dr;
      let col = origin.col + dc;
      while (this.inBounds(row, col) && this.isEmptyForPath(row, col, sourceKey, targetKey)) {
        moves.add(this.coordKey(row, col));
        row += dr;
        col += dc;
      }
    }
    return moves;
  }

  private collectMovableQueens(): Set<string> {
    const currentOwner: 'white' | 'black' | null =
      this.currentPlayer === 0 ? 'white' : this.currentPlayer === 1 ? 'black' : null;
    if (!currentOwner) {
      return new Set<string>();
    }
    const movable = new Set<string>();
    for (let row = 0; row < this.boardRows; row += 1) {
      for (let col = 0; col < this.boardCols; col += 1) {
        if (this.ownerForValue(this.board[row]?.[col] ?? 0) !== currentOwner) {
          continue;
        }
        const fromKey = this.coordKey(row, col);
        if (this.collectRayMoves(fromKey, null, null).size > 0) {
          movable.add(fromKey);
        }
      }
    }
    return movable;
  }

  private refreshCells(): void {
    if (!this.boardRows || !this.boardCols) {
      this.cells = [];
      this.arrowCount = 0;
      this.cdr.markForCheck();
      return;
    }
    const allowLegal = this.awaitingHumanMove && !this.suppressLegalHighlights;
    this.dynamicLegalFrom = allowLegal ? this.collectMovableQueens() : new Set<string>();
    if (this.selectedFromKey && !this.dynamicLegalFrom.has(this.selectedFromKey)) {
      this.selectedFromKey = null;
      this.selectedToKey = null;
    }
    const activeFromKey = this.selectedFromKey;
    const allLegalTo =
      allowLegal && activeFromKey ? this.collectRayMoves(activeFromKey, null, null) : new Set<string>();
    if (this.selectedToKey && !allLegalTo.has(this.selectedToKey)) {
      this.selectedToKey = null;
    }
    const selectingDestination = allowLegal && Boolean(activeFromKey) && !this.selectedToKey;
    this.dynamicLegalTo = selectingDestination ? allLegalTo : new Set<string>();
    this.dynamicLegalArrow =
      allowLegal && this.selectedFromKey && this.selectedToKey
        ? this.collectRayMoves(this.selectedToKey, this.selectedFromKey, this.selectedToKey)
        : new Set<string>();
    const winnerColor: 'white' | 'black' | null =
      this.hasWinner && this.matchWinner !== null
        ? this.matchWinner === 0
          ? 'white'
          : 'black'
        : null;

    const cells: AmazonsCell[] = [];
    for (let row = 0; row < this.boardRows; row += 1) {
      for (let col = 0; col < this.boardCols; col += 1) {
        const key = this.coordKey(row, col);
        const value = this.board[row]?.[col] ?? 0;
        const owner = this.ownerForValue(value);
        const arrow = this.isArrowValue(value, owner);
        cells.push({
          key,
          row,
          col,
          isDark: (row + col) % 2 === 1,
          owner,
          arrow,
          legalFrom: allowLegal && this.dynamicLegalFrom.has(key),
          legalTo: allowLegal && this.dynamicLegalTo.has(key),
          legalArrow: allowLegal && this.dynamicLegalArrow.has(key),
          selectedFrom: this.selectedFromKey === key,
          selectedTo: this.selectedToKey === key,
          lastMovedQueen: this.lastMovedQueenKey === key,
          lastPlacedArrow: this.lastPlacedArrowKey === key,
          illegal: Boolean(this.illegalMoveKey && this.illegalMoveKey === key),
          winning: Boolean(winnerColor && owner === winnerColor)
        });
      }
    }
    this.cells = cells;
    this.arrowCount = cells.reduce((count, cell) => (cell.arrow ? count + 1 : count), 0);
    this.cdr.markForCheck();
  }

  private ownerForValue(value: number): 'white' | 'black' | null {
    if (value === 0) {
      return null;
    }
    if (this.whitePieceValue !== null && value === this.whitePieceValue) {
      return 'white';
    }
    if (this.blackPieceValue !== null && value === this.blackPieceValue) {
      return 'black';
    }
    return null;
  }

  private isArrowValue(value: number, owner: 'white' | 'black' | null): boolean {
    if (value === 0 || owner) {
      return false;
    }
    if (this.arrowValue !== null) {
      return value === this.arrowValue;
    }
    return true;
  }

  private countPieces(board: number[][]): { whiteCount: number; blackCount: number } {
    let whiteCount = 0;
    let blackCount = 0;
    for (const row of board) {
      for (const value of row) {
        const owner = this.ownerForValue(value);
        if (owner === 'white') {
          whiteCount += 1;
        } else if (owner === 'black') {
          blackCount += 1;
        }
      }
    }
    return { whiteCount, blackCount };
  }

  private countArrows(board: number[][]): number {
    let arrows = 0;
    for (const row of board) {
      for (const value of row) {
        if (this.isArrowValue(value, this.ownerForValue(value))) {
          arrows += 1;
        }
      }
    }
    return arrows;
  }

  private hasBoardChanged(
    previousBoard: number[][],
    nextBoard: number[][],
    previousRows: number,
    previousCols: number,
    nextRows: number,
    nextCols: number
  ): boolean {
    if (previousRows !== nextRows || previousCols !== nextCols) {
      return true;
    }
    if (previousRows <= 0 || previousCols <= 0) {
      return false;
    }
    for (let row = 0; row < previousRows; row += 1) {
      if (previousBoard[row]?.length !== previousCols || nextBoard[row]?.length !== previousCols) {
        return true;
      }
      for (let col = 0; col < previousCols; col += 1) {
        if ((previousBoard[row]?.[col] ?? 0) !== (nextBoard[row]?.[col] ?? 0)) {
          return true;
        }
      }
    }
    return false;
  }

  private resolveLatestMove(
    previousBoard: number[][],
    nextBoard: number[][],
    rows: number,
    cols: number
  ): { queenToKey: string; arrowKey: string } | null {
    if (rows <= 0 || cols <= 0) {
      return null;
    }
    if (previousBoard.length !== rows || nextBoard.length !== rows) {
      return null;
    }
    let movedColor: 'white' | 'black' | null = null;
    let queenFromKey: string | null = null;
    let queenToKey: string | null = null;
    let arrowAddedKey: string | null = null;
    for (let row = 0; row < rows; row += 1) {
      if (previousBoard[row]?.length !== cols || nextBoard[row]?.length !== cols) {
        return null;
      }
      for (let col = 0; col < cols; col += 1) {
        const key = this.coordKey(row, col);
        const prevValue = previousBoard[row]?.[col] ?? 0;
        const nextValue = nextBoard[row]?.[col] ?? 0;
        const prevOwner = prevValue === 1 ? 'white' : prevValue === 2 ? 'black' : null;
        const nextOwner = nextValue === 1 ? 'white' : nextValue === 2 ? 'black' : null;
        const prevArrow = prevValue === -1;
        const nextArrow = nextValue === -1;
        if (prevOwner !== nextOwner) {
          if (prevOwner && !nextOwner) {
            if (queenFromKey) {
              return null;
            }
            queenFromKey = key;
            movedColor ??= prevOwner;
            if (movedColor !== prevOwner) {
              return null;
            }
          } else if (!prevOwner && nextOwner) {
            if (queenToKey) {
              return null;
            }
            queenToKey = key;
            movedColor ??= nextOwner;
            if (movedColor !== nextOwner) {
              return null;
            }
          } else {
            return null;
          }
        }
        if (prevArrow !== nextArrow) {
          if (!prevArrow && nextArrow) {
            if (arrowAddedKey) {
              return null;
            }
            arrowAddedKey = key;
          } else {
            return null;
          }
        }
      }
    }
    if (!queenFromKey || !queenToKey || !arrowAddedKey || !movedColor) {
      return null;
    }
    return { queenToKey, arrowKey: arrowAddedKey };
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
