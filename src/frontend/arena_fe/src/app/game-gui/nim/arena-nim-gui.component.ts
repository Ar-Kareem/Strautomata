import { ChangeDetectionStrategy, ChangeDetectorRef, Component, Input, OnDestroy } from '@angular/core';
import type { MatchResultSummary, StatusTone } from '@main/arena.constants';

type NimToken = {
  key: string;
  pileIndex: number;
  take: number;
  offset: number;
  legalTake: boolean;
  illegal: boolean;
  inactive: boolean;
  leftHighlight: boolean;
  hovered: boolean;
};

type NimPile = {
  key: string;
  index: number;
  count: number;
  tokens: NimToken[];
  selectable: boolean;
  selected: boolean;
};

@Component({
  selector: 'arena-nim-gui',
  standalone: true,
  templateUrl: './arena-nim-gui.component.html',
  styleUrl: './arena-nim-gui.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ArenaNimGuiComponent implements OnDestroy {
  piles: NimPile[] = [];
  totalObjects = 0;
  maxPileSize = 0;
  tokenSize = 18;
  currentPlayer: number | null = null;
  matchBannerMessage: string | null = null;
  hasWinner = false;
  @Input() botA = 'Automaton A';
  @Input() botB = 'Automaton B';
  @Input() statusTone: StatusTone = 'idle';
  @Input() statusMessage = '';
  @Input() showHumanControls = false;
  private awaitingHuman = false;
  @Input() set awaitingHumanMove(value: boolean) {
    this.awaitingHuman = value;
    this.hoveredOffsetByPile.clear();
    if (!value) {
      this.selectedPile = null;
    } else {
      this.suppressLegalHighlights = false;
    }
    this.refreshPiles();
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
  selectedPile: number | null = null;
  private pileCounts: number[] = [];
  private bannerTimer: number | null = null;
  private lastMatchStamp: number | null = null;
  private matchWinner: number | null = null;
  private matchIllegal = false;
  private currentLegalMoves: string[] = [];
  private legalMovesByKey = new Map<string, string>();
  private legalTakesByPile = new Map<number, Set<number>>();
  private selectablePiles = new Set<number>();
  private illegalMove: { pile: number; take: number } | null = null;
  private suppressLegalHighlights = false;
  private hoveredOffsetByPile = new Map<number, number>();

  constructor(private readonly cdr: ChangeDetectorRef) {
    (window as any).GUI_COMPONENT = this;
  }

  @Input() set legalMoves(value: string[] | null) {
    this.currentLegalMoves = Array.isArray(value) ? value : [];
    this.rebuildLegalMoves(true);
    this.refreshPiles();
  }

  get legalMoves(): string[] {
    return this.currentLegalMoves;
  }

  @Input() set illegalAction(value: string | null) {
    this.illegalMove = this.parseMove(value, this.pileCounts.length);
    this.refreshPiles();
  }

  @Input() set matchResult(value: MatchResultSummary | null) {
    if (!value) {
      this.lastMatchStamp = null;
      this.matchWinner = null;
      this.matchIllegal = false;
      this.hasWinner = false;
      this.refreshPiles();
      this.clearBanner();
      return;
    }
    if (this.lastMatchStamp === value.finishedAt) {
      return;
    }
    this.lastMatchStamp = value.finishedAt;
    this.matchIllegal = value.illegal;
    this.matchWinner = value.illegal ? null : value.winner;
    this.hasWinner = this.matchWinner !== null && !this.matchIllegal;
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
      this.piles = [];
      this.pileCounts = [];
      this.totalObjects = 0;
      this.maxPileSize = 0;
      this.currentPlayer = null;
      this.hoveredOffsetByPile.clear();
      return;
    }
    this.pileCounts = parsed.piles;
    this.currentPlayer = parsed.player;
    if (this.selectedPile !== null && (this.selectedPile < 0 || this.selectedPile >= this.pileCounts.length)) {
      this.selectedPile = null;
    }
    this.hoveredOffsetByPile.clear();
    this.updateMetrics();
    this.rebuildLegalMoves(false);
    this.refreshPiles();
  }

  onTokenClick(event: Event, token: NimToken): void {
    event.stopPropagation();
    if (!this.awaitingHumanMove || !this.submitHumanMove) {
      return;
    }
    const pileIndex = token.pileIndex;
    if (this.selectedPile === null) {
      if (!this.selectablePiles.has(pileIndex)) {
        this.showIllegalClick('Select a legal pile.');
        return;
      }
      const pileTakes = this.legalTakesByPile.get(pileIndex);
      if (pileTakes && pileTakes.has(token.take)) {
        const move = this.legalMovesByKey.get(`${pileIndex}|${token.take}`) ?? `${pileIndex},${token.take}`;
        this.suppressLegalHighlights = true;
        this.refreshPiles();
        this.submitHumanMove(move);
        return;
      }
      this.selectedPile = pileIndex;
      this.refreshPiles();
      return;
    }
    if (this.selectedPile !== pileIndex) {
      if (!this.selectablePiles.has(pileIndex)) {
        this.showIllegalClick('Select a legal pile.');
        return;
      }
      this.selectedPile = pileIndex;
      this.refreshPiles();
      return;
    }
    const move = this.legalMovesByKey.get(`${pileIndex}|${token.take}`);
    if (!move) {
      this.showIllegalClick('Illegal move.');
      return;
    }
    this.selectedPile = null;
    this.suppressLegalHighlights = true;
    this.refreshPiles();
    this.submitHumanMove(move);
  }

  onTokenEnter(token: NimToken): void {
    if (!this.awaitingHumanMove) {
      return;
    }
    this.hoveredOffsetByPile.set(token.pileIndex, token.offset);
    this.refreshPiles();
  }

  onTokenLeave(token: NimToken): void {
    if (!this.awaitingHumanMove) {
      return;
    }
    const current = this.hoveredOffsetByPile.get(token.pileIndex);
    if (current === token.offset) {
      this.hoveredOffsetByPile.delete(token.pileIndex);
      this.refreshPiles();
    }
  }


  ngOnDestroy(): void {
    this.clearBannerTimer();
  }

  private parseObservation(value: unknown | null): { piles: number[]; player: number | null } | null {
    if (!value || typeof value !== 'object') {
      return null;
    }
    const statePlayer = value as { state?: unknown; player?: unknown };
    const record = (statePlayer.state ?? value) as Record<string, unknown>;
    const piles = this.parsePiles(record['piles'] ?? (value as { piles?: unknown }).piles);
    if (!piles) {
      return null;
    }
    const player =
      typeof statePlayer.player === 'number'
        ? statePlayer.player
        : typeof record['player'] === 'number'
          ? (record['player'] as number)
          : typeof record['turn'] === 'number'
            ? (record['turn'] as number)
            : null;
    return { piles, player };
  }

  private parsePiles(value: unknown): number[] | null {
    if (!Array.isArray(value)) {
      return null;
    }
    const piles: number[] = [];
    for (const entry of value) {
      const count = Number(entry);
      if (!Number.isFinite(count)) {
        return null;
      }
      piles.push(Math.max(0, Math.floor(count)));
    }
    return piles;
  }

  private parseMove(value: string | null, numPiles: number): { pile: number; take: number } | null {
    if (!value) {
      return null;
    }
    const trimmed = String(value).trim();
    if (!trimmed) {
      return null;
    }
    const pileMatch = trimmed.match(/pile\s*[:=]\s*(-?\d+)/i);
    const takeMatch = trimmed.match(/take\s*[:=]\s*(-?\d+)/i);
    if (pileMatch && takeMatch) {
      const pile = Number(pileMatch[1]);
      const take = Number(takeMatch[1]);
      if (Number.isFinite(pile) && Number.isFinite(take) && take > 0) {
        if (numPiles > 0 && (pile < 0 || pile >= numPiles)) {
          return null;
        }
        return { pile, take };
      }
    }
    const numbers = trimmed.match(/-?\d+/g);
    if (numbers) {
      if (numbers.length >= 2) {
        const pile = Number(numbers[0]);
        const take = Number(numbers[1]);
        if (Number.isFinite(pile) && Number.isFinite(take) && take > 0) {
          if (numPiles > 0 && (pile < 0 || pile >= numPiles)) {
            return null;
          }
          return { pile, take };
        }
      }
      if (numbers.length === 1 && numPiles > 0) {
        const action = Number(numbers[0]);
        if (!Number.isFinite(action) || action < 0) {
          return null;
        }
        const pile = action % numPiles;
        const take = Math.floor(action / numPiles) + 1;
        return { pile, take };
      }
    }
    return null;
  }

  private updateMetrics(): void {
    this.totalObjects = this.pileCounts.reduce((total, count) => total + count, 0);
    this.maxPileSize = this.pileCounts.reduce((max, count) => Math.max(max, count), 0);
    if (this.maxPileSize > 0) {
      this.tokenSize = Math.max(18, Math.min(28, Math.floor(320 / this.maxPileSize)));
    }
  }

  private rebuildLegalMoves(resetSelection: boolean): void {
    this.legalMovesByKey.clear();
    this.legalTakesByPile.clear();
    this.selectablePiles.clear();
    if (resetSelection) {
      this.selectedPile = null;
    }
    if (this.awaitingHumanMove) {
      this.suppressLegalHighlights = false;
    }
    const numPiles = this.pileCounts.length;
    for (const move of this.currentLegalMoves) {
      const parsed = this.parseMove(move, numPiles);
      if (!parsed) {
        continue;
      }
      const { pile, take } = parsed;
      if (take <= 0) {
        continue;
      }
      if (numPiles > 0 && (pile < 0 || pile >= numPiles)) {
        continue;
      }
      const key = `${pile}|${take}`;
      if (!this.legalMovesByKey.has(key)) {
        this.legalMovesByKey.set(key, move);
      }
      this.selectablePiles.add(pile);
      let pileTakes = this.legalTakesByPile.get(pile);
      if (!pileTakes) {
        pileTakes = new Set<number>();
        this.legalTakesByPile.set(pile, pileTakes);
      }
      pileTakes.add(take);
    }
    if (this.legalMovesByKey.size === 0) {
      this.populateFallbackLegalMoves();
    }
    if (this.selectedPile !== null && !this.selectablePiles.has(this.selectedPile)) {
      this.selectedPile = null;
    }
  }

  private populateFallbackLegalMoves(): void {
    for (let index = 0; index < this.pileCounts.length; index += 1) {
      const count = this.pileCounts[index];
      if (count <= 0) {
        continue;
      }
      this.selectablePiles.add(index);
      let pileTakes = this.legalTakesByPile.get(index);
      if (!pileTakes) {
        pileTakes = new Set<number>();
        this.legalTakesByPile.set(index, pileTakes);
      }
      for (let take = 1; take <= count; take += 1) {
        const key = `${index}|${take}`;
        if (!this.legalMovesByKey.has(key)) {
          this.legalMovesByKey.set(key, `${index},${take}`);
        }
        pileTakes.add(take);
      }
    }
  }

  private refreshPiles(): void {
    const allowLegal = this.awaitingHumanMove && !this.suppressLegalHighlights;
    const selectablePiles = allowLegal ? this.selectablePiles : new Set<number>();
    const legalTakesByPile = allowLegal ? this.legalTakesByPile : new Map<number, Set<number>>();
    this.piles = this.buildPiles(
      this.pileCounts,
      selectablePiles,
      legalTakesByPile,
      this.selectedPile,
      this.illegalMove
    );
    this.cdr.markForCheck();
  }

  private buildPiles(
    counts: number[],
    selectablePiles: Set<number>,
    legalTakesByPile: Map<number, Set<number>>,
    selectedPile: number | null,
    illegalMove: { pile: number; take: number } | null
  ): NimPile[] {
    const allowHover = this.awaitingHumanMove;
    return counts.map((count, index) => {
      const offsets = this.buildOffsets(count);
      const takeByIndex = this.buildTakeMapping(offsets);
      const pileTakes = legalTakesByPile.get(index) ?? new Set<number>();
      const hoveredOffset = allowHover ? this.hoveredOffsetByPile.get(index) ?? null : null;
      const tokens: NimToken[] = [];
      for (let offset = 0; offset < count; offset += 1) {
        const take = takeByIndex.get(offset) ?? offset + 1;
        const tokenOffset = offsets[offset] ?? 0;
        const legalTake = selectedPile === index && pileTakes.has(take);
        const illegal = Boolean(illegalMove && illegalMove.pile === index && illegalMove.take === take);
        const inactive = selectedPile === index && !pileTakes.has(take);
        const leftHighlight = hoveredOffset !== null && tokenOffset <= hoveredOffset;
        const hovered = hoveredOffset !== null && tokenOffset === hoveredOffset;
        tokens.push({
          key: `pile-${index}-take-${take}`,
          pileIndex: index,
          take,
          offset: tokenOffset,
          legalTake,
          illegal,
          inactive,
          leftHighlight,
          hovered
        });
      }
      return {
        key: `pile-${index}`,
        index,
        count,
        tokens,
        selectable: selectablePiles.has(index),
        selected: selectedPile === index
      };
    });
  }

  private buildOffsets(count: number): number[] {
    const offsets: number[] = [];
    for (let index = 0; index < count; index += 1) {
      const isEven = count % 2 === 0;
      if (!isEven && index === 0) {
        offsets.push(0);
        continue;
      }
      const step = isEven ? Math.ceil((index + 1) / 2) : Math.ceil(index / 2);
      const direction = isEven ? (index % 2 === 0 ? -1 : 1) : index % 2 === 1 ? -1 : 1;
      const shift = isEven ? 0.5 : 0;
      offsets.push((step - shift) * direction);
    }
    return offsets;
  }

  private buildTakeMapping(offsets: number[]): Map<number, number> {
    const ordered = offsets
      .map((value, index) => ({ value, index }))
      .sort((a, b) => a.value - b.value);
    const mapping = new Map<number, number>();
    ordered.forEach((entry, idx) => {
      mapping.set(entry.index, idx + 1);
    });
    return mapping;
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
