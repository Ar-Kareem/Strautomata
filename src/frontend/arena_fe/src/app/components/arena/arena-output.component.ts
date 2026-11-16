import { NgComponentOutlet } from '@angular/common';
import {
  ChangeDetectorRef,
  Component,
  ElementRef,
  OnDestroy,
  afterRenderEffect,
  signal,
  untracked,
  ViewChild,
  inject,
  type Type
} from '@angular/core';
import { Store } from '@ngrx/store';
import { TooltipModule } from 'primeng/tooltip';
import { getActiveGame, resolveBotLabel } from '@main/arena.utils';
import { arenaActions, type ArenaState, type HungAutomatonChoice } from '@main/arena.store';


import { GAME_GUI_MAP } from '@game-gui/game-gui-map';
import { ArenaGuiAlertComponent } from '../arena-gui-helpers/arena-gui-alert.component';
import { ArenaKbdLayerComponent } from '../arena-gui-helpers/arena-kbd-layer.component';
import { ModelLogoComponent } from '../shared/model-logo.component';

/** two players with the same name (Human vs Human) get their seat appended */
const withSeats = (a: string, b: string): [string, string] => (a === b ? [`${a} A`, `${b} B`] : [a, b]);

@Component({
  selector: 'arena-output',
  standalone: true,
  templateUrl: './arena-output.component.html',
  styleUrl: './arena-output.component.scss',
  imports: [NgComponentOutlet, TooltipModule, ArenaGuiAlertComponent, ArenaKbdLayerComponent, ModelLogoComponent]
})
export class ArenaOutputComponent implements OnDestroy {
  private readonly store = inject(Store<{ arena: ArenaState }>);
  private readonly cdr = inject(ChangeDetectorRef);
  @ViewChild('outputPanel', { static: true }) private outputPanelRef?: ElementRef<HTMLElement>;
  readonly state = this.store.selectSignal((root: { arena: ArenaState }) => root.arena);
  readonly resolveBotLabel = resolveBotLabel;
  readonly sides = [0, 1] as const;
  /** per-side colours read from the game GUI's legend, so the strip matches the board */
  readonly sideColors = signal<[string | null, string | null]>([null, null]);
  private consoleCollapsedOverride: boolean | null = null;
  panelMaxWidth = 650;
  isResizingPanel = false;
  private resizeStartX = 0;
  private resizeStartWidth = 650;
  private previousBodyCursor = '';
  private previousBodyUserSelect = '';
  private readonly clampWidthFromSetupHandler = () => this.clampPanelMaxWidthToRendered();
  private readonly pointerMoveHandler = (event: PointerEvent) => this.onResizePointerMove(event);
  private readonly pointerUpHandler = () => this.stopPanelResize();
  readonly submitHumanMove = (action: string, forceApply?: boolean): void => {
    this.store.dispatch(arenaActions.humanMoveSubmitted({ action, forceApply }));
  };

  constructor() {
    window.addEventListener('arena:clamp-output-width', this.clampWidthFromSetupHandler);
    // the game GUI renders its legend from the same state, so re-read it after every state-driven render
    afterRenderEffect(() => {
      this.state();
      const panel = this.outputPanelRef?.nativeElement;
      if (panel) {
        untracked(() => this.readLegendColors(panel));
      }
    });
  }

  /** scoreboard names */
  scoreLabel(side: 0 | 1): string {
    const { catalog, selection } = this.state();
    return withSeats(
      resolveBotLabel(catalog.bots, selection.botAId, 'Automaton A'),
      resolveBotLabel(catalog.bots, selection.botBId, 'Automaton B')
    )[side];
  }

  botId(side: 0 | 1): string | null {
    const { selection } = this.state();
    return side === 0 ? selection.botAId : selection.botBId;
  }

  /** side with more wins, or null when tied */
  get leader(): 0 | 1 | null {
    const { botAWins, botBWins } = this.state().match.scoreboard;
    return botAWins === botBWins ? null : botAWins > botBWins ? 0 : 1;
  }

  /** selected side to move, read from the observation's turn/player field when the game exposes one */
  get toMove(): 0 | 1 | null {
    const obs = this.state().match.matchObservation as { player?: unknown; state?: { turn?: unknown } } | null;
    const player = typeof obs?.state?.turn === 'number' ? obs.state.turn : obs?.player;
    if (player !== 0 && player !== 1) {
      return null;
    }
    return this.seatsSwapped ? (player === 0 ? 1 : 0) : player;
  }

  /** seats alternate every game, so seat A can hold the selected B bot */
  private get seatsSwapped(): boolean {
    const { match, selection } = this.state();
    return match.activeBotAId === selection.botBId && match.activeBotAId !== selection.botAId;
  }

  /** match each legend dot to a side by bot name; legends without bot names (e.g. HIT/MISS) leave the default colours */
  private readLegendColors(panel: HTMLElement): void {
    const items = [...panel.querySelectorAll('.arena-game-gui .legend-item')]
      .map((item) => ({ text: item.textContent ?? '', color: legendDotColor(item.querySelector('.legend-dot')) }))
      .filter((item): item is { text: string; color: string } => item.color !== null);
    const { catalog, selection } = this.state();
    const labels = [selection.botAId, selection.botBId].map((id) => resolveBotLabel(catalog.bots, id, ''));
    const colors: [string | null, string | null] = [null, null];
    if (labels[0] && labels[1] && labels[0] !== labels[1]) {
      for (const side of this.sides) {
        const matches = items.filter((item) => item.text.includes(labels[side]) && !item.text.includes(labels[1 - side]));
        colors[side] = matches.length === 1 ? matches[0].color : null;
      }
    }
    // same-named bots (e.g. Human vs Human) can't be told apart by text, so fall back to legend order
    if (labels[0] && labels[0] === labels[1] && items.length >= 2) {
      const seats = this.seatsSwapped ? [items[1], items[0]] : [items[0], items[1]];
      colors[0] ??= seats[0].color;
      colors[1] ??= seats[1].color;
    }
    const current = this.sideColors();
    if (current[0] !== colors[0] || current[1] !== colors[1]) {
      this.sideColors.set(colors);
    }
  }

  get activeGui(): Type<unknown> | null {
    const gameId = this.state().selection.gameId;
    return gameId ? GAME_GUI_MAP[gameId] ?? null : null;
  }

  get guiInputs(): Record<string, unknown> {
    const state = this.state();
    const [botA, botB] = withSeats(
      resolveBotLabel(
        state.catalog.bots,
        state.match.activeBotAId,
        resolveBotLabel(state.catalog.bots, state.selection.botAId, 'Automaton A')
      ),
      resolveBotLabel(
        state.catalog.bots,
        state.match.activeBotBId,
        resolveBotLabel(state.catalog.bots, state.selection.botBId, 'Automaton B')
      )
    );
    const inputs: Record<string, unknown> = {
      observation: state.match.matchObservation,
      botA,
      botB,
      statusTone: state.status.tone,
      statusMessage: state.status.message,
      showHumanControls: state.selection.botAId === 'human' || state.selection.botBId === 'human',
      awaitingHumanMove: state.match.awaitingHumanMove,
      legalMoves: state.match.legalMoves,
      submitHumanMove: this.submitHumanMove,
      illegalAction: state.match.illegalAction,
      matchResult: state.match.lastMatchResult
    };
    return inputs;
  }

  get isConsoleCollapsed(): boolean {
    return this.consoleCollapsedOverride ?? Boolean(this.activeGui);
  }

  get canControlMatch(): boolean {
    const state = this.state();
    return Boolean(getActiveGame(state) && state.selection.botAId && state.selection.botBId);
  }

  get hasHumanPlayer(): boolean {
    const selection = this.state().selection;
    return (
      selection.matchup === 'human-vs-ai' ||
      selection.matchup === 'human-vs-human' ||
      selection.botAId === 'human' ||
      selection.botBId === 'human'
    );
  }

  get isHumanVsHuman(): boolean {
    return this.state().selection.matchup === 'human-vs-human';
  }

  get isAiVsAi(): boolean {
    return !this.hasHumanPlayer;
  }

  get isHumanVsAi(): boolean {
    return this.hasHumanPlayer && !this.isHumanVsHuman;
  }

  get showNextRoundButton(): boolean {
    const match = this.state().match;
    return this.hasHumanPlayer && Boolean(match.lastMatchResult) && !match.stepInFlight;
  }

  toggleConsole(): void {
    this.consoleCollapsedOverride = !this.isConsoleCollapsed;
  }

  chooseHung(choice: HungAutomatonChoice): void {
    this.store.dispatch(arenaActions.hungAutomatonChoice({ choice }));
  }

  restartSeries(): void {
    this.store.dispatch(arenaActions.restartSeriesRequested());
  }

  startNextRound(): void {
    this.store.dispatch(arenaActions.togglePlayRequested());
  }

  togglePlay(): void {
    this.store.dispatch(arenaActions.togglePlayRequested());
  }

  get isAiStepBusy(): boolean {
    return this.state().match.stepInFlight;
  }

  onAiStepBusyClick(): void {
    if (!this.canControlMatch) {
      return;
    }
    const match = this.state().match;
    if (match.isPlaying) {
      this.store.dispatch(arenaActions.togglePlayRequested());
    }
    if (!match.stepInFlight) {
      this.store.dispatch(arenaActions.stepRequested());
    }
  }
  
  onSpeedChange(event: Event): void {
    const target = event.target as HTMLInputElement;
    const next = Number(target.value);
    if (!Number.isFinite(next)) {
      return;
    }
    this.store.dispatch(arenaActions.speedChangeRequested({ speed: next }));
  }

  onPanelResizeStart(event: PointerEvent): void {
    if (event.button !== 0) {
      return;
    }
    const panel = this.outputPanelRef?.nativeElement ?? (event.currentTarget as HTMLElement | null)?.parentElement;
    const measuredWidth = panel ? Math.floor(panel.getBoundingClientRect().width) : this.panelMaxWidth;
    event.preventDefault();
    this.isResizingPanel = true;
    this.resizeStartX = event.clientX;
    this.resizeStartWidth = measuredWidth;
    this.panelMaxWidth = measuredWidth;
    this.previousBodyCursor = document.body.style.cursor;
    this.previousBodyUserSelect = document.body.style.userSelect;
    document.body.style.cursor = 'ew-resize';
    document.body.style.userSelect = 'none';
    window.addEventListener('pointermove', this.pointerMoveHandler);
    window.addEventListener('pointerup', this.pointerUpHandler);
    window.addEventListener('pointercancel', this.pointerUpHandler);
    this.cdr.markForCheck();
  }

  ngOnDestroy(): void {
    window.removeEventListener('arena:clamp-output-width', this.clampWidthFromSetupHandler);
    this.stopPanelResize();
  }

  private onResizePointerMove(event: PointerEvent): void {
    if (!this.isResizingPanel) {
      return;
    }
    const deltaX = event.clientX - this.resizeStartX;
    const minWidth = 520;
    const maxWidth = Math.max(minWidth, Math.floor(window.innerWidth - 32));
    const nextWidth = Math.max(minWidth, Math.min(maxWidth, Math.floor(this.resizeStartWidth + deltaX)));
    if (nextWidth === this.panelMaxWidth) {
      return;
    }
    this.panelMaxWidth = nextWidth;
    this.cdr.markForCheck();
  }

  private stopPanelResize(): void {
    if (!this.isResizingPanel) {
      return;
    }
    this.isResizingPanel = false;
    window.removeEventListener('pointermove', this.pointerMoveHandler);
    window.removeEventListener('pointerup', this.pointerUpHandler);
    window.removeEventListener('pointercancel', this.pointerUpHandler);
    document.body.style.cursor = this.previousBodyCursor;
    document.body.style.userSelect = this.previousBodyUserSelect;
    this.cdr.markForCheck();
  }

  private clampPanelMaxWidthToRendered(): void {
    if (this.isResizingPanel) {
      return;
    }
    const panel = this.outputPanelRef?.nativeElement;
    if (!panel) {
      return;
    }
    const renderedWidth = Math.floor(panel.getBoundingClientRect().width);
    if (!Number.isFinite(renderedWidth) || renderedWidth <= 0) {
      return;
    }
    if (renderedWidth >= this.panelMaxWidth) {
      return;
    }
    this.panelMaxWidth = renderedWidth;
    this.cdr.markForCheck();
  }

}

/** first opaque colour of a legend dot (solid fill, gradient stop, then border); near-black is lifted so it shows on the dark strip */
function legendDotColor(dot: Element | null): string | null {
  if (!dot) {
    return null;
  }
  const style = getComputedStyle(dot);
  const candidates = [style.backgroundColor, ...(style.backgroundImage.match(/rgba?\([^)]+\)/g) ?? []), style.borderTopColor];
  for (const candidate of candidates) {
    const [r, g, b, a = 1] = (candidate.match(/[\d.]+/g) ?? []).map(Number);
    if (r === undefined || a < 0.5) {
      continue;
    }
    const luminance = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255;
    return luminance < 0.25 ? 'var(--ink-500)' : `rgb(${r}, ${g}, ${b})`;
  }
  return null;
}
