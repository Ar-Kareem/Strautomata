import { ChangeDetectionStrategy, Component, computed, DestroyRef, effect, inject, input, signal, untracked } from '@angular/core';
import type { HistoryIndexGame, ModelGame, ModelPage, OverallBoard } from '@main/history.types';
import { AutomatonTipService, type TipBody, type TipLine } from './automaton-tip';
import { MatchesFightButtonComponent } from './fight-button.component';
import { ModelLogoComponent } from '../shared/model-logo.component';
import { HistoryService } from './history.service';
import { familyColor, formatRating } from './history-format';

export interface HeroStat {
  label: string;
  value: string;
  /** shown small after the value, e.g. the 53 in #3/53 */
  of?: string;
  big?: boolean;
  /** shown on hover */
  tip?: TipBody;
}

export interface HeroGroup {
  /** caption over the group, none when the card has a single group */
  title: string | null;
  stats: HeroStat[];
}

const MEDALS = [
  { name: 'Gold', tone: 'gold' },
  { name: 'Silver', tone: 'silver' },
  { name: 'Bronze', tone: 'bronze' }
] as const;

/** hover list of the games where the model finished in the top `maxRank` (CI rank, so ties share a medal) */
function medalTip(title: string, games: ModelGame[], labels: ReadonlyMap<string, string>, maxRank: number): TipBody {
  const lines: TipLine[] = games
    .filter((g) => g.rating !== null && g.rating.rank <= maxRank)
    .sort((a, b) => a.rating!.rank - b.rating!.rank || (labels.get(a.id) ?? a.id).localeCompare(labels.get(b.id) ?? b.id))
    .map((g) => {
      const medal = MEDALS[g.rating!.rank - 1];
      return { label: labels.get(g.id) ?? g.id, value: `${medal.name} · Elo ${formatRating(g.rating!.rating)}`, tone: medal.tone };
    });
  return { title, badge: null, lines, text: lines.length ? undefined : 'None', note: null };
}

/** A model across every listed game: median Elo and its rank (overall leaderboard), wins, podiums, automata. */
export function overallStats(page: ModelPage, board: OverallBoard | null, listed: readonly HistoryIndexGame[]): HeroStat[] {
  const labels = new Map(listed.map((g) => [g.id, g.label]));
  const out: HeroStat[] = [];
  const row = board?.rows.find((r) => r.model === page.model);
  if (board && row) {
    const ranked = [...board.rows].sort((a, b) => b.median - a.median);
    out.push({ label: 'Median Elo', value: formatRating(row.median), big: true });
    out.push({ label: 'Overall', value: `#${ranked.findIndex((r) => r.model === row.model) + 1}`, of: String(ranked.length) });
  }
  const games = page.games.filter((g) => labels.has(g.id));
  const automata = games.flatMap((g) => g.automata);
  out.push({
    label: '1st place',
    value: String(games.filter((g) => g.rating?.rank === 1).length),
    of: String(games.length),
    tip: medalTip('1st place', games, labels, 1)
  });
  out.push({
    label: 'Podiums',
    value: String(games.filter((g) => g.rating !== null && g.rating.rank <= 3).length),
    tip: medalTip('Podiums', games, labels, 3)
  });
  out.push({ label: 'Automata', value: String(automata.length) });
  out.push({ label: 'Qualified', value: String(automata.filter((a) => a.qualified).length) });
  return out;
}

/** A model in one game: its Elo and rank there, and its automata. */
export function gameStats(data: ModelGame): HeroStat[] {
  const out: HeroStat[] = [];
  if (data.rating) {
    out.push({ label: 'Elo', value: formatRating(data.rating.rating), big: true });
    out.push({ label: 'Rank', value: `#${data.rating.rank}`, of: String(data.models) });
  }
  out.push({ label: 'Automata', value: String(data.automata.length) });
  out.push({ label: 'Qualified', value: String(data.automata.filter((a) => a.qualified).length) });
  return out;
}

/** A model's name card with groups of stats beside it; groups after the first are drawn quieter. */
@Component({
  selector: 'matches-model-hero',
  standalone: true,
  imports: [ModelLogoComponent],
  template: `
    <header class="mp-hero" [class.is-stacked]="groups().length > 1">
      <div class="mp-id">
        <span class="mp-logo"><model-logo [family]="family()" [bot]="model()" [size]="34"></model-logo></span>
        <div>
          <h2 class="mp-name">@for (part of nameParts(); track $index) {@if (!$first) {_<wbr>}{{ part }}}</h2>
          @if (family(); as f) {
            <span class="mp-family">{{ f }}</span>
          }
        </div>
      </div>
      <div class="mp-groups">
        @for (group of groups(); track $index) {
          <div class="mp-group" [class.is-secondary]="$index > 0">
            @if (group.title) {
              <span class="mp-group-title">{{ group.title }}</span>
            }
            <div class="mp-stats">
              @for (s of group.stats; track s.label) {
                <div
                  class="mp-stat"
                  [class.is-big]="s.big"
                  [class.has-tip]="!!s.tip"
                  (pointerenter)="s.tip && tips.show($event, s.tip)"
                  (pointerleave)="s.tip && tips.hide()"
                >
                  <span class="mp-stat-label">{{ s.label }}</span>
                  <span class="mp-stat-value">{{ s.value }}@if (s.of) {<small>/{{ s.of }}</small>}</span>
                </div>
              }
            </div>
          </div>
        }
      </div>
    </header>
  `,
  styleUrl: './matches-model-hero.component.scss',
  host: { '[style.--family]': 'color()' },
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class MatchesModelHeroComponent {
  readonly model = input.required<string>();
  readonly family = input<string | null>(null);
  readonly groups = input<HeroGroup[]>([]);

  readonly tips = inject(AutomatonTipService);
  // the tip lives in a shared host, so hide it if the card goes away mid-hover
  private readonly hideTipOnDestroy = inject(DestroyRef).onDestroy(() => this.tips.hide());

  readonly color = computed(() => familyColor(this.family() ?? 'Other'));
  /** a long name breaks at its underscores, not mid-word */
  readonly nameParts = computed(() => this.model().split('_'));
}

/** The model hero for one game: its standing there first, then across every game. */
@Component({
  selector: 'matches-model-game-hero',
  standalone: true,
  imports: [MatchesModelHeroComponent, MatchesFightButtonComponent],
  template: `
    <matches-model-hero [model]="model()" [family]="page()?.family ?? null" [groups]="groups()"></matches-model-hero>
    @if (topBot(); as bot) {
      <matches-fight-button [game]="game()" [bot]="bot"></matches-fight-button>
    }
  `,
  // Fight as a full-height tile beside the card, like the automaton page's
  styles: `
    :host {
      display: flex;
      align-items: stretch;
      gap: 10px;
    }
    matches-model-hero {
      flex: 1;
      min-width: 0;
    }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class MatchesModelGameHeroComponent {
  private readonly history = inject(HistoryService);

  readonly game = input.required<HistoryIndexGame>();
  readonly model = input.required<string>();
  /** every game listed on the site, for the overall wins and podiums */
  readonly games = input<HistoryIndexGame[]>([]);

  readonly page = signal<ModelPage | null>(null);
  readonly overall = signal<OverallBoard | null>(null);

  constructor() {
    effect(() => {
      const model = this.model();
      untracked(() => {
        this.page.set(null);
        this.history
          .loadModel(model)
          .then((page) => model === this.model() && this.page.set(page))
          .catch(() => undefined);
      });
    });
    this.history
      .loadOverall()
      .then((board) => this.overall.set(board))
      .catch(() => undefined);
  }

  /** the model's best automaton in this game, the one Fight plays against */
  readonly topBot = computed(() => this.page()?.games.find((g) => g.id === this.game().id)?.top_bot ?? null);

  readonly groups = computed<HeroGroup[]>(() => {
    const page = this.page();
    const game = this.game();
    const data = page?.games.find((g) => g.id === game.id);
    if (!page || !data) {
      return [];
    }
    return [
      { title: 'All games', stats: overallStats(page, this.overall(), this.games()) },
      { title: game.label, stats: gameStats(data) }
    ];
  });
}
