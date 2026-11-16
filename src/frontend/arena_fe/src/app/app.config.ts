import { ApplicationConfig, provideBrowserGlobalErrorListeners } from '@angular/core';
import { providePrimeNG } from 'primeng/config';
import Aura from '@primeuix/themes/aura';

import { provideStore, type MetaReducer } from '@ngrx/store';
import { arenaReducer } from '@main/arena.store';

const debugMetaReducer: MetaReducer = (reducer) => (state, action) => {
  const nextState = reducer(state, action);
  // console.debug('[Store]', action, nextState);
  return nextState;
};

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideStore({ arena: arenaReducer }, { metaReducers: [debugMetaReducer] }),
    providePrimeNG({ theme: { preset: Aura } })
  ]
};
