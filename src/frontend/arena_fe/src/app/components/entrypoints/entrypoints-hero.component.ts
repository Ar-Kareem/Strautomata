import { ChangeDetectionStrategy, Component, DestroyRef, ElementRef, afterNextRender, afterRenderEffect, computed, inject, signal, viewChild } from '@angular/core';
import { DecimalPipe } from '@angular/common';
import { Store } from '@ngrx/store';
import { arenaActions } from '@main/arena.store';
import { resolveBotLogo, setHashRouteState } from '@main/arena.utils';
import { PAPER_URL } from '../../paper-link';
import { AutomataTermComponent } from '../shared/automata-term.component';

type LeaderRow = { name: string; logo: string | null; elo: number };
type Bar = LeaderRow & { kind: 'model' | 'random'; pct: number };
/** A chart column: a bar, or the "+N more" gap for the models that do not fit before the random baseline. */
type Column = Bar | { kind: 'more'; name: string; count: number };
type ParetoPoint = {
  name: string; cost: number; tau: number; saturated: boolean; arena: boolean; ours: boolean;
  benchmark: string; url: string; models: number;
  astraCost: number; fableCost: number; astraEffort: string; fableEffort: string;
};
type LegendItem = { kind: 'individual' | 'arena' | 'saturated' | 'alignment'; label: string; description: string; note?: string };

/** Leaderboard column chart: px per column (sets how many models fit), plot height, Elo at the axis. */
const COL_PX = 28;
const PLOT_PX = 280;
const ELO_LO = 500;
/** Room kept above the tallest bar for its value label. */
const VALUE_PX = 16;

/** Pareto chart in px: minimum height, plot margins, axis ranges. Its size follows the card. */
const P = { height: 300, left: 60, right: 12, top: 10, bottom: 60, logLo: Math.log10(5), logHi: Math.log10(25000), tauLo: 0.2, tauHi: 0.8 };

const NAME_TOKENS: Record<string, string> = {
  gpt: 'GPT', claude: 'Claude', gemini: 'Gemini', kimi: 'Kimi', deepseek: 'DeepSeek', glm: 'GLM', qwen: 'Qwen',
  grok: 'Grok', minimax: 'MiniMax', mimo: 'MiMo', oss: 'OSS', tng: 'TNG', kat: 'KAT'
};
const EFFORTS: Record<string, string> = { low: 'Low', medium: 'Medium', high: 'High', xhigh: 'XHigh', max: 'Max' };

/** "gpt_5.5_xhigh" -> "GPT-5.5 (XHigh)", "kimi_k3" -> "Kimi K3". */
const modelName = (id: string): string => {
  const tokens = id.split('_').filter((t) => t !== 'preview' && t !== 'free');
  const effort = EFFORTS[tokens[tokens.length - 1]];
  const words = (effort ? tokens.slice(0, -1) : tokens).map((t) =>
    NAME_TOKENS[t] ?? (/^[a-z]\d/.test(t) ? t.toUpperCase() : t.charAt(0).toUpperCase() + t.slice(1))
  );
  const name = words[0] === 'GPT' && words.length > 1 ? [`GPT-${words[1]}`, ...words.slice(2)].join(' ') : words.join(' ');
  return effort ? `${name} (${effort})` : name;
};

/** Landing-page summary above the game cards: pitch, scale, leaderboard (as many models as fit), cost-alignment Pareto frontier. */
@Component({
  selector: 'arena-entrypoint-hero',
  standalone: true,
  imports: [DecimalPipe, AutomataTermComponent],
  templateUrl: './entrypoints-hero.component.html',
  styleUrl: './entrypoints-hero.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class ArenaEntrypointHeroComponent {
  private readonly store = inject(Store);
  readonly paperUrl = PAPER_URL;
  readonly alignmentHelp: LegendItem = {
    kind: 'alignment', label: 'Benchmark alignment',
    description: 'Agreement between this benchmark’s model ranking and the average ranking across other benchmarks. Higher values mean stronger agreement.',
    note: 'Click to read the BenchBench paper on arXiv.'
  };

  private readonly paretoEl = viewChild<ElementRef<SVGElement>>('pareto');
  private readonly tooltipEl = viewChild<ElementRef<HTMLDivElement>>('paretoTooltip');
  private readonly legendTooltipEl = viewChild<ElementRef<HTMLDivElement>>('legendTooltip');
  readonly legend: LegendItem[] = [
    { kind: 'individual', label: 'Individual', description: 'Each model is scored on tasks or questions independently, rather than through head-to-head comparisons with other participants.' },
    { kind: 'arena', label: 'Arena (pairwise)', description: 'Models or their outputs compete head to head and are compared in pairs.', note: 'We claim this type of benchmark is better as it is saturation resistant; Relative comparisons can still distinguish strong models compared to regular benchmarks where multiple models simply reach ~100%' },
    { kind: 'saturated', label: 'Saturated', description: 'The top five models all score above 90% on this benchmark. These small, faded points remain visible but are excluded from the Pareto frontier.' }
  ];
  readonly activeLegend = signal<(LegendItem & { left: number; top: number; width: number; maxHeight: number }) | null>(null);
  private readonly paretoWidth = signal(480);
  private readonly paretoHeight = signal(P.height);
  /** Pareto plot box in px. */
  readonly plot = computed(() => ({
    width: this.paretoWidth(),
    height: this.paretoHeight(),
    x0: P.left,
    x1: this.paretoWidth() - P.right,
    y0: P.top,
    y1: this.paretoHeight() - P.bottom
  }));
  readonly leaders = signal<LeaderRow[]>([]);
  readonly baseline = signal<number | null>(null);
  readonly points = signal<ParetoPoint[]>([]);
  readonly visiblePoints = computed(() => this.points().filter((p) => p.tau >= P.tauLo && p.tau <= P.tauHi));
  readonly activePoint = signal<ParetoPoint | null>(null);
  private tooltipTimer: ReturnType<typeof setTimeout> | undefined;
  readonly tooltip = computed(() => {
    const point = this.activePoint();
    if (!point) return null;
    const plot = this.plot();
    const bounds = this.paretoEl()?.nativeElement.getBoundingClientRect();
    const width = Math.min(270, window.innerWidth - 16);
    const x = (bounds?.left ?? 0) + this.px(point.cost) * (bounds?.width ?? plot.width) / plot.width;
    const y = (bounds?.top ?? 0) + this.py(point.tau) * (bounds?.height ?? plot.height) / plot.height;
    const top = Math.max(8, Math.min(y > window.innerHeight / 2 ? y - 300 : y + 14, window.innerHeight - 300));
    return {
      point, width, top, maxHeight: window.innerHeight - top - 8,
      left: Math.max(8, Math.min(x + 14 + width <= window.innerWidth ? x + 14 : x - width - 14, window.innerWidth - width - 8))
    };
  });

  readonly plotPx = PLOT_PX;
  private readonly columnsEl = viewChild<ElementRef<HTMLElement>>('colsEl');
  private readonly columnsWidth = signal(0);
  private readonly eloHi = computed(() => Math.ceil(Math.max(...this.leaders().map((row) => row.elo), 2000) / 100) * 100);

  /**
   * As many top models as fit the card's width, always ending on the random baseline; models cut to make room are
   * counted in a "+N more" column. Names sit inside the bar (cut with an ellipsis if the bar is too short).
   */
  readonly columns = computed<Column[]>(() => {
    const fit = Math.max(8, Math.floor(this.columnsWidth() / COL_PX));
    const bar = (row: LeaderRow, kind: Bar['kind']): Bar => ({ ...row, kind, pct: this.eloPct(row.elo) });
    const leaders = this.leaders();
    const baseline = this.baseline();
    const room = baseline === null ? fit : fit - 1;
    const shown = leaders.length <= room ? leaders : leaders.slice(0, room - 1);
    const out: Column[] = shown.map((row) => bar(row, 'model'));
    if (shown.length < leaders.length) {
      out.push({ kind: 'more', name: 'more', count: leaders.length - shown.length });
    }
    if (baseline !== null) {
      out.push(bar({ name: 'Random', logo: null, elo: baseline }, 'random'));
    }
    return out;
  });

  readonly eloTicks = computed(() =>
    [1000, 1400, 1800, 2200].filter((v) => v < this.eloHi()).map((v) => ({ pct: this.eloPct(v), label: String(v) }))
  );

  readonly xTicks = computed(() =>
    [10, 100, 1000, 10000].map((v) => ({ x: this.px(v), label: v >= 1000 ? `$${v / 1000}k` : `$${v}` }))
  );
  readonly yTicks = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8].map((v) => ({ y: this.py(v), label: v.toFixed(1) }));

  /** Highest alignment reachable at each cost, over non-saturated benchmarks. */
  readonly frontier = computed(() => {
    let best = -Infinity;
    const pts: { x: number; y: number }[] = [];
    for (const p of this.visiblePoints()) {
      if (!p.saturated && p.tau > best) {
        best = p.tau;
        pts.push({ x: this.px(p.cost), y: this.py(p.tau) });
      }
    }
    // Label the widest segment on the lower-cost side of Strautomata.
    const ours = this.visiblePoints().find((p) => p.ours);
    const labelMaxX = ours ? this.px(ours.cost) : Infinity;
    let label: { x: number; y: number; angle: number } | null = null;
    let widest = 0;
    for (let i = 1; i < pts.length; i++) {
      const [p0, p1] = [pts[i - 1], pts[i]];
      if (p1.x <= labelMaxX && p1.x - p0.x > widest) {
        widest = p1.x - p0.x;
        label = { x: (p0.x + p1.x) / 2, y: (p0.y + p1.y) / 2 - 7, angle: (Math.atan2(p1.y - p0.y, p1.x - p0.x) * 180) / Math.PI };
      }
    }
    return { points: pts.map((p) => `${p.x},${p.y}`).join(' '), label };
  });

  constructor() {
    // The top layer keeps the tooltip above sibling panels and outside their clipping.
    afterRenderEffect(() => {
      for (const tooltip of [this.tooltipEl()?.nativeElement, this.legendTooltipEl()?.nativeElement]) {
        if (tooltip && !tooltip.matches(':popover-open')) tooltip.showPopover();
      }
    });
    void this.loadLeaders();
    void this.loadPareto();
    const destroyRef = inject(DestroyRef);
    afterNextRender(() => {
      const observer = new ResizeObserver((entries) => {
        for (const entry of entries) {
          const width = entry.contentRect.width;
          if (entry.target === this.columnsEl()?.nativeElement) {
            this.columnsWidth.set(width);
          } else if (width > 0) {
            this.paretoWidth.set(width);
            this.paretoHeight.set(Math.max(P.height, entry.contentRect.height));
          }
        }
      });
      for (const el of [this.columnsEl()?.nativeElement, this.paretoEl()?.nativeElement]) {
        if (el) {
          observer.observe(el);
        }
      }
      destroyRef.onDestroy(() => {
        observer.disconnect();
        clearTimeout(this.tooltipTimer);
      });
    });
  }

  /** Height of a bar as a percentage of the plot, keeping room for the value label at the top. */
  private eloPct(elo: number): number {
    return ((elo - ELO_LO) / (this.eloHi() - ELO_LO)) * (100 - (VALUE_PX / PLOT_PX) * 100);
  }

  px(cost: number): number {
    const { x0, x1 } = this.plot();
    return x0 + ((Math.log10(cost) - P.logLo) / (P.logHi - P.logLo)) * (x1 - x0);
  }

  py(tau: number): number {
    const { y0, y1 } = this.plot();
    return y1 - ((tau - P.tauLo) / (P.tauHi - P.tauLo)) * (y1 - y0);
  }

  triangle(p: ParetoPoint, r: number): string {
    const x = this.px(p.cost);
    const y = this.py(p.tau);
    return `${x},${y - r} ${x + r * 0.95},${y + r * 0.7} ${x - r * 0.95},${y + r * 0.7}`;
  }

  pointTitle(p: ParetoPoint): string {
    return `${p.name}: τ = ${p.tau.toFixed(2)}, $${Math.round(p.cost).toLocaleString()}${p.saturated ? ' (saturated)' : ''}`;
  }

  showPoint(point: ParetoPoint): void {
    clearTimeout(this.tooltipTimer);
    this.activeLegend.set(null);
    this.activePoint.set(point);
  }

  showLegend(item: LegendItem, event: Event): void {
    this.hidePoint();
    const bounds = (event.currentTarget as HTMLElement).getBoundingClientRect();
    const width = Math.min(270, window.innerWidth - 16);
    let top = Math.max(8, Math.min(bounds.top > 160 ? bounds.top - 150 : bounds.bottom + 10, window.innerHeight - 160));
    let left = Math.max(8, Math.min(bounds.left + bounds.width / 2 - width / 2, window.innerWidth - width - 8));
    if (item.kind === 'alignment') {
      // Keep the link itself clear while its explanation is open.
      if (bounds.right + 12 + width <= window.innerWidth - 8) {
        left = bounds.right + 12;
      } else if (bounds.left - width - 12 >= 8) {
        left = bounds.left - width - 12;
      } else {
        top = bounds.bottom + 12;
      }
    }
    this.activeLegend.set({
      ...item, width, top, left, maxHeight: window.innerHeight - top - 8
    });
  }

  keepTooltip(): void {
    clearTimeout(this.tooltipTimer);
  }

  hidePoint(): void {
    clearTimeout(this.tooltipTimer);
    this.activePoint.set(null);
    this.activeLegend.set(null);
  }

  scheduleHidePoint(): void {
    clearTimeout(this.tooltipTimer);
    this.tooltipTimer = setTimeout(() => this.hidePoint(), 150);
  }

  openLeaderboard(): void {
    setHashRouteState('/matches');
    this.store.dispatch(arenaActions.selectEntry({ entryId: 'matches' }));
  }

  private async fetchText(file: string): Promise<string | null> {
    try {
      const response = await fetch(new URL(file, document.baseURI).toString());
      return response.ok ? await response.text() : null;
    } catch {
      return null;
    }
  }

  private async loadLeaders(): Promise<void> {
    const text = await this.fetchText('leaderboard_models.csv');
    if (!text) {
      return;
    }
    const [header, ...lines] = text.trim().split(/\r?\n/);
    const median = header.split(',').indexOf('Median ELO');
    const rows = lines
      .map((line) => line.split(','))
      .map((cells) => ({ id: cells[0], elo: Number(cells[median]) }))
      .filter((row) => row.id && Number.isFinite(row.elo));
    this.baseline.set(rows.find((row) => row.id === 'random')?.elo ?? null);
    this.leaders.set(
      rows
        .filter((row) => row.id !== 'random')
        .sort((a, b) => b.elo - a.elo)
        .map((row) => ({ name: modelName(row.id), logo: resolveBotLogo(row.id), elo: row.elo }))
    );
  }

  private async loadPareto(): Promise<void> {
    const text = await this.fetchText('pareto.json');
    if (text) {
      this.points.set((JSON.parse(text) as ParetoPoint[]).sort((a, b) => a.cost - b.cost));
    }
  }
}
