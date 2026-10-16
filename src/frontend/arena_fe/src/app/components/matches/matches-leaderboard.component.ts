import { ModelLogoComponent } from '../shared/model-logo.component';
import { ChangeDetectionStrategy, Component, computed, input, output, signal } from '@angular/core';
import type { LeaderboardRow } from '@main/history.types';
import { familyColor, formatRating } from './history-format';

type SortKey = 'rank' | 'label' | 'rating' | 'win' | 'loss' | 'draw' | 'fault' | 'n' | 'avg_moves';

@Component({
  selector: 'matches-leaderboard',
  standalone: true,
  imports: [ModelLogoComponent],
  templateUrl: './matches-leaderboard.component.html',
  styleUrl: './matches-leaderboard.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class MatchesLeaderboardComponent {
  readonly rows = input.required<LeaderboardRow[]>();
  /** fixed rating axis for the CI bars (the whole stage), so filtering does not rescale them */
  readonly ciScale = input<{ lo: number; hi: number } | null>(null);
  readonly selectedId = input<string | null>(null);
  readonly showQualified = input(false);
  readonly subLabel = input<string>('Model');
  readonly select = output<string>();

  readonly familyColor = familyColor;
  readonly formatRating = formatRating;

  readonly sortKey = signal<SortKey>('rank');
  readonly sortDir = signal<'asc' | 'desc'>('asc');

  readonly ciRange = computed(() => {
    const fixed = this.ciScale();
    if (fixed && fixed.hi > fixed.lo) {
      return { lo: fixed.lo, hi: Math.ceil(fixed.hi / 100) * 100 };
    }
    let lo = Number.POSITIVE_INFINITY;
    let hi = Number.NEGATIVE_INFINITY;
    for (const row of this.rows()) {
      const a = row.q025 ?? row.rating;
      const b = row.q975 ?? row.rating;
      if (a !== null && a !== undefined) {
        lo = Math.min(lo, a);
      }
      if (b !== null && b !== undefined) {
        hi = Math.max(hi, b);
      }
    }
    if (!Number.isFinite(lo) || !Number.isFinite(hi) || hi <= lo) {
      return { lo: 0, hi: 1 };
    }
    // the axis ends at the top rating rounded up to the next 100, labelled in the header
    return { lo, hi: Math.ceil(hi / 100) * 100 };
  });

  readonly sortedRows = computed(() => {
    const key = this.sortKey();
    const dir = this.sortDir() === 'asc' ? 1 : -1;
    const value = (row: LeaderboardRow): number | string => {
      switch (key) {
        case 'label':
          return row.label.toLowerCase();
        case 'rating':
          return row.rating ?? Number.NEGATIVE_INFINITY;
        case 'win':
          return row.record?.win ?? -1;
        case 'loss':
          return row.record?.loss ?? -1;
        case 'draw':
          return row.record?.draw ?? -1;
        case 'fault':
          return (row.record?.error ?? 0) + (row.record?.timeout ?? 0);
        case 'n':
          return row.n;
        case 'avg_moves':
          return row.record?.avg_moves ?? -1;
        default:
          return row.dnq ? Number.POSITIVE_INFINITY : row.rank || Number.POSITIVE_INFINITY - 1;
      }
    };
    return [...this.rows()].sort((x, y) => {
      if (x.dnq !== y.dnq) {
        return x.dnq ? 1 : -1;
      }
      const a = value(x);
      const b = value(y);
      if (a < b) {
        return -dir;
      }
      if (a > b) {
        return dir;
      }
      // ties (e.g. shared rank): higher rating first, then name
      const rx = x.rating ?? Number.NEGATIVE_INFINITY;
      const ry = y.rating ?? Number.NEGATIVE_INFINITY;
      if (rx !== ry) {
        return ry - rx;
      }
      return x.label.localeCompare(y.label);
    });
  });

  setSort(key: SortKey): void {
    if (this.sortKey() === key) {
      this.sortDir.set(this.sortDir() === 'asc' ? 'desc' : 'asc');
      return;
    }
    this.sortKey.set(key);
    this.sortDir.set(key === 'rank' || key === 'label' ? 'asc' : 'desc');
  }

  sortMark(key: SortKey): string {
    if (this.sortKey() !== key) {
      return '';
    }
    return this.sortDir() === 'asc' ? '▲' : '▼';
  }

  /** round rating values (3-5 of them) marked in the header and as faint lines in every bar */
  readonly ticks = computed(() => {
    const { lo, hi } = this.ciRange();
    const span = hi - lo;
    if (!(span > 0)) {
      return [];
    }
    const step = [25, 50, 100, 200, 250, 500, 1000, 2000].find((s) => span / s <= 5) ?? 5000;
    const out: { value: number; pct: number; edge: 'start' | 'end' | null; label: boolean }[] = [];
    for (let v = Math.ceil(lo / step) * step; v < hi; v += step) {
      const pct = ((v - lo) / span) * 100;
      // keep the gridline, but drop the label when it would crowd the labelled end of the axis
      out.push({ value: v, pct, edge: pct < 6 ? 'start' : null, label: pct < 82 });
    }
    out.push({ value: hi, pct: 100, edge: 'end', label: true });
    return out;
  });

  ciStyle(row: LeaderboardRow): Record<string, string> {
    const { lo, hi } = this.ciRange();
    const span = hi - lo || 1;
    const left = row.q025 ?? row.rating ?? lo;
    const right = row.q975 ?? row.rating ?? lo;
    const point = row.rating ?? left;
    return {
      '--ci-left': `${((left - lo) / span) * 100}%`,
      '--ci-width': `${Math.max(0.5, ((right - left) / span) * 100)}%`,
      '--ci-point': `${((point - lo) / span) * 100}%`
    };
  }

  faults(row: LeaderboardRow): number {
    return (row.record?.error ?? 0) + (row.record?.timeout ?? 0);
  }

  trackRow(_index: number, row: LeaderboardRow): string {
    return row.id;
  }
}
