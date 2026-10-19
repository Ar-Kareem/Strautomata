import { ChangeDetectionStrategy, ChangeDetectorRef, Component, Input } from '@angular/core';
import type { MatchResultSummary, StatusTone } from '@main/arena.constants';
import { kbdSquareFromTop } from '../../components/arena-gui-helpers/arena-kbd-keys';

type LoaCell = {
  key: string;
  row: number;
  col: number;
  owner: 'p0' | 'p1' | null;
  legalFrom: boolean;
  legalTo: boolean;
  illegal: boolean;
  selected: boolean;
  winning: boolean;
};

type ParsedMove = {
  fromRow: number;
  fromCol: number;
  toRow: number;
  toCol: number;
};

@Component({
  selector: 'arena-lines-of-action-gui',
  standalone: true,
  templateUrl: './arena-lines-of-action-gui.component.html',
  styleUrl: './arena-lines-of-action-gui.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ArenaLinesOfActionGuiComponent {
  boardRows = 0;
  boardCols = 0;
  cells: LoaCell[] = [];
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
      this.selectedFromKey = null;
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
  private board: number[][] = [];
  illegalClickMessage: string | null = null;
  illegalClickToken = 0;
  selectedFromKey: string | null = null;

  @Input() set legalMoves(value: string[] | null) {
    this.currentLegalMoves = Array.isArray(value) ? value : [];
    this.movesByKey.clear();
    this.fromKeys.clear();
    this.toKeysByFrom.clear();
    this.selectedFromKey = null;
    for (const move of this.currentLegalMoves) {
      const parsed = this.parseMove(move);
      if (!parsed) {
        continue;
      }
      const fromKey = this.coordKey(parsed.fromRow, parsed.fromCol);
      const toKey = this.coordKey(parsed.toRow, parsed.toCol);
      const moveKey = `${fromKey}|${toKey}`;
      this.movesByKey.set(moveKey, move);
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

  constructor(private readonly cdr: ChangeDetectorRef) {
    (window as any).GUI_COMPONENT = this;
  }

  @Input() set illegalAction(value: string | null) {
    const parsed = value ? this.parseMove(value) : null;
    if (parsed) {
      this.illegalMoveKey = this.coordKey(parsed.toRow, parsed.toCol);
    } else {
      this.illegalMoveKey = null;
    }
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
      this.boardRows = 0;
      this.boardCols = 0;
      this.cells = [];
      this.player0Count = 0;
      this.player1Count = 0;
      this.currentPlayer = null;
      this.board = [];
      return;
    }
    this.board = parsed.board;
    this.boardRows = parsed.rows;
    this.boardCols = parsed.cols;
    const nextPlayer =
      parsed.player !== null && parsed.player >= 0 ? parsed.player : this.currentPlayer;
    this.currentPlayer = nextPlayer;
    const counts = this.countBoard(this.board);
    this.player0Count = counts.player0Count;
    this.player1Count = counts.player1Count;
    this.refreshCells();
  }

  /** keyboard hint: movable pieces, then the selected piece's destinations */
  kbdLabel(cell: LoaCell): string | null {
    const target = this.selectedFromKey ? cell.legalTo : cell.legalFrom;
    return target ? kbdSquareFromTop(cell.col, cell.row, this.boardRows) : null;
  }

  onCellClick(cell: LoaCell): void {
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
    this.refreshCells();
    this.submitHumanMove(move);
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
          : null;
    const rows = board.length;
    const cols = board[0]?.length ?? 0;
    return {
      board,
      rows,
      cols,
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

  private refreshCells(): void {
    this.cells = this.buildCells(
      this.board,
      this.fromKeys,
      this.selectedFromKey,
      this.illegalMoveKey,
      this.awaitingHumanMove
    );
    this.cdr.markForCheck();
  }

  private buildCells(
    board: number[][],
    legalFrom: Set<string>,
    selectedFrom: string | null,
    illegalKey: string | null,
    allowLegal: boolean
  ): LoaCell[] {
    if (board.length === 0) {
      return [];
    }
    const cells: LoaCell[] = [];
    const legalTargets =
      selectedFrom && allowLegal ? this.toKeysByFrom.get(selectedFrom) ?? new Set<string>() : new Set<string>();
    for (let row = 0; row < board.length; row += 1) {
      for (let col = 0; col < board[row].length; col += 1) {
        const value = board[row][col];
        const playerIndex = this.mapValueToPlayer(value);
        const owner: LoaCell['owner'] = value === 1 ? 'p1' : value === -1 ? 'p0' : null;
        const key = this.coordKey(row, col);
        cells.push({
          key,
          row,
          col,
          owner,
          legalFrom: allowLegal && legalFrom.has(key),
          legalTo: allowLegal && Boolean(selectedFrom && legalTargets.has(key)),
          illegal: Boolean(illegalKey && illegalKey === key),
          selected: selectedFrom === key,
          winning: this.matchWinner !== null && playerIndex === this.matchWinner
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

  private parseMove(value: string): ParsedMove | null {
    const trimmed = String(value ?? '').trim();
    if (!trimmed) {
      return null;
    }
    const coordMatch = trimmed.match(/(-?\d+)\s*,\s*(-?\d+)\s*:\s*(-?\d+)\s*,\s*(-?\d+)/);
    if (coordMatch) {
      const fromRow = Number(coordMatch[1]);
      const fromCol = Number(coordMatch[2]);
      const toRow = Number(coordMatch[3]);
      const toCol = Number(coordMatch[4]);
      if ([fromRow, fromCol, toRow, toCol].every((entry) => Number.isFinite(entry))) {
        return { fromRow, fromCol, toRow, toCol };
      }
    }
    const algebraic = trimmed.match(/[a-h][1-8]/gi);
    if (!algebraic || algebraic.length < 2) {
      return null;
    }
    const from = algebraic[0].toLowerCase();
    const to = algebraic[1].toLowerCase();
    const fromCol = from.charCodeAt(0) - 97;
    const fromRow = Number(from[1]) - 1;
    const toCol = to.charCodeAt(0) - 97;
    const toRow = Number(to[1]) - 1;
    if ([fromRow, fromCol, toRow, toCol].every((entry) => Number.isFinite(entry))) {
      return { fromRow, fromCol, toRow, toCol };
    }
    return null;
  }

  private toHumanMove(move: ParsedMove): string {
    return `${move.fromRow},${move.fromCol}:${move.toRow},${move.toCol}`;
  }

  private coordKey(row: number, col: number): string {
    return `${row},${col}`;
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
}
