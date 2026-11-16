import { ChangeDetectionStrategy, ChangeDetectorRef, Component, Input, OnDestroy } from '@angular/core';
import type { MatchResultSummary, StatusTone } from '@main/arena.constants';
import { kbdPentagoRotation, kbdSquareFromTop } from '../../components/arena-gui-helpers/arena-kbd-keys';

type PentagoOwner = 0 | 1 | null;
type RotationDir = 'L' | 'R';

type PentagoCell = {
  key: string;
  row: number;
  col: number;
  owner: 'black' | 'white' | null;
  legal: boolean;
  selected: boolean;
  illegal: boolean;
  winning: boolean;
};

type PentagoGhostCell = {
  key: string;
  owner: 'black' | 'white' | null;
};

@Component({
  selector: 'arena-pentago-gui',
  standalone: true,
  templateUrl: './arena-pentago-gui.component.html',
  styleUrl: './arena-pentago-gui.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ArenaPentagoGuiComponent implements OnDestroy {
  boardSize = 0;
  halfCells = 3;
  cells: PentagoCell[] = [];
  blackCount = 0;
  whiteCount = 0;
  currentPlayer: number | null = null;
  matchBannerMessage: string | null = null;
  hasWinningLine = false;
  halfPercent = '50%';
  quarterPercent = '25%';
  @Input() botA = 'Automaton A';
  @Input() botB = 'Automaton B';
  @Input() statusTone: StatusTone = 'idle';
  @Input() statusMessage = '';
  @Input() showHumanControls = false;
  private awaitingHuman = false;
  @Input() set awaitingHumanMove(value: boolean) {
    this.awaitingHuman = value;
    if (!value) {
      this.selectedPlacementKey = null;
    }
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
  selectedPlacementKey: string | null = null;
  private board: PentagoOwner[][] = [];
  private illegalCell: { row: number; col: number } | null = null;
  private currentLegalMoves: string[] = [];
  private legalMovesByKey = new Map<string, string>();
  private legalPlacements = new Set<string>();
  private rotationOptionsByPlacement = new Map<string, Set<string>>();
  private winningCells = new Set<string>();
  private suppressLegalHighlights = false;
  private rotationTimer: number | null = null;
  animatingQuadrant: number | null = null;
  animatingDir: RotationDir | null = null;
  rotationGhostQuadrant: number | null = null;
  rotationGhostCells: PentagoGhostCell[] = [];
  private bannerTimer: number | null = null;
  private lastMatchStamp: number | null = null;
  private matchWinner: number | null = null;
  private matchIllegal = false;

  constructor(private readonly cdr: ChangeDetectorRef) {
    (window as any).GUI_COMPONENT = this;
  }

  @Input() set legalMoves(value: string[] | null) {
    this.currentLegalMoves = Array.isArray(value) ? value : [];
    this.legalMovesByKey.clear();
    this.legalPlacements.clear();
    this.rotationOptionsByPlacement.clear();
    this.selectedPlacementKey = null;
    if (this.awaitingHumanMove) {
      this.suppressLegalHighlights = false;
    }
    for (const move of this.currentLegalMoves) {
      const parsed = this.parseMove(move);
      if (!parsed) {
        continue;
      }
      const placementKey = this.coordKey(parsed.row, parsed.col);
      const rotationKey = this.rotationKey(parsed.quadrant, parsed.dir);
      const moveKey = this.moveKey(parsed.row, parsed.col, parsed.quadrant, parsed.dir);
      if (!this.legalMovesByKey.has(moveKey)) {
        this.legalMovesByKey.set(moveKey, move);
      }
      this.legalPlacements.add(placementKey);
      const options = this.rotationOptionsByPlacement.get(placementKey) ?? new Set<string>();
      options.add(rotationKey);
      this.rotationOptionsByPlacement.set(placementKey, options);
    }
    this.refreshCells();
  }

  get legalMoves(): string[] {
    return this.currentLegalMoves;
  }

  get rotationActive(): boolean {
    return this.awaitingHumanMove && this.selectedPlacementKey !== null;
  }

  @Input() set illegalAction(value: string | null) {
    const parsed = this.parseMove(value);
    this.illegalCell = parsed ? { row: parsed.row, col: parsed.col } : null;
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
    const rotationEvent = this.parseRotationEvent(value);
    if (!parsed) {
      this.boardSize = 0;
      this.cells = [];
      this.blackCount = 0;
      this.whiteCount = 0;
      this.currentPlayer = null;
      this.board = [];
      this.winningCells = new Set<string>();
      this.hasWinningLine = false;
      this.suppressLegalHighlights = false;
      this.rotationGhostQuadrant = null;
      this.rotationGhostCells = [];
      this.animatingQuadrant = null;
      this.animatingDir = null;
      return;
    }
    this.suppressLegalHighlights = true;
    this.board = parsed.board;
    this.boardSize = parsed.size;
    this.currentPlayer = parsed.player;
    this.blackCount = parsed.blackCount;
    this.whiteCount = parsed.whiteCount;
    this.updateBoardMetrics();
    if (rotationEvent && rotationEvent.oldBoard.length === this.board.length) {
      const ghostCells = this.buildGhostCellsForRotation(
        rotationEvent.oldBoard,
        rotationEvent.quadrant
      );
      this.triggerRotationAnimation(rotationEvent.quadrant, rotationEvent.dir, ghostCells);
    }
    this.updateWinningCells();
  }

  /** keyboard hint: legal squares, then the rotations for the selected square */
  kbdLabel(cell: PentagoCell): string | null {
    return cell.legal && !this.selectedPlacementKey ? kbdSquareFromTop(cell.col, cell.row, this.boardSize) : null;
  }

  kbdRotation(quadrant: number, dir: RotationDir): string | null {
    return this.rotationActive && this.isRotationLegal(quadrant, dir) ? kbdPentagoRotation(quadrant, dir) : null;
  }

  onCellClick(cell: PentagoCell): void {
    if (!this.awaitingHumanMove || !this.submitHumanMove) {
      return;
    }
    if (!cell.legal) {
      this.showIllegalClick('Select a legal square.');
      return;
    }
    if (!this.selectedPlacementKey) {
      this.selectedPlacementKey = cell.key;
      this.refreshCells();
      return;
    }
    if (this.selectedPlacementKey === cell.key) {
      this.selectedPlacementKey = null;
      this.refreshCells();
      return;
    }
    this.selectedPlacementKey = cell.key;
    this.refreshCells();
  }

  onRotationClick(quadrant: number, dir: RotationDir): void {
    if (!this.awaitingHumanMove || !this.submitHumanMove) {
      return;
    }
    if (!this.selectedPlacementKey) {
      this.showIllegalClick('Select a square first.');
      return;
    }
    const rotationKey = this.rotationKey(quadrant, dir);
    const moveKey = `${this.selectedPlacementKey}|${rotationKey}`;
    const move = this.legalMovesByKey.get(moveKey);
    if (!move) {
      this.showIllegalClick('Illegal rotation.');
      return;
    }
    this.selectedPlacementKey = null;
    this.suppressLegalHighlights = true;
    this.refreshCells();
    this.submitHumanMove(move);
  }

  isRotationLegal(quadrant: number, dir: RotationDir): boolean {
    if (!this.selectedPlacementKey) {
      return false;
    }
    const options = this.rotationOptionsByPlacement.get(this.selectedPlacementKey);
    if (!options) {
      return false;
    }
    return options.has(this.rotationKey(quadrant, dir));
  }

  ngOnDestroy(): void {
    this.clearBannerTimer();
    this.clearRotationTimer();
  }

  private parseObservation(value: unknown | null): {
    board: PentagoOwner[][];
    size: number;
    player: number | null;
    blackCount: number;
    whiteCount: number;
  } | null {
    if (!value) {
      return null;
    }
    if (Array.isArray(value)) {
      const board = this.parseBoard(value);
      if (!board) {
        return null;
      }
      const derived = this.combineBoards(board, this.emptyBoard(board.length));
      return {
        board: derived.board,
        size: derived.board.length,
        player: null,
        blackCount: derived.blackCount,
        whiteCount: derived.whiteCount
      };
    }
    if (typeof value !== 'object') {
      return null;
    }
    const statePlayer = value as { state?: unknown; player?: unknown };
    const record = (statePlayer.state ?? value) as Record<string, unknown>;
    const player = this.resolvePlayer(record, statePlayer);
    const p0 = this.parseBoard(record['p0']);
    const p1 = this.parseBoard(record['p1']);
    if (p0 && p1) {
      const combined = this.combineBoards(p0, p1);
      return {
        board: combined.board,
        size: combined.board.length,
        player,
        blackCount: combined.blackCount,
        whiteCount: combined.whiteCount
      };
    }
    const you = this.parseBoard(record['you']);
    const opponent = this.parseBoard(record['opponent']);
    if (you && opponent) {
      const youIsPlayer0 = player !== 1;
      const combined = this.combineBoards(youIsPlayer0 ? you : opponent, youIsPlayer0 ? opponent : you);
      return {
        board: combined.board,
        size: combined.board.length,
        player,
        blackCount: combined.blackCount,
        whiteCount: combined.whiteCount
      };
    }
    const board = this.parseBoard(record['board']);
    if (board) {
      const combined = this.combineBoards(board, this.emptyBoard(board.length));
      return {
        board: combined.board,
        size: combined.board.length,
        player,
        blackCount: combined.blackCount,
        whiteCount: combined.whiteCount
      };
    }
    return null;
  }

  private resolvePlayer(record: Record<string, unknown>, statePlayer: { player?: unknown }): number | null {
    if (typeof record['player'] === 'number' && Number.isFinite(record['player'])) {
      return record['player'] as number;
    }
    if (typeof record['turn'] === 'number' && Number.isFinite(record['turn'])) {
      return record['turn'] as number;
    }
    if (typeof statePlayer.player === 'number' && Number.isFinite(statePlayer.player)) {
      return statePlayer.player as number;
    }
    return null;
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
    if (!width || rows.length !== width) {
      return null;
    }
    return rows;
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

  private emptyBoard(size: number): number[][] {
    const rows: number[][] = [];
    for (let row = 0; row < size; row += 1) {
      rows.push(Array.from({ length: size }, () => 0));
    }
    return rows;
  }

  private combineBoards(
    player0: number[][],
    player1: number[][]
  ): { board: PentagoOwner[][]; blackCount: number; whiteCount: number } {
    const size = player0.length;
    const board: PentagoOwner[][] = [];
    let blackCount = 0;
    let whiteCount = 0;
    for (let row = 0; row < size; row += 1) {
      const nextRow: PentagoOwner[] = [];
      for (let col = 0; col < size; col += 1) {
        let owner: PentagoOwner = null;
        if (player0[row]?.[col]) {
          owner = 0;
        }
        if (player1[row]?.[col]) {
          owner = 1;
        }
        if (owner === 0) {
          blackCount += 1;
        } else if (owner === 1) {
          whiteCount += 1;
        }
        nextRow.push(owner);
      }
      board.push(nextRow);
    }
    return { board, blackCount, whiteCount };
  }

  private updateBoardMetrics(): void {
    const half = this.boardSize / 2;
    const quarter = this.boardSize / 4;
    this.halfCells = Math.max(1, Math.floor(half));
    this.halfPercent = this.boardSize > 0 ? `${(half / this.boardSize) * 100}%` : '50%';
    this.quarterPercent = this.boardSize > 0 ? `${(quarter / this.boardSize) * 100}%` : '25%';
  }

  private buildCells(
    board: PentagoOwner[][],
    legalPlacements: Set<string>,
    selectedPlacementKey: string | null,
    illegalCell: { row: number; col: number } | null,
    allowLegal: boolean
  ): PentagoCell[] {
    if (!board.length) {
      return [];
    }
    const cells: PentagoCell[] = [];
    for (let row = 0; row < board.length; row += 1) {
      for (let col = 0; col < board[row].length; col += 1) {
        const ownerIndex = board[row][col];
        const owner: PentagoCell['owner'] =
          ownerIndex === 0 ? 'black' : ownerIndex === 1 ? 'white' : null;
        const key = this.coordKey(row, col);
        cells.push({
          key,
          row,
          col,
          owner,
          legal: allowLegal && legalPlacements.has(key),
          selected: selectedPlacementKey === key,
          illegal: Boolean(illegalCell && illegalCell.row === row && illegalCell.col === col),
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

  private triggerRotationAnimation(
    quadrant: number,
    dir: RotationDir,
    ghostCells: PentagoGhostCell[] = []
  ): void {
    this.animatingQuadrant = quadrant;
    this.animatingDir = dir;
    this.rotationGhostQuadrant = quadrant;
    this.rotationGhostCells = ghostCells;
    this.cdr.markForCheck();
    this.clearRotationTimer();
    this.rotationTimer = window.setTimeout(() => {
      this.animatingQuadrant = null;
      this.animatingDir = null;
      this.rotationGhostQuadrant = null;
      this.rotationGhostCells = [];
      this.rotationTimer = null;
      this.cdr.markForCheck();
    }, 420);
  }

  private clearRotationTimer(): void {
    if (this.rotationTimer !== null) {
      window.clearTimeout(this.rotationTimer);
      this.rotationTimer = null;
    }
  }

  private parseRotationEvent(
    value: unknown
  ): { oldBoard: PentagoOwner[][]; quadrant: number; dir: RotationDir } | null {
    if (!value || typeof value !== 'object' || Array.isArray(value)) {
      return null;
    }
    const record = value as Record<string, unknown>;
    const actionValue = typeof record['action'] === 'string' ? record['action'] : null;
    const parsedAction = this.parseMove(actionValue);
    if (!parsedAction) {
      return null;
    }
    const oldParsed = this.parseObservation(record['old_state'] ?? null);
    if (!oldParsed || oldParsed.board.length === 0) {
      return null;
    }
    return {
      oldBoard: oldParsed.board,
      quadrant: parsedAction.quadrant,
      dir: parsedAction.dir
    };
  }

  private buildGhostCellsForRotation(
    board: PentagoOwner[][],
    quadrant: number
  ): PentagoGhostCell[] {
    if (!board.length || board.length % 2 !== 0) {
      return [];
    }
    const half = Math.floor(board.length / 2);
    const offsets = this.getQuadrantOffsets(quadrant, half);
    if (!offsets) {
      return [];
    }

    const cells: PentagoGhostCell[] = [];
    for (let row = 0; row < half; row += 1) {
      for (let col = 0; col < half; col += 1) {
        const ownerIndex = board[offsets.row + row][offsets.col + col] ?? null;
        cells.push({
          key: `${row},${col}`,
          owner: ownerIndex === 0 ? 'black' : ownerIndex === 1 ? 'white' : null
        });
      }
    }
    return cells;
  }

  private getQuadrantOffsets(quadrant: number, half: number): { row: number; col: number } | null {
    if (quadrant < 0 || quadrant > 3) {
      return null;
    }
    const row = quadrant >= 2 ? half : 0;
    const col = quadrant % 2 === 1 ? half : 0;
    return { row, col };
  }

  private showIllegalClick(message: string): void {
    this.illegalClickMessage = message;
    this.illegalClickToken += 1;
    this.cdr.markForCheck();
  }

  private parseMove(value: string | null): { row: number; col: number; quadrant: number; dir: RotationDir } | null {
    if (!value) {
      return null;
    }
    const trimmed = String(value).trim();
    const shorthand = trimmed.match(/^([a-z])(\d+)([s-z])$/i);
    if (shorthand) {
      const col = shorthand[1].toLowerCase().charCodeAt(0) - 97;
      const row = Number(shorthand[2]) - 1;
      const suffix = shorthand[3].toLowerCase();
      const mapping: Record<string, { quadrant: number; dir: RotationDir }> = {
        s: { quadrant: 0, dir: 'L' },
        t: { quadrant: 0, dir: 'R' },
        u: { quadrant: 1, dir: 'L' },
        v: { quadrant: 1, dir: 'R' },
        w: { quadrant: 3, dir: 'L' },
        x: { quadrant: 3, dir: 'R' },
        y: { quadrant: 2, dir: 'L' },
        z: { quadrant: 2, dir: 'R' }
      };
      const mapped = mapping[suffix];
      if (!mapped || !Number.isFinite(row) || !Number.isFinite(col)) {
        return null;
      }
      return { row, col, quadrant: mapped.quadrant, dir: mapped.dir };
    }
    const match = trimmed.match(/(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*([LR])/i);
    if (!match) {
      return null;
    }
    const row = Number(match[1]) - 1;
    const col = Number(match[2]) - 1;
    const quadrant = Number(match[3]);
    const dir = match[4].toUpperCase() as RotationDir;
    if (!Number.isFinite(row) || !Number.isFinite(col) || !Number.isFinite(quadrant)) {
      return null;
    }
    return { row, col, quadrant, dir };
  }

  private coordKey(row: number, col: number): string {
    return `${row},${col}`;
  }

  private rotationKey(quadrant: number, dir: RotationDir): string {
    return `${quadrant}|${dir}`;
  }

  private moveKey(row: number, col: number, quadrant: number, dir: RotationDir): string {
    return `${this.coordKey(row, col)}|${this.rotationKey(quadrant, dir)}`;
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
    const allowLegal = this.awaitingHumanMove && !this.suppressLegalHighlights;
    this.cells = this.buildCells(
      this.board,
      this.legalPlacements,
      this.selectedPlacementKey,
      this.illegalCell,
      allowLegal
    );
    this.cdr.markForCheck();
  }

  private findWinningCells(board: PentagoOwner[][], winner: number): Set<string> {
    const size = board.length;
    if (!size) {
      return new Set<string>();
    }
    const winLength = Math.min(5, size);
    const directions = [
      { dr: 0, dc: 1 },
      { dr: 1, dc: 0 },
      { dr: 1, dc: 1 },
      { dr: 1, dc: -1 }
    ];
    for (let row = 0; row < size; row += 1) {
      for (let col = 0; col < size; col += 1) {
        if (board[row]?.[col] !== winner) {
          continue;
        }
        for (const { dr, dc } of directions) {
          const coords: Array<[number, number]> = [];
          let valid = true;
          for (let i = 0; i < winLength; i += 1) {
            const nextRow = row + dr * i;
            const nextCol = col + dc * i;
            if (nextRow < 0 || nextRow >= size || nextCol < 0 || nextCol >= size) {
              valid = false;
              break;
            }
            if (board[nextRow]?.[nextCol] !== winner) {
              valid = false;
              break;
            }
            coords.push([nextRow, nextCol]);
          }
          if (valid && coords.length === winLength) {
            return new Set(coords.map(([r, c]) => this.coordKey(r, c)));
          }
        }
      }
    }
    return new Set<string>();
  }
}
