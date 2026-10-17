import { ChangeDetectionStrategy, ChangeDetectorRef, Component, Input, OnDestroy } from '@angular/core';
import type { MatchResultSummary, StatusTone } from '@main/arena.constants';

type TicTacToe3dOwner = 0 | 1 | null;

type TicTacToe3dCell = {
  key: string;
  layer: number;
  row: number;
  col: number;
  owner: 'p0' | 'p1' | null;
  legal: boolean;
  illegal: boolean;
  winning: boolean;
};

type LayerView = {
  layer: number;
  cells: TicTacToe3dCell[];
  pieceCount: number;
  legalCount: number;
};

@Component({
  selector: 'arena-tic-tac-toe-3d-gui',
  standalone: true,
  templateUrl: './arena-tic-tac-toe-3d-gui.component.html',
  styleUrl: './arena-tic-tac-toe-3d-gui.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ArenaTicTacToe3dGuiComponent implements OnDestroy {
  boardSize = 0;
  layerViews: LayerView[] = [];
  activeLayer = 0;
  layerSwapAnimating = false;
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
  get activeLayerView(): LayerView | null {
    return (
      this.layerViews.find((layerView) => layerView.layer === this.activeLayer) ??
      this.layerViews[0] ??
      null
    );
  }
  illegalClickMessage: string | null = null;
  illegalClickToken = 0;
  private bannerTimer: number | null = null;
  private layerSwapFrame: number | null = null;
  private layerSwapTimer: number | null = null;
  private lastMatchStamp: number | null = null;
  private matchWinner: number | null = null;
  private matchIllegal = false;
  private currentLegalMoves: string[] = [];
  private legalMovesByKey = new Map<string, string>();
  private legalCells = new Set<string>();
  private illegalCell: { layer: number; row: number; col: number } | null = null;
  private board: TicTacToe3dOwner[][][] = [];
  private winningCells = new Set<string>();
  private hasRenderedBoard = false;

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
      const key = this.cellKey(parsed.layer, parsed.row, parsed.col);
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
      this.clearLayerSwapAnimation();
      this.boardSize = 0;
      this.layerViews = [];
      this.activeLayer = 0;
      this.layerSwapAnimating = false;
      this.player0Count = 0;
      this.player1Count = 0;
      this.currentPlayer = null;
      this.board = [];
      this.winningCells = new Set<string>();
      this.hasWinningLine = false;
      this.hasRenderedBoard = false;
      this.cdr.markForCheck();
      return;
    }
    const changedLayer = this.detectChangedLayer(this.board, parsed.board);
    const hadRenderedBoard = this.hasRenderedBoard;
    this.board = parsed.board;
    this.boardSize = parsed.size;
    this.currentPlayer = parsed.player;
    this.player0Count = parsed.player0Count;
    this.player1Count = parsed.player1Count;
    if (changedLayer !== null) {
      this.setActiveLayer(changedLayer, hadRenderedBoard);
    } else if (this.activeLayer < 0 || this.activeLayer >= this.boardSize) {
      this.setActiveLayer(0, false);
    }
    this.hasRenderedBoard = this.boardSize > 0;
    this.updateWinningCells();
  }

  onLayerSelect(layer: number): void {
    if (layer < 0 || layer >= this.boardSize) {
      return;
    }
    this.setActiveLayer(layer, true);
    this.cdr.markForCheck();
  }

  onCellClick(cell: TicTacToe3dCell): void {
    if (!this.awaitingHumanMove || !this.submitHumanMove) {
      return;
    }
    if (!cell.legal) {
      this.showIllegalClick('Select a legal cube.');
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
    this.clearLayerSwapAnimation();
  }

  private parseObservation(value: unknown | null): {
    board: TicTacToe3dOwner[][][];
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
    const counts = this.countOwners(board);
    return {
      board,
      size: board.length,
      player,
      player0Count: counts.player0Count,
      player1Count: counts.player1Count
    };
  }

  private parseBoard(value: unknown): TicTacToe3dOwner[][][] | null {
    const layers = this.readArray(value);
    if (!layers || layers.length === 0) {
      return null;
    }
    const size = layers.length;
    const board: TicTacToe3dOwner[][][] = [];
    for (const layerRaw of layers) {
      const rows = this.readArray(layerRaw);
      if (!rows || rows.length !== size) {
        return null;
      }
      const parsedRows: TicTacToe3dOwner[][] = [];
      for (const rowRaw of rows) {
        const row = this.readArray(rowRaw);
        if (!row || row.length !== size) {
          return null;
        }
        parsedRows.push(row.map((cell) => this.resolveOwner(cell)));
      }
      board.push(parsedRows);
    }
    return board;
  }

  private readArray(value: unknown): unknown[] | null {
    if (Array.isArray(value) || ArrayBuffer.isView(value)) {
      return Array.from(value as Iterable<unknown>);
    }
    return null;
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

  private resolveOwner(cell: unknown): TicTacToe3dOwner {
    if (cell === null || cell === undefined) {
      return null;
    }
    if (typeof cell === 'string') {
      const trimmed = cell.trim().toLowerCase();
      if (trimmed === 'o' || trimmed === 'white' || trimmed === 'w' || trimmed === 'p0') {
        return 0;
      }
      if (trimmed === 'x' || trimmed === 'black' || trimmed === 'b' || trimmed === 'p1') {
        return 1;
      }
    }
    const numeric = Number(cell);
    if (!Number.isFinite(numeric)) {
      return null;
    }
    if (numeric === 1) {
      return 0;
    }
    if (numeric === -1 || numeric === 2) {
      return 1;
    }
    return null;
  }

  private countOwners(board: TicTacToe3dOwner[][][]): { player0Count: number; player1Count: number } {
    let player0Count = 0;
    let player1Count = 0;
    for (const layer of board) {
      for (const row of layer) {
        for (const owner of row) {
          if (owner === 0) {
            player0Count += 1;
          } else if (owner === 1) {
            player1Count += 1;
          }
        }
      }
    }
    return { player0Count, player1Count };
  }

  private buildLayerViews(
    board: TicTacToe3dOwner[][][],
    legalCells: Set<string>,
    illegalCell: { layer: number; row: number; col: number } | null
  ): LayerView[] {
    if (!board.length) {
      return [];
    }
    const size = board.length;
    const layers = Array.from({ length: size }, (_, index) => index);
    const layerViews: LayerView[] = [];
    for (const layer of layers) {
      const cells: TicTacToe3dCell[] = [];
      let pieceCount = 0;
      let legalCount = 0;
      for (let row = 0; row < size; row += 1) {
        for (let col = 0; col < size; col += 1) {
          const ownerIndex = board[layer]?.[row]?.[col] ?? null;
          const owner: TicTacToe3dCell['owner'] =
            ownerIndex === 0 ? 'p0' : ownerIndex === 1 ? 'p1' : null;
          if (owner !== null) {
            pieceCount += 1;
          }
          const key = this.cellKey(layer, row, col);
          const legal = legalCells.has(key);
          if (legal) {
            legalCount += 1;
          }
          const isIllegal = Boolean(
            illegalCell && illegalCell.layer === layer && illegalCell.row === row && illegalCell.col === col
          );
          cells.push({
            key,
            layer,
            row,
            col,
            owner,
            legal,
            illegal: isIllegal,
            winning: this.winningCells.has(key)
          });
        }
      }
      layerViews.push({
        layer,
        cells,
        pieceCount,
        legalCount
      });
    }
    return layerViews;
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

  private parseMove(value: string | null): { layer: number; row: number; col: number } | null {
    if (!value) {
      return null;
    }
    const numbers = String(value).match(/-?\d+/g);
    if (!numbers || numbers.length < 3) {
      return null;
    }
    const layer = Number(numbers[0]);
    const row = Number(numbers[1]);
    const col = Number(numbers[2]);
    if (!Number.isFinite(layer) || !Number.isFinite(row) || !Number.isFinite(col)) {
      return null;
    }
    return { layer, row, col };
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
    this.layerViews = this.buildLayerViews(this.board, legalCells, this.illegalCell);
    this.syncActiveLayer(allowLegal);
    this.cdr.markForCheck();
  }

  private syncActiveLayer(allowLegal: boolean): void {
    if (this.boardSize <= 0) {
      this.activeLayer = 0;
      return;
    }
    if (this.activeLayer < 0 || this.activeLayer >= this.boardSize) {
      this.activeLayer = 0;
    }
    if (!allowLegal || this.legalCells.size === 0) {
      return;
    }
    if (this.layerViews.some((layer) => layer.layer === this.activeLayer && layer.legalCount > 0)) {
      return;
    }
    const preferred = this.layerViews.find((layer) => layer.legalCount > 0);
    if (preferred) {
      this.setActiveLayer(preferred.layer, true);
    }
  }

  private setActiveLayer(layer: number, animate: boolean): void {
    if (layer < 0 || layer >= this.boardSize) {
      return;
    }
    if (this.activeLayer === layer) {
      return;
    }
    this.activeLayer = layer;
    if (animate) {
      this.triggerLayerSwapAnimation();
    }
  }

  private triggerLayerSwapAnimation(): void {
    this.layerSwapAnimating = false;
    if (this.layerSwapFrame !== null) {
      window.cancelAnimationFrame(this.layerSwapFrame);
      this.layerSwapFrame = null;
    }
    if (this.layerSwapTimer !== null) {
      window.clearTimeout(this.layerSwapTimer);
      this.layerSwapTimer = null;
    }
    this.layerSwapFrame = window.requestAnimationFrame(() => {
      this.layerSwapFrame = null;
      this.layerSwapAnimating = true;
      this.cdr.markForCheck();
      this.layerSwapTimer = window.setTimeout(() => {
        this.layerSwapAnimating = false;
        this.layerSwapTimer = null;
        this.cdr.markForCheck();
      }, 220);
    });
  }

  private clearLayerSwapAnimation(): void {
    if (this.layerSwapFrame !== null) {
      window.cancelAnimationFrame(this.layerSwapFrame);
      this.layerSwapFrame = null;
    }
    if (this.layerSwapTimer !== null) {
      window.clearTimeout(this.layerSwapTimer);
      this.layerSwapTimer = null;
    }
  }

  private findWinningCells(board: TicTacToe3dOwner[][][], winner: number): Set<string> {
    const size = board.length;
    if (!size) {
      return new Set<string>();
    }
    const winning = new Set<string>();
    const directions: Array<[number, number, number]> = [];
    for (let dl = -1; dl <= 1; dl += 1) {
      for (let dr = -1; dr <= 1; dr += 1) {
        for (let dc = -1; dc <= 1; dc += 1) {
          if (dl === 0 && dr === 0 && dc === 0) {
            continue;
          }
          if (!this.isCanonicalDirection(dl, dr, dc)) {
            continue;
          }
          directions.push([dl, dr, dc]);
        }
      }
    }
    for (let layer = 0; layer < size; layer += 1) {
      for (let row = 0; row < size; row += 1) {
        for (let col = 0; col < size; col += 1) {
          if (board[layer]?.[row]?.[col] !== winner) {
            continue;
          }
          for (const [dl, dr, dc] of directions) {
            const prevLayer = layer - dl;
            const prevRow = row - dr;
            const prevCol = col - dc;
            if (this.inBounds(prevLayer, prevRow, prevCol, size)) {
              continue;
            }
            const coords: Array<[number, number, number]> = [];
            let allMatch = true;
            for (let step = 0; step < size; step += 1) {
              const nextLayer = layer + dl * step;
              const nextRow = row + dr * step;
              const nextCol = col + dc * step;
              if (!this.inBounds(nextLayer, nextRow, nextCol, size)) {
                allMatch = false;
                break;
              }
              if (board[nextLayer]?.[nextRow]?.[nextCol] !== winner) {
                allMatch = false;
                break;
              }
              coords.push([nextLayer, nextRow, nextCol]);
            }
            if (allMatch && coords.length === size) {
              for (const [nextLayer, nextRow, nextCol] of coords) {
                winning.add(this.cellKey(nextLayer, nextRow, nextCol));
              }
            }
          }
        }
      }
    }
    return winning;
  }

  private isCanonicalDirection(dl: number, dr: number, dc: number): boolean {
    if (dl !== 0) {
      return dl > 0;
    }
    if (dr !== 0) {
      return dr > 0;
    }
    return dc > 0;
  }

  private inBounds(layer: number, row: number, col: number, size: number): boolean {
    return layer >= 0 && row >= 0 && col >= 0 && layer < size && row < size && col < size;
  }

  private detectChangedLayer(
    previous: TicTacToe3dOwner[][][],
    next: TicTacToe3dOwner[][][]
  ): number | null {
    const size = next.length;
    if (!size || previous.length !== size) {
      return null;
    }
    let changedLayer: number | null = null;
    for (let layer = 0; layer < size; layer += 1) {
      for (let row = 0; row < size; row += 1) {
        for (let col = 0; col < size; col += 1) {
          if (previous[layer]?.[row]?.[col] === next[layer]?.[row]?.[col]) {
            continue;
          }
          if (changedLayer === null) {
            changedLayer = layer;
            continue;
          }
          if (changedLayer !== layer) {
            return null;
          }
        }
      }
    }
    return changedLayer;
  }

  private cellKey(layer: number, row: number, col: number): string {
    return `${layer},${row},${col}`;
  }
}
