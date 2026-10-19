import { ModelLogoComponent } from '../shared/model-logo.component';
import { NgTemplateOutlet } from '@angular/common';
import { ChangeDetectionStrategy, Component, DestroyRef, ElementRef, HostListener, computed, effect, inject, input, output, signal, untracked } from '@angular/core';
import type { PairwiseCounts } from '@main/history.types';
import { familyColor, pairScore, shareColor } from './history-format';

export interface HeatmapCell {
  row: string;
  col: string;
  color: string;
  share: number | null;
  /** tooltip lines under the "row vs col" heading */
  lines: string[];
  /** accessible name of the square */
  label: string;
  isDiagonal: boolean;
}

type HoverTip = { row: string; col: string; lines: string[]; left: number; top: number };

@Component({
  selector: 'matches-heatmap',
  standalone: true,
  imports: [ModelLogoComponent, NgTemplateOutlet],
  templateUrl: './matches-heatmap.component.html',
  styleUrl: './matches-heatmap.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class MatchesHeatmapComponent {
  private readonly host = inject<ElementRef<HTMLElement>>(ElementRef);
  readonly bots = input.required<string[]>();
  readonly labels = input.required<Record<string, string>>();
  readonly families = input<Record<string, string>>({});
  readonly pairwise = input.required<Record<string, PairwiseCounts>>();
  readonly compact = input(false);
  /** Fixed cell size in px (full screen); null = size from the number of rows. */
  readonly cellOverride = input<number | null>(null);
  /** Use the full screen height (full-screen mode) instead of the 640px scroll box. */
  readonly fill = input(false);
  /** Clicked cell: its row and column are highlighted. */
  readonly picked = signal<{ row: string; col: string } | null>(null);
  readonly selectedRow = computed(() => this.picked()?.row ?? null);
  readonly selectedCol = computed(() => this.picked()?.col ?? null);
  /** "View replays" in the pinned tooltip: open the matches between row and column */
  readonly openPair = output<{ row: string; col: string }>();
  /** where the pinned (clicked) tooltip is drawn, next to its cell */
  readonly pinPos = signal<{ left: number; top: number } | null>(null);
  readonly pinnedCell = computed(() => {
    const pick = this.picked();
    if (!pick) {
      return null;
    }
    const bots = this.bots();
    return this.cells()[bots.indexOf(pick.row)]?.[bots.indexOf(pick.col)] ?? null;
  });

  constructor() {
    // a pin whose row or column was filtered away goes away with it
    effect(() => {
      if (this.picked() && !this.pinnedCell()) {
        untracked(() => this.unpin());
      }
    });
    // keep the pinned tooltip next to its cell while the page or the heatmap scrolls
    const onScroll = () => this.placePin();
    window.addEventListener('scroll', onScroll, true);
    window.addEventListener('resize', onScroll);
    inject(DestroyRef).onDestroy(() => {
      window.removeEventListener('scroll', onScroll, true);
      window.removeEventListener('resize', onScroll);
    });
  }

  readonly familyColor = familyColor;

  readonly cellSize = computed(() => {
    const override = this.cellOverride();
    if (override) {
      return override;
    }
    const n = this.bots().length;
    if (this.compact()) {
      return 26;
    }
    if (n <= 12) {
      return 30;
    }
    if (n <= 30) {
      return 20;
    }
    if (n <= 60) {
      return 14;
    }
    return 11;
  });

  readonly cells = computed<HeatmapCell[][]>(() => {
    const bots = this.bots();
    const labels = this.labels();
    const pairwise = this.pairwise();
    return bots.map((row) =>
      bots.map((col) => {
        if (row === col) {
          return { row, col, color: 'transparent', share: null, lines: [], label: '', isDiagonal: true };
        }
        const { share, counts, rowIsA } = pairScore(pairwise, row, col);
        const lines: string[] = [];
        if (counts) {
          const [n, aWins, bWins, draws, aErr, bErr, aTo, bTo] = counts;
          const rowWins = rowIsA ? aWins : bWins;
          const colWins = rowIsA ? bWins : aWins;
          const rowErr = rowIsA ? aErr : bErr;
          const colErr = rowIsA ? bErr : aErr;
          const rowTo = rowIsA ? aTo : bTo;
          const colTo = rowIsA ? bTo : aTo;
          lines.push(`${n} games · row wins ${rowWins} · col wins ${colWins} · draws ${draws}`);
          lines.push(`row faults ${rowErr + rowTo} (err ${rowErr}, timeout ${rowTo}) · col faults ${colErr + colTo}`);
          lines.push(`row score ${share === null ? '–' : Math.round(share * 100) + '%'}`);
        } else {
          lines.push('no games');
        }
        const vs = `${labels[row] ?? row} vs ${labels[col] ?? col}`;
        const label = counts ? `${vs}: row score ${share === null ? 'none' : Math.round(share * 100) + '%'}` : `${vs}: no games`;
        return { row, col, color: shareColor(share), share, lines, label, isDiagonal: false };
      })
    );
  });

  readonly tip = signal<HoverTip | null>(null);
  /** the one square in the tab order (roving tabindex); arrow keys move it */
  readonly focusPos = signal<{ r: number; c: number }>({ r: 0, c: 1 });

  /** Keyboard focus shows the same details as hovering. */
  onGridFocus(event: FocusEvent): void {
    const target = (event.target as HTMLElement).closest<HTMLElement>('.hm-cell');
    if (!target) {
      return;
    }
    const r = Number(target.dataset['r']);
    const c = Number(target.dataset['c']);
    this.focusPos.set({ r, c });
    const cell = this.cells()[r]?.[c];
    const pick = this.picked();
    if (!cell || cell.isDiagonal || (pick?.row === cell.row && pick.col === cell.col)) {
      this.tip.set(null);
      return;
    }
    const rect = target.getBoundingClientRect();
    const width = 420;
    const left = rect.right + 10 + width > window.innerWidth ? rect.left - 10 - width : rect.right + 10;
    const top = Math.min(rect.bottom + 6, window.innerHeight - 110);
    this.tip.set({ row: cell.row, col: cell.col, lines: cell.lines, left: Math.max(8, left), top });
  }

  onGridBlur(event: FocusEvent): void {
    const next = event.relatedTarget as Node | null;
    if (!next || !(event.currentTarget as HTMLElement).contains(next)) {
      this.tip.set(null);
    }
  }

  /** Arrow keys / Home / End move between squares, skipping the diagonal. */
  onGridKey(event: KeyboardEvent): void {
    const target = (event.target as HTMLElement).closest<HTMLElement>('.hm-cell');
    const n = this.bots().length;
    if (!target || n < 2) {
      return;
    }
    let r = Number(target.dataset['r']);
    let c = Number(target.dataset['c']);
    const step: Record<string, [number, number]> = { ArrowUp: [-1, 0], ArrowDown: [1, 0], ArrowLeft: [0, -1], ArrowRight: [0, 1] };
    if (step[event.key]) {
      const [dr, dc] = step[event.key];
      const clamp = (v: number) => Math.max(0, Math.min(n - 1, v));
      let nr = clamp(r + dr);
      let nc = clamp(c + dc);
      if (nr === nc) {
        // hop over the diagonal; stay put at the edge
        const hr = clamp(nr + dr);
        const hc = clamp(nc + dc);
        if (hr === hc) {
          nr = r;
          nc = c;
        } else {
          nr = hr;
          nc = hc;
        }
      }
      r = nr;
      c = nc;
    } else if (event.key === 'Home') {
      c = r === 0 ? 1 : 0;
    } else if (event.key === 'End') {
      c = r === n - 1 ? n - 2 : n - 1;
    } else {
      return;
    }
    event.preventDefault();
    this.focusPos.set({ r, c });
    this.host.nativeElement.querySelector<HTMLElement>(`.hm-cell[data-r="${r}"][data-c="${c}"]`)?.focus();
  }

  /** One listener for the whole grid: show the custom tooltip for the hovered cell right away. */
  onGridPointer(event: PointerEvent): void {
    const target = (event.target as HTMLElement).closest<HTMLElement>('.hm-cell');
    const r = Number(target?.dataset['r']);
    const c = Number(target?.dataset['c']);
    const cell = target ? this.cells()[r]?.[c] : undefined;
    const pick = this.picked();
    if (!cell || cell.isDiagonal || (pick?.row === cell.row && pick.col === cell.col)) {
      this.tip.set(null); // the pinned cell already shows its tooltip
      return;
    }
    const width = 420;
    const left = event.clientX + 16 + width > window.innerWidth ? event.clientX - 16 - width : event.clientX + 16;
    const top = Math.min(event.clientY + 16, window.innerHeight - 110);
    this.tip.set({ row: cell.row, col: cell.col, lines: cell.lines, left: Math.max(8, left), top });
  }

  hideTip(): void {
    this.tip.set(null);
  }

  labelOf(bot: string): string {
    return this.labels()[bot] ?? bot;
  }

  /** Pin the cell: highlight its row and column and keep its tooltip open; clicking it again unpins. */
  onCell(cell: HeatmapCell): void {
    if (cell.isDiagonal) {
      return;
    }
    const current = this.picked();
    if (current?.row === cell.row && current.col === cell.col) {
      this.unpin();
      return;
    }
    this.picked.set({ row: cell.row, col: cell.col });
    this.tip.set(null);
    this.placePin();
  }

  unpin(): void {
    this.picked.set(null);
    this.pinPos.set(null);
  }

  viewReplays(): void {
    const pick = this.picked();
    if (pick) {
      this.openPair.emit(pick);
    }
  }

  @HostListener('document:keydown.escape')
  onEscape(): void {
    this.unpin();
  }

  /** Put the pinned tooltip beside its cell, flipping left/up when it would leave the screen. */
  private placePin(): void {
    const pick = this.picked();
    if (!pick) {
      return;
    }
    const bots = this.bots();
    const el = this.host.nativeElement.querySelector<HTMLElement>(
      `.hm-cell[data-r="${bots.indexOf(pick.row)}"][data-c="${bots.indexOf(pick.col)}"]`
    );
    if (!el) {
      return;
    }
    const rect = el.getBoundingClientRect();
    const width = 420;
    const height = 140;
    const left = rect.right + 10 + width > window.innerWidth ? rect.left - 10 - width : rect.right + 10;
    const top = rect.bottom + 6 + height > window.innerHeight ? rect.top - 6 - height : rect.bottom + 6;
    this.pinPos.set({ left: Math.max(8, left), top: Math.max(8, top) });
  }
}
