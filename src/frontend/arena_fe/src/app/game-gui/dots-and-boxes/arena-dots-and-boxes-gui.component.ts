import { ChangeDetectionStrategy, ChangeDetectorRef, Component, Input, OnDestroy } from '@angular/core';
import type { MatchResultSummary, StatusTone } from '@main/arena.constants';
import { kbdSquareFromTop } from '../../components/arena-gui-helpers/arena-kbd-keys';

type DotsAndBoxesCell = {
  key: string;
  row: number;
  col: number;
  type: 'dot' | 'h' | 'v' | 'box';
  owner: 'black' | 'white' | null;
  legal: boolean;
  illegal: boolean;
  winning: boolean;
};

type ParsedMove = {
  row: number;
  col: number;
  dir: 'H' | 'V';
};

@Component({
  selector: 'arena-dots-and-boxes-gui',
  standalone: true,
  templateUrl: './arena-dots-and-boxes-gui.component.html',
  styleUrl: './arena-dots-and-boxes-gui.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ArenaDotsAndBoxesGuiComponent implements OnDestroy {
  dotRows = 0;
  dotCols = 0;
  gridRows = 0;
  gridCols = 0;
  cells: DotsAndBoxesCell[] = [];
  whiteScore = 0;
  blackScore = 0;
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
  private legalMovesByKey = new Map<string, string>();
  private legalKeys = new Set<string>();
  private illegalMoveKey: string | null = null;
  private horizontal: number[][] = [];
  private vertical: number[][] = [];
  private capture: number[][] = [];
  illegalClickMessage: string | null = null;
  illegalClickToken = 0;

  constructor(private readonly cdr: ChangeDetectorRef) {
    (window as any).GUI_COMPONENT = this;
  }

  @Input() set legalMoves(value: string[] | null) {
    this.currentLegalMoves = Array.isArray(value) ? value : [];
    this.legalMovesByKey.clear();
    this.legalKeys.clear();
    for (const move of this.currentLegalMoves) {
      const parsed = this.parseMove(move);
      if (!parsed) {
        continue;
      }
      const key = this.lineKey(parsed.dir, parsed.row, parsed.col);
      if (!this.legalMovesByKey.has(key)) {
        this.legalMovesByKey.set(key, move);
      }
      this.legalKeys.add(key);
    }
    this.refreshCells();
  }

  get legalMoves(): string[] {
    return this.currentLegalMoves;
  }

  @Input() set illegalAction(value: string | null) {
    const parsed = value ? this.parseMove(value) : null;
    this.illegalMoveKey = parsed ? this.lineKey(parsed.dir, parsed.row, parsed.col) : null;
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
      this.dotRows = 0;
      this.dotCols = 0;
      this.gridRows = 0;
      this.gridCols = 0;
      this.cells = [];
      this.whiteScore = 0;
      this.blackScore = 0;
      this.currentPlayer = null;
      this.horizontal = [];
      this.vertical = [];
      this.capture = [];
      this.refreshCells();
      return;
    }
    this.horizontal = parsed.horizontal;
    this.vertical = parsed.vertical;
    this.capture = parsed.capture;
    this.dotRows = parsed.dotRows;
    this.dotCols = parsed.dotCols;
    this.gridRows = Math.max(0, this.dotRows * 2 - 1);
    this.gridCols = Math.max(0, this.dotCols * 2 - 1);
    this.currentPlayer = parsed.player;
    const scores = this.countCaptures(this.capture, this.dotRows, this.dotCols);
    this.blackScore = scores.black;
    this.whiteScore = scores.white;
    this.refreshCells();
  }

  /** Square on the full grid of dots and lines. cell.legal is never set, so check legalKeys. */
  kbdLabel(cell: DotsAndBoxesCell): string | null {
    return this.awaitingHumanMove && this.legalKeys.has(cell.key)
      ? kbdSquareFromTop(cell.col, cell.row, this.gridRows)
      : null;
  }

  onCellClick(cell: DotsAndBoxesCell): void {
    if (!this.awaitingHumanMove || !this.submitHumanMove) {
      return;
    }
    if (cell.type !== 'h' && cell.type !== 'v') {
      return;
    }
    if (!this.legalKeys.has(cell.key)) {
      this.showIllegalClick('Select a legal line.');
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
    horizontal: number[][];
    vertical: number[][];
    capture: number[][];
    dotRows: number;
    dotCols: number;
    player: number | null;
  } | null {
    if (!value || typeof value !== 'object') {
      return null;
    }
    const statePlayer = value as { state?: unknown; player?: unknown };
    const record = (statePlayer.state ?? value) as Record<string, unknown>;
    const player =
      typeof statePlayer.player === 'number'
        ? (statePlayer.player as number)
        : typeof record['turn'] === 'number'
          ? (record['turn'] as number)
          : typeof record['player'] === 'number'
            ? (record['player'] as number)
            : null;
    const horizontal = this.parseGrid(record['horizontal'] ?? (value as { horizontal?: unknown }).horizontal);
    const vertical = this.parseGrid(record['vertical'] ?? (value as { vertical?: unknown }).vertical);
    const capture = this.parseGrid(record['capture'] ?? (value as { capture?: unknown }).capture);
    if (!horizontal || !vertical || !capture) {
      return null;
    }
    if (horizontal.length === 0 || horizontal[0].length === 0) {
      return null;
    }
    if (vertical.length !== horizontal.length || vertical[0].length !== horizontal[0].length) {
      return null;
    }
    return {
      horizontal,
      vertical,
      capture,
      dotRows: horizontal.length,
      dotCols: horizontal[0].length,
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
        rowValues = new Array(maxIndex + 1).fill(0);
        for (const entry of entries) {
          rowValues[entry.index] = entry.cell ?? 0;
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
        const num = Number(cell ?? 0);
        if (!Number.isFinite(num)) {
          return null;
        }
        parsedRow.push(num);
      }
      rows.push(parsedRow);
    }
    return rows;
  }

  private countCaptures(capture: number[][], dotRows: number, dotCols: number): { black: number; white: number } {
    let black = 0;
    let white = 0;
    const rows = Math.max(0, dotRows - 1);
    const cols = Math.max(0, dotCols - 1);
    for (let row = 0; row < rows; row += 1) {
      for (let col = 0; col < cols; col += 1) {
        const value = capture[row]?.[col] ?? 0;
        if (value === 1) {
          black += 1;
        } else if (value === -1) {
          white += 1;
        }
      }
    }
    return { black, white };
  }

  private buildCells(
    horizontal: number[][],
    vertical: number[][],
    capture: number[][],
    dotRows: number,
    dotCols: number,
    legalKeys: Set<string>,
    illegalKey: string | null,
    allowLegal: boolean
  ): DotsAndBoxesCell[] {
    if (dotRows <= 0 || dotCols <= 0) {
      return [];
    }
    const winnerOwner = this.resolveWinnerOwner();
    const cells: DotsAndBoxesCell[] = [];
    const rows = dotRows * 2 - 1;
    const cols = dotCols * 2 - 1;
    for (let row = 0; row < rows; row += 1) {
      for (let col = 0; col < cols; col += 1) {
        const isDotRow = row % 2 === 0;
        const isDotCol = col % 2 === 0;
        if (isDotRow && isDotCol) {
          cells.push({
            key: `d:${row / 2},${col / 2}`,
            row,
            col,
            type: 'dot',
            owner: null,
            legal: false,
            illegal: false,
            winning: false
          });
          continue;
        }
        if (isDotRow) {
          const lineRow = row / 2;
          const lineCol = (col - 1) / 2;
          const value = horizontal[lineRow]?.[lineCol] ?? 0;
          const owner = this.resolveOwner(value);
          const key = this.lineKey('H', lineRow, lineCol);
          cells.push({
            key,
            row,
            col,
            type: 'h',
            owner,
            legal: allowLegal && legalKeys.has(key),
            illegal: Boolean(illegalKey && illegalKey === key),
            winning: false
          });
          continue;
        }
        if (isDotCol) {
          const lineRow = (row - 1) / 2;
          const lineCol = col / 2;
          const value = vertical[lineRow]?.[lineCol] ?? 0;
          const owner = this.resolveOwner(value);
          const key = this.lineKey('V', lineRow, lineCol);
          cells.push({
            key,
            row,
            col,
            type: 'v',
            owner,
            legal: allowLegal && legalKeys.has(key),
            illegal: Boolean(illegalKey && illegalKey === key),
            winning: false
          });
          continue;
        }
        const boxRow = (row - 1) / 2;
        const boxCol = (col - 1) / 2;
        const value = capture[boxRow]?.[boxCol] ?? 0;
        const owner = this.resolveOwner(value);
        cells.push({
          key: `b:${boxRow},${boxCol}`,
          row,
          col,
          type: 'box',
          owner,
          legal: false,
          illegal: false,
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

  private resolveOwner(value: number): 'black' | 'white' | null {
    if (value === 1) {
      return 'black';
    }
    if (value === -1) {
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

  private parseMove(value: string): ParsedMove | null {
    const trimmed = String(value ?? '').trim();
    if (!trimmed) {
      return null;
    }
    const main = trimmed.split(':')[0]?.trim();
    if (!main) {
      return null;
    }
    const match = main.match(/(-?\d+)\s*,\s*(-?\d+)\s*,\s*([HV])/i);
    if (!match) {
      return null;
    }
    const row = Number(match[1]);
    const col = Number(match[2]);
    const dir = match[3].toUpperCase() as ParsedMove['dir'];
    if (!Number.isFinite(row) || !Number.isFinite(col)) {
      return null;
    }
    return { row, col, dir };
  }

  private lineKey(dir: ParsedMove['dir'], row: number, col: number): string {
    return `${dir}:${row},${col}`;
  }

  private refreshCells(): void {
    const allowLegal = false;
    const legalKeys = new Set<string>();
    this.cells = this.buildCells(
      this.horizontal,
      this.vertical,
      this.capture,
      this.dotRows,
      this.dotCols,
      legalKeys,
      this.illegalMoveKey,
      allowLegal
    );
    this.cdr.markForCheck();
  }
}
