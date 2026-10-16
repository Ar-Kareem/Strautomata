import { ChangeDetectorRef, Component, OnDestroy, effect, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { Store } from '@ngrx/store';
import { TooltipModule } from 'primeng/tooltip';
import { BotPickerComponent } from './bot-picker.component';
import { getActiveGame, resolveBotLabel, resolveEloColumn, setHashRouteState } from '@main/arena.utils';
import type { BotOption, GameWorldOption } from '@main/arena.constants';
import { arenaActions, ArenaState, MatchupMode } from '@main/arena.store';

type StrategySections = {
  strategy: string | null;
  code: string | null;
};

const SHOW_ALL_BOTS_TOOLTIP =
  'Show all automata. Turn off to only show the highest Elo automaton per model.';

@Component({
  selector: 'arena-setup',
  standalone: true,
  imports: [FormsModule, TooltipModule, BotPickerComponent],
  templateUrl: './arena-setup.component.html',
  styleUrls: ['./arena-setup.component.scss']
})
export class ArenaSetupComponent implements OnDestroy {
  private readonly store = inject(Store<{ arena: ArenaState }>);
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly sanitizer = inject(DomSanitizer);
  readonly state = this.store.selectSignal((root: { arena: ArenaState }) => root.arena);
  readonly resolveBotLabel = resolveBotLabel;
  readonly showAllBotsTooltip = SHOW_ALL_BOTS_TOOLTIP;
  panelMaxWidth: number | null = null;
  isResizingPanel = false;
  private resizeStartX = 0;
  private resizeStartWidth = 650;
  private previousBodyCursor = '';
  private previousBodyUserSelect = '';
  private resizedGridElement: HTMLElement | null = null;
  private readonly pointerMoveHandler = (event: PointerEvent) => this.onResizePointerMove(event);
  private readonly pointerUpHandler = () => this.stopPanelResize();
  showAllBots = false;
  private strategyModalOpen = false;
  private strategyModalSlot: 'a' | 'b' | null = null;
  private forcedShowAllBotsByMissingElo = false;
  private readonly codeHtmlCache = new Map<string, SafeHtml>();
  private readonly pythonKeywords = new Set([
    'False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await', 'break', 'class', 'continue',
    'def', 'del', 'elif', 'else', 'except', 'finally', 'for', 'from', 'global', 'if', 'import', 'in',
    'is', 'lambda', 'nonlocal', 'not', 'or', 'pass', 'raise', 'return', 'try', 'while', 'with', 'yield'
  ]);
  private readonly pythonBuiltins = new Set([
    'abs', 'all', 'any', 'bool', 'dict', 'enumerate', 'float', 'int', 'len', 'list', 'max', 'min',
    'print', 'range', 'round', 'set', 'sorted', 'str', 'sum', 'tuple', 'zip'
  ]);

  constructor() {
    effect(() => {
      const state = this.state();
      if (!this.isEloLoaded(state)) {
        this.showAllBots = true;
        this.forcedShowAllBotsByMissingElo = true;
        return;
      }
      if (this.forcedShowAllBotsByMissingElo) {
        this.showAllBots = false;
        this.forcedShowAllBotsByMissingElo = false;
      }
      this.shuffleBotsIfNeeded(state);
    });
  }

  get activeGame(): GameWorldOption | null {
    return getActiveGame(this.state());
  }

  get canPickBots(): boolean {
    return Boolean(this.activeGame) ;
  }

  get canUseHumanBots(): boolean {
    return Boolean(this.activeGame?.hasGui);
  }

  get isShowAllBotsToggleEnabled(): boolean {
    return this.isEloLoaded(this.state());
  }

  get activeEloMap(): Record<string, number> | null {
    return this.getActiveEloMap();
  }

  get visibleBots(): BotOption[] {
    return this.getVisibleBots(this.state());
  }

  get isBotsSuccessful(): boolean {
    const botsStatus = this.state().match.botsStatus;
    return botsStatus === 'ready';
  }

  get isStrategyModalOpen(): boolean {
    return this.strategyModalOpen && this.strategyModalSlot !== null;
  }

  get strategyModalTitle(): string {
    return this.strategyModalSlot === 'a' ? 'Automaton A strategy' : 'Automaton B strategy';
  }

  get activeStrategyLabel(): string {
    const state = this.state();
    if (this.strategyModalSlot === 'a') {
      return resolveBotLabel(state.catalog.bots, state.selection.botAId, 'Automaton A');
    }
    if (this.strategyModalSlot === 'b') {
      return resolveBotLabel(state.catalog.bots, state.selection.botBId, 'Automaton B');
    }
    return 'Automaton strategy';
  }

  get isActiveStrategyHuman(): boolean {
    const selection = this.state().selection;
    const botId = this.strategyModalSlot === 'a' ? selection.botAId : this.strategyModalSlot === 'b' ? selection.botBId : null;
    return botId === 'human';
  }

  get activeStrategy(): { text: string | null; loading: boolean; error: string | null } | null {
    if (!this.strategyModalSlot) {
      return null;
    }
    return this.state().botStrategies[this.strategyModalSlot];
  }

  getInlineStrategySections(slot: 'a' | 'b'): StrategySections {
    const text = this.state().botStrategies[slot].text ?? '';
    return this.splitStrategyAndCode(text);
  }

  getModalStrategySections(): StrategySections {
    const text = this.activeStrategy?.text ?? '';
    return this.splitStrategyAndCode(text);
  }

  highlightCodeHtml(code: string | null): SafeHtml | null {
    if (!code) {
      return null;
    }
    const cached = this.codeHtmlCache.get(code);
    if (cached) {
      return cached;
    }
    const html = this.pythonToHighlightedHtml(code);
    const safe = this.sanitizer.bypassSecurityTrustHtml(html);
    this.codeHtmlCache.set(code, safe);
    return safe;
  }

  onGameChange(value: string | null): void {
    if (!value) {
      this.updateArenaSubgameUrl(null, null);
      this.store.dispatch(arenaActions.gameChangeRequested({ id: '', gameId: null, worldId: null }));
      return;
    }
    const [gameId, worldId] = value.split('/');
    this.updateArenaSubgameUrl(gameId ?? null, worldId ?? null);
    this.store.dispatch(arenaActions.gameChangeRequested({ id: value, gameId: gameId, worldId: worldId }));
  }

  onMatchupChange(mode: MatchupMode): void {
    if (!this.canUseHumanBots && mode !== 'ai-vs-ai') {
      return;
    }
    this.store.dispatch(arenaActions.matchupChangeRequested({ mode }));
  }

  onBotChange(slot: 'a' | 'b', value: string | null): void {
    this.store.dispatch(arenaActions.botChangeRequested({ slot, botId: value }));
  }

  onShowAllBotsChange(value: boolean): void {
    if (!this.isShowAllBotsToggleEnabled) {
      this.showAllBots = true;
      this.forcedShowAllBotsByMissingElo = true;
      return;
    }
    this.showAllBots = Boolean(value);
    this.forcedShowAllBotsByMissingElo = false;
    if (!this.showAllBots) {
      this.shuffleBotsIfNeeded(this.state());
    }
  }
  
  selectRandomBot(slot: 'a' | 'b'): void {
    this.store.dispatch(arenaActions.randomBotRequested({ slot }));
  }

  onPanelResizeStart(event: PointerEvent): void {
    if (event.button !== 0) {
      return;
    }
    const panel = (event.currentTarget as HTMLElement | null)?.parentElement;
    this.resizedGridElement = panel?.closest('.main-grid') as HTMLElement | null;
    const measuredWidth = panel ? Math.floor(panel.getBoundingClientRect().width) : this.panelMaxWidth ?? 650;
    event.preventDefault();
    this.isResizingPanel = true;
    this.resizeStartX = event.clientX;
    this.resizeStartWidth = measuredWidth;
    this.panelMaxWidth = measuredWidth;
    this.resizedGridElement?.style.setProperty('--arena-setup-column-width', `${measuredWidth}px`);
    this.previousBodyCursor = document.body.style.cursor;
    this.previousBodyUserSelect = document.body.style.userSelect;
    document.body.style.cursor = 'ew-resize';
    document.body.style.userSelect = 'none';
    window.addEventListener('pointermove', this.pointerMoveHandler);
    window.addEventListener('pointerup', this.pointerUpHandler);
    window.addEventListener('pointercancel', this.pointerUpHandler);
    this.cdr.markForCheck();
  }

  getBotEloDisplay(botId: string | null): string {
    if (botId === 'human') {
      return 'N/A';
    }
    const eloMap = this.getActiveEloMap();
    if (!botId || !eloMap) {
      return '—';
    }
    const value = eloMap[botId];
    if (value === undefined) {
      return 'DNQ';
    }
    return String(Math.round(value));
  }

  getBotEloTooltip(botId: string | null): string | undefined {
    if (!botId) {
      return undefined;
    }
    return `ELO: ${this.getBotEloDisplay(botId)}`;
  }

  isBotEloEmpty(botId: string | null): boolean {
    const eloMap = this.getActiveEloMap();
    return !botId || (!eloMap && botId !== 'human');
  }

  isBotEloDnq(botId: string | null): boolean {
    const eloMap = this.getActiveEloMap();
    return Boolean(botId && botId !== 'human' && eloMap && eloMap[botId] === undefined);
  }

  openStrategyModal(slot: 'a' | 'b'): void {
    if (slot === 'a' && !this.state().selection.botAId) {
      return;
    }
    if (slot === 'b' && !this.state().selection.botBId) {
      return;
    }
    this.strategyModalSlot = slot;
    this.strategyModalOpen = true;
  }

  closeStrategyModal(): void {
    this.strategyModalOpen = false;
    this.strategyModalSlot = null;
  }

  ngOnDestroy(): void {
    this.stopPanelResize();
  }

  private getActiveEloMap(state: ArenaState = this.state()): Record<string, number> | null {
    const column = resolveEloColumn(state.selection.gameId, state.selection.worldId);
    if (!column) {
      return null;
    }
    return state.catalog.eloByColumn?.[column] ?? null;
  }

  private isEloLoaded(state: ArenaState): boolean {
    return Boolean(state.catalog.eloByColumn);
  }

  private getVisibleBots(state: ArenaState): BotOption[] {
    const bots = state.catalog.bots;
    if (this.showAllBots || !this.isEloLoaded(state)) {
      return bots;
    }
    const eloMap = this.getActiveEloMap(state);
    if (!eloMap) {
      return bots;
    }
    const bestByParent = new Map<string, BotOption>();
    const parentOf = (botId: string): string => {
      const slashIdx = botId.indexOf('/');
      return slashIdx > 0 ? botId.slice(0, slashIdx) : botId;
    };
    for (const bot of bots) {
      const parent = parentOf(bot.id);
      const currentBest = bestByParent.get(parent);
      if (!currentBest) {
        bestByParent.set(parent, bot);
        continue;
      }
      const currentElo = eloMap[currentBest.id];
      const nextElo = eloMap[bot.id];
      if (nextElo === undefined) {
        continue;
      }
      if (currentElo === undefined || nextElo > currentElo) {
        bestByParent.set(parent, bot);
      }
    }
    return bots.filter((bot) => bestByParent.get(parentOf(bot.id))?.id === bot.id);
  }

  /** With "show all bots" off, swap a hidden pick for the best bot of the same model. */
  private shuffleBotsIfNeeded(state: ArenaState): void {
    if (this.showAllBots || !this.isEloLoaded(state)) {
      return;
    }
    if (state.match.botsStatus !== 'ready') {
      return;
    }
    const visibleBots = this.getVisibleBots(state);
    const visibleIds = new Set(visibleBots.map((bot) => bot.id));
    const modelOf = (botId: string) => botId.split('/')[0];
    for (const slot of ['a', 'b'] as const) {
      const botId = slot === 'a' ? state.selection.botAId : state.selection.botBId;
      if (!botId || visibleIds.has(botId)) {
        continue;
      }
      const replacement = visibleBots.find((bot) => modelOf(bot.id) === modelOf(botId));
      if (replacement) {
        this.onBotChange(slot, replacement.id);
        return; // the other slot is handled on the next state change
      }
    }
  }

  private updateArenaSubgameUrl(gameId: string | null, worldId: string | null): void {
    try {
      const params = new URLSearchParams();
      if (gameId && worldId) {
        params.set('game', gameId);
        params.set('sub', worldId);
      }
      setHashRouteState('/arena', params);
    } catch {
      // ignore
    }
  }

  private onResizePointerMove(event: PointerEvent): void {
    if (!this.isResizingPanel) {
      return;
    }
    const deltaX = event.clientX - this.resizeStartX;
    const grid = this.resizedGridElement;
    const computedGrid = grid ? window.getComputedStyle(grid) : null;
    const gridGap = computedGrid ? Number.parseFloat(computedGrid.columnGap || '0') : 24;
    const minWidth = 520;
    const minOutputWidth = 520;
    const viewportMax = Math.floor(window.innerWidth - 32);
    const gridMax = grid ? Math.floor(grid.clientWidth - gridGap - minOutputWidth) : viewportMax;
    const maxWidth = Math.max(minWidth, Math.min(viewportMax, gridMax));
    const nextWidth = Math.max(minWidth, Math.min(maxWidth, Math.floor(this.resizeStartWidth + deltaX)));
    if (nextWidth === this.panelMaxWidth) {
      return;
    }
    const previousWidth = this.panelMaxWidth ?? this.resizeStartWidth;
    this.panelMaxWidth = nextWidth;
    this.resizedGridElement?.style.setProperty('--arena-setup-column-width', `${nextWidth}px`);
    if (nextWidth > previousWidth) {
      window.dispatchEvent(new Event('arena:clamp-output-width'));
    }
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

  private splitStrategyAndCode(response: string): StrategySections {
    const raw = String(response ?? '').trim();
    if (!raw) {
      return { strategy: null, code: null };
    }

    let code = raw;
    let foundCode = false;
    let foundBlock = false;

    if (code.includes('<code>')) {
      foundCode = true;
      const parts = code.split('<code>');
      code = parts[parts.length - 1] ?? '';
    }
    if (code.includes('</code>')) {
      code = code.split('</code>')[0] ?? '';
    }
    if (code.includes('```python')) {
      const parts = code.split('```python');
      code = parts[parts.length - 1] ?? '';
      foundBlock = true;
    }
    if (code.includes('```')) {
      code = code.split('```')[0] ?? '';
    }

    const hasStructuredCode = foundCode || foundBlock;
    const codeText = hasStructuredCode ? code.trim() || null : null;

    if (!hasStructuredCode) {
      return { strategy: raw, code: null };
    }

    const startIdx = foundCode
      ? raw.indexOf('<code>')
      : raw.includes('```python')
        ? raw.indexOf('```python')
        : raw.indexOf('```');
    const strategyText = startIdx >= 0 ? raw.slice(0, startIdx).trim() : raw;
    return {
      strategy: strategyText || null,
      code: codeText
    };
  }

  private pythonToHighlightedHtml(code: string): string {
    const tokenRegex = /("""[\s\S]*?"""|'''[\s\S]*?'''|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|#[^\n]*|@[A-Za-z_]\w*|\b\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\b|\b[A-Za-z_][A-Za-z0-9_]*\b)/g;
    let out = '';
    let last = 0;
    let expectDefinitionName = false;
    let match: RegExpExecArray | null;

    while ((match = tokenRegex.exec(code)) !== null) {
      const [token] = match;
      const index = match.index;
      const between = code.slice(last, index);
      out += this.escapeHtml(between);
      if (expectDefinitionName && /[^\s]/.test(between)) {
        expectDefinitionName = false;
      }
      const wrapped = this.wrapPythonToken(token, expectDefinitionName);
      out += wrapped.html;
      expectDefinitionName = wrapped.expectDefinitionName;
      last = index + token.length;
    }
    out += this.escapeHtml(code.slice(last));
    return this.markPolicyEntrypoint(out);
  }

  private wrapPythonToken(token: string, expectDefinitionName: boolean): { html: string; expectDefinitionName: boolean } {
    const escaped = this.escapeHtml(token);
    if (expectDefinitionName && this.isPythonIdentifier(token)) {
      return {
        html: `<span class="py-definition-name">${escaped}</span>`,
        expectDefinitionName: false
      };
    }
    if (token.startsWith('#')) {
      return { html: `<span class="py-comment">${escaped}</span>`, expectDefinitionName: false };
    }
    if (token.startsWith('"') || token.startsWith("'")) {
      return { html: `<span class="py-string">${escaped}</span>`, expectDefinitionName: false };
    }
    if (token.startsWith('@')) {
      return { html: `<span class="py-decorator">${escaped}</span>`, expectDefinitionName: false };
    }
    if (/^\d/.test(token)) {
      return { html: `<span class="py-number">${escaped}</span>`, expectDefinitionName: false };
    }
    if (this.pythonKeywords.has(token)) {
      return {
        html: `<span class="py-keyword">${escaped}</span>`,
        expectDefinitionName: token === 'def'
      };
    }
    if (this.pythonBuiltins.has(token)) {
      return { html: `<span class="py-builtin">${escaped}</span>`, expectDefinitionName: false };
    }
    return { html: escaped, expectDefinitionName: false };
  }

  private isPythonIdentifier(token: string): boolean {
    return /^[A-Za-z_][A-Za-z0-9_]*$/.test(token);
  }

  private markPolicyEntrypoint(html: string): string {
    const entrypointRegex = /(^|\n)([ \t]*)(<span class="py-keyword">def<\/span>)(\s+)(<span class="py-definition-name">policy<\/span>)(\s*\()/;
    return html.replace(
      entrypointRegex,
      '$1$2<span class="py-entrypoint-indicator" title="Entrypoint">▶</span> $3$4$5$6'
    );
  }

  private escapeHtml(value: string): string {
    return value
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#39;');
  }

}
