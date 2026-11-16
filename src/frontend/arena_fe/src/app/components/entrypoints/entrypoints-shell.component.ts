import { NgComponentOutlet } from '@angular/common';
import { Component, DestroyRef, OnInit, inject, type Type } from '@angular/core';
import { Store } from '@ngrx/store';
import { ArenaEntrypointGameComponent } from './entrypoints-game.component';
import { ArenaEntrypointCorewarsComponent } from './entrypoints-corewars.component';
import { ArenaEntrypointPickerComponent } from './entrypoints-picker.component';
import { ArenaEntrypointPlaceholderComponent } from './entrypoints-placeholder.component';
import { ArenaEntrypointMatchesComponent } from './entrypoints-matches.component';
import { ArenaEntrypointCreateComponent } from './entrypoints-create.component';
import { ArenaEntrypointTeamComponent } from './entrypoints-team.component';
import { ArenaEntrypointPaperComponent } from './entrypoints-paper.component';
import { arenaActions } from '@main/arena.store';
import { ArenaState } from '@main/arena.store';
import { getHashRouteState } from '@main/arena.utils';

const ENTRYPOINT_COMPONENTS: Record<string, Type<unknown>> = {
  ga: ArenaEntrypointGameComponent,
  corewars: ArenaEntrypointCorewarsComponent,
  matches: ArenaEntrypointMatchesComponent,
  create: ArenaEntrypointCreateComponent,
  team: ArenaEntrypointTeamComponent,
  paper: ArenaEntrypointPaperComponent,
  sim: ArenaEntrypointPlaceholderComponent
};

const ENTRY_BY_PATH: Record<string, string> = {
  '/core': 'corewars',
  '/create': 'create',
  '/matches': 'matches',
  '/sim': 'sim',
  '/team': 'team',
  '/paper': 'paper',
  '/arena': 'ga',
  '/ga': 'ga'
};

@Component({
  selector: 'arena-entrypoint-shell',
  standalone: true,
  imports: [NgComponentOutlet],
  templateUrl: './entrypoints-shell.component.html'
})
export class ArenaEntrypointShellComponent implements OnInit {
  private readonly store = inject(Store<{ arena: ArenaState }>);
  private readonly destroyRef = inject(DestroyRef);
  readonly state = this.store.selectSignal((root: { arena: ArenaState }) => root.arena);

  ngOnInit(): void {
    this.applyRoute();
    // browser back/forward: follow the URL to the matching page
    const onPopState = () => this.applyRoute();
    window.addEventListener('popstate', onPopState);
    this.destroyRef.onDestroy(() => window.removeEventListener('popstate', onPopState));
  }

  private applyRoute(): void {
    const entryId = ENTRY_BY_PATH[getHashRouteState().path.toLowerCase()] ?? null;
    if (entryId === this.state().selection.entryId) {
      return;
    }
    if (entryId) {
      this.store.dispatch(arenaActions.selectEntry({ entryId }));
    } else {
      this.store.dispatch(arenaActions.resetEntry());
    }
  }

  get activeEntrypoint(): Type<unknown> {
    const entryId = this.state().selection.entryId;
    return entryId
      ? ENTRYPOINT_COMPONENTS[entryId] ?? ArenaEntrypointPlaceholderComponent
      : ArenaEntrypointPickerComponent;
  }
}
