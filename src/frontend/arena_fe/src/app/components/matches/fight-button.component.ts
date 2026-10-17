import { ChangeDetectionStrategy, Component, computed, inject, input } from '@angular/core';
import { Store } from '@ngrx/store';
import { GAME_GUI_IDS } from '@main/arena.constants';
import { arenaActions, type ArenaState } from '@main/arena.store';
import { setHashRouteState } from '@main/arena.utils';
import type { HistoryIndexGame } from '@main/history.types';

/** Opens the Play page with you against this automaton; hidden for games without a board to play on. */
@Component({
  selector: 'matches-fight-button',
  standalone: true,
  template: `
    @if (playable()) {
      <button type="button" class="fight" (click)="fight($event)">
        <i class="fa-solid fa-hand-fist" aria-hidden="true"></i>
        Fight
      </button>
    }
  `,
  styles: `
    :host {
      display: contents;
    }
    .fight {
      appearance: none;
      display: inline-flex;
      align-items: center;
      gap: 7px;
      padding: 6px 14px;
      border-radius: 8px;
      border: 1px solid rgba(255, 111, 141, 0.5);
      background: rgba(255, 111, 141, 0.1);
      color: #ff9cb0;
      font-family: var(--font-display);
      font-size: 0.78rem;
      font-weight: 600;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      white-space: nowrap;
      cursor: pointer;
      transition: background 0.2s ease, box-shadow 0.2s ease;
    }
    .fight:hover {
      background: rgba(255, 111, 141, 0.2);
      box-shadow: 0 0 14px rgba(255, 111, 141, 0.3);
    }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class MatchesFightButtonComponent {
  private readonly store = inject(Store<{ arena: ArenaState }>);

  readonly game = input.required<HistoryIndexGame>();
  readonly bot = input.required<string>();

  readonly playable = computed(() => GAME_GUI_IDS.includes(this.game().game));

  fight(event: Event): void {
    event.stopPropagation();
    const game = this.game();
    setHashRouteState('/arena', new URLSearchParams({ game: game.game, sub: game.world, mode: 'human', vs: this.bot() }));
    this.store.dispatch(arenaActions.selectEntry({ entryId: 'ga' }));
  }
}
