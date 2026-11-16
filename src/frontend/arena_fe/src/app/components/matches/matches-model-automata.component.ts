import { ChangeDetectionStrategy, Component, computed, effect, inject, input, output, signal, untracked } from '@angular/core';
import type { HistoryIndexGame, ModelAutomaton, ModelGame } from '@main/history.types';
import { automatonTip, crownedBots } from './automaton-tip';
import { HistoryService } from './history.service';
import { MatchesFightButtonComponent } from './fight-button.component';
import { formatRating } from './history-format';
import { MatchesAutomatonSourceComponent } from './matches-automaton-source.component';
import { MatchesBotChipComponent } from './matches-bot-chip.component';

/** Every automaton one model wrote for one game, qualified or not, each with its strategy and code. */
@Component({
  selector: 'matches-model-automata',
  standalone: true,
  imports: [MatchesBotChipComponent, MatchesAutomatonSourceComponent, MatchesFightButtonComponent],
  templateUrl: './matches-model-automata.component.html',
  styleUrl: './matches-model-automata.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class MatchesModelAutomataComponent {
  private readonly history = inject(HistoryService);

  readonly game = input.required<HistoryIndexGame>();
  readonly model = input.required<string>();
  /** one automaton's page in this game */
  readonly openBot = output<{ bot: string; qualified: boolean }>();

  readonly formatRating = formatRating;
  readonly data = signal<ModelGame | null>(null);
  /** the one automaton whose strategy and code are spread out */
  readonly expanded = signal<string | null>(null);

  constructor() {
    effect(() => {
      const model = this.model();
      const gameId = this.game()?.id;
      if (!model || !gameId) {
        return;
      }
      untracked(() => {
        this.data.set(null);
        this.expanded.set(null);
        this.history
          .loadModel(model)
          .then((page) => model === this.model() && this.data.set(page.games.find((g) => g.id === gameId) ?? null))
          .catch(() => undefined);
      });
    });
  }

  readonly top = computed(() => crownedBots(this.data()?.automata ?? []));

  /** qualified first (by tournament rank), then the rest by qualification rank */
  readonly rows = computed(() => {
    const data = this.data();
    if (!data) {
      return [];
    }
    const top = this.top();
    const ctx = { gameLabel: this.game()?.label ?? '', top, tourneyBots: data.tourney_bots, siblings: data.automata.length };
    return [...data.automata]
      .sort(
        (a, b) =>
          Number(b.qualified) - Number(a.qualified) ||
          (a.tourney?.rank ?? 1e9) - (b.tourney?.rank ?? 1e9) ||
          (b.tourney?.rating ?? -1e9) - (a.tourney?.rating ?? -1e9) ||
          (a.quals?.rank ?? 1e9) - (b.quals?.rank ?? 1e9)
      )
      .map((a) => ({ a, top: top.has(a.bot), tip: automatonTip(a, ctx) }));
  });

  /** an opened automaton's header closes it again */
  toggle(bot: string): void {
    this.expanded.set(this.expanded() === bot ? null : bot);
  }

  pick(a: ModelAutomaton): void {
    this.openBot.emit({ bot: a.bot, qualified: a.qualified && a.tourney !== null });
  }
}
