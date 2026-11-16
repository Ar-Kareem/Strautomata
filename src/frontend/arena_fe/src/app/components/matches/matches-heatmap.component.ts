import { ModelLogoComponent } from '../shared/model-logo.component';
import { NgTemplateOutlet } from '@angular/common';
import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  ElementRef,
  HostListener,
  afterRenderEffect,
  computed,
  effect,
  inject,
  input,
  output,
  signal,
  untracked,
  viewChild
} from '@angular/core';
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
type Pos = { r: number; c: number };

/** px between squares, the grid's `gap` */
const GAP = 1;

/**
 * Head-to-head grid. The squares are drawn on one canvas (an n×n grid of elements froze the page
 * for 100+ automata); the row and column labels stay elements so they can stick while scrolling.
 */
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
  private readonly canvas = viewChild.required<ElementRef<HTMLCanvasElement>>('canvas');
  private readonly scroller = viewChild.required<ElementRef<HTMLElement>>('scroller');
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
    const r = bots.indexOf(pick.row);
    const c = bots.indexOf(pick.col);
    return r < 0 || c < 0 ? null : this.cellAt(r, c);
  });

  /** square under the pointer (drawn raised) */
  readonly hover = signal<Pos | null>(null);
  /** the keyboard's square; drawn with a focus ring while the canvas has focus */
  readonly focusPos = signal<Pos>({ r: 0, c: 1 });
  readonly hasFocus = signal(false);
  /** spoken when the keyboard moves to a square */
  readonly focusLabel = computed(() => {
    const { r, c } = this.focusPos();
    return this.hasFocus() && r < this.bots().length && c < this.bots().length ? this.cellAt(r, c).label : '';
  });

  constructor() {
    // a pin whose row or column was filtered away goes away with it
    effect(() => {
      if (this.picked() && !this.pinnedCell()) {
        untracked(() => this.unpin());
      }
    });
    afterRenderEffect(() => this.draw());
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

  /** CSS px size of the canvas: n squares and the gaps between them */
  readonly gridPx = computed(() => {
    const n = this.bots().length;
    return Math.max(0, n * this.cellSize() + (n - 1) * GAP);
  });

  /** fill color of every square, row-major */
  readonly colors = computed<string[]>(() => {
    const bots = this.bots();
    const pairwise = this.pairwise();
    const out: string[] = [];
    for (const row of bots) {
      for (const col of bots) {
        out.push(row === col ? '' : shareColor(pairScore(pairwise, row, col).share));
      }
    }
    return out;
  });

  /** The details of one square, built when it is hovered, focused or pinned. */
  cellAt(r: number, c: number): HeatmapCell {
    const bots = this.bots();
    const row = bots[r];
    const col = bots[c];
    if (row === col) {
      return { row, col, color: 'transparent', share: null, lines: [], label: '', isDiagonal: true };
    }
    const labels = this.labels();
    const { share, counts, rowIsA } = pairScore(this.pairwise(), row, col);
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
  }

  readonly tip = signal<HoverTip | null>(null);

  private draw(): void {
    const el = this.canvas().nativeElement;
    const n = this.bots().length;
    const size = this.cellSize();
    const px = this.gridPx();
    const colors = this.colors();
    const pick = this.picked();
    const bots = this.bots();
    const pr = pick ? bots.indexOf(pick.row) : -1;
    const pc = pick ? bots.indexOf(pick.col) : -1;
    const hover = this.hover();
    const focus = this.hasFocus() ? this.focusPos() : null;

    const dpr = window.devicePixelRatio || 1;
    const w = Math.round(px * dpr);
    if (el.width !== w || el.height !== w) {
      el.width = w;
      el.height = w;
    }
    const ctx = el.getContext('2d');
    if (!ctx) {
      return;
    }
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, px, px);
    if (!n) {
      return;
    }
    const styles = getComputedStyle(this.host.nativeElement);
    const cssVar = (name: string, fallback: string) => styles.getPropertyValue(name).trim() || fallback;
    const step = size + GAP;
    const radius = Math.min(2, size / 4);
    const square = (x: number, y: number, s: number) => {
      ctx.beginPath();
      ctx.roundRect(x, y, s, s, radius);
    };

    // diagonal: hatched
    const hatch = document.createElement('canvas');
    hatch.width = hatch.height = 4;
    const hctx = hatch.getContext('2d')!;
    hctx.strokeStyle = 'rgba(255, 255, 255, 0.06)';
    hctx.lineWidth = 2;
    hctx.beginPath();
    hctx.moveTo(-1, 5);
    hctx.lineTo(5, -1);
    hctx.stroke();
    const hatchFill = ctx.createPattern(hatch, 'repeat');

    for (let r = 0; r < n; r++) {
      for (let c = 0; c < n; c++) {
        const lit = pr < 0 || r === pr || c === pc;
        ctx.globalAlpha = lit ? 1 : 0.35;
        ctx.fillStyle = r === c ? hatchFill ?? 'transparent' : colors[r * n + c];
        square(c * step, r * step, size);
        ctx.fill();
      }
    }
    ctx.globalAlpha = 1;

    // the picked cell's row and column, then the cell itself
    if (pr >= 0) {
      ctx.strokeStyle = 'rgba(255, 210, 120, 0.55)';
      ctx.lineWidth = 1;
      for (let i = 0; i < n; i++) {
        ctx.strokeRect(i * step + 0.5, pr * step + 0.5, size - 1, size - 1);
        ctx.strokeRect(pc * step + 0.5, i * step + 0.5, size - 1, size - 1);
      }
      ctx.strokeStyle = cssVar('--accent-3', '#ffd278');
      ctx.lineWidth = 2;
      ctx.strokeRect(pc * step + 1, pr * step + 1, size - 2, size - 2);
    }

    // hovered / focused cell: raised above its neighbours
    const raise = (pos: Pos, scale: number, outline: string, width: number) => {
      if (pos.r === pos.c || pos.r >= n || pos.c >= n) {
        return;
      }
      const s = size * scale;
      const x = pos.c * step + size / 2 - s / 2;
      const y = pos.r * step + size / 2 - s / 2;
      ctx.fillStyle = 'rgb(6, 12, 8)';
      square(x, y, s);
      ctx.fill();
      ctx.fillStyle = colors[pos.r * n + pos.c];
      ctx.fill();
      ctx.strokeStyle = outline;
      ctx.lineWidth = width;
      ctx.strokeRect(x - width / 2, y - width / 2, s + width, s + width);
    };
    if (hover && (hover.r !== focus?.r || hover.c !== focus?.c)) {
      raise(hover, 1.35, cssVar('--ink-900', '#e8eef7'), 1);
    }
    if (focus) {
      raise(focus, 1.5, cssVar('--accent-1', '#4ea8ff'), 2);
    }
  }

  /** the square under a viewport point, or null between squares / off the grid */
  private posAt(clientX: number, clientY: number): Pos | null {
    const rect = this.canvas().nativeElement.getBoundingClientRect();
    const step = this.cellSize() + GAP;
    const x = clientX - rect.left;
    const y = clientY - rect.top;
    const c = Math.floor(x / step);
    const r = Math.floor(y / step);
    const n = this.bots().length;
    if (x < 0 || y < 0 || r >= n || c >= n || x - c * step >= this.cellSize() || y - r * step >= this.cellSize()) {
      return null;
    }
    return { r, c };
  }

  /** a square's box in viewport coordinates */
  private cellRect(pos: Pos): DOMRect {
    const rect = this.canvas().nativeElement.getBoundingClientRect();
    const step = this.cellSize() + GAP;
    return new DOMRect(rect.left + pos.c * step, rect.top + pos.r * step, this.cellSize(), this.cellSize());
  }

  /** Show the custom tooltip for the hovered cell right away. */
  onPointerMove(event: PointerEvent): void {
    const pos = this.posAt(event.clientX, event.clientY);
    const hover = this.hover();
    if (pos?.r !== hover?.r || pos?.c !== hover?.c) {
      this.hover.set(pos);
    }
    const cell = pos ? this.cellAt(pos.r, pos.c) : null;
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

  onPointerLeave(): void {
    this.hover.set(null);
    this.hideTip();
  }

  onCanvasClick(event: MouseEvent): void {
    const pos = this.posAt(event.clientX, event.clientY);
    if (pos) {
      this.focusPos.set(pos);
      this.onCell(this.cellAt(pos.r, pos.c));
    }
  }

  onFocus(): void {
    this.hasFocus.set(true);
    this.showFocusTip();
  }

  onBlur(): void {
    this.hasFocus.set(false);
    this.tip.set(null);
  }

  /** Keyboard focus shows the same details as hovering. */
  private showFocusTip(): void {
    const pos = this.focusPos();
    const cell = this.cellAt(pos.r, pos.c);
    const pick = this.picked();
    if (cell.isDiagonal || (pick?.row === cell.row && pick.col === cell.col)) {
      this.tip.set(null);
      return;
    }
    const rect = this.cellRect(pos);
    const width = 420;
    const left = rect.right + 10 + width > window.innerWidth ? rect.left - 10 - width : rect.right + 10;
    const top = Math.min(rect.bottom + 6, window.innerHeight - 110);
    this.tip.set({ row: cell.row, col: cell.col, lines: cell.lines, left: Math.max(8, left), top });
  }

  /** Arrow keys / Home / End move between squares, skipping the diagonal; Enter or Space pins. */
  onKey(event: KeyboardEvent): void {
    const n = this.bots().length;
    if (n < 2) {
      return;
    }
    let { r, c } = this.focusPos();
    r = Math.min(r, n - 1);
    c = Math.min(c, n - 1);
    const step: Record<string, [number, number]> = { ArrowUp: [-1, 0], ArrowDown: [1, 0], ArrowLeft: [0, -1], ArrowRight: [0, 1] };
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      this.onCell(this.cellAt(r, c));
      return;
    }
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
    this.scrollIntoView({ r, c });
    this.showFocusTip();
  }

  /** Scroll the box so a square is not hidden under the sticky labels or past the edge. */
  private scrollIntoView(pos: Pos): void {
    const box = this.scroller().nativeElement;
    const boxRect = box.getBoundingClientRect();
    const canvasRect = this.canvas().nativeElement.getBoundingClientRect();
    const cell = this.cellRect(pos);
    // the sticky labels cover the strip between the box's edge and the canvas's resting position
    const labelW = canvasRect.left + box.scrollLeft - boxRect.left;
    const labelH = canvasRect.top + box.scrollTop - boxRect.top;
    const pad = 4;
    if (cell.left < boxRect.left + labelW) {
      box.scrollLeft -= boxRect.left + labelW - cell.left + pad;
    } else if (cell.right > boxRect.right) {
      box.scrollLeft += cell.right - boxRect.right + pad;
    }
    if (cell.top < boxRect.top + labelH) {
      box.scrollTop -= boxRect.top + labelH - cell.top + pad;
    } else if (cell.bottom > boxRect.bottom) {
      box.scrollTop += cell.bottom - boxRect.bottom + pad;
    }
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
    const r = bots.indexOf(pick.row);
    const c = bots.indexOf(pick.col);
    if (r < 0 || c < 0) {
      return;
    }
    const rect = this.cellRect({ r, c });
    const width = 420;
    const height = 140;
    const left = rect.right + 10 + width > window.innerWidth ? rect.left - 10 - width : rect.right + 10;
    const top = rect.bottom + 6 + height > window.innerHeight ? rect.top - 6 - height : rect.bottom + 6;
    this.pinPos.set({ left: Math.max(8, left), top: Math.max(8, top) });
  }
}
