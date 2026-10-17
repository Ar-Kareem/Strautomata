import { Component, OnInit, inject } from '@angular/core';
import { Store } from '@ngrx/store';
import type { ArenaState } from '@main/arena.store';
import { arenaActions, type MatchupMode } from '@main/arena.store';
import { ArenaOutputComponent } from '@arena/arena-output.component';
import { ArenaSetupComponent } from '@arena/arena-setup.component';
import { getHashRouteState, setHashRouteState } from '@main/arena.utils';
import { ArenaMatchRunner } from '../../controllers/arena-match-runner';

const MODE_BY_PARAM: Record<string, MatchupMode> = {
  human: 'human-vs-ai',
  ai: 'ai-vs-ai'
};

@Component({
  selector: 'arena-entrypoint-game',
  standalone: true,
  imports: [ArenaSetupComponent, ArenaOutputComponent],
  templateUrl: './entrypoints-game.component.html'
})
export class ArenaEntrypointGameComponent implements OnInit {
  private readonly store = inject(Store<{ arena: ArenaState }>);
  private readonly runner = inject(ArenaMatchRunner);
  readonly state = this.store.selectSignal((root: { arena: ArenaState }) => root.arena);

  ngOnInit(): void {
    const { path, params } = getHashRouteState();
    const isArenaRoute = path === '/arena';
    // the player picks how to play (Players section); a ?mode= link can still preselect it
    const mode = isArenaRoute ? MODE_BY_PARAM[params.get('mode') ?? ''] ?? null : null;
    const state = this.state();
    this.store.dispatch(arenaActions.patchState({ selection: { ...state.selection, matchup: mode } }));
    params.delete('mode');
    // ?vs=<automaton> (a Fight button): play against that automaton once the game's automata load
    this.runner.setPendingOpponent(isArenaRoute ? params.get('vs') : null);
    params.delete('vs');
    const initialised = this.state().catalog.games.length > 0;
    this.store.dispatch(arenaActions.initRequested());
    if (!isArenaRoute) {
      setHashRouteState('/arena');
      return;
    }
    setHashRouteState('/arena', params);
    // first visit: init reads game/sub from the URL itself; later visits need an explicit change
    const game = this.state().catalog.games.find(
      (option) => option.gameId === params.get('game') && option.worldId === params.get('sub')
    );
    if (initialised && game) {
      this.store.dispatch(
        arenaActions.gameChangeRequested({ id: game.id, gameId: game.gameId, worldId: game.worldId })
      );
    }
  }

  get isBotsSuccessful(): boolean {
    const state = this.state();
    const botsStatus = state.match.botsStatus;
    const hasSelectedGame = Boolean(state.selection.gameId && state.selection.worldId);
    return botsStatus === 'ready' && hasSelectedGame && state.selection.matchup !== null;
  }

}
