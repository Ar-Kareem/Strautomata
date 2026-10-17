import { ChangeDetectionStrategy, Component, computed, DestroyRef, effect, inject, input, output, signal, untracked } from '@angular/core';
import type { HistoryIndexGame, ModelAutomaton, ModelGame, ModelPage, OverallBoard } from '@main/history.types';
import { GamePreviewComponent } from '../previews/game-preview.component';
import { AutomatonTipService, automatonTip, crownedBots, type TipBody } from './automaton-tip';
import { HistoryService } from './history.service';
import { MatchesBotChipComponent } from './matches-bot-chip.component';
import { MatchesModelHeroComponent, overallStats, type HeroGroup } from './matches-model-hero.component';
import { botShortLabel, familyColor, formatRating } from './history-format';

interface GameCard {
  game: HistoryIndexGame;
  data: ModelGame;
  /** the model's best automata in this game (crowned) */
  top: ReadonlySet<string>;
  tips: ReadonlyMap<string, TipBody>;
  /** 0..1, 1 = best model in this game */
  standing: number;
  medal: 'gold' | 'silver' | 'bronze' | null;
}

/**
 * One model across every game (history/models/<model>.json): its overall standing, then a card
 * per game with its rating there and every automaton it wrote, qualified or not.
 */
@Component({
  selector: 'matches-model',
  standalone: true,
  imports: [GamePreviewComponent, MatchesBotChipComponent, MatchesModelHeroComponent],
  templateUrl: './matches-model.component.html',
  styleUrl: './matches-model.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class MatchesModelComponent {
  private readonly history = inject(HistoryService);
  readonly tips = inject(AutomatonTipService);
  // the tip lives in a shared host, so a hovered element destroyed mid-hover never fires pointerleave
  private readonly hideTipOnDestroy = inject(DestroyRef).onDestroy(() => this.tips.hide());

  readonly model = input.required<string>();
  readonly games = input<HistoryIndexGame[]>([]);
  /** the model in one game: that game's model page */
  readonly openGame = output<string>();
  /** one automaton in one game */
  readonly openBot = output<{ gameId: string; bot: string; qualified: boolean }>();

  readonly formatRating = formatRating;
  readonly botShortLabel = botShortLabel;

  readonly page = signal<ModelPage | null>(null);
  readonly overall = signal<OverallBoard | null>(null);
  readonly error = signal<string | null>(null);

  constructor() {
    effect(() => {
      const model = this.model();
      untracked(() => void this.load(model));
    });
    this.history
      .loadOverall()
      .then((board) => this.overall.set(board))
      .catch(() => undefined);
  }

  private async load(model: string): Promise<void> {
    this.page.set(null);
    this.error.set(null);
    try {
      const page = await this.history.loadModel(model);
      if (model === this.model()) {
        this.page.set(page);
      }
    } catch (err) {
      if (model === this.model()) {
        this.error.set(err instanceof Error ? err.message : String(err));
      }
    }
  }

  readonly color = computed(() => familyColor(this.page()?.family ?? 'Other'));

  readonly cards = computed<GameCard[]>(() => {
    const page = this.page();
    if (!page) {
      return [];
    }
    const byId = new Map(this.games().map((game) => [game.id, game]));
    const cards: GameCard[] = [];
    for (const data of page.games) {
      const game = byId.get(data.id);
      if (!game) {
        continue;
      }
      const rank = data.rating?.rank ?? null;
      const top = crownedBots(data.automata);
      cards.push({
        game,
        data,
        top,
        tips: new Map(
          data.automata.map((a) => [a.bot, automatonTip(a, { gameLabel: game.label, top, tourneyBots: data.tourney_bots, siblings: data.automata.length })])
        ),
        standing: rank === null ? 0 : data.models > 1 ? (data.models - rank) / (data.models - 1) : 1,
        medal: rank === 1 ? 'gold' : rank === 2 ? 'silver' : rank === 3 ? 'bronze' : null
      });
    }
    return cards.sort((a, b) => a.game.label.localeCompare(b.game.label));
  });

  readonly heroGroups = computed<HeroGroup[]>(() => {
    const page = this.page();
    return page ? [{ title: null, stats: overallStats(page, this.overall(), this.games()) }] : [];
  });

  showEloTip(card: GameCard, event: Event): void {
    const r = card.data.rating;
    if (!r) {
      return;
    }
    this.tips.show(event, {
      title: `${card.game.label} Elo`,
      badge: null,
      lines: [
        { label: 'Rank', value: `#${r.rank} of ${card.data.models} models` },
        { label: 'Elo', value: formatRating(r.rating) },
        { label: '95% CI', value: `${formatRating(r.q025)} – ${formatRating(r.q975)}` }
      ],
      note: null
    });
  }

  pickBot(card: GameCard, a: ModelAutomaton): void {
    this.openBot.emit({ gameId: card.game.id, bot: a.bot, qualified: a.qualified && a.tourney !== null });
  }
}
