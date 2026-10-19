import { ChangeDetectionStrategy, ChangeDetectorRef, Component, Input, OnDestroy } from '@angular/core';
import type { MatchResultSummary, StatusTone } from '@main/arena.constants';
import { ArenaBannerComponent } from '../../components/arena-gui-helpers/arena-banner.component';
import { ArenaGuiAlertComponent } from '../../components/arena-gui-helpers/arena-gui-alert.component';
import { ArenaGuiEmptyComponent } from '../../components/arena-gui-helpers/arena-gui-empty.component';
import { ArenaGuiLegendComponent } from '../../components/arena-gui-helpers/arena-gui-legend.component';
import { kbdNumber } from '../../components/arena-gui-helpers/arena-kbd-keys';

type MancalaSide = 'left' | 'right';

type MancalaPitCell = {
  key: string;
  side: MancalaSide;
  pitIndex: number;
  seeds: number;
  legal: boolean;
  illegal: boolean;
  winning: boolean;
};

@Component({
  selector: 'arena-mancala-gui',
  standalone: true,
  templateUrl: './arena-mancala-gui.component.html',
  styleUrl: './arena-mancala-gui.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    ArenaBannerComponent,
    ArenaGuiAlertComponent,
    ArenaGuiEmptyComponent,
    ArenaGuiLegendComponent
  ]
})
export class ArenaMancalaGuiComponent implements OnDestroy {
  topPits: MancalaPitCell[] = [];
  bottomPits: MancalaPitCell[] = [];
  leftStore = 0;
  rightStore = 0;
  currentPlayer: number | null = null;
  boardReady = false;
  matchBannerMessage: string | null = null;
  illegalClickMessage: string | null = null;
  illegalClickToken = 0;
  hasWinner = false;

  @Input() botA = 'Automaton A';
  @Input() botB = 'Automaton B';
  @Input() statusTone: StatusTone = 'idle';
  @Input() statusMessage = '';
  @Input() showHumanControls = false;
  @Input() awaitingHumanMove = false;
  @Input() submitHumanMove?: (move: string) => void;

  private leftPits: number[] = [0, 0, 0, 0, 0, 0];
  private rightPits: number[] = [0, 0, 0, 0, 0, 0];
  private legalMovesByPit = new Map<number, string>();
  private currentLegalMoves: string[] = [];
  private illegalPit: { side: MancalaSide; pitIndex: number } | null = null;
  private bannerTimer: number | null = null;
  private lastMatchStamp: number | null = null;
  private matchWinner: number | null = null;

  constructor(private readonly cdr: ChangeDetectorRef) {}

  get activePlayerLabel(): string {
    if (this.currentPlayer === 0) {
      return this.blackPlayerName;
    }
    if (this.currentPlayer === 1) {
      return this.whitePlayerName;
    }
    return '';
  }

  get blackPlayerName(): string {
    return this.botA;
  }

  get whitePlayerName(): string {
    return this.botB;
  }


  @Input() set legalMoves(value: string[] | null) {
    this.currentLegalMoves = Array.isArray(value) ? value : [];
    this.rebuildLegalMoves();
    this.refreshPits();
  }

  get legalMoves(): string[] {
    return this.currentLegalMoves;
  }

  @Input() set illegalAction(value: string | null) {
    const parsed = this.parsePitIndex(value);
    if (parsed === null || this.currentPlayer === null) {
      this.illegalPit = null;
    } else {
      this.illegalPit = { side: this.currentPlayer === 0 ? 'right' : 'left', pitIndex: parsed };
    }
    this.refreshPits();
  }

  @Input() set matchResult(value: MatchResultSummary | null) {
    if (!value) {
      this.lastMatchStamp = null;
      this.matchWinner = null;
      this.hasWinner = false;
      this.clearBanner();
      this.refreshPits();
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
      this.refreshPits();
      return;
    }
    this.matchBannerMessage = this.resolveResultMessage(value.winner);
    this.resetBannerTimer();
    this.refreshPits();
  }

  @Input() set observation(value: unknown | null) {
    const parsed = this.parseObservation(value);
    if (!parsed) {
      this.boardReady = false;
      this.leftPits = [0, 0, 0, 0, 0, 0];
      this.rightPits = [0, 0, 0, 0, 0, 0];
      this.leftStore = 0;
      this.rightStore = 0;
      this.currentPlayer = null;
      this.topPits = [];
      this.bottomPits = [];
      return;
    }
    this.boardReady = true;
    this.leftPits = parsed.left.slice(0, 6);
    this.rightPits = parsed.right.slice(0, 6);
    this.leftStore = parsed.left[6] ?? 0;
    this.rightStore = parsed.right[6] ?? 0;
    this.currentPlayer = parsed.player;
    this.refreshPits();
  }

  /** The pit number as printed. */
  kbdLabel(pit: MancalaPitCell): string | null {
    return pit.legal && this.awaitingHumanMove && this.showHumanControls ? kbdNumber(pit.pitIndex, this.bottomPits.length) : null;
  }

  onPitClick(pit: MancalaPitCell): void {
    if (!this.awaitingHumanMove || !this.submitHumanMove) {
      return;
    }
    const expectedSide: MancalaSide | null =
      this.currentPlayer === 0 ? 'right' : this.currentPlayer === 1 ? 'left' : null;
    if (!expectedSide || pit.side !== expectedSide) {
      this.showIllegalClick('Select a legal pit on your side.');
      return;
    }
    const move = this.legalMovesByPit.get(pit.pitIndex);
    if (!move) {
      this.showIllegalClick('Illegal move.');
      return;
    }
    this.submitHumanMove(move);
  }

  isStoreWinning(side: MancalaSide): boolean {
    if (this.matchWinner === null) {
      return false;
    }
    if (this.matchWinner === 0) {
      return side === 'right';
    }
    if (this.matchWinner === 1) {
      return side === 'left';
    }
    return false;
  }

  ngOnDestroy(): void {
    this.clearBannerTimer();
  }

  private parseObservation(value: unknown | null): {
    left: number[];
    right: number[];
    player: number | null;
  } | null {
    if (!value || typeof value !== 'object') {
      return null;
    }
    const statePlayer = value as { state?: unknown; player?: unknown };
    const record = (statePlayer.state ?? value) as Record<string, unknown>;
    const left = this.parseSide(record['left_player'] ?? record['left']);
    const right = this.parseSide(record['right_player'] ?? record['right']);
    if (!left || !right || left.length < 7 || right.length < 7) {
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
    return { left, right, player };
  }

  private parseSide(value: unknown): number[] | null {
    let entries: unknown[] | null = null;
    if (Array.isArray(value) || ArrayBuffer.isView(value)) {
      entries = Array.from(value as Iterable<unknown>);
    } else if (value && typeof value === 'object') {
      const sorted = Object.entries(value as Record<string, unknown>)
        .map(([key, cell]) => ({ index: Number(key), cell }))
        .filter(({ index }) => Number.isInteger(index) && index >= 0)
        .sort((a, b) => a.index - b.index);
      if (sorted.length === 0) {
        return null;
      }
      entries = sorted.map((entry) => entry.cell);
    }
    if (!entries || entries.length < 7) {
      return null;
    }
    const parsed: number[] = [];
    for (const entry of entries.slice(0, 7)) {
      const num = Number(entry);
      if (!Number.isFinite(num)) {
        return null;
      }
      parsed.push(Math.max(0, Math.floor(num)));
    }
    return parsed;
  }

  private rebuildLegalMoves(): void {
    this.legalMovesByPit.clear();
    for (const move of this.currentLegalMoves) {
      const pitIndex = this.parsePitIndex(move);
      if (pitIndex === null) {
        continue;
      }
      if (!this.legalMovesByPit.has(pitIndex)) {
        this.legalMovesByPit.set(pitIndex, move);
      }
    }
  }

  private refreshPits(): void {
    const canHighlight = this.awaitingHumanMove && this.showHumanControls;
    this.topPits = this.buildPitRow('left', this.leftPits, true, canHighlight);
    this.bottomPits = this.buildPitRow('right', this.rightPits, false, canHighlight);
    this.cdr.markForCheck();
  }

  private buildPitRow(
    side: MancalaSide,
    pits: number[],
    reverseOrder: boolean,
    canHighlight: boolean
  ): MancalaPitCell[] {
    const cells: MancalaPitCell[] = [];
    const iterable = reverseOrder ? [...pits.keys()].reverse() : [...pits.keys()];
    for (const pitIndex of iterable) {
      const expectedSide: MancalaSide | null =
        this.currentPlayer === 0 ? 'right' : this.currentPlayer === 1 ? 'left' : null;
      const legal = canHighlight && expectedSide === side && this.legalMovesByPit.has(pitIndex);
      const illegal =
        Boolean(this.illegalPit) &&
        this.illegalPit?.side === side &&
        this.illegalPit.pitIndex === pitIndex;
      const winning =
        this.matchWinner !== null &&
        ((this.matchWinner === 0 && side === 'right') || (this.matchWinner === 1 && side === 'left'));
      cells.push({
        key: `${side}-${pitIndex}`,
        side,
        pitIndex,
        seeds: pits[pitIndex] ?? 0,
        legal,
        illegal,
        winning
      });
    }
    return cells;
  }

  private parsePitIndex(value: string | null): number | null {
    const raw = String(value ?? '').trim();
    if (!raw) {
      return null;
    }
    const match = raw.match(/-?\d+/);
    if (!match) {
      return null;
    }
    const pit = Number(match[0]);
    if (!Number.isInteger(pit) || pit < 0 || pit > 5) {
      return null;
    }
    return pit;
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
}
