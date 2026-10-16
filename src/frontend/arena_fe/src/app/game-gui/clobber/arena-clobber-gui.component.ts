import { ChangeDetectionStrategy, ChangeDetectorRef, Component, Input, OnDestroy } from '@angular/core';
import { HumanMovePanelComponent } from '@arena/human-move-panel.component';
import type { MatchResultSummary, StatusTone } from '@main/arena.constants';

type ClobberCell = {
  key: string;
  row: number;
  col: number;
  isDark: boolean;
  owner: 'black' | 'white' | null;
  legalFrom: boolean;
  legalTo: boolean;
  moveDir: 'up' | 'right' | 'down' | 'left' | null;
  selected: boolean;
  illegal: boolean;
  lastMoveTo: boolean;
  lastMoveDir: 'up' | 'right' | 'down' | 'left' | null;
  winning: boolean;
};

type ParsedMove = {
  fromRow: number;
  fromCol: number;
  toRow: number;
  toCol: number;
  dir: 'U' | 'R' | 'D' | 'L';
};

@Component({
  selector: 'arena-clobber-gui',
  standalone: true,
  templateUrl: './arena-clobber-gui.component.html',
  styleUrl: './arena-clobber-gui.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [HumanMovePanelComponent]
})
export class ArenaClobberGuiComponent implements OnDestroy {
  boardRows = 0;
  boardCols = 0;
  cells: ClobberCell[] = [];
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
    if (this.currentPlayer === 0) {
      return this.botA;
    }
    if (this.currentPlayer === 1) {
      return this.botB;
    }
    return '';
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
  private matchIllegal = false;
  hasWinner = false;
  private currentLegalMoves: string[] = [];
  private movesByKey = new Map<string, string>();
  private fromKeys = new Set<string>();
  private toKeysByFrom = new Map<string, Set<string>>();
  private suppressLegalHighlights = false;
  private illegalMoveKey: string | null = null;
  private blackBoard: number[][] = [];
  private whiteBoard: number[][] = [];
  private lastMoveToKey: string | null = null;
  private lastMoveDir: 'up' | 'right' | 'down' | 'left' | null = null;
  illegalClickMessage: string | null = null;
  illegalClickToken = 0;
  selectedFromKey: string | null = null;

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
      this.matchIllegal = false;
      this.hasWinner = false;
      this.clearBanner();
      this.refreshCells();
      return;
    }
    if (this.lastMatchStamp === value.finishedAt) {
      return;
    }
    this.lastMatchStamp = value.finishedAt;
    this.matchIllegal = value.illegal;
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
      this.boardRows = 0;
      this.boardCols = 0;
      this.cells = [];
      this.blackCount = 0;
      this.whiteCount = 0;
      this.currentPlayer = null;
      this.blackBoard = [];
      this.whiteBoard = [];
      this.lastMoveToKey = null;
      this.lastMoveDir = null;
      this.refreshCells();
      return;
    }
    const previousRows = this.boardRows;
    const previousCols = this.boardCols;
    const boardChanged = this.haveBoardsChanged(
      this.blackBoard,
      this.whiteBoard,
      parsed.black,
      parsed.white,
      previousRows,
      previousCols
    );
    const latestMove = this.resolveLatestMove(
      this.blackBoard,
      this.whiteBoard,
      parsed.black,
      parsed.white,
      previousRows,
      previousCols
    );
    if (latestMove) {
      this.lastMoveToKey = latestMove.toKey;
      this.lastMoveDir = latestMove.dir;
    } else if (boardChanged) {
      this.lastMoveToKey = null;
      this.lastMoveDir = null;
    }
    this.blackBoard = parsed.black;
    this.whiteBoard = parsed.white;
    this.boardRows = parsed.rows;
    this.boardCols = parsed.cols;
    this.currentPlayer = parsed.player;
    this.blackCount = this.countPieces(this.blackBoard);
    this.whiteCount = this.countPieces(this.whiteBoard);
    this.refreshCells();
  }

  onCellClick(cell: ClobberCell): void {
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
    this.submitHumanMove(this.stripActionSuffix(move));
  }

  get humanHint(): string {
    if (!this.awaitingHumanMove) {
      return 'Waiting for your turn.';
    }
    if (this.selectedFromKey) {
      return 'Select a target to clobber. Arrows show direction.';
    }
    return 'Select a piece, then a target.';
  }

  ngOnDestroy(): void {
    this.clearBannerTimer();
  }

  private parseObservation(value: unknown | null): {
    black: number[][];
    white: number[][];
    rows: number;
    cols: number;
    player: number | null;
  } | null {
    if (!value || typeof value !== 'object') {
      return null;
    }
    const statePlayer = value as { state?: unknown; player?: unknown };
    const record = (statePlayer.state ?? value) as Record<string, unknown>;
    const player =
      typeof record['turn'] === 'number'
        ? (record['turn'] as number)
        : typeof statePlayer.player === 'number'
          ? (statePlayer.player as number)
          : typeof record['player'] === 'number'
            ? (record['player'] as number)
            : null;
    const black = this.parseGrid(record['you'] ?? (value as { you?: unknown }).you);
    const white = this.parseGrid(record['opponent'] ?? (value as { opponent?: unknown }).opponent);
    if (!black || !white) {
      return null;
    }
    if (black.length === 0 || white.length === 0) {
      return null;
    }
    if (black.length !== white.length || black[0].length !== white[0].length) {
      return null;
    }
    return {
      black,
      white,
      rows: black.length,
      cols: black[0].length,
      player
    };
  }

  private parseGrid(value: unknown): number[][] | null {
    if (!Array.isArray(value) || value.length === 0) {
      return null;
    }
    const rows: number[][] = [];
    let width = -1;
    for (const row of value) {
      let rowValues: unknown[] | null = null;
      if (Array.isArray(row)) {
        rowValues = row;
      } else if (row && typeof row === 'object') {
        const entries = Object.entries(row as Record<string, unknown>)
          .map(([key, cell]) => ({ index: Number(key), cell }))
          .filter(({ index }) => Number.isInteger(index) && index >= 0)
          .sort((a, b) => a.index - b.index);
        if (entries.length === 0) {
          return null;
        }
        const maxIndex = entries[entries.length - 1].index;
        rowValues = new Array(maxIndex + 1).fill(undefined);
        for (const entry of entries) {
          rowValues[entry.index] = entry.cell;
        }
      } else {
        return null;
      }
      if (width < 0) {
        width = rowValues.length;
      } else if (rowValues.length !== width) {
        return null;
      }
      const parsedRow: number[] = [];
      for (const cell of rowValues) {
        const num = Number(cell);
        if (!Number.isFinite(num)) {
          return null;
        }
        parsedRow.push(num);
      }
      rows.push(parsedRow);
    }
    return rows;
  }

  private countPieces(board: number[][]): number {
    let count = 0;
    for (const row of board) {
      for (const value of row) {
        if (value === 1) {
          count += 1;
        }
      }
    }
    return count;
  }

  private buildCells(
    black: number[][],
    white: number[][],
    rows: number,
    cols: number,
    legalFrom: Set<string>,
    legalTo: Set<string>,
    selectedFrom: string | null,
    illegalKey: string | null,
    allowLegal: boolean
  ): ClobberCell[] {
    if (rows <= 0 || cols <= 0) {
      return [];
    }
    const winnerOwner = this.resolveWinnerOwner();
    const selectedFromCoord = selectedFrom ? this.parseCoordKey(selectedFrom) : null;
    const cells: ClobberCell[] = [];
    for (let row = 0; row < rows; row += 1) {
      for (let col = 0; col < cols; col += 1) {
        const key = this.coordKey(row, col);
        const blackValue = black[row]?.[col] ?? 0;
        const whiteValue = white[row]?.[col] ?? 0;
        let owner: ClobberCell['owner'] = null;
        if (blackValue === 1) {
          owner = 'black';
        } else if (whiteValue === 1) {
          owner = 'white';
        }
        const isLegalTo = allowLegal && Boolean(selectedFrom && legalTo.has(key));
        const moveDir =
          isLegalTo && selectedFromCoord
            ? this.resolveDirectionFromCoords(selectedFromCoord.row, selectedFromCoord.col, row, col)
            : null;
        const lastMoveTo = this.lastMoveToKey === key;
        cells.push({
          key,
          row,
          col,
          isDark: (row + col) % 2 === 0,
          owner,
          legalFrom: allowLegal && legalFrom.has(key),
          legalTo: isLegalTo,
          moveDir,
          selected: selectedFrom === key,
          illegal: Boolean(illegalKey && illegalKey === key),
          lastMoveTo,
          lastMoveDir: lastMoveTo ? this.lastMoveDir : null,
          winning: Boolean(winnerOwner && owner === winnerOwner)
        });
      }
    }
    return cells;
  }

  private resolveWinnerOwner(): 'black' | 'white' | null {
    if (this.matchIllegal || this.matchWinner === null) {
      return null;
    }
    if (this.matchWinner === 0) {
      return 'black';
    }
    if (this.matchWinner === 1) {
      return 'white';
    }
    return null;
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

  private haveBoardsChanged(
    previousBlack: number[][],
    previousWhite: number[][],
    nextBlack: number[][],
    nextWhite: number[][],
    rows: number,
    cols: number
  ): boolean {
    if (rows <= 0 || cols <= 0) {
      return false;
    }
    if (
      previousBlack.length !== rows
      || previousWhite.length !== rows
      || nextBlack.length !== rows
      || nextWhite.length !== rows
    ) {
      return true;
    }
    for (let row = 0; row < rows; row += 1) {
      if (
        previousBlack[row]?.length !== cols
        || previousWhite[row]?.length !== cols
        || nextBlack[row]?.length !== cols
        || nextWhite[row]?.length !== cols
      ) {
        return true;
      }
      for (let col = 0; col < cols; col += 1) {
        if ((previousBlack[row]?.[col] ?? 0) !== (nextBlack[row]?.[col] ?? 0)) {
          return true;
        }
        if ((previousWhite[row]?.[col] ?? 0) !== (nextWhite[row]?.[col] ?? 0)) {
          return true;
        }
      }
    }
    return false;
  }

  private resolveLatestMove(
    previousBlack: number[][],
    previousWhite: number[][],
    nextBlack: number[][],
    nextWhite: number[][],
    rows: number,
    cols: number
  ): { fromKey: string; toKey: string; dir: 'up' | 'right' | 'down' | 'left' } | null {
    if (rows <= 0 || cols <= 0) {
      return null;
    }
    const blackMove = this.resolveColorMove(previousBlack, nextBlack, rows, cols);
    const whiteMove = this.resolveColorMove(previousWhite, nextWhite, rows, cols);
    const moves = [blackMove, whiteMove].filter(
      (
        value
      ): value is {
        fromRow: number;
        fromCol: number;
        toRow: number;
        toCol: number;
      } => Boolean(value)
    );
    if (moves.length !== 1) {
      return null;
    }
    const move = moves[0];
    const dir = this.resolveDirectionFromCoords(move.fromRow, move.fromCol, move.toRow, move.toCol);
    if (!dir) {
      return null;
    }
    return {
      fromKey: this.coordKey(move.fromRow, move.fromCol),
      toKey: this.coordKey(move.toRow, move.toCol),
      dir
    };
  }

  private resolveColorMove(
    previousBoard: number[][],
    nextBoard: number[][],
    rows: number,
    cols: number
  ): { fromRow: number; fromCol: number; toRow: number; toCol: number } | null {
    if (previousBoard.length !== rows || nextBoard.length !== rows) {
      return null;
    }
    const removed: Array<{ row: number; col: number }> = [];
    const added: Array<{ row: number; col: number }> = [];
    for (let row = 0; row < rows; row += 1) {
      if (previousBoard[row]?.length !== cols || nextBoard[row]?.length !== cols) {
        return null;
      }
      for (let col = 0; col < cols; col += 1) {
        const wasPresent = (previousBoard[row]?.[col] ?? 0) === 1;
        const isPresent = (nextBoard[row]?.[col] ?? 0) === 1;
        if (wasPresent && !isPresent) {
          removed.push({ row, col });
        } else if (!wasPresent && isPresent) {
          added.push({ row, col });
        }
      }
    }
    if (removed.length !== 1 || added.length !== 1) {
      return null;
    }
    return {
      fromRow: removed[0].row,
      fromCol: removed[0].col,
      toRow: added[0].row,
      toCol: added[0].col
    };
  }

  private parseMove(value: string): ParsedMove | null {
    const trimmed = String(value ?? '').trim();
    if (!trimmed) {
      return null;
    }
    const main = trimmed.split(':')[0]?.trim();
    if (!main) {
      return null;
    }
    const match = main.match(/(-?\d+)\s*,\s*(-?\d+)\s*,\s*([URDL])/i);
    if (!match) {
      return null;
    }
    const fromRow = Number(match[1]);
    const fromCol = Number(match[2]);
    const dir = match[3].toUpperCase() as ParsedMove['dir'];
    if (!Number.isFinite(fromRow) || !Number.isFinite(fromCol)) {
      return null;
    }
    const delta = this.directionDelta(dir);
    if (!delta) {
      return null;
    }
    const toRow = fromRow + delta.row;
    const toCol = fromCol + delta.col;
    if (this.boardRows > 0 && this.boardCols > 0) {
      if (toRow < 0 || toRow >= this.boardRows || toCol < 0 || toCol >= this.boardCols) {
        return null;
      }
    }
    return { fromRow, fromCol, toRow, toCol, dir };
  }

  private directionDelta(dir: string): { row: number; col: number } | null {
    switch (dir) {
      case 'U':
        return { row: -1, col: 0 };
      case 'R':
        return { row: 0, col: 1 };
      case 'D':
        return { row: 1, col: 0 };
      case 'L':
        return { row: 0, col: -1 };
      default:
        return null;
    }
  }

  private resolveDirectionFromCoords(
    fromRow: number,
    fromCol: number,
    toRow: number,
    toCol: number
  ): 'up' | 'right' | 'down' | 'left' | null {
    const deltaRow = toRow - fromRow;
    const deltaCol = toCol - fromCol;
    if (deltaRow === -1 && deltaCol === 0) {
      return 'up';
    }
    if (deltaRow === 0 && deltaCol === 1) {
      return 'right';
    }
    if (deltaRow === 1 && deltaCol === 0) {
      return 'down';
    }
    if (deltaRow === 0 && deltaCol === -1) {
      return 'left';
    }
    return null;
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
    return { row, col };
  }

  private stripActionSuffix(move: string): string {
    return String(move ?? '').split(':')[0].trim();
  }

  private refreshCells(): void {
    const allowLegal = this.awaitingHumanMove && !this.suppressLegalHighlights;
    const legalFrom = allowLegal ? this.fromKeys : new Set<string>();
    const legalTo =
      allowLegal && this.selectedFromKey ? this.toKeysByFrom.get(this.selectedFromKey) ?? new Set<string>() : new Set<string>();
    this.cells = this.buildCells(
      this.blackBoard,
      this.whiteBoard,
      this.boardRows,
      this.boardCols,
      legalFrom,
      legalTo,
      this.selectedFromKey,
      this.illegalMoveKey,
      allowLegal
    );
    this.cdr.markForCheck();
  }
}
