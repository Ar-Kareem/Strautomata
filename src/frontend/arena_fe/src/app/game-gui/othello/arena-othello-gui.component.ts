import { ChangeDetectionStrategy, ChangeDetectorRef, Component, Input, OnDestroy } from '@angular/core';
import { HumanMovePanelComponent } from '@arena/human-move-panel.component';
import type { MatchResultSummary, StatusTone } from '@main/arena.constants';
import { ArenaBannerComponent } from '../../components/arena-gui-helpers/arena-banner.component';
import { ArenaGuiAlertComponent } from '../../components/arena-gui-helpers/arena-gui-alert.component';
import { ArenaGuiEmptyComponent } from '../../components/arena-gui-helpers/arena-gui-empty.component';
import { ArenaGuiLegendComponent } from '../../components/arena-gui-helpers/arena-gui-legend.component';

type OthelloCell = {
  key: string;
  row: number;
  col: number;
  isDark: boolean;
  owner: 'black' | 'white' | null;
  legal: boolean;
  illegal: boolean;
  winning: boolean;
};

type OthelloBoard = {
  black: number[][];
  white: number[][];
  size: number;
  player: number | null;
};

@Component({
  selector: 'arena-othello-gui',
  standalone: true,
  templateUrl: './arena-othello-gui.component.html',
  styleUrl: './arena-othello-gui.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    HumanMovePanelComponent,
    ArenaBannerComponent,
    ArenaGuiAlertComponent,
    ArenaGuiEmptyComponent,
    ArenaGuiLegendComponent
  ]
})
export class ArenaOthelloGuiComponent implements OnDestroy {
  boardSize = 0;
  cells: OthelloCell[] = [];
  blackCount = 0;
  whiteCount = 0;
  currentPlayer: number | null = null;
  matchBannerMessage: string | null = null;
  illegalClickMessage: string | null = null;
  illegalClickToken = 0;

  @Input() botA = 'Automaton A';
  @Input() botB = 'Automaton B';
  @Input() statusTone: StatusTone = 'idle';
  @Input() statusMessage = '';
  @Input() showHumanControls = false;
  @Input() awaitingHumanMove = false;
  @Input() submitHumanMove?: (move: string) => void;

  private blackLayer: number[][] = [];
  private whiteLayer: number[][] = [];
  private currentLegalMoves: string[] = [];
  private legalMovesByKey = new Map<string, string>();
  private illegalMoveKey: string | null = null;
  private bannerTimer: number | null = null;
  private lastMatchStamp: number | null = null;
  private matchWinner: number | null = null;
  hasWinner = false;

  constructor(private readonly cdr: ChangeDetectorRef) {}

  get activePlayerLabel(): string {
    if (this.currentPlayer === 0) {
      return this.botA;
    }
    if (this.currentPlayer === 1) {
      return this.botB;
    }
    return '';
  }

  get humanHint(): string {
    if (!this.showHumanControls) {
      return '';
    }
    if (!this.awaitingHumanMove) {
      return 'Waiting for your turn.';
    }
    return 'Your turn. Click a legal square.';
  }

  @Input() set legalMoves(value: string[] | null) {
    this.currentLegalMoves = Array.isArray(value) ? value : [];
    this.rebuildLegalMoves();
    this.refreshCells();
  }

  get legalMoves(): string[] {
    return this.currentLegalMoves;
  }

  @Input() set illegalAction(value: string | null) {
    const point = value ? this.parseMovePoint(value, this.boardSize) : null;
    this.illegalMoveKey = point ? this.coordKey(point[0], point[1]) : null;
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
      this.blackLayer = [];
      this.whiteLayer = [];
      this.blackCount = 0;
      this.whiteCount = 0;
      this.currentPlayer = null;
      this.cells = [];
      this.rebuildLegalMoves();
      return;
    }
    this.blackLayer = parsed.black;
    this.whiteLayer = parsed.white;
    this.boardSize = parsed.size;
    this.currentPlayer = parsed.player;
    this.blackCount = this.countPieces(this.blackLayer);
    this.whiteCount = this.countPieces(this.whiteLayer);
    this.rebuildLegalMoves();
    this.refreshCells();
  }

  onCellClick(cell: OthelloCell): void {
    if (!this.awaitingHumanMove || !this.submitHumanMove) {
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

  private parseObservation(value: unknown | null): OthelloBoard | null {
    if (!value || typeof value !== 'object') {
      return null;
    }
    const statePlayer = value as { state?: unknown; player?: unknown };
    const record = (statePlayer.state ?? value) as Record<string, unknown>;
    const black = this.parseLayer(record['p0'] ?? record['black']);
    const white = this.parseLayer(record['p1'] ?? record['white']);
    if (!black || !white) {
      return null;
    }
    if (black.length !== white.length || black[0]?.length !== white[0]?.length) {
      return null;
    }
    const size = black.length;
    if (size <= 0 || black[0]?.length !== size) {
      return null;
    }
    const player =
      typeof statePlayer.player === 'number'
        ? statePlayer.player
        : typeof record['turn'] === 'number'
          ? (record['turn'] as number)
          : typeof record['player'] === 'number'
            ? (record['player'] as number)
            : null;
    return { black, white, size, player };
  }

  private parseLayer(value: unknown): number[][] | null {
    if (!Array.isArray(value) || value.length === 0) {
      return null;
    }
    const rows: number[][] = [];
    let width = -1;
    for (const row of value) {
      const parsedRow = this.parseLayerRow(row);
      if (!parsedRow || parsedRow.length === 0) {
        return null;
      }
      if (width < 0) {
        width = parsedRow.length;
      }
      if (parsedRow.length !== width) {
        return null;
      }
      rows.push(parsedRow);
    }
    return rows;
  }

  private parseLayerRow(value: unknown): number[] | null {
    if (Array.isArray(value) || ArrayBuffer.isView(value)) {
      return Array.from(value as Iterable<unknown>, (entry) => this.normalizeBinary(entry));
    }
    if (!value || typeof value !== 'object') {
      return null;
    }
    const entries = Object.entries(value as Record<string, unknown>)
      .map(([key, cell]) => ({ index: Number(key), cell }))
      .filter(({ index }) => Number.isInteger(index) && index >= 0)
      .sort((a, b) => a.index - b.index);
    if (entries.length === 0) {
      return null;
    }
    return entries.map((entry) => this.normalizeBinary(entry.cell));
  }

  private normalizeBinary(value: unknown): number {
    const num = Number(value);
    return Number.isFinite(num) && num > 0 ? 1 : 0;
  }

  private countPieces(layer: number[][]): number {
    let total = 0;
    for (const row of layer) {
      for (const value of row) {
        if (value === 1) {
          total += 1;
        }
      }
    }
    return total;
  }

  private rebuildLegalMoves(): void {
    this.legalMovesByKey.clear();
    for (const move of this.currentLegalMoves) {
      const point = this.parseMovePoint(move, this.boardSize);
      if (!point) {
        continue;
      }
      const key = this.coordKey(point[0], point[1]);
      if (!this.legalMovesByKey.has(key)) {
        this.legalMovesByKey.set(key, move);
      }
    }
  }

  private refreshCells(): void {
    const legalKeys =
      this.awaitingHumanMove && this.showHumanControls
        ? new Set(this.legalMovesByKey.keys())
        : new Set<string>();
    this.cells = this.buildCells(
      this.blackLayer,
      this.whiteLayer,
      this.boardSize,
      legalKeys,
      this.illegalMoveKey
    );
    this.cdr.markForCheck();
  }

  private buildCells(
    black: number[][],
    white: number[][],
    size: number,
    legalKeys: Set<string>,
    illegalKey: string | null
  ): OthelloCell[] {
    if (size <= 0) {
      return [];
    }
    const cells: OthelloCell[] = [];
    for (let row = 0; row < size; row += 1) {
      for (let col = 0; col < size; col += 1) {
        const key = this.coordKey(row, col);
        const hasBlack = black[row]?.[col] === 1;
        const hasWhite = white[row]?.[col] === 1;
        let owner: OthelloCell['owner'] = null;
        if (hasBlack) {
          owner = 'black';
        } else if (hasWhite) {
          owner = 'white';
        }
        const winning =
          this.matchWinner !== null &&
          ((this.matchWinner === 0 && owner === 'black') ||
            (this.matchWinner === 1 && owner === 'white'));
        cells.push({
          key,
          row,
          col,
          isDark: (row + col) % 2 === 1,
          owner,
          legal: legalKeys.has(key),
          illegal: Boolean(illegalKey && illegalKey === key),
          winning
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

  private parseMovePoint(value: string, boardSize: number): [number, number] | null {
    const trimmed = String(value ?? '').trim();
    if (!trimmed) {
      return null;
    }
    const coordMatch = trimmed.match(/-?\d+/g);
    if (coordMatch && coordMatch.length >= 2) {
      const first = Number(coordMatch[0]);
      const second = Number(coordMatch[1]);
      if (Number.isFinite(first) && Number.isFinite(second)) {
        if (boardSize > 0) {
          if (first >= 0 && first < boardSize && second >= 0 && second < boardSize) {
            return [first, second];
          }
          if (first > 0 && first <= boardSize && second > 0 && second <= boardSize) {
            return [first - 1, second - 1];
          }
        } else {
          return [first, second];
        }
      }
    }
    const algebraic = trimmed.match(/^([a-zA-Z])\s*([0-9]{1,2})$/);
    if (!algebraic) {
      return null;
    }
    const col = algebraic[1].toLowerCase().charCodeAt(0) - 97;
    const row = Number(algebraic[2]) - 1;
    if (!Number.isFinite(row) || !Number.isFinite(col)) {
      return null;
    }
    if (boardSize > 0 && (row < 0 || row >= boardSize || col < 0 || col >= boardSize)) {
      return null;
    }
    return [row, col];
  }

  private coordKey(row: number, col: number): string {
    return `${row},${col}`;
  }
}
