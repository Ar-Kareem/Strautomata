import { ChangeDetectionStrategy, Component, HostListener, Injectable, inject, signal } from '@angular/core';
import type { BotRecord, ModelAutomaton } from '@main/history.types';
import { botShortLabel, formatRating, modelOf } from './history-format';

export type AutomatonBadge = 'top' | 'qualified' | 'dnq';

export interface TipLine {
  label: string;
  value: string;
  /** colours the value, e.g. a medal */
  tone?: 'gold' | 'silver' | 'bronze';
}

export interface TipBody {
  title: string;
  badge: AutomatonBadge | null;
  lines: TipLine[];
  /** plain explanation under the heading */
  text?: string;
  note: string | null;
}

interface Tip extends TipBody {
  left: number;
  top: number;
  /** drawn above its anchor (top is then the anchor's top edge) */
  above: boolean;
}

/**
 * The model's best automata in one game: the best tournament rank, and among those the highest
 * rating (ranks come from confidence intervals, so several can share #1). None for the random
 * baseline, which has a single automaton to be best among.
 */
export const crownedBots = (automata: ModelAutomaton[]): ReadonlySet<string> => {
  const rated = automata.filter((a) => a.tourney && modelOf(a.bot) !== 'random');
  const bestRank = Math.min(...rated.map((a) => a.tourney!.rank));
  const best = rated.filter((a) => a.tourney!.rank === bestRank);
  const bestRating = Math.max(...best.map((a) => a.tourney!.rating ?? -Infinity));
  return new Set(best.filter((a) => (a.tourney!.rating ?? -Infinity) === bestRating).map((a) => a.bot));
};

export const automatonBadge = (a: ModelAutomaton, top: ReadonlySet<string>): AutomatonBadge =>
  top.has(a.bot) ? 'top' : a.qualified ? 'qualified' : 'dnq';

/** wins (including the opponent's faults) plus half the draws, as a share of games */
export const recordScore = (rec: BotRecord | null): number | null =>
  rec && rec.n ? (rec.win + rec.enemy_error + rec.enemy_timeout + rec.draw / 2) / rec.n : null;

/** the record of the stage that ranks the automaton: tournament if it qualified, else qualification */
export const automatonRecord = (a: ModelAutomaton): BotRecord | null =>
  a.qualified ? a.tourney_record ?? a.quals_record : a.quals_record;

export const automatonTip = (
  a: ModelAutomaton,
  ctx: { gameLabel: string; top: ReadonlySet<string>; tourneyBots: number; siblings: number }
): TipBody => {
  const lines: TipLine[] = [];
  if (a.tourney) {
    lines.push({ label: 'Tournament', value: `#${a.tourney.rank} of ${ctx.tourneyBots} · Elo ${formatRating(a.tourney.rating)}` });
  }
  if (a.quals) {
    lines.push({ label: 'Qualification', value: `#${a.quals.rank} of ${ctx.siblings} · Elo ${formatRating(a.quals.rating)}` });
  }
  const rec = automatonRecord(a);
  const score = recordScore(rec);
  if (rec && score !== null) {
    const wins = rec.win + rec.enemy_error + rec.enemy_timeout;
    const losses = rec.loss + rec.error + rec.timeout;
    lines.push({ label: 'Score', value: `${Math.round(score * 100)}% · ${wins}W ${rec.draw}D ${losses}L` });
  }
  return {
    title: `${ctx.gameLabel} ${botShortLabel(a.bot)}`,
    badge: automatonBadge(a, ctx.top),
    lines,
    note: a.qualified ? null : 'Not in the tournament. It only played qualification games against this model’s other automata.'
  };
};

/** One hover tooltip for the match viewer, drawn by <matches-tip> outside any transformed card. */
@Injectable({ providedIn: 'root' })
export class AutomatonTipService {
  readonly tip = signal<Tip | null>(null);

  /** below the element, or above it when there is no room */
  show(event: Event, body: TipBody): void {
    const rect = (event.currentTarget as HTMLElement).getBoundingClientRect();
    const above = rect.bottom + 150 > window.innerHeight;
    this.tip.set({
      ...body,
      left: Math.max(8, Math.min(rect.left, window.innerWidth - 300)),
      top: above ? rect.top - 6 : rect.bottom + 6,
      above
    });
  }

  hide(): void {
    this.tip.set(null);
  }
}

@Component({
  selector: 'matches-tip',
  standalone: true,
  template: `
    @if (service.tip(); as t) {
      <div class="tip" role="tooltip" [class.is-above]="t.above" [style.left.px]="t.left" [style.top.px]="t.top">
        <div class="tip-head">
          <span>{{ t.title }}</span>
          @switch (t.badge) {
            @case ('top') { <span class="tip-badge is-top"><i class="fa-solid fa-crown" aria-hidden="true"></i> Top</span> }
            @case ('qualified') { <span class="tip-badge is-qualified">Qualified</span> }
            @case ('dnq') { <span class="tip-badge is-dnq">Did not qualify</span> }
          }
        </div>
        @if (t.text) {
          <div class="tip-text">{{ t.text }}</div>
        }
        @if (t.lines.length) {
          <div class="tip-lines">
            @for (line of t.lines; track line.label) {
              <span class="tip-label">{{ line.label }}</span><span [attr.data-tone]="line.tone ?? null">{{ line.value }}</span>
            }
          </div>
        }
        @if (t.note) {
          <div class="tip-note">{{ t.note }}</div>
        }
      </div>
    }
  `,
  styles: `
    .tip {
      position: fixed;
      z-index: 1000;
      width: max-content;
      max-width: 300px;
      padding: 8px 10px;
      border-radius: 10px;
      border: 1px solid rgba(78, 168, 255, 0.4);
      background: rgba(7, 13, 22, 0.97);
      box-shadow: 0 12px 30px rgba(0, 0, 0, 0.55);
      pointer-events: none;
      font-size: 0.74rem;
      color: var(--ink-700);
      font-variant-numeric: tabular-nums;
    }
    .tip.is-above {
      transform: translateY(-100%);
    }
    .tip-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 5px;
      color: var(--ink-900);
      font-weight: 600;
    }
    .tip-badge {
      padding: 1px 6px;
      border-radius: 999px;
      font-size: 0.66rem;
      font-weight: 500;
      border: 1px solid currentColor;
    }
    .tip-badge.is-top { color: #ffd166; }
    .tip-badge.is-qualified { color: var(--accent-2); }
    .tip-badge.is-dnq { color: var(--danger); }
    /* labels in one column as wide as the longest, values lined up beside them */
    .tip-lines {
      display: grid;
      grid-template-columns: minmax(92px, auto) auto;
      column-gap: 10px;
      line-height: 1.6;
    }
    [data-tone='gold'] { color: #ffd166; }
    [data-tone='silver'] { color: #d4dcea; }
    [data-tone='bronze'] { color: #e3a06b; }
    .tip-text {
      line-height: 1.4;
    }
    .tip-label {
      color: var(--ink-500);
    }
    .tip-note {
      margin-top: 5px;
      padding-top: 5px;
      border-top: 1px solid rgba(255, 111, 141, 0.25);
      color: var(--danger);
      line-height: 1.4;
    }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class MatchesTipComponent {
  readonly service = inject(AutomatonTipService);

  @HostListener('window:scroll')
  onScroll(): void {
    this.service.hide();
  }
}
