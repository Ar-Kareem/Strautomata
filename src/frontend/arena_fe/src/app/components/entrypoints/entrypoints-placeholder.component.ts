import { Component, inject } from '@angular/core';
import { Store } from '@ngrx/store';
import type { EntrypointOption } from '@main/arena.constants';
import { arenaActions, ArenaState } from '@main/arena.store';

@Component({
  selector: 'arena-entrypoint-placeholder',
  standalone: true,
  templateUrl: './entrypoints-placeholder.component.html'
})
export class ArenaEntrypointPlaceholderComponent {
  private readonly store = inject(Store<{ arena: ArenaState }>);
  readonly state = this.store.selectSignal((root: { arena: ArenaState }) => root.arena);

  get activeEntry(): EntrypointOption | null {
    const state = this.state();
    return state.catalog.entrypoints.find((entry) => entry.id === state.selection.entryId) ?? null;
  }

  resetEntry(): void {
    this.store.dispatch(arenaActions.resetEntry());
  }
}
