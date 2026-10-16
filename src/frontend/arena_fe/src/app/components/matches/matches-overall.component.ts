import { ChangeDetectionStrategy, Component, HostListener, computed, input, output, signal } from '@angular/core';
import type { HistoryIndexGame } from '@main/history.types';
import { resolveBotLogo } from '@main/arena.utils';
import { formatRating } from './history-format';

type Row = { model: string; logo: string | null; median: number; byGame: Record<string, number | null> };
type SortKey = 'median' | 'model' | string;

const MEDIAN_COLUMN = 'Median ELO';

/** Column order: the best-known games first; anything not listed keeps its CSV order at the end. */
const COLUMN_ORDER = [
  'Chess UCI', 'Go', 'Checkers', 'Backgammon', 'Othello', 'Connect4', 'Hex', 'Breakthrough', 'Amazons',
  'LoA', 'Havannah', 'Dots&B', 'Mancala', 'Clobber', 'Pentago', 'Battleships', 'Nim', '3D TTT', '4x4 TTT', '3x3 TTT'
];

const COLUMN_LABELS: Record<string, string> = { 'Chess UCI': 'Chess' };

/**
 * Model leaderboard across all games: each model's rating per game and the median over games.
 * Data: public/leaderboard_models.csv, a copy of the `rating_df.csv` written by
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
  readonly openModel = output<{ model: string; gameId: string }>();

  /** model-name popup: which model, and where to draw it */
  readonly modelMenu = signal<{ model: string; left: number; top: number } | null>(null);

  readonly menuGames = computed(() => {
    const rank = (column: string) => {
      const index = COLUMN_ORDER.indexOf(column);
      return index === -1 ? COLUMN_ORDER.length : index;
    };
    return [...this.games()]
      .sort((a, b) => rank(a.column) - rank(b.column))
      .map((game) => ({ id: game.id, label: COLUMN_LABELS[game.column] ?? game.label }));
  });

  readonly formatRating = formatRating;
  readonly columns = signal<string[]>([]);
  readonly rows = signal<Row[]>([]);
  readonly error = signal<string | null>(null);
  readonly sortKey = signal<SortKey>('median');
  readonly sortDesc = signal(true);

  readonly sortedRows = computed(() => {
    const key = this.sortKey();
    const dir = this.sortDesc() ? -1 : 1;
    const value = (row: Row): number | string =>
      key === 'median' ? row.median : key === 'model' ? row.model : row.byGame[key] ?? -Infinity;
    return [...this.rows()].sort((a, b) => {
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
      const response = await fetch(new URL('leaderboard_models.csv', document.baseURI).toString());
      if (!response.ok) {
        throw new Error(`${response.status}`);
      }
      const [header, ...lines] = (await response.text()).trim().split(/\r?\n/);
      const names = header.split(',');
      const rank = (name: string) => {
        const index = COLUMN_ORDER.indexOf(name);
        return index === -1 ? COLUMN_ORDER.length : index;
      };
      const columns = names
        .slice(1)
        .filter((name) => name !== MEDIAN_COLUMN)
        .sort((a, b) => rank(a) - rank(b));
      const rows = lines.map((line) => {
        const cells = line.split(',');
        const value = (name: string): number | null => {
          const cell = cells[names.indexOf(name)];
          return cell === undefined || cell === '' ? null : Number(cell);
        };
        const model = cells[0];
        return {
          model,
          logo: resolveBotLogo(model),
          median: value(MEDIAN_COLUMN) ?? NaN,
          byGame: Object.fromEntries(columns.map((column) => [column, value(column)]))
        };
      });
      this.columns.set(columns);
      this.rows.set(rows.filter((row) => !Number.isNaN(row.median)));
    } catch (err) {
      this.error.set(err instanceof Error ? err.message : String(err));
    }
  }

  toggleModelMenu(model: string, event: MouseEvent): void {
    if (this.modelMenu()?.model === model) {
      this.modelMenu.set(null);
      return;
    }
    const rect = (event.currentTarget as HTMLElement).getBoundingClientRect();
    const height = 360;
    const top = rect.bottom + 4 + height > window.innerHeight ? Math.max(8, rect.top - 4 - height) : rect.bottom + 4;
    this.modelMenu.set({ model, left: rect.left, top });
  }

  pickGame(gameId: string): void {
    const menu = this.modelMenu();
    if (menu) {
      this.openModel.emit({ model: menu.model, gameId });
    }
    this.modelMenu.set(null);
  }

  @HostListener('document:pointerdown', ['$event'])
  onDocumentPointerDown(event: PointerEvent): void {
    const target = event.target as HTMLElement;
    if (this.modelMenu() && !target.closest('.mo-menu') && !target.closest('.mo-model-btn')) {
      this.modelMenu.set(null);
    }
  }

  @HostListener('document:keydown.escape')
  onEscape(): void {
    this.modelMenu.set(null);
  }

  @HostListener('window:scroll')
  onScroll(): void {
    this.modelMenu.set(null);
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

  cellStyle(value: number | null, column: string): Record<string, string> {
    const share = this.share(value, this.gameRanges()[column] ?? [0, 0]);
    return { background: `rgba(78, 168, 255, ${(0.02 + share * 0.16).toFixed(3)})` };
  }

  private range(values: (number | null | undefined)[]): [number, number] {
    const nums = values.filter((value): value is number => typeof value === 'number' && !Number.isNaN(value));
    return nums.length ? [Math.min(...nums), Math.max(...nums)] : [0, 0];
  }
}
