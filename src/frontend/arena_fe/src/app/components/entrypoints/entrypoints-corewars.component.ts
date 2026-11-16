import { ChangeDetectionStrategy, ChangeDetectorRef, Component, DestroyRef, HostListener, OnInit, ViewChild, effect, inject } from '@angular/core';
import { Store } from '@ngrx/store';
import { ArenaBannerComponent } from '../arena-gui-helpers/arena-banner.component';
import { BlockUIModule } from 'primeng/blockui';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { DialogModule } from 'primeng/dialog';
import { CorewarBotSetupComponent } from '../corewar/corewar-bot-setup.component';
import { CorewarMatchControlsComponent } from '../corewar/corewar-match-controls.component';
import { CorewarMatchSummaryCardComponent } from '../corewar/corewar-match-summary-card.component';
import { CorewarRosterComponent } from '../corewar/corewar-roster.component';
import { CorewarViewerComponent } from '../corewar/corewar-viewer.component';
import { DEFAULT_SIM_CONFIG } from '../corewar/corewar.constants';
import { CorewarSimConfig } from '../corewar/corewar.constants';
import { arenaActions, ArenaState, CorewarLeaveAction } from '@main/arena.store';
import { CorewarMatchSessionService } from '../corewar/corewar-match-session.service';
import { CorewarConsoleRunner } from '../../controllers/corewar-console-runner';
import { getHashRouteState, setHashRouteState } from '@main/arena.utils';

@Component({
  selector: 'arena-entrypoint-corewars',
  standalone: true,
  imports: [
    ArenaBannerComponent,
    BlockUIModule,
    ProgressSpinnerModule,
    DialogModule,
    CorewarBotSetupComponent,
    CorewarMatchControlsComponent,
    CorewarMatchSummaryCardComponent,
    CorewarRosterComponent,
    CorewarViewerComponent,
  ],
  providers: [CorewarMatchSessionService],
  templateUrl: './entrypoints-corewars.component.html',
  styleUrl: './entrypoints-corewars.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class ArenaEntrypointCorewarsComponent implements OnInit {
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly destroyRef = inject(DestroyRef);
  private readonly store = inject(Store<{ arena: ArenaState }>);
  private readonly matchSession = inject(CorewarMatchSessionService);
  private readonly corewarRunner = inject(CorewarConsoleRunner);

  readonly arenaState = this.store.selectSignal((root: { arena: ArenaState }) => root.arena);
  @ViewChild(CorewarBotSetupComponent) botSetupRef?: CorewarBotSetupComponent;
  @ViewChild(CorewarViewerComponent) viewerRef?: CorewarViewerComponent;

  loading = true;
  simConfig: CorewarSimConfig = { ...DEFAULT_SIM_CONFIG };
  botSetupMode: 'simple' | 'advanced' = 'advanced';
  leaveDialogOpen = false;
  reloadDialogOpen = false;
  private hasConfigOverrides = false;
  private pendingSeedParam: string | null = null;
  private leaveDialogAction: CorewarLeaveAction | null = null;
  private lastLeaveRequestId = 0;
  private runtimeWarmupStarted = false;
  private runtimeWarmupLoading = false;
  private botSetupLoading = true;

  get matchState() {
    return this.matchSession.matchState;
  }

  get error(): string | null {
    return this.matchSession.error;
  }

  set error(value: string | null) {
    this.matchSession.setError(value);
  }

  get running(): boolean {
    return this.matchSession.running;
  }

  get moveSpeed(): number {
    return this.matchSession.moveSpeed;
  }

  get matchBannerMessage(): string | null {
    return this.matchSession.matchBannerMessage;
  }

  get matchSummaryDismissed(): boolean {
    return this.matchSession.matchSummaryDismissed;
  }

  get roundWins(): number[] {
    return this.matchSession.roundWins;
  }

  get roundSummaryDismissed(): boolean {
    return this.matchSession.roundSummaryDismissed;
  }

  get activeWarriorCodes(): string[] {
    return this.matchSession.activeWarriorCodes;
  }

  get selectedWarriorIndex(): number | null {
    return this.matchSession.selectedWarriorIndex;
  }

  get selectedProcessQueue(): number[] {
    return this.matchSession.selectedProcessQueue;
  }

  get rosterResetToken(): number {
    return this.matchSession.rosterResetToken;
  }

  // Match session delegates (grouped)
  get cycleLabel(): string {
    return this.matchSession.cycleLabel;
  }

  get roundLabel(): string {
    return this.matchSession.roundLabel;
  }

  get aliveLabel(): string {
    return this.matchSession.aliveLabel;
  }

  get lastExecutedByWarrior(): Array<number | null> {
    return this.matchSession.lastExecutedByWarrior;
  }

  get scoreboardRows() {
    return this.matchSession.scoreboardRows;
  }

  async startMatch(): Promise<void> {
    await this.matchSession.startMatch(this.simConfig, this.loading);
  }

  toggleRunning(force?: boolean): void {
    this.matchSession.toggleRunning(force);
  }

  async stepOnce(): Promise<void> {
    await this.matchSession.stepOnce(this.loading);
  }

  async nextRound(): Promise<void> {
    await this.matchSession.nextRound();
  }

  async resetMatch(): Promise<void> {
    await this.matchSession.resetMatch();
  }

  onProcessSelectionChange(selection: { warriorIndex: number | null; queue: number[] }): void {
    this.matchSession.setProcessSelection(selection);
  }

  onMoveSpeedChange(value: number): void {
    this.matchSession.onMoveSpeedChange(value);
  }

  dismissRoundSummary(): void {
    this.matchSession.dismissRoundSummary();
  }

  dismissMatchSummary(): void {
    this.matchSession.dismissMatchSummary();
  }

  get detailedScoreboard(): boolean {
    return this.arenaState().corewar.viewSettings.detailedScoreboard;
  }

  constructor() {
    this.matchSession.bindHooks({
      getBotSetup: () => this.botSetupRef,
      getViewer: () => this.viewerRef,
      flush: () => this.flush()
    });

    effect(() => {
      const request = this.arenaState().corewar.leaveRequest;
      if (!request.action || request.id === this.lastLeaveRequestId) {
        return;
      }
      this.lastLeaveRequestId = request.id;
      if (!this.matchSession.isMatchInProgress()) {
        void this.handleLeaveAction(request.action);
        this.store.dispatch(arenaActions.clearCorewarLeaveRequest());
        return;
      }
      this.openLeaveDialog(request.action);
    });

    effect(() => {
      const entryId = this.arenaState().selection.entryId;
      if (entryId !== 'corewars') {
        this.resetCorewarUrl();
      }
    });

    this.destroyRef.onDestroy(() => {
      this.matchSession.destroy();
      this.store.dispatch(arenaActions.clearCorewarLeaveRequest());
      this.store.dispatch(arenaActions.updateHeroTheme({ theme: 'default' }));
      this.resetCorewarUrl();
    });
  }

  ngOnInit(): void {
    this.startRuntimeWarmup();
    this.store.dispatch(arenaActions.updateHeroTheme({ theme: 'corewar' }));
    const route = getHashRouteState();
    const params = route.path === '/core' ? route.params : new URLSearchParams(window.location.search);
    if (route.path !== '/core') {
      setHashRouteState('/core');
    }
    const seedParam = params.get('seed');
    if (seedParam) {
      this.pendingSeedParam = seedParam;
    }
    const overrides = this.parseConfigOverrides(params);
    this.hasConfigOverrides = Object.keys(overrides).length > 0;
    this.botSetupMode = this.hasConfigOverrides ? 'advanced' : 'simple';
    if (Object.keys(overrides).length > 0) {
      this.simConfig = { ...this.simConfig, ...overrides };
      this.flush();
    }
  }

  @HostListener('window:keydown', ['$event'])
  onWindowKeydown(event: KeyboardEvent): void {
    if (this.reloadDialogOpen || this.leaveDialogOpen) {
      return;
    }
    const isRoundSummaryOpen = this.matchState.roundDone && !this.matchState.matchDone && !this.roundSummaryDismissed;
    if (isRoundSummaryOpen) {
      if (event.key === 'Enter' || event.code === 'Space' || event.key === ' ') {
        event.preventDefault();
        event.stopPropagation();
        if (event.repeat) {
          return;
        }
        void this.nextRound();
        return;
      }
      if (event.key === 'Escape' || event.key === 'Esc' || event.code === 'Escape') {
        event.preventDefault();
        event.stopPropagation();
        this.dismissRoundSummary();
        return;
      }
    }
    const stepKeys = ['ArrowRight', 'f', 'F', 'l', 'L', '.'];
    if (stepKeys.includes(event.key) || event.code === 'ArrowRight') {
      const target = event.target as HTMLElement | null;
      const tagName = target?.tagName?.toLowerCase();
      if (tagName === 'input' || tagName === 'textarea' || target?.isContentEditable) {
        return;
      }
      if (!this.matchState.matchId || this.matchState.roundDone || this.matchState.matchDone || this.loading) {
        return;
      }
      event.preventDefault();
      void this.stepOnce();
      return;
    }
    if (event.code !== 'Space' && event.key !== ' ') {
      return;
    }
    const target = event.target as HTMLElement | null;
    const tagName = target?.tagName?.toLowerCase();
    if (tagName === 'input' || tagName === 'textarea' || target?.isContentEditable) {
      return;
    }
    if (!this.matchState.matchId || this.matchState.roundDone || this.matchState.matchDone || this.loading) {
      return;
    }
    if (event.repeat) {
      event.preventDefault();
      return;
    }
    event.preventDefault();
    this.toggleRunning();
  }

  @HostListener('window:beforeunload', ['$event'])
  onBeforeUnload(event: BeforeUnloadEvent): void {
    if (this.matchSession.isMatchInProgress()) {
      event.preventDefault();
      event.returnValue = '';
    }
  }

  requestLeave(action: CorewarLeaveAction): void {
    if (!this.matchSession.isMatchInProgress()) {
      void this.handleLeaveAction(action);
      return;
    }
    this.openLeaveDialog(action);
  }

  openReloadDialog(): void {
    if (!this.matchState.matchId) {
      return;
    }
    if (this.running) {
      this.toggleRunning(false);
    }
    this.reloadDialogOpen = true;
    this.flush();
    this.focusDialogButton('.corewar-reload-dialog .corewar-leave-confirm');
  }

  confirmReloadDialog(event?: Event): void {
    if (!this.reloadDialogOpen) {
      return;
    }
    if (event) {
      event.preventDefault();
      event.stopPropagation();
    }
    this.reloadDialogOpen = false;
    this.flush();
    void this.matchSession.reloadRound();
  }

  cancelReloadDialog(): void {
    this.reloadDialogOpen = false;
    this.flush();
  }

  confirmLeaveDialog(event?: Event): void {
    if (!this.leaveDialogOpen) {
      return;
    }
    if (event) {
      event.preventDefault();
      event.stopPropagation();
    }
    const action = this.leaveDialogAction;
    this.leaveDialogOpen = false;
    this.leaveDialogAction = null;
    this.store.dispatch(arenaActions.clearCorewarLeaveRequest());
    if (action) {
      void this.handleLeaveAction(action);
    }
    this.flush();
  }

  cancelLeaveDialog(): void {
    this.leaveDialogOpen = false;
    this.leaveDialogAction = null;
    this.store.dispatch(arenaActions.clearCorewarLeaveRequest());
    this.flush();
  }

  private openLeaveDialog(action: CorewarLeaveAction): void {
    this.leaveDialogAction = action;
    if (this.running) {
      this.toggleRunning(false);
    }
    this.leaveDialogOpen = true;
    this.flush();
    this.focusDialogButton('.corewar-leave-dialog .corewar-leave-confirm');
  }

  private focusDialogButton(selector: string): void {
    window.setTimeout(() => {
      const button = document.querySelector<HTMLButtonElement>(selector);
      button?.focus();
    }, 0);
  }

  private async handleLeaveAction(action: CorewarLeaveAction): Promise<void> {
    if (action === 'reset-match') {
      await this.resetMatch();
      return;
    }
    await this.resetMatch();
    this.resetCorewarUrl();
    this.store.dispatch(arenaActions.resetEntry());
  }

  private resetCorewarUrl(): void {
    try {
      setHashRouteState('/');
    } catch {
      // ignore
    }
  }

  private applyPendingSeed(): void {
    if (!this.pendingSeedParam || !this.botSetupRef) {
      return;
    }
    const error = this.botSetupRef.applySeedValue(this.pendingSeedParam);
    if (error) {
      this.error = `Seed param invalid: ${error}`;
    } else {
      this.syncBotSetupModeFromSelections();
    }
    this.pendingSeedParam = null;
    this.flush();
  }

  private syncBotSetupModeFromSelections(): void {
    if (!this.botSetupRef || this.hasConfigOverrides) {
      return;
    }
    const allSimple = this.botSetupRef.areSelectionsSimple();
    if (allSimple && this.botSetupMode !== 'simple') {
      this.botSetupRef.setSetupMode('simple');
      return;
    }
    if (!allSimple && this.botSetupMode !== 'advanced') {
      this.botSetupRef.setSetupMode('advanced');
    }
  }

  private parseConfigOverrides(params: URLSearchParams): Partial<CorewarSimConfig> {
    const keys: Array<keyof CorewarSimConfig> = ['rounds', 'size', 'cycles', 'processes', 'length', 'distance'];
    const overrides: Partial<CorewarSimConfig> = {};
    keys.forEach((key) => {
      const value = params.get(key);
      if (value === null) {
        return;
      }
      const parsed = Number.parseInt(value, 10);
      if (Number.isFinite(parsed)) {
        overrides[key] = parsed;
      }
    });
    return overrides;
  }

  onSimConfigChange(config: CorewarSimConfig): void {
    this.simConfig = { ...config };
    this.flush();
  }

  onBotSetupModeChange(mode: 'simple' | 'advanced'): void {
    this.botSetupMode = mode;
    this.simConfig = mode === 'simple' ? { ...DEFAULT_SIM_CONFIG } : this.simConfig;
    this.flush();
  }

  onSeedChange(seed: string): void {
    if (this.matchState.matchId) {
      return;
    }
    if (this.pendingSeedParam) {
      return;
    }
    try {
      const route = getHashRouteState();
      const params = route.path === '/core' ? new URLSearchParams(route.params) : new URLSearchParams();
      if (seed) {
        params.set('seed', seed);
      } else {
        params.delete('seed');
      }
      setHashRouteState('/core', params);
    } catch {
      // ignore
    }
  }

  onLoadingChange(isLoading: boolean): void {
    this.botSetupLoading = isLoading;
    this.syncLoadingState();
    if (!isLoading) {
      if (this.pendingSeedParam) {
        this.applyPendingSeed();
      } else {
        this.syncBotSetupModeFromSelections();
      }
    }
    this.flush();
  }

  private startRuntimeWarmup(): void {
    if (this.runtimeWarmupStarted) {
      return;
    }
    this.runtimeWarmupStarted = true;
    this.runtimeWarmupLoading = true;
    this.syncLoadingState();
    void this.corewarRunner.ensureRunner().catch((error) => {
      this.error = error instanceof Error ? error.message : String(error);
      this.runtimeWarmupStarted = false;
      this.runtimeWarmupLoading = false;
      this.syncLoadingState();
      this.flush();
    }).then(() => {
      this.runtimeWarmupLoading = false;
      this.syncLoadingState();
      this.flush();
    });
  }

  private syncLoadingState(): void {
    this.loading = this.botSetupLoading || this.runtimeWarmupLoading;
  }

  private flush(): void {
    this.cdr.markForCheck();
  }
}
