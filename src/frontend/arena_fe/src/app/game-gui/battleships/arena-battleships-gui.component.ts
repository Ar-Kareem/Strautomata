import { ChangeDetectionStrategy, ChangeDetectorRef, Component, Input, OnDestroy } from '@angular/core';
import { ArenaBannerComponent } from '../../components/arena-gui-helpers/arena-banner.component';
import { ArenaGuiAlertComponent } from '../../components/arena-gui-helpers/arena-gui-alert.component';
import { ArenaGuiLegendComponent } from '../../components/arena-gui-helpers/arena-gui-legend.component';
import { ArenaGuiEmptyComponent } from '../../components/arena-gui-helpers/arena-gui-empty.component';
import type { MatchResultSummary, StatusTone } from '@main/arena.constants';
import { kbdFile, kbdRankLetter } from '../../components/arena-gui-helpers/arena-kbd-keys';

type BattleshipsCell = {
  key: string;
  row: number;
  col: number;
  status: 'unknown' | 'miss' | 'hit';
  legal: boolean;
  illegal: boolean;
};

type BattleshipsBoard = number[][];

type BattleshipsStats = {
  shipsRemaining: number[] | null;
  shipsSunkCells: number[] | null;
  moveCount: number | null;
};

type BattleshipsBoardView = {
  player: number;
  size: number;
  cells: BattleshipsCell[];
  hitCount: number;
  missCount: number;
  unknownCount: number;
  active: boolean;
  isWinner: boolean;
  isLoser: boolean;
};

@Component({
  selector: 'arena-battleships-gui',
  standalone: true,
  templateUrl: './arena-battleships-gui.component.html',
  styleUrl: './arena-battleships-gui.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    ArenaBannerComponent,
    ArenaGuiAlertComponent,
    ArenaGuiLegendComponent,
    ArenaGuiEmptyComponent
  ]
})
export class ArenaBattleshipsGuiComponent implements OnDestroy {
  boardViews: BattleshipsBoardView[] = [];
  currentPlayer: number | null = null;
  turn: number | null = null;
  stats: BattleshipsStats | null = null;
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
    return 'Unknown';
  }
  private awaitingHuman = false;
  @Input() set awaitingHumanMove(value: boolean) {
    this.awaitingHuman = value;
  }
  get awaitingHumanMove(): boolean {
    return this.awaitingHuman;
  }

  get hiddenAiPlayer(): number | null {
    const isHumanA = this.botA === 'Human';
    const isHumanB = this.botB === 'Human';
    if (isHumanA === isHumanB) {
      return null;
    }
    return isHumanA ? 1 : 0;
  }

  isAiBoardHidden(player: number): boolean {
    return this.hiddenAiPlayer === player && !this.matchFinished;
  }

  @Input() submitHumanMove?: (move: string) => void;
  private bannerTimer: number | null = null;
  private lastMatchStamp: number | null = null;
  private matchWinner: number | null = null;
  private matchFinished = false;
  private currentLegalMoves: string[] = [];
  private legalMovesByKey = new Map<string, string>();
  private illegalMove: [number, number] | null = null;
  private boardByPlayer: Array<BattleshipsBoard | null> = [null, null];
  illegalClickMessage: string | null = null;
  illegalClickToken = 0;

  /** column picked by keyboard, whose cells then get row hints */
  kbdColumn: number | null = null;

  @Input() set legalMoves(value: string[] | null) {
    this.currentLegalMoves = Array.isArray(value) ? value : [];
    this.kbdColumn = null;
    this.legalMovesByKey.clear();
    for (const move of this.currentLegalMoves) {
      const point = this.parseMovePoint(move);
      if (!point) {
        continue;
      }
      const key = `${point[0]},${point[1]}`;
      if (!this.legalMovesByKey.has(key)) {
        this.legalMovesByKey.set(key, move);
      }
    }
    this.refreshBoardViews();
  }

  get legalMoves(): string[] {
    return this.currentLegalMoves;
  }

  constructor(private readonly cdr: ChangeDetectorRef) {
    (window as any).GUI_COMPONENT = this;
  }

  @Input() set illegalAction(value: string | null) {
    this.illegalMove = this.parseIllegalAction(value);
    this.refreshBoardViews();
  }

  @Input() set matchResult(value: MatchResultSummary | null) {
    if (!value) {
      this.lastMatchStamp = null;
      this.clearBanner();
      this.matchWinner = null;
      this.matchFinished = false;
      this.refreshBoardViews();
      return;
    }
    if (this.lastMatchStamp === value.finishedAt) {
      return;
    }
    this.lastMatchStamp = value.finishedAt;
    this.matchFinished = true;
    if (value.illegal) {
      this.clearBanner();
      this.matchWinner = null;
      this.refreshBoardViews();
      return;
    }
    this.matchWinner = value.winner ?? null;
    this.matchBannerMessage = this.resolveResultMessage(value.winner);
    this.resetBannerTimer();
    this.refreshBoardViews();
  }

  @Input() set observation(value: unknown | null) {
    const parsed = this.parseObservation(value);
    if (!parsed) {
      this.boardViews = [];
      this.boardByPlayer = [null, null];
      this.currentPlayer = null;
      this.turn = null;
      this.stats = null;
      return;
    }
    this.currentPlayer = parsed.player;
    this.turn = parsed.turn;
    this.stats = parsed.stats;
    this.boardByPlayer = [parsed.boards[0], parsed.boards[1]];
    this.refreshBoardViews();
  }

  private kbdTarget(view: BattleshipsBoardView, cell: BattleshipsCell): boolean {
    return this.awaitingHumanMove && view.active && cell.status === 'unknown' && cell.legal;
  }

  /** keyboard hint on a target of the active board: its row letter (a at the bottom), on the picked column only */
  kbdLabel(view: BattleshipsBoardView, cell: BattleshipsCell): string | null {
    return this.kbdTarget(view, cell) && cell.col === this.kbdColumn ? kbdRankLetter(view.size - 1 - cell.row) : null;
  }

  /** keyboard hint on a column's top cell of the active board: its letter while no column is picked */
  kbdColumnLabel(view: BattleshipsBoardView, col: number): string | null {
    if (this.kbdColumn !== null || !view.cells.some((cell) => cell.col === col && this.kbdTarget(view, cell))) {
      return null;
    }
    return kbdFile(col);
  }

  /** picking the picked column again goes back to the column pick */
  onKbdColumn(col: number): void {
    this.kbdColumn = this.kbdColumn === col ? null : col;
    this.cdr.markForCheck();
  }

  onCellClick(player: number, cell: BattleshipsCell): void {
    if (!this.awaitingHumanMove || !this.submitHumanMove) {
      return;
    }
    if (this.currentPlayer !== player) {
      return;
    }
    if (cell.status !== 'unknown') {
      this.showIllegalClick('Location already targeted.');
      return;
    }
    if (!cell.legal) {
      this.showIllegalClick('Select a legal target.');
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
    boards: [BattleshipsBoard, BattleshipsBoard];
    player: number | null;
    turn: number | null;
    stats: BattleshipsStats | null;
  } | null {
    if (!value || typeof value !== 'object') {
      return null;
    }
    const statePlayer = value as { state?: unknown; player?: unknown };
    const record = (statePlayer.state ?? value) as Record<string, unknown>;
    if (!record || typeof record !== 'object') {
      return null;
    }
    const blackBoard = this.parseBoard(record['black']);
    const whiteBoard = this.parseBoard(record['white']);
    if (!blackBoard || !whiteBoard) {
      return null;
    }
    const player =
      typeof statePlayer.player === 'number'
        ? statePlayer.player
        : typeof record['turn'] === 'number'
          ? (record['turn'] as number)
          : null;
    const turn = typeof record['turn'] === 'number' ? (record['turn'] as number) : null;
    const stats = this.parseStats(record['final_stats'] ?? record['stats']);
    return {
      boards: [whiteBoard, blackBoard],
      player,
      turn,
      stats
    };
  }

  private parseStats(value: unknown): BattleshipsStats | null {
    if (!value || typeof value !== 'object') {
      return null;
    }
    const record = value as {
      ships_remaining?: unknown;
      ships_sunk_cells?: unknown;
      move_count?: unknown;
    };
    const shipsRemaining = Array.isArray(record.ships_remaining)
      ? record.ships_remaining.map((entry) => Number(entry)).filter((entry) => Number.isFinite(entry))
      : null;
    const shipsSunkCells = Array.isArray(record.ships_sunk_cells)
      ? record.ships_sunk_cells.map((entry) => Number(entry)).filter((entry) => Number.isFinite(entry))
      : null;
    const moveCount = typeof record.move_count === 'number' ? record.move_count : null;
    return {
      shipsRemaining: shipsRemaining && shipsRemaining.length > 0 ? shipsRemaining : null,
      shipsSunkCells: shipsSunkCells && shipsSunkCells.length > 0 ? shipsSunkCells : null,
      moveCount
    };
  }

  private parseBoard(value: unknown): BattleshipsBoard | null {
    if (!Array.isArray(value) || value.length === 0) {
      return null;
    }
    if (!Array.isArray(value[0])) {
      const flat = value.map((entry) => this.parseCell(entry));
      const size = Math.sqrt(flat.length);
      if (!Number.isInteger(size) || size <= 0) {
        return null;
      }
      const rows: BattleshipsBoard = [];
      for (let row = 0; row < size; row += 1) {
        rows.push(flat.slice(row * size, row * size + size));
      }
      return rows;
    }
    const rows: BattleshipsBoard = [];
    let width = 0;
    for (const row of value) {
      if (!Array.isArray(row)) {
        return null;
      }
      const parsed = row.map((entry) => this.parseCell(entry));
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

  private parseCell(value: unknown): number {
    if (value === null || value === undefined) {
      return 0;
    }
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) {
      return 0;
    }
    if (numeric === 1) {
      return 1;
    }
    if (numeric === -1) {
      return -1;
    }
    return 0;
  }

  private countBoard(board: BattleshipsBoard): {
    hitCount: number;
    missCount: number;
    unknownCount: number;
  } {
    let hitCount = 0;
    let missCount = 0;
    let unknownCount = 0;
    for (const row of board) {
      for (const value of row) {
        if (value === 1) {
          hitCount += 1;
        } else if (value === -1) {
          missCount += 1;
        } else {
          unknownCount += 1;
        }
      }
    }
    return { hitCount, missCount, unknownCount };
  }

  private buildCellsFromBoard(
    board: BattleshipsBoard,
    legalMovesByKey: Map<string, string>,
    illegalMove: [number, number] | null
  ): BattleshipsCell[] {
    const cells: BattleshipsCell[] = [];
    for (let row = 0; row < board.length; row += 1) {
      for (let col = 0; col < board[row].length; col += 1) {
        const value = board[row][col];
        let status: BattleshipsCell['status'] = 'unknown';
        if (value === 1) {
          status = 'hit';
        } else if (value === -1) {
          status = 'miss';
        }
        const key = `${row},${col}`;
        cells.push({
          key,
          row,
          col,
          status,
          legal: legalMovesByKey.has(key),
          illegal: Boolean(illegalMove && illegalMove[0] === row && illegalMove[1] === col)
        });
      }
    }
    return cells;
  }
  
  private refreshBoardViews(): void {
    const views: BattleshipsBoardView[] = [];
    const players = [0, 1];
    for (const player of players) {
      const board = this.boardByPlayer[player];
      const size = board ? board.length : 0;
      const counts = board ? this.countBoard(board) : { hitCount: 0, missCount: 0, unknownCount: 0 };
      const active = player === this.currentPlayer;
      const hasWinner = this.matchWinner !== null;
      const isWinner = hasWinner && player === this.matchWinner;
      const isLoser = hasWinner && player !== this.matchWinner;
      const cells = board
        ? this.buildCellsFromBoard(
            board,
            active ? this.legalMovesByKey : new Map<string, string>(),
            active ? this.illegalMove : null
          )
        : [];
      views.push({
        player,
        size,
        cells,
        hitCount: counts.hitCount,
        missCount: counts.missCount,
        unknownCount: counts.unknownCount,
        active,
        isWinner,
        isLoser
      });
    }
    this.boardViews = views;
    this.cdr.markForCheck();
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
      this.cdr.detectChanges();
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

  private parseIllegalAction(value: string | null): [number, number] | null {
    if (!value) {
      return null;
    }
    const trimmed = String(value).trim();
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
    return null;
  }

  private parseMovePoint(value: string): [number, number] | null {
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
    return null;
  }
}
