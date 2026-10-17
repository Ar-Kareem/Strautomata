import { ChangeDetectionStrategy, ChangeDetectorRef, Component, Input, OnDestroy } from '@angular/core';
import type { MatchResultSummary, StatusTone } from '@main/arena.constants';

type Connect4Cell = {
  key: string;
  row: number;
  col: number;
  owner: 'p0' | 'p1' | null;
  legal: boolean;
  illegal: boolean;
  winning: boolean;
};

@Component({
  selector: 'arena-connect4-gui',
  standalone: true,
  templateUrl: './arena-connect4-gui.component.html',
  styleUrl: './arena-connect4-gui.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ArenaConnect4GuiComponent implements OnDestroy {
  boardRows = 0;
  boardCols = 0;
  cells: Connect4Cell[] = [];
  player0Count = 0;
  player1Count = 0;
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
      this.hoveredColumn = null;
    } else if (this.pointerColumn !== null) {
      this.hoveredColumn = this.pointerColumn;
    }
    this.refreshCells();
  }
  get awaitingHumanMove(): boolean {
    return this.awaitingHuman;
  }
  @Input() submitHumanMove?: (move: string) => void;
  @Input() set illegalAction(value: string | null) {
    this.illegalColumn = this.parseIllegalAction(value);
    this.cells = this.buildCells(this.board, this.legalColumns, this.illegalColumn);
  }
  private bannerTimer: number | null = null;
  private lastMatchStamp: number | null = null;
  private matchWinner: number | null = null;
  private matchIllegal = false;
  hasWinningLine = false;
  private currentLegalMoves: string[] = [];
  private legalMovesByColumn = new Map<number, string>();
  private legalColumns = new Set<number>();
  private illegalColumn: number | null = null;
  private board: number[][] = [];
  private winningCells = new Set<string>();
  private pointerColumn: number | null = null;
  hoveredColumn: number | null = null;
  illegalClickMessage: string | null = null;
  illegalClickToken = 0;

  @Input() set legalMoves(value: string[] | null) {
    this.currentLegalMoves = Array.isArray(value) ? value : [];
    this.legalMovesByColumn.clear();
    this.legalColumns.clear();
    for (const move of this.currentLegalMoves) {
      const column = this.parseMoveColumn(move);
      if (column === null) {
        continue;
      }
      if (!this.legalMovesByColumn.has(column)) {
        this.legalMovesByColumn.set(column, move);
      }
      this.legalColumns.add(column);
    }
    this.refreshCells();
  }

  get legalMoves(): string[] {
    return this.currentLegalMoves;
  }

  constructor(private readonly cdr: ChangeDetectorRef) {
    (window as any).GUI_COMPONENT = this;
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
      this.boardRows = 0;
      this.boardCols = 0;
      this.cells = [];
      this.player0Count = 0;
      this.player1Count = 0;
      this.currentPlayer = null;
      this.board = [];
      this.winningCells = new Set<string>();
      this.hasWinningLine = false;
      return;
    }
    this.board = parsed.board;
    this.boardRows = parsed.rows;
    this.boardCols = parsed.cols;
    this.currentPlayer = parsed.player;
    this.player0Count = parsed.player0Count;
    this.player1Count = parsed.player1Count;
    this.updateWinningCells();
  }

  onCellClick(cell: Connect4Cell): void {
    if (!this.awaitingHumanMove || !this.submitHumanMove) {
      return;
    }
    if (!cell.legal) {
      this.showIllegalClick('Select a legal column.');
      return;
    }
    const move = this.legalMovesByColumn.get(cell.col);
    if (!move) {
      this.showIllegalClick('Illegal move.');
      return;
    }
    this.submitHumanMove(move);
  }

  onCellEnter(cell: Connect4Cell): void {
    this.pointerColumn = cell.col;
    if (!this.awaitingHumanMove) {
      return;
    }
    this.hoveredColumn = cell.col;
  }

  onCellLeave(cell: Connect4Cell): void {
    if (this.pointerColumn === cell.col) {
      this.pointerColumn = null;
    }
    if (!this.awaitingHumanMove) {
      return;
    }
    if (this.hoveredColumn === cell.col) {
      this.hoveredColumn = null;
    }
  }

  ngOnDestroy(): void {
    this.clearBannerTimer();
  }

  private parseObservation(value: unknown | null): {
    board: number[][];
    rows: number;
    cols: number;
    player: number | null;
    player0Count: number;
    player1Count: number;
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
          : null;
    const rows = board.length;
    const cols = board[0]?.length ?? 0;
    const counts = this.countBoard(board);
    return {
      board,
      rows,
      cols,
      player,
      player0Count: counts.player0Count,
      player1Count: counts.player1Count
    };
  }

  private parseBoard(value: unknown): number[][] | null {
    if (!Array.isArray(value) || value.length === 0) {
      return null;
    }
    const rows: number[][] = [];
    let width = 0;
    for (const row of value) {
      if (!Array.isArray(row)) {
        return null;
      }
      const parsed = row.map((entry) => (Number.isFinite(Number(entry)) ? Number(entry) : 0));
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

  private countBoard(board: number[][]): { player0Count: number; player1Count: number } {
    let player0Count = 0;
    let player1Count = 0;
    for (const row of board) {
      for (const value of row) {
        const playerIndex = this.mapValueToPlayer(value);
        if (playerIndex === 0) {
          player0Count += 1;
        } else if (playerIndex === 1) {
          player1Count += 1;
        }
      }
    }
    return { player0Count, player1Count };
  }

  private buildCells(
    board: number[][],
    legalColumns: Set<number>,
    illegalColumn: number | null
  ): Connect4Cell[] {
    if (board.length === 0) {
      return [];
    }
    const allowLegal = this.awaitingHumanMove;
    const cells: Connect4Cell[] = [];
    for (let row = 0; row < board.length; row += 1) {
      for (let col = 0; col < board[row].length; col += 1) {
        const value = board[row][col];
        const playerIndex = this.mapValueToPlayer(value);
        const owner: Connect4Cell['owner'] =
          playerIndex === 0 ? 'p0' : playerIndex === 1 ? 'p1' : null;
        const key = `${row},${col}`;
        cells.push({
          key,
          row,
          col,
          owner,
          legal: allowLegal && legalColumns.has(col),
          illegal: illegalColumn === col,
          winning: this.winningCells.has(key)
        });
      }
    }
    return cells;
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

  private parseIllegalAction(value: string | null): number | null {
    if (!value) {
      return null;
    }
    return this.parseMoveColumn(value);
  }

  private parseMoveColumn(value: string): number | null {
    const trimmed = String(value ?? '').trim();
    if (!trimmed) {
      return null;
    }
    const labeled = trimmed.match(/col\s*[:=]\s*(-?\d+)/i);
    if (labeled) {
      const col = Number(labeled[1]);
      if (Number.isFinite(col)) {
        return col;
      }
    }
    if (/^-?\d+$/.test(trimmed)) {
      const col = Number(trimmed);
      if (Number.isFinite(col)) {
        return col;
      }
    }
    const numbers = trimmed.match(/-?\d+/g);
    if (numbers && numbers.length >= 1) {
      const col = Number(numbers[numbers.length - 1]);
      if (Number.isFinite(col)) {
        return col;
      }
    }
    return null;
  }

  private mapValueToPlayer(value: number): number | null {
    if (value === 1) {
      return 0;
    }
    if (value === -1) {
      return 1;
    }
    return null;
  }

  private updateWinningCells(): void {
    if (!this.board.length || this.matchWinner === null || this.matchIllegal) {
      this.winningCells = new Set<string>();
      this.refreshCells();
      return;
    }
    this.winningCells = this.findWinningCells(this.board, this.currentPlayer, this.matchWinner);
    this.hasWinningLine = this.winningCells.size > 0;
    this.refreshCells();
  }

  private refreshCells(): void {
    this.cells = this.buildCells(this.board, this.legalColumns, this.illegalColumn);
  }

  private findWinningCells(
    board: number[][],
    currentPlayer: number | null,
    winner: number
  ): Set<string> {
    if (board.length === 0) {
      return new Set<string>();
    }
    const rows = board.length;
    const cols = board[0]?.length ?? 0;
    const directions = [
      { dr: 0, dc: 1 },
      { dr: 1, dc: 0 },
      { dr: 1, dc: 1 },
      { dr: 1, dc: -1 }
    ];
    const ownerAt = (row: number, col: number): number | null =>
      this.mapValueToPlayer(board[row][col]);

    for (let row = 0; row < rows; row += 1) {
      for (let col = 0; col < cols; col += 1) {
        if (ownerAt(row, col) !== winner) {
          continue;
        }
        for (const { dr, dc } of directions) {
          const coords = [[row, col]] as Array<[number, number]>;
          for (let i = 1; i < 4; i += 1) {
            const nextRow = row + dr * i;
            const nextCol = col + dc * i;
            if (nextRow < 0 || nextRow >= rows || nextCol < 0 || nextCol >= cols) {
              break;
            }
            if (ownerAt(nextRow, nextCol) !== winner) {
              break;
            }
            coords.push([nextRow, nextCol]);
          }
          if (coords.length === 4) {
            return new Set(coords.map(([r, c]) => `${r},${c}`));
          }
        }
      }
    }
    return new Set<string>();
  }
}
