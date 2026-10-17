import { Component, inject, signal } from '@angular/core';
import { Store } from '@ngrx/store';
import { arenaActions, ArenaState } from '@main/arena.store';
import { setHashRouteState } from '@main/arena.utils';
import { AutomataTermComponent } from './components/shared/automata-term.component';

type NavItem = {
  id: 'home' | 'play' | 'create' | 'leaderboard';
  label: string;
  icon: string;
  /** entrypoints that count as this section (null = main menu) */
  entries: (string | null)[];
};

/** Secondary links after the main nav; an empty url shows the button as "coming soon". */
type ExternalLink = {
  label: string;
  icon: string;
  url: string;
  /** in-app page instead of a url */
  entryId?: string;
  /** thin divider before this button */
  separatorBefore?: boolean;
};

const EXTERNAL_LINKS: ExternalLink[] = [
  { label: 'Team', icon: 'fa-solid fa-users', url: '', entryId: 'team', separatorBefore: true },
  { label: 'Paper', icon: 'fa-solid fa-file-lines', url: '', entryId: 'paper' }
];

/** Short, non-technical labels for the status pill (anything else is shown as is). */
const STATUS_LABELS: Record<string, string> = {
  'Loading Pyodide runtime': 'Loading engine',
  'Loading numpy': 'Loading engine',
  'Loading game arena': 'Loading engine',
  'Preparing arena runtime': 'Loading engine',
  'Installing OpenSpiel': 'Loading engine',
  'Restarting Pyodide worker': 'Loading engine',
  'Reinitializing Pyodide runtime': 'Loading engine',
  'Pyodide ready': 'Engine ready',
  'OpenSpiel ready': 'Engine ready',
  'Pyodide idle': 'Idle',
  'Pyodide error': 'Engine error',
  'Pyodide worker error': 'Engine error',
  'Waiting for human move': 'Your move',
  'Failed to load game arena manifest': 'Could not load games',
  'Unexpected error. More details in the logs.': 'Unexpected error'
};

/** True while the media query matches; follows window resizes. */
const mediaSignal = (query: string) => {
  const media = window.matchMedia(query);
  const matches = signal(media.matches);
  media.addEventListener('change', (event) => matches.set(event.matches));
  return matches.asReadonly();
};

/** Fired when a nav button is clicked for the page that is already open. */
export const NAV_HOME_EVENT = 'arena:nav-home';

const NAV_ITEMS: NavItem[] = [
  { id: 'home', label: 'Home', icon: 'fa-house', entries: [null] },
  { id: 'play', label: 'Play', icon: 'fa-gamepad', entries: ['ga'] },
  { id: 'create', label: 'Create Automata', icon: 'fa-code', entries: ['create'] },
  { id: 'leaderboard', label: 'Leaderboard', icon: 'fa-trophy', entries: ['matches'] }
];

@Component({
  selector: 'fe-header',
  standalone: true,
  imports: [AutomataTermComponent],
  templateUrl: './header.component.html'
})
export class FeHeaderComponent {
  private readonly store = inject(Store<{ arena: ArenaState }>);
  readonly state = this.store.selectSignal((root: { arena: ArenaState }) => root.arena);
  readonly navItems = NAV_ITEMS;
  readonly externalLinks = EXTERNAL_LINKS;
  /** labels hidden by app.scss at these widths, so the icons name themselves in a tooltip */
  readonly navIconsOnly = mediaSignal('(max-width: 960px)');
  readonly statusDotOnly = mediaSignal('(max-width: 560px)');

  get statusLabel(): string {
    const message = this.state().status.message;
    return STATUS_LABELS[message] ?? message;
  }

  get heroTheme(): 'default' | 'corewar' {
    return this.state().heroTheme ?? 'default';
  }

  get corewarMatchInProgress(): boolean {
    return Boolean(this.state().corewar.matchInProgress);
  }

  onHeroTitleClick(): void {
    if (this.heroTheme !== 'corewar') {
      if (this.state().selection.entryId !== null) {
        this.resetEntry();
      }
      return;
    }
    if (this.corewarMatchInProgress) {
      this.store.dispatch(arenaActions.requestCorewarLeave({ action: 'reset-entry' }));
      return;
    }
    this.resetEntry();
  }

  resetEntry(): void {
    this.store.dispatch(arenaActions.resetEntry());
  }

  isNavActive(item: NavItem): boolean {
    return item.entries.includes(this.state().selection.entryId);
  }

  /** The main menu may still be rendering after a reset, so wait (up to ~1s) for the games section. */
  private scrollToGames(framesLeft = 60): void {
    const games = document.getElementById('games');
    if (games) {
      games.scrollIntoView({ behavior: 'smooth', block: 'start' });
      // content above can still be loading and push the section down mid-scroll; correct once at the end
      window.addEventListener(
        'scrollend',
        () => {
          if (Math.abs(games.getBoundingClientRect().top) > 2) {
            games.scrollIntoView({ behavior: 'smooth', block: 'start' });
          }
        },
        { once: true }
      );
    } else if (framesLeft > 0) {
      requestAnimationFrame(() => this.scrollToGames(framesLeft - 1));
    }
  }

  openPage(entryId: string): void {
    if (this.state().selection.entryId === entryId) {
      return;
    }
    setHashRouteState('/' + entryId);
    this.store.dispatch(arenaActions.selectEntry({ entryId }));
  }

  /** Home opens the main menu at its top; Play opens it at the games; the others open their page. */
  navigate(item: NavItem): void {
    if (item.id === 'home') {
      if (this.state().selection.entryId !== null) {
        this.resetEntry();
      }
      window.scrollTo({ top: 0, behavior: 'smooth' });
      return;
    }
    if (item.id === 'play') {
      if (this.state().selection.entryId !== null) {
        this.resetEntry();
      }
      this.scrollToGames();
      return;
    }
    const target = item.id === 'create' ? { path: '/create', entryId: 'create' } : { path: '/matches', entryId: 'matches' };
    if (this.state().selection.entryId === target.entryId) {
      // already on that page: take it back to its start (e.g. the leaderboard overview)
      window.dispatchEvent(new CustomEvent(NAV_HOME_EVENT, { detail: target.entryId }));
      return;
    }
    setHashRouteState(target.path);
    this.store.dispatch(arenaActions.selectEntry({ entryId: target.entryId }));
  }
}
