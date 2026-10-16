import { NgComponentOutlet } from '@angular/common';
import {
  ChangeDetectorRef,
  Component,
  ElementRef,
  OnDestroy,
  ViewChild,
  inject,
  type Type
} from '@angular/core';
import { Store } from '@ngrx/store';
import { TooltipModule } from 'primeng/tooltip';
import { getActiveGame, resolveBotLabel } from '@main/arena.utils';
import { arenaActions, type ArenaState } from '@main/arena.store';


import { GAME_GUI_MAP } from '@game-gui/game-gui-map';

@Component({
  selector: 'arena-output',
  standalone: true,
  templateUrl: './arena-output.component.html',
  styleUrl: './arena-output.component.scss',
  imports: [NgComponentOutlet, TooltipModule]
})
export class ArenaOutputComponent implements OnDestroy {
  private readonly store = inject(Store<{ arena: ArenaState }>);
  private readonly cdr = inject(ChangeDetectorRef);
  @ViewChild('outputPanel', { static: true }) private outputPanelRef?: ElementRef<HTMLElement>;
  readonly state = this.store.selectSignal((root: { arena: ArenaState }) => root.arena);
  readonly resolveBotLabel = resolveBotLabel;
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
  }

  get activeGui(): Type<unknown> | null {
    const gameId = this.state().selection.gameId;
    return gameId ? GAME_GUI_MAP[gameId] ?? null : null;
  }

  get guiInputs(): Record<string, unknown> {
    const state = this.state();
    const inputs: Record<string, unknown> = {
      observation: state.match.matchObservation,
      botA: resolveBotLabel(
        state.catalog.bots,
        state.match.activeBotAId,
        resolveBotLabel(state.catalog.bots, state.selection.botAId, 'Automaton A')
      ),
      botB: resolveBotLabel(
        state.catalog.bots,
        state.match.activeBotBId,
        resolveBotLabel(state.catalog.bots, state.selection.botBId, 'Automaton B')
      ),
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
