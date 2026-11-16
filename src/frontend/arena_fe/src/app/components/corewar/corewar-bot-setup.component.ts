import { ChangeDetectionStrategy, ChangeDetectorRef, Component, ElementRef, EventEmitter, Input, OnInit, Output, ViewChild, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Store } from '@ngrx/store';
import { DialogModule } from 'primeng/dialog';
import { InputTextModule } from 'primeng/inputtext';
import { SelectModule } from 'primeng/select';
import { TooltipModule } from 'primeng/tooltip';

import { CorewarConsoleRunner } from '../../controllers/corewar-console-runner';
import { arenaActions, ArenaState } from '@main/arena.store';
import { type CorewarSimConfig, type GroupedWarriorOption, type WarriorOption } from './corewar.constants';

@Component({
  selector: 'corewar-bot-setup',
  standalone: true,
  imports: [DialogModule, FormsModule, InputTextModule, SelectModule, TooltipModule],
  templateUrl: './corewar-bot-setup.component.html',
  styleUrl: './corewar-bot-setup.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class CorewarBotSetupComponent implements OnInit {
  private readonly runner = inject(CorewarConsoleRunner);
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly store = inject(Store<{ arena: ArenaState }>);

  @Input() simConfig: CorewarSimConfig | null = null;
  @Input() initialMode: 'simple' | 'advanced' = 'advanced';
  @Output() loadingChange = new EventEmitter<boolean>();
  @Output() modeChange = new EventEmitter<'simple' | 'advanced'>();
  @Output() seedChange = new EventEmitter<string>();

  loading = true;
  error: string | null = null;
  warriors: WarriorOption[] = [];
  groupedWarriorOptions: GroupedWarriorOption[] = [];
  selections: number[] = [];
  errorIndices = new Set<number>();
  setupMode: 'simple' | 'advanced' = 'advanced';

  isSeedDialogOpen = false;
  seedValue = '';
  seedError: string | null = null;

  isBotPreviewOpen = false;
  botPreviewName = '';
  botPreviewCode = '';
  private botPreviewIndex: number | null = null;
  private botPreviewOriginalCode = '';
  botPreviewReadOnly = false;
  botPreviewCompileError: string | null = null;
  botPreviewCompileErrorLine: number | null = null;
  botPreviewLineNumbers: number[] = [0];
  private compileTimer: number | null = null;
  private compileToken = 0;
  private modeInitialized = false;
  private pendingWarriorCodeLoads = new Map<string, Promise<string>>();

  ngOnInit(): void {
    if (!this.modeInitialized) {
      this.setupMode = this.initialMode;
      this.modeInitialized = true;
    }
    void this.loadWarriors();
  }

  @ViewChild('codeGutter') private codeGutterRef?: ElementRef<HTMLDivElement>;
  @ViewChild('seedInput') private seedInputRef?: ElementRef<HTMLInputElement>;

  async getSelectedWarriorSpecs(): Promise<Array<{ source: string; code: string }>> {
    await this.waitForSelectedWarriorCodeLoads();
    const selected = this.selections
      .map((index) => this.warriors[index])
      .filter((warrior): warrior is WarriorOption => Boolean(warrior));
    const missing = selected.find((warrior) => warrior.path && !warrior.codeLoaded);
    if (missing) {
      throw new Error(`Warrior code is still loading: ${missing.name}`);
    }
    return selected.map((warrior) => ({ source: 'inline', code: warrior.code ?? '' }));
  }

  addSlot(): void {
    this.clearErrorIndex();
    const idx = this.isSimpleMode
      ? this.pickRandomFromIndices(1, this.getOrigIndices())[0] ?? 0
      : this.pickRandomSelections(1, this.warriors.length)[0] ?? 0;
    this.selections = [...this.selections, idx];
    this.onSelectionsUpdated();
  }

  randomizeSlot(index: number): void {
    if (this.warriors.length === 0) {
      return;
    }
    this.clearErrorIndex();
    const idx = this.isSimpleMode
      ? this.pickRandomFromIndices(1, this.getOrigIndices())[0] ?? 0
      : this.pickRandomSelections(1, this.warriors.length)[0] ?? 0;
    const next = [...this.selections];
    next[index] = idx;
    this.selections = next;
    this.onSelectionsUpdated();
  }

  requestOpenConfig(): void {
    if (this.isSimpleMode) {
      return;
    }
    if (this.loading) {
      return;
    }
    this.store.dispatch(arenaActions.updateCorewarConfigDialogOpen({ open: true }));
  }

  openSeedDialog(): void {
    if (this.isSimpleMode) {
      return;
    }
    if (this.loading) {
      return;
    }
    this.seedError = null;
    this.seedValue = this.formatSeedValue();
    this.isSeedDialogOpen = true;
    this.flush();
  }

  closeSeedDialog(): void {
    this.isSeedDialogOpen = false;
    this.seedError = null;
    this.flush();
  }

  onSeedDialogHide(): void {
    this.closeSeedDialog();
  }

  onSeedDialogShow(): void {
    this.selectSeedText();
  }

  applySeed(): void {
    this.clearErrorIndex();
    const result = this.parseSeedValue(this.seedValue);
    if (typeof result === 'string') {
      this.seedError = result;
      this.flush();
      return;
    }
    this.selections = result;
    this.seedError = null;
    this.isSeedDialogOpen = false;
    this.seedValue = this.formatSeedValue();
    this.onSelectionsUpdated();
  }

  applySeedValue(value: string): string | null {
    this.clearErrorIndex();
    const result = this.parseSeedValue(value);
    if (typeof result === 'string') {
      this.seedError = result;
      this.flush();
      return result;
    }
    this.selections = result;
    this.seedError = null;
    this.isSeedDialogOpen = false;
    this.seedValue = this.formatSeedValue();
    this.onSelectionsUpdated();
    return null;
  }

  private parseSeedValue(rawValue: string): number[] | string {
    if (this.warriors.length === 0) {
      return 'No warriors available.';
    }
    const parts = rawValue
      .split('-')
      .map((entry) => entry.trim())
      .filter((entry) => entry.length > 0);
    if (parts.length === 0) {
      return 'Enter a seed like "N--a-b-c".';
    }
    const count = Number.parseInt(parts[0], 10);
    if (!Number.isFinite(count) || count < 2) {
      return 'N must be at least 2.';
    }
    if (parts.length !== count + 1) {
      return `Expected ${count} bot numbers.`;
    }
    const picks: number[] = [];
    for (let i = 0; i < count; i += 1) {
      const value = Number.parseInt(parts[i + 1], 10);
      if (!Number.isFinite(value) || value < 1 || value > this.warriors.length) {
        return `Bot numbers must be between 1 and ${this.warriors.length}.`;
      }
      picks.push(value - 1);
    }
    return picks;
  }

  removeSlot(index: number): void {
    if (this.selections.length <= 2) {
      return;
    }
    this.clearErrorIndex();
    this.selections = this.selections.filter((_, i) => i !== index);
    this.onSelectionsUpdated();
  }

  async openBotPreview(slotIndex: number): Promise<void> {
    if (this.isSimpleMode) {
      return;
    }
    const warriorIndex = this.selections[slotIndex];
    const warrior = this.warriors[warriorIndex];
    if (!warrior) {
      return;
    }
    try {
      this.error = null;
      if (warrior.path) {
        const pending = this.pendingWarriorCodeLoads.get(warrior.path);
        if (pending) {
          await pending;
        }
      }
      const latest = this.warriors[warriorIndex];
      this.resetCompileState();
      this.botPreviewName = warrior.name || `Bot ${slotIndex + 1}`;
      this.botPreviewCode = latest?.code ?? warrior.code ?? 'No source available.';
      this.botPreviewOriginalCode = this.botPreviewCode;
      this.botPreviewIndex = warriorIndex;
      this.botPreviewReadOnly = false;
      this.updatePreviewLineNumbers();
      this.isBotPreviewOpen = true;
      this.flush();
    } catch (error) {
      this.error = error instanceof Error ? error.message : String(error);
      this.flush();
    }
  }

  requestCloseBotPreview(): void {
    if (this.hasUnsavedChanges) {
      const shouldClose = window.confirm('Discard unsaved changes?');
      if (!shouldClose) {
        return;
      }
    }
    this.closeBotPreview();
  }

  closeBotPreview(): void {
    this.resetCompileState();
    this.isBotPreviewOpen = false;
    this.botPreviewName = '';
    this.botPreviewCode = '';
    this.botPreviewOriginalCode = '';
    this.botPreviewIndex = null;
    this.botPreviewReadOnly = false;
    this.botPreviewLineNumbers = [0];
    this.flush();
  }

  saveBotPreview(): void {
    if (this.botPreviewReadOnly) {
      return;
    }
    if (this.botPreviewIndex === null) {
      return;
    }
    const updated = this.botPreviewCode ?? '';
    const next = [...this.warriors];
    const target = next[this.botPreviewIndex];
    if (!target) {
      return;
    }
    next[this.botPreviewIndex] = { ...target, code: updated, codeLoaded: true };
    this.warriors = next;
    this.botPreviewOriginalCode = updated;
    this.closeBotPreview();
    this.flush();
  }

  onBotPreviewInput(event: Event): void {
    if (this.botPreviewReadOnly) {
      return;
    }
    const target = event.target as HTMLTextAreaElement | null;
    const value = target?.value ?? this.botPreviewCode ?? '';
    this.updatePreviewLineNumbersFromValue(value);
    this.scheduleCompile(value);
  }

  onBotPreviewScroll(event: Event): void {
    const target = event.target as HTMLTextAreaElement | null;
    if (!target || !this.codeGutterRef) {
      return;
    }
    this.codeGutterRef.nativeElement.scrollTop = target.scrollTop;
  }

  get hasUnsavedChanges(): boolean {
    return !this.botPreviewReadOnly && this.botPreviewCode !== this.botPreviewOriginalCode;
  }

  async loadWarriors(): Promise<void> {
    this.loading = true;
    this.error = null;
    this.clearErrorIndex();
    this.loadingChange.emit(true);
    this.flush();
    try {
      const result = await this.runner.listFileWarriors();
      const payload = result as { warriors?: WarriorOption[]; error?: string };
      if (payload.error) {
        throw new Error(payload.error);
      }
      this.warriors = (payload.warriors ?? []).map((warrior) => ({
        ...warrior,
        code: warrior.code ?? '',
        codeLoaded: Boolean(warrior.codeLoaded ?? warrior.code)
      }));
      this.refreshGroupedOptions();
      if (this.warriors.length === 0) {
        this.selections = [];
      } else if (this.selections.length === 0) {
        const defaultSeed = '5--16-8-11-13-5';
        const result = this.parseSeedValue(defaultSeed);
        if (Array.isArray(result)) {
          this.selections = result;
        } else {
          const slotCount = 2;
          if (this.isSimpleMode) {
            this.selections = this.pickRandomFromIndices(slotCount, this.getOrigIndices());
          } else {
            this.selections = this.pickRandomSelections(slotCount, this.warriors.length);
          }
        }
      }
      this.emitSeedChange();
      await this.prefetchSelectedWarriorCodes();
    } catch (error) {
      this.error = error instanceof Error ? error.message : String(error);
    } finally {
      this.loading = false;
      this.loadingChange.emit(false);
      this.flush();
    }
  }

  private async ensureWarriorCode(index: number): Promise<string> {
    const warrior = this.warriors[index];
    if (!warrior) {
      return '';
    }
    if (warrior.codeLoaded) {
      return warrior.code ?? '';
    }
    if (!warrior.path) {
      const next = [...this.warriors];
      const current = next[index];
      if (current) {
        next[index] = { ...current, codeLoaded: true };
        this.warriors = next;
      }
      return warrior.code ?? '';
    }
    const code = await this.fetchWarriorCode(warrior.path);
    const next = [...this.warriors];
    const current = next[index];
    if (current) {
      next[index] = { ...current, code, codeLoaded: true };
      this.warriors = next;
    }
    return code;
  }

  private async waitForSelectedWarriorCodeLoads(): Promise<void> {
    const pending: Promise<string>[] = [];
    const seen = new Set<string>();
    for (const index of this.selections) {
      const path = this.warriors[index]?.path;
      if (!path || seen.has(path)) {
        continue;
      }
      seen.add(path);
      const promise = this.pendingWarriorCodeLoads.get(path);
      if (promise) {
        pending.push(promise);
      }
    }
    if (pending.length > 0) {
      await Promise.all(pending);
    }
  }

  private async prefetchSelectedWarriorCodes(): Promise<void> {
    const unique = new Set<number>(this.selections);
    const indices = [...unique].filter((index) => {
      const warrior = this.warriors[index];
      return Boolean(warrior && !warrior.codeLoaded && warrior.path);
    });
    if (indices.length === 0) {
      return;
    }
    try {
      await Promise.all(indices.map((index) => this.ensureWarriorCode(index)));
      this.flush();
    } catch (error) {
      this.error = error instanceof Error ? error.message : String(error);
      this.flush();
    }
  }

  private fetchWarriorCode(path: string): Promise<string> {
    const existing = this.pendingWarriorCodeLoads.get(path);
    if (existing) {
      return existing;
    }
    const promise = (async () => {
      const result = await this.runner.loadWarriorCode(path);
      const payload = result as { code?: string; error?: string };
      if (payload.error) {
        throw new Error(payload.error);
      }
      return payload.code ?? '';
    })();
    this.pendingWarriorCodeLoads.set(path, promise);
    return promise.finally(() => {
      this.pendingWarriorCodeLoads.delete(path);
    });
  }

  private pickRandomSelections(count: number, total: number): number[] {
    if (total <= 0 || count <= 0) {
      return [];
    }
    const indices = Array.from({ length: total }, (_, i) => i);
    for (let i = indices.length - 1; i > 0; i -= 1) {
      const j = Math.floor(Math.random() * (i + 1));
      [indices[i], indices[j]] = [indices[j], indices[i]];
    }
    if (total >= count) {
      return indices.slice(0, count);
    }
    const result = indices.slice();
    while (result.length < count) {
      result.push(Math.floor(Math.random() * total));
    }
    return result;
  }

  private buildGroupedOptions(warriors: WarriorOption[], simpleOnly: boolean): GroupedWarriorOption[] {
    if (simpleOnly) {
      const items: Array<{ label: string; value: number }> = [];
      warriors.forEach((warrior, index) => {
        const rawName = warrior.name ?? '';
        if (this.isOrigWarriorName(rawName)) {
          items.push({ label: this.formatSimpleName(rawName), value: index });
        }
      });
      if (items.length === 0) {
        return [];
      }
      return [{ label: 'Original Repo', value: 'orig', items }];
    }
    const labelMap: Record<string, string> = {
      drq: 'Dgtl. Red. Q.',
      gw: 'GPT Warriors',
      orig: 'Original Repo',
    };
    const order = ['drq', 'gw', 'orig'];
    const groups = new Map<string, GroupedWarriorOption>();

    const ensureGroup = (key: string): GroupedWarriorOption => {
      if (!groups.has(key)) {
        groups.set(key, { label: labelMap[key] ?? key, value: key, items: [] });
      }
      return groups.get(key)!;
    };

    warriors.forEach((warrior, index) => {
      const rawName = warrior.name ?? '';
      let prefix = 'orig';
      let label = rawName;
      const colonIndex = rawName.indexOf(':');
      if (colonIndex > 0) {
        const maybePrefix = rawName.slice(0, colonIndex);
        if (maybePrefix === 'drq' || maybePrefix === 'gw' || maybePrefix === 'orig') {
          prefix = maybePrefix;
        }
      }
      ensureGroup(prefix).items.push({ label, value: index });
    });

    const result: GroupedWarriorOption[] = [];
    order.forEach((key) => {
      const group = groups.get(key);
      if (group && group.items.length > 0) {
        result.push(group);
        groups.delete(key);
      }
    });
    for (const group of groups.values()) {
      if (group.items.length > 0) {
        result.push(group);
      }
    }
    return result;
  }

  private formatSeedValue(): string {
    const count = this.selections.length;
    const entries = this.selections.map((value) => value + 1);
    if (entries.length === 0) {
      return String(count);
    }
    return `${count}--${entries.map((value) => String(value)).join('-')}`;
  }

  private emitSeedChange(): void {
    if (this.selections.length < 2) {
      return;
    }
    this.seedChange.emit(this.formatSeedValue());
  }

  onSelectionChange(): void {
    this.clearErrorIndex();
    this.onSelectionsUpdated();
  }

  setSetupMode(mode: 'simple' | 'advanced'): void {
    if (this.setupMode === mode) {
      return;
    }
    this.setupMode = mode;
    if (this.isSimpleMode) {
      this.constrainSelectionsToOrig();
      this.isSeedDialogOpen = false;
      this.closeBotPreview();
    }
    this.refreshGroupedOptions();
    this.modeChange.emit(mode);
    this.onSelectionsUpdated();
  }

  areSelectionsSimple(): boolean {
    if (this.warriors.length === 0) {
      return false;
    }
    return this.selections.every((index) => {
      const name = this.warriors[index]?.name ?? '';
      return this.isOrigWarriorName(name);
    });
  }

  get isSimpleMode(): boolean {
    return this.setupMode === 'simple';
  }

  setErrorIndices(indices: number[] | null | undefined): void {
    const next = new Set<number>();
    if (Array.isArray(indices)) {
      indices.forEach((value) => {
        if (Number.isFinite(value)) {
          next.add(value);
        }
      });
    }
    this.errorIndices = next;
    this.flush();
  }

  private scheduleCompile(code: string): void {
    this.clearCompileTimer();
    this.botPreviewCompileError = null;
    this.botPreviewCompileErrorLine = null;
    const token = this.bumpCompileToken();
    this.compileTimer = window.setTimeout(() => {
      void this.compileBotPreview(code, token);
    }, 250);
    this.flush();
  }

  private async compileBotPreview(code: string, token: number): Promise<void> {
    if (token !== this.compileToken) {
      return;
    }
    try {
      const result = await this.runner.compileWarrior({ code, config: this.simConfig ?? undefined });
      if (token !== this.compileToken) {
        return;
      }
      const payload = result as { ok?: boolean; error?: string };
      if (payload.error || payload.ok === false) {
        this.botPreviewCompileError = payload.error ?? 'Compile error.';
        this.botPreviewCompileErrorLine = this.extractErrorLine(payload.error ?? null);
      } else {
        this.botPreviewCompileError = null;
        this.botPreviewCompileErrorLine = null;
      }
    } catch (error) {
      if (token !== this.compileToken) {
        return;
      }
      this.botPreviewCompileError = error instanceof Error ? error.message : String(error);
      this.botPreviewCompileErrorLine = this.extractErrorLine(this.botPreviewCompileError);
    } finally {
      if (token === this.compileToken) {
        this.flush();
      }
    }
  }

  private resetCompileState(): void {
    this.clearCompileTimer();
    this.bumpCompileToken();
    this.botPreviewCompileError = null;
    this.botPreviewCompileErrorLine = null;
  }

  private updatePreviewLineNumbers(): void {
    this.updatePreviewLineNumbersFromValue(this.botPreviewCode ?? '');
  }

  private updatePreviewLineNumbersFromValue(raw: string): void {
    const count = Math.max(1, raw.split('\n').length);
    this.botPreviewLineNumbers = Array.from({ length: count }, (_, index) => index);
  }

  private extractErrorLine(message: string | null | undefined): number | null {
    if (!message) {
      return null;
    }
    const match = message.match(/line\s+(\d+)/i);
    if (!match) {
      return null;
    }
    const value = Number.parseInt(match[1], 10);
    if (!Number.isFinite(value) || value < 0) {
      return null;
    }
    return value;
  }

  private clearCompileTimer(): void {
    if (this.compileTimer === null) {
      return;
    }
    window.clearTimeout(this.compileTimer);
    this.compileTimer = null;
  }

  private bumpCompileToken(): number {
    this.compileToken += 1;
    return this.compileToken;
  }

  private clearErrorIndex(): void {
    if (this.errorIndices.size === 0) {
      return;
    }
    this.errorIndices = new Set<number>();
    this.flush();
  }

  private refreshGroupedOptions(): void {
    this.groupedWarriorOptions = this.buildGroupedOptions(this.warriors, this.isSimpleMode);
  }

  private isOrigWarriorName(name: string): boolean {
    return name.trim().toLowerCase().startsWith('orig:');
  }

  private formatSimpleName(rawName: string): string {
    let name = rawName.trim();
    if (name.toLowerCase().startsWith('orig:')) {
      name = name.slice(5);
    }
    name = name.replace(/\.red$/i, '');
    name = name.replace(/[_-]+/g, ' ').trim();
    if (!name) {
      return rawName;
    }
    return name
      .toLowerCase()
      .replace(/\b[a-z0-9]/g, (char) => char.toUpperCase());
  }

  private getOrigIndices(): number[] {
    const indices: number[] = [];
    this.warriors.forEach((warrior, index) => {
      if (this.isOrigWarriorName(warrior.name ?? '')) {
        indices.push(index);
      }
    });
    return indices;
  }

  private constrainSelectionsToOrig(): void {
    const origIndices = this.getOrigIndices();
    if (origIndices.length === 0) {
      this.selections = [];
      return;
    }
    const origSet = new Set(origIndices);
    const filtered = this.selections.filter((value) => origSet.has(value));
    if (filtered.length >= 2) {
      this.selections = filtered;
      return;
    }
    const targetCount = Math.max(2, filtered.length);
    this.selections = this.pickRandomFromIndices(targetCount, origIndices);
  }

  private pickRandomFromIndices(count: number, pool: number[]): number[] {
    if (pool.length === 0 || count <= 0) {
      return [];
    }
    const indices = [...pool];
    for (let i = indices.length - 1; i > 0; i -= 1) {
      const j = Math.floor(Math.random() * (i + 1));
      [indices[i], indices[j]] = [indices[j], indices[i]];
    }
    if (indices.length >= count) {
      return indices.slice(0, count);
    }
    const result = indices.slice();
    while (result.length < count) {
      result.push(pool[Math.floor(Math.random() * pool.length)]);
    }
    return result;
  }

  private selectSeedText(): void {
    const input = this.seedInputRef?.nativeElement;
    if (!input) {
      return;
    }
    requestAnimationFrame(() => {
      input.focus();
      input.select();
    });
  }

  private onSelectionsUpdated(): void {
    this.emitSeedChange();
    void this.prefetchSelectedWarriorCodes();
    this.flush();
  }

  private flush(): void {
    this.cdr.markForCheck();
  }
}
