import { ChangeDetectionStrategy, ChangeDetectorRef, Component, Input, OnDestroy } from '@angular/core';
import type { MatchResultSummary, StatusTone } from '@main/arena.constants';

type TicTacToeOwner = 0 | 1 | null;

type TicTacToeCell = {
  key: string;
  row: number;
  col: number;
  owner: 'p0' | 'p1' | null;
  legal: boolean;
  illegal: boolean;
  winning: boolean;
};

@Component({
  selector: 'arena-tic-tac-toe-gui',
  standalone: true,
  templateUrl: './arena-tic-tac-toe-gui.component.html',
  styleUrl: './arena-tic-tac-toe-gui.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ArenaTicTacToeGuiComponent implements OnDestroy {
  boardSize = 0;
  cells: TicTacToeCell[] = [];
  player0Count = 0;
  player1Count = 0;
  currentPlayer: number | null = null;
  matchBannerMessage: string | null = null;
  hasWinningLine = false;
  @Input() botA = 'Automaton A';
  @Input() botB = 'Automaton B';
  @Input() statusTone: StatusTone = 'idle';
  @Input() statusMessage = '';
  @Input() showHumanControls = false;
  private awaitingHuman = false;
  @Input() set awaitingHumanMove(value: boolean) {
    this.awaitingHuman = value;
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
  @Input() submitHumanMove?: (move: string) => void;
  illegalClickMessage: string | null = null;
  illegalClickToken = 0;
  private bannerTimer: number | null = null;
  private lastMatchStamp: number | null = null;
  private matchWinner: number | null = null;
  private matchIllegal = false;
  private currentLegalMoves: string[] = [];
  private legalMovesByKey = new Map<string, string>();
  private legalCells = new Set<string>();
  private illegalCell: { row: number; col: number } | null = null;
  private board: TicTacToeOwner[][] = [];
  private winningCells = new Set<string>();

  constructor(private readonly cdr: ChangeDetectorRef) {
    (window as any).GUI_COMPONENT = this;
  }

  @Input() set legalMoves(value: string[] | null) {
    this.currentLegalMoves = Array.isArray(value) ? value : [];
    this.legalMovesByKey.clear();
    this.legalCells.clear();
    for (const move of this.currentLegalMoves) {
      const parsed = this.parseMove(move);
      if (!parsed) {
        continue;
      }
      const key = `${parsed.row},${parsed.col}`;
      if (!this.legalMovesByKey.has(key)) {
        this.legalMovesByKey.set(key, move);
      }
      this.legalCells.add(key);
    }
    this.refreshCells();
  }

  get legalMoves(): string[] {
    return this.currentLegalMoves;
  }

  @Input() set illegalAction(value: string | null) {
    this.illegalCell = this.parseMove(value);
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
      this.player0Count = 0;
      this.player1Count = 0;
      this.currentPlayer = null;
      this.board = [];
      this.winningCells = new Set<string>();
      this.hasWinningLine = false;
      return;
    }
    this.board = parsed.board;
    this.boardSize = parsed.size;
    this.currentPlayer = parsed.player;
    this.player0Count = parsed.player0Count;
    this.player1Count = parsed.player1Count;
    this.updateWinningCells();
  }

  onCellClick(cell: TicTacToeCell): void {
    if (!this.awaitingHumanMove || !this.submitHumanMove) {
      return;
    }
    if (!cell.legal) {
      this.showIllegalClick('Select a legal square.');
      return;
    }
    const move = this.legalMovesByKey.get(cell.key);
    if (!move) {
      this.showIllegalClick('Illegal move.');
      return;
    }
    this.submitHumanMove(move);
  }

  ngOnDestroy(): void {
    this.clearBannerTimer();
  }

  private parseObservation(value: unknown | null): {
    board: TicTacToeOwner[][];
    size: number;
    player: number | null;
    player0Count: number;
    player1Count: number;
  } | null {
    if (!value || typeof value !== 'object') {
      return null;
    }
    const statePlayer = value as { state?: unknown; player?: unknown };
    const record = (statePlayer.state ?? value) as Record<string, unknown>;
    const boardValue = record['board'] ?? (value as { board?: unknown }).board;
    const board = this.parseBoard(boardValue);
    if (!board) {
      return null;
    }
    const player = this.resolvePlayer(record, statePlayer);
    const normalized = this.normalizeBoard(board, player);
    return {
      board: normalized.board,
      size: normalized.board.length,
      player,
      player0Count: normalized.player0Count,
      player1Count: normalized.player1Count
    };
  }

  private parseBoard(value: unknown): unknown[][] | null {
    if (!Array.isArray(value) || value.length === 0) {
      return null;
    }
    const rows: unknown[][] = [];
    let width = 0;
    for (const row of value) {
      if (!Array.isArray(row)) {
        return null;
      }
      if (!width) {
        width = row.length;
      }
      if (row.length !== width) {
        return null;
      }
      rows.push(row);
    }
    if (!width || rows.length !== width) {
      return null;
    }
    return rows;
  }

  private resolvePlayer(record: Record<string, unknown>, statePlayer: { player?: unknown }): number | null {
    const turnValue = record['turn'];
    if (typeof record['player'] === 'number' && Number.isFinite(record['player'])) {
      return record['player'] as number;
    }
    if (typeof turnValue === 'number' && Number.isFinite(turnValue)) {
      return turnValue;
    }
    if (typeof statePlayer.player === 'number' && Number.isFinite(statePlayer.player)) {
      return statePlayer.player;
    }
    if (typeof turnValue === 'string') {
      const trimmed = turnValue.trim().toLowerCase();
      if (trimmed === 'o') {
        return 0;
      }
      if (trimmed === 'x') {
        return 1;
      }
    }
    return null;
  }

  private normalizeBoard(
    board: unknown[][],
    currentPlayer: number | null
  ): { board: TicTacToeOwner[][]; player0Count: number; player1Count: number } {
    let player0Count = 0;
    let player1Count = 0;
    const normalized = board.map((row) =>
      row.map((cell) => {
        const owner = this.resolveOwner(cell, currentPlayer);
        if (owner === 0) {
          player0Count += 1;
        } else if (owner === 1) {
          player1Count += 1;
        }
        return owner;
      })
    );
    return { board: normalized, player0Count, player1Count };
  }

  private resolveOwner(cell: unknown, currentPlayer: number | null): TicTacToeOwner {
    if (cell === null || cell === undefined) {
      return null;
    }
    if (typeof cell === 'string') {
      const trimmed = cell.trim().toLowerCase();
      if (trimmed === 'o') {
        return 0;
      }
      if (trimmed === 'x') {
        return 1;
      }
    }
    const numeric = Number(cell);
    if (!Number.isFinite(numeric)) {
      return null;
    }
    if (numeric === 1) {
      return currentPlayer === 0 || currentPlayer === 1 ? currentPlayer : 0;
    }
    if (numeric === -1) {
      return currentPlayer === 0 || currentPlayer === 1 ? (currentPlayer === 0 ? 1 : 0) : 1;
    }
    return null;
  }

  private buildCells(
    board: TicTacToeOwner[][],
    legalCells: Set<string>,
    illegalCell: { row: number; col: number } | null
  ): TicTacToeCell[] {
    if (!board.length) {
      return [];
    }
    const cells: TicTacToeCell[] = [];
    for (let row = 0; row < board.length; row += 1) {
      for (let col = 0; col < board.length; col += 1) {
        const ownerIndex = board[row]?.[col] ?? null;
        const owner: TicTacToeCell['owner'] =
          ownerIndex === 0 ? 'p0' : ownerIndex === 1 ? 'p1' : null;
        const key = `${row},${col}`;
        const isIllegal = Boolean(illegalCell && illegalCell.row === row && illegalCell.col === col);
        cells.push({
          key,
          row,
          col,
          owner,
          legal: legalCells.has(key),
          illegal: isIllegal,
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

  private parseMove(value: string | null): { row: number; col: number } | null {
    if (!value) {
      return null;
    }
    const numbers = String(value).match(/-?\d+/g);
    if (!numbers || numbers.length < 2) {
      return null;
    }
    const row = Number(numbers[0]);
    const col = Number(numbers[1]);
    if (!Number.isFinite(row) || !Number.isFinite(col)) {
      return null;
    }
    return { row, col };
  }

  private updateWinningCells(): void {
    if (!this.board.length || this.matchWinner === null || this.matchIllegal) {
      this.winningCells = new Set<string>();
      this.hasWinningLine = false;
      this.refreshCells();
      return;
    }
    this.winningCells = this.findWinningCells(this.board, this.matchWinner);
    this.hasWinningLine = this.winningCells.size > 0;
    this.refreshCells();
  }

  private refreshCells(): void {
    const allowLegal = this.awaitingHumanMove;
    const legalCells = allowLegal ? this.legalCells : new Set<string>();
    this.cells = this.buildCells(this.board, legalCells, this.illegalCell);
    this.cdr.markForCheck();
  }

  private findWinningCells(board: TicTacToeOwner[][], winner: number): Set<string> {
    const size = board.length;
    if (!size) {
      return new Set<string>();
    }
    const winning = new Set<string>();
    const addLine = (coords: Array<[number, number]>): void => {
      for (const [row, col] of coords) {
        winning.add(`${row},${col}`);
      }
    };
    for (let row = 0; row < size; row += 1) {
      const coords: Array<[number, number]> = [];
      let allMatch = true;
      for (let col = 0; col < size; col += 1) {
        coords.push([row, col]);
        if (board[row]?.[col] !== winner) {
          allMatch = false;
        }
      }
      if (allMatch) {
        addLine(coords);
      }
    }
    for (let col = 0; col < size; col += 1) {
      const coords: Array<[number, number]> = [];
      let allMatch = true;
      for (let row = 0; row < size; row += 1) {
        coords.push([row, col]);
        if (board[row]?.[col] !== winner) {
          allMatch = false;
        }
      }
      if (allMatch) {
        addLine(coords);
      }
    }
    const mainDiag: Array<[number, number]> = [];
    let mainMatch = true;
    for (let i = 0; i < size; i += 1) {
      mainDiag.push([i, i]);
      if (board[i]?.[i] !== winner) {
        mainMatch = false;
      }
    }
    if (mainMatch) {
      addLine(mainDiag);
    }
    const antiDiag: Array<[number, number]> = [];
    let antiMatch = true;
    for (let i = 0; i < size; i += 1) {
      const col = size - 1 - i;
      antiDiag.push([i, col]);
      if (board[i]?.[col] !== winner) {
        antiMatch = false;
      }
    }
    if (antiMatch) {
      addLine(antiDiag);
    }
    return winning;
  }
}
