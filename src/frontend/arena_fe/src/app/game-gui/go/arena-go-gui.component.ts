import { ChangeDetectionStrategy, ChangeDetectorRef, Component, Input, OnDestroy } from '@angular/core';
import { HumanMovePanelComponent } from '@arena/human-move-panel.component';
import type { MatchResultSummary, StatusTone } from '@main/arena.constants';

type GoPoint = [number, number];

type GoCell = {
  key: string;
  row: number;
  col: number;
  owner: 'black' | 'white' | null;
  illegal: boolean;
};

@Component({
  selector: 'arena-go-gui',
  standalone: true,
  templateUrl: './arena-go-gui.component.html',
  styleUrl: './arena-go-gui.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [HumanMovePanelComponent]
})
export class ArenaGoGuiComponent implements OnDestroy {
  boardSize = 0;
  cells: GoCell[] = [];
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
  @Input() awaitingHumanMove = false;
  @Input() submitHumanMove?: (move: string) => void;
  private blackPoints: GoPoint[] = [];
  private whitePoints: GoPoint[] = [];
  private illegalMove: GoPoint | null = null;
  private bannerTimer: number | null = null;
  private lastMatchStamp: number | null = null;
  private currentLegalMoves: string[] = [];
  private legalMovesByPoint = new Map<string, string>();
  private passMove: string | null = null;
  illegalClickMessage: string | null = null;
  illegalClickToken = 0;

  @Input() set legalMoves(value: string[] | null) {
    this.currentLegalMoves = Array.isArray(value) ? value : [];
    this.legalMovesByPoint.clear();
    this.passMove = null;
    for (const move of this.currentLegalMoves) {
      const point = this.parseMovePoint(move);
      if (!point) {
        continue;
      }
      if (point[0] === 0 && point[1] === 0) {
        this.passMove = move;
        continue;
      }
      const key = `${point[0]},${point[1]}`;
      if (!this.legalMovesByPoint.has(key)) {
        this.legalMovesByPoint.set(key, move);
      }
    }
  }

  get legalMoves(): string[] {
    return this.currentLegalMoves;
  }

  get hasPassMove(): boolean {
    return Boolean(this.passMove);
  }

  constructor(private readonly cdr: ChangeDetectorRef) {
    (window as any).GUI_COMPONENT = this;
  }

  @Input() set illegalAction(value: string | null) {
    this.illegalMove = this.parseIllegalAction(value);
    this.cells = this.buildCells(this.blackPoints, this.whitePoints, this.boardSize, this.illegalMove);
  }

  @Input() set matchResult(value: MatchResultSummary | null) {
    if (!value) {
      this.lastMatchStamp = null;
      this.clearBanner();
      return;
    }
    if (this.lastMatchStamp === value.finishedAt) {
      return;
    }
    this.lastMatchStamp = value.finishedAt;
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
      this.blackCount = 0;
      this.whiteCount = 0;
      this.currentPlayer = null;
      this.blackPoints = [];
      this.whitePoints = [];
      return;
    }
    if (parsed.black && parsed.white) {
      this.blackPoints = parsed.black;
      this.whitePoints = parsed.white;
    } else {
      const isMeBlack = parsed.player !== 1;
      this.blackPoints = isMeBlack ? parsed.me : parsed.opponent;
      this.whitePoints = isMeBlack ? parsed.opponent : parsed.me;
    }
    this.blackCount = this.blackPoints.length;
    this.whiteCount = this.whitePoints.length;
    this.currentPlayer = parsed.player;
    this.boardSize = this.resolveBoardSize([...this.blackPoints, ...this.whitePoints]);
    this.cells = this.buildCells(
      this.blackPoints,
      this.whitePoints,
      this.boardSize,
      this.illegalMove
    );
  }

  onCellClick(cell: GoCell): void {
    if (!this.awaitingHumanMove || !this.submitHumanMove) {
      return;
    }
    const key = `${cell.row},${cell.col}`;
    const move = this.legalMovesByPoint.get(key);
    if (!move) {
      this.showIllegalClick('Illegal move.');
      return;
    }
    this.submitHumanMove(move);
  }

  submitPass(): void {
    if (!this.awaitingHumanMove || !this.submitHumanMove || !this.passMove) {
      return;
    }
    this.submitHumanMove(this.passMove);
  }

  private parseObservation(value: unknown | null): {
    me: GoPoint[];
    opponent: GoPoint[];
    black: GoPoint[] | null;
    white: GoPoint[] | null;
    player: number | null;
  } | null {
    if (!value || typeof value !== 'object') {
      return null;
    }
    const statePlayer = value as { state?: unknown; player?: unknown };
    const record = (statePlayer.state ?? value) as {
      me?: unknown;
      opponent?: unknown;
      black?: unknown;
      white?: unknown;
      turn?: unknown;
    };
    const player =
      typeof record.turn === 'number'
        ? record.turn
        : (statePlayer.player as number | null);
    const black = this.parsePoints(record.black);
    const white = this.parsePoints(record.white);
    if (black && white) {
      return { black, white, me: [], opponent: [], player };
    }
    const me = this.parsePoints(record.me);
    const opponent = this.parsePoints(record.opponent);
    if (!me || !opponent) {
      return null;
    }
    return { me, opponent, black: null, white: null, player };
  }

  private parsePoints(value: unknown): GoPoint[] | null {
    if (!Array.isArray(value)) {
      return null;
    }
    const points: GoPoint[] = [];
    for (const entry of value) {
      if (!Array.isArray(entry) || entry.length < 2) {
        continue;
      }
      const row = Number(entry[0]);
      const col = Number(entry[1]);
      if (!Number.isFinite(row) || !Number.isFinite(col)) {
        continue;
      }
      points.push([row, col]);
    }
    return points;
  }

  private resolveBoardSize(points: GoPoint[]): number {
    let maxCoord = 0;
    for (const [row, col] of points) {
      maxCoord = Math.max(maxCoord, row, col);
    }
    return Math.max(19, maxCoord);
  }

  private buildCells(
    blackPoints: GoPoint[],
    whitePoints: GoPoint[],
    size: number,
    illegalMove: GoPoint | null
  ): GoCell[] {
    if (size <= 0) {
      return [];
    }
    const blackSet = new Set(blackPoints.map(([row, col]) => `${row},${col}`));
    const whiteSet = new Set(whitePoints.map(([row, col]) => `${row},${col}`));
    const illegalKey = illegalMove ? `${illegalMove[0]},${illegalMove[1]}` : null;
    const cells: GoCell[] = [];
    for (let row = 1; row <= size; row += 1) {
      for (let col = 1; col <= size; col += 1) {
        const key = `${row},${col}`;
        let owner: GoCell['owner'] = null;
        if (blackSet.has(key)) {
          owner = 'black';
        } else if (whiteSet.has(key)) {
          owner = 'white';
        }
        const illegal = Boolean(illegalKey && illegalKey === key);
        cells.push({ key, row, col, owner, illegal });
      }
    }
    return cells;
  }

  ngOnDestroy(): void {
    this.clearBannerTimer();
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

  private parseIllegalAction(value: string | null): GoPoint | null {
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
      if (Number.isFinite(row) && Number.isFinite(col) && row > 0 && col > 0) {
        return [row, col];
      }
    }
    const alphaMatch = trimmed.match(/([A-Za-z])\s*([0-9]+)/);
    if (alphaMatch) {
      const col = alphaMatch[1].toUpperCase().charCodeAt(0) - 64;
      const row = Number(alphaMatch[2]);
      if (Number.isFinite(row) && Number.isFinite(col) && row > 0 && col > 0) {
        return [row, col];
      }
    }
    return null;
  }

  private parseMovePoint(value: string): GoPoint | null {
    const trimmed = String(value ?? '').trim();
    if (!trimmed) {
      return null;
    }
    if (trimmed.toLowerCase() === 'pass') {
      return [0, 0];
    }
    const numbers = trimmed.match(/-?\d+/g);
    if (numbers && numbers.length >= 2) {
      const row = Number(numbers[0]);
      const col = Number(numbers[1]);
      if (Number.isFinite(row) && Number.isFinite(col)) {
        return [row, col];
      }
    }
    const alphaMatch = trimmed.match(/([A-Za-z])\s*([0-9]+)/);
    if (alphaMatch) {
      const col = alphaMatch[1].toUpperCase().charCodeAt(0) - 64;
      const row = Number(alphaMatch[2]);
      if (Number.isFinite(row) && Number.isFinite(col)) {
        return [row, col];
      }
    }
    return null;
  }
}
