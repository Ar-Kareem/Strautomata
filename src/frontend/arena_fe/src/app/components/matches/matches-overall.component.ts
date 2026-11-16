import { ChangeDetectionStrategy, Component, computed, DestroyRef, inject, input, output, signal } from '@angular/core';
import type { HistoryIndexGame } from '@main/history.types';
import { resolveBotLogo } from '@main/arena.utils';
import { formatRating } from './history-format';
import { HistoryService } from './history.service';
import { AutomatonTipService, type TipBody } from './automaton-tip';

type Row = { model: string; logo: string | null; median: number; byGame: Record<string, number | null> };
type SortKey = 'median' | 'meanRank' | 'model' | string;
type Metric = 'elo' | 'rank';

/** Column order: the best-known games first; anything not listed keeps its CSV order at the end. */
export const COLUMN_ORDER = [
  'Chess UCI', 'Go', 'Checkers', 'Backgammon', 'Othello', 'Connect4', 'Hex', 'Breakthrough', 'Amazons',
  'LoA', 'Havannah', 'Dots&B', 'Mancala', 'Clobber', 'Pentago', 'Battleships', 'Nim', '3D TTT', '4x4 TTT', '3x3 TTT'
];

const COLUMN_LABELS: Record<string, string> = { 'Chess UCI': 'Chess' };

/**
 * Model leaderboard across all games: each model's rating per game and the median over games.
 * Data: public/leaderboard_models.csv (HistoryService.loadOverall), a copy of the `rating_df.csv` written by
 * `exp_plotting plot_pkl --mode models` for the current tournament (sept_5, top2mean).
 */
@Component({
  selector: 'matches-overall',
  standalone: true,
  templateUrl: './matches-overall.component.html',
  styleUrl: './matches-overall.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class MatchesOverallComponent {
  /** games of the match viewer, listed in the model popup */
  readonly games = input<HistoryIndexGame[]>([]);
  /** models that have per-game match data */
  readonly availableModels = input<ReadonlySet<string>>(new Set());
  /** sidebar selection: only these models are listed (empty = all) */
  readonly selection = input<ReadonlySet<string>>(new Set());
  /** a model's page */
  readonly openModel = output<string>();
  /** a model in one game */
  readonly openModelInGame = output<{ model: string; gameId: string }>();
  private readonly history = inject(HistoryService);
  readonly tips = inject(AutomatonTipService);
  // the tip lives in a shared host, so a hovered element destroyed mid-hover never fires pointerleave
  private readonly hideTipOnDestroy = inject(DestroyRef).onDestroy(() => this.tips.hide());
  readonly meanRankHelp: TipBody = {
    title: 'Mean rank',
    badge: null,
    lines: [],
    text: "A model's rank averaged over all games. Lower is better. Per game: 1 + the number of models whose whole 95% CI sits above this one, so models with overlapping CIs share a rank.",
    note: null
  };

  /** game column -> match viewer game id, for clickable cells */
  readonly gameByColumn = computed(() => new Map(this.games().map((game) => [game.column, game.id])));

  readonly formatRating = formatRating;
  readonly columns = signal<string[]>([]);
  readonly rows = signal<Row[]>([]);
  readonly error = signal<string | null>(null);
  readonly sortKey = signal<SortKey>('median');
  readonly sortDesc = signal(true);
  /** what the game columns show: each model's Elo in the game, or its rank among the models there */
  readonly metric = signal<Metric>('elo');

  /** rank of each model in each game (1 = best Elo, ties share a rank); null where it has no rating */
  /** CI rank per game (same rank as the game's own leaderboard), so models whose CIs overlap share a rank */
  readonly gameRanks = computed(() => {
    const ranksByColumn = new Map(this.games().map((game) => [game.column, game.model_ranks ?? {}]));
    const out = new Map<string, Record<string, number | null>>(this.rows().map((row) => [row.model, {}]));
    for (const column of this.columns()) {
      const ranks = ranksByColumn.get(column) ?? {};
      for (const row of this.rows()) {
        out.get(row.model)![column] = ranks[row.model] ?? null;
      }
    }
    return out;
  });

  readonly meanRank = computed(() => {
    const out = new Map<string, number>();
    for (const [model, ranks] of this.gameRanks()) {
      const values = Object.values(ranks).filter((rank): rank is number => rank !== null);
      out.set(model, values.length ? values.reduce((sum, rank) => sum + rank, 0) / values.length : Infinity);
    }
    return out;
  });

  readonly sortedRows = computed(() => {
    const key = this.sortKey();
    const dir = this.sortDesc() ? -1 : 1;
    const byRank = this.metric() === 'rank';
    // ranks sort low-is-best, so they are negated to share the Elo direction
    const value = (row: Row): number | string =>
      key === 'median'
        ? row.median
        : key === 'model'
          ? row.model
          : key === 'meanRank'
            ? -(this.meanRank().get(row.model) ?? Infinity)
            : byRank
              ? -(this.gameRanks().get(row.model)?.[key] ?? Infinity)
              : row.byGame[key] ?? -Infinity;
    const selection = this.selection();
    const rows = selection.size ? this.rows().filter((row) => selection.has(row.model)) : this.rows();
    return [...rows].sort((a, b) => {
      const va = value(a);
      const vb = value(b);
      return (typeof va === 'string' ? va.localeCompare(vb as string) : va - (vb as number)) * dir;
    });
  });

  /** Rank by median, independent of the current sort. */
  readonly rankOf = computed(() => {
    const ranked = [...this.rows()].sort((a, b) => b.median - a.median);
    return new Map(ranked.map((row, index) => [row.model, index + 1]));
  });

  readonly medianRange = computed(() => this.range(this.rows().map((row) => row.median)));
  readonly gameRanges = computed(() => {
    const out: Record<string, [number, number]> = {};
    for (const column of this.columns()) {
      out[column] = this.range(this.rows().map((row) => row.byGame[column]));
    }
    return out;
  });

  constructor() {
    void this.load();
  }

  private async load(): Promise<void> {
    try {
      const board = await this.history.loadOverall();
      const rank = (name: string) => {
        const index = COLUMN_ORDER.indexOf(name);
        return index === -1 ? COLUMN_ORDER.length : index;
      };
      this.columns.set([...board.columns].sort((a, b) => rank(a) - rank(b)));
      this.rows.set(board.rows.map((row) => ({ ...row, logo: resolveBotLogo(row.model) })));
    } catch (err) {
      this.error.set(err instanceof Error ? err.message : String(err));
    }
  }

  openRowModel(model: string): void {
    if (this.availableModels().has(model)) {
      this.openModel.emit(model);
    }
  }

  openCell(model: string, column: string): void {
    const gameId = this.gameByColumn().get(column);
    if (gameId && this.availableModels().has(model)) {
      this.openModelInGame.emit({ model, gameId });
    }
  }

  setMetric(metric: Metric): void {
    this.metric.set(metric);
    if (metric === 'elo' && this.sortKey() === 'meanRank') {
      this.sortKey.set('median');
      this.sortDesc.set(true);
    }
  }

  cellValue(row: Row, column: string): string {
    if (this.metric() === 'elo') {
      return formatRating(row.byGame[column]);
    }
    return String(this.gameRanks().get(row.model)?.[column] ?? '–');
  }

  /** 0..1 length of the mean-rank bar: full at rank 1, empty at the last place */
  meanRankShare(model: string): number {
    const value = this.meanRank().get(model) ?? Infinity;
    const last = this.rows().length;
    return Number.isFinite(value) && last > 1 ? Math.max(0, Math.min(1, (last - value) / (last - 1))) : 0;
  }

  /** podium places in a game get their medal colour */
  rankClass(row: Row, column: string): string {
    const rank = this.metric() === 'rank' ? this.gameRanks().get(row.model)?.[column] : null;
    return rank === 1 ? 'is-gold' : rank === 2 ? 'is-silver' : rank === 3 ? 'is-bronze' : '';
  }

  formatMeanRank(model: string): string {
    const value = this.meanRank().get(model) ?? Infinity;
    return Number.isFinite(value) ? value.toFixed(1) : '–';
  }

  columnLabel(column: string): string {
    return COLUMN_LABELS[column] ?? column;
  }

  /** Header clicks cycle: natural direction, then reversed, then back to the default median order. */
  setSort(key: SortKey): void {
    const naturalDesc = key !== 'model';
    if (this.sortKey() !== key) {
      this.sortKey.set(key);
      this.sortDesc.set(naturalDesc);
    } else if (this.sortDesc() === naturalDesc) {
      this.sortDesc.set(!naturalDesc);
    } else {
      this.sortKey.set('median');
      this.sortDesc.set(true);
    }
  }

  sortMark(key: SortKey): string {
    return this.sortKey() === key ? (this.sortDesc() ? '▾' : '▴') : '';
  }

  /** 0..1 position of a rating within its column, for the bar and cell shading. */
  share(value: number | null, [lo, hi]: [number, number]): number {
    if (value === null || hi <= lo) {
      return 0;
    }
    return Math.max(0, Math.min(1, (value - lo) / (hi - lo)));
  }

  cellStyle(row: Row, column: string): Record<string, string> {
    // shading follows the Elo either way: a better rank is a higher Elo
    const share = this.share(row.byGame[column], this.gameRanges()[column] ?? [0, 0]);
    return { background: `rgba(78, 168, 255, ${(0.02 + share * 0.16).toFixed(3)})` };
  }

  private range(values: (number | null | undefined)[]): [number, number] {
    const nums = values.filter((value): value is number => typeof value === 'number' && !Number.isNaN(value));
    return nums.length ? [Math.min(...nums), Math.max(...nums)] : [0, 0];
  }
}
