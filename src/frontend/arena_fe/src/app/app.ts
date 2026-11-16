import { Component, ViewEncapsulation, inject } from '@angular/core';
import { Store } from '@ngrx/store';
import { arenaActions, type ArenaState } from '@main/arena.store';
import { setHashRouteState } from '@main/arena.utils';
import { version as appVersion } from '../../package.json';
import { ArenaMatchRunner } from './controllers/arena-match-runner';
import { CorewarConsoleRunner } from './controllers/corewar-console-runner';
import { FeHeaderComponent } from './header.component';
import { ArenaEntrypointShellComponent } from './components/entrypoints/entrypoints-shell.component';

@Component({
  selector: 'app-root',
  templateUrl: './app.html',
  styleUrl: './app.scss',
  standalone: true,
  encapsulation: ViewEncapsulation.None,
  imports: [FeHeaderComponent, ArenaEntrypointShellComponent]
})
export class App {
  private readonly store = inject(Store<{ arena: ArenaState }>);
  readonly state = this.store.selectSignal((root: { arena: ArenaState }) => root.arena);
  readonly version = appVersion;

  constructor(
    private readonly matchRunner: ArenaMatchRunner,
    private readonly corewarRunner: CorewarConsoleRunner
  ) {
    void this.matchRunner;
    void this.corewarRunner;
  }

  openTeam(): void {
    window.scrollTo({ top: 0 });
    if (this.state().selection.entryId === 'team') {
      return;
    }
    setHashRouteState('/team');
    this.store.dispatch(arenaActions.selectEntry({ entryId: 'team' }));
  }
}
