import { Component, OnInit, inject } from '@angular/core';
import { Store } from '@ngrx/store';
import { arenaActions, ArenaState } from '@main/arena.store';
import { GAME_GUI_IDS, GAME_WORLD_LABELS } from '@main/arena.constants';
import { setHashRouteState } from '@main/arena.utils';
import { GamePreviewComponent } from '../previews/game-preview.component';
import { ArenaEntrypointHeroComponent } from './entrypoints-hero.component';
import { ArenaMatchRunner } from '../../controllers/arena-match-runner';

type GameCard = { gameId: string; worldId: string; label: string };

@Component({
  selector: 'arena-entrypoint-picker',
  standalone: true,
  imports: [GamePreviewComponent, ArenaEntrypointHeroComponent],
  templateUrl: './entrypoints-picker.component.html',
  styleUrl: './entrypoints-picker.component.scss'
})
export class ArenaEntrypointPickerComponent implements OnInit {
  private readonly store = inject(Store<{ arena: ArenaState }>);
  private readonly runner = inject(ArenaMatchRunner);
  private readonly prefetched = new Set<string>();
  readonly state = this.store.selectSignal((root: { arena: ArenaState }) => root.arena);

  readonly games: GameCard[] = Object.entries(GAME_WORLD_LABELS)
    .flatMap(([gameId, worlds]) => Object.entries(worlds).map(([worldId, label]) => ({ gameId, worldId, label })))
    .filter((game) => GAME_GUI_IDS.includes(game.gameId))
    .sort((a, b) => a.label.localeCompare(b.label));

  ngOnInit(): void {
    // boot Pyodide while the user browses the menu so a game card opens straight into play
    this.runner.warmRuntime();
  }

  prefetchGame(game: GameCard): void {
    const key = `${game.gameId}/${game.worldId}`;
    if (!this.prefetched.has(key)) {
      this.prefetched.add(key);
      this.runner.prefetchGame(game.gameId, game.worldId);
    }
  }

  /** Open the clicked game; the player then picks how to play. */
  playGame(game: GameCard): void {
    setHashRouteState('/arena', new URLSearchParams({ game: game.gameId, sub: game.worldId }));
    this.store.dispatch(arenaActions.selectEntry({ entryId: 'ga' }));
  }
}
