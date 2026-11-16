import { Injectable, inject } from '@angular/core';
import { Store } from '@ngrx/store';
import { arenaActions, ArenaState, CorewarViewSettings } from '@main/arena.store';

const STORAGE_KEY = 'CoreWarViewSettings';
const ONE_DAY_MS = 24 * 60 * 60 * 1000;
const MAX_VIEW_SIZE = 35;

@Injectable()
export class CorewarViewSettingsStore {
  private readonly store = inject(Store<{ arena: ArenaState }>);
  readonly settings = this.store.selectSignal((root: { arena: ArenaState }) => root.arena.corewar.viewSettings);

  dialogOpen = false;
  draft: CorewarViewSettings = this.settings();
  private didLoadFromStorage = false;

  ensureLoadedFromStorage(): void {
    if (this.didLoadFromStorage) {
      return;
    }
    this.didLoadFromStorage = true;
    const parsed = this.readStorage();
    if (!parsed) {
      this.syncDraftToSettings();
      return;
    }
    const next = this.normalize({
      inspectorViewSize: parsed.inspectorViewSize,
      detailedScoreboard: parsed.detailedScoreboard,
      showIcons: parsed.showIcons,
      showLastModifiedColor: parsed.showLastModifiedColor,
      maxColumns: parsed.maxColumns,
      cellSize: parsed.cellSize,
      makeNonDatWhite: parsed.makeNonDatWhite,
      makeWarriorDatWhite: parsed.makeWarriorDatWhite
    });
    this.store.dispatch(arenaActions.updateCorewarViewSettings({ patch: next }));
    this.writeStorage(next);
    this.syncDraftToSettings(next);
  }

  openDialog(): void {
    this.syncDraftToSettings();
    this.dialogOpen = true;
  }

  closeDialog(): void {
    this.dialogOpen = false;
  }

  setInspectorViewSizeDraft(value: number): void {
    this.draft = { ...this.draft, inspectorViewSize: this.normalizeInspectorViewSize(value) };
  }

  setDetailedScoreboardDraft(value: boolean): void {
    this.draft = { ...this.draft, detailedScoreboard: value };
  }

  setMaxColumnsDraft(value: number | string): void {
    const parsed = Number.parseInt(String(value), 10);
    if (!Number.isFinite(parsed)) {
      return;
    }
    this.draft = { ...this.draft, maxColumns: parsed };
  }

  setCellSizeDraft(value: number | string): void {
    const parsed = Number.parseInt(String(value), 10);
    if (!Number.isFinite(parsed)) {
      return;
    }
    this.draft = { ...this.draft, cellSize: parsed };
  }

  setShowIconsDraft(value: boolean): void {
    this.draft = {
      ...this.draft,
      showIcons: value,
      makeNonDatWhite: value ? false : this.draft.makeNonDatWhite
    };
  }

  setShowLastModifiedColorDraft(value: boolean): void {
    this.draft = {
      ...this.draft,
      showLastModifiedColor: value,
      makeWarriorDatWhite: value ? false : this.draft.makeWarriorDatWhite
    };
  }

  setMakeNonDatWhiteDraft(value: boolean): void {
    this.draft = {
      ...this.draft,
      makeNonDatWhite: this.draft.showIcons ? false : value
    };
  }

  setMakeWarriorDatWhiteDraft(value: boolean): void {
    this.draft = {
      ...this.draft,
      makeWarriorDatWhite: this.draft.showLastModifiedColor ? false : value
    };
  }

  resetDraft(): void {
    this.draft = {
      inspectorViewSize: 1,
      detailedScoreboard: false,
      showIcons: false,
      showLastModifiedColor: false,
      maxColumns: 100,
      cellSize: 12,
      makeNonDatWhite: true,
      makeWarriorDatWhite: true
    };
  }

  saveDraft(): { previous: CorewarViewSettings; next: CorewarViewSettings } {
    const previous = this.settings();
    const next = this.normalize(this.draft);
    this.store.dispatch(arenaActions.updateCorewarViewSettings({ patch: next }));
    this.writeStorage(next);
    this.dialogOpen = false;
    this.syncDraftToSettings(next);
    return { previous, next };
  }

  private syncDraftToSettings(next?: CorewarViewSettings): void {
    const settings = next ?? this.settings();
    this.draft = { ...settings };
  }

  private normalize(value: CorewarViewSettings): CorewarViewSettings {
    const showIcons = Boolean(value.showIcons);
    const showLastModifiedColor = Boolean(value.showLastModifiedColor);
    return {
      inspectorViewSize: this.normalizeInspectorViewSize(value.inspectorViewSize),
      detailedScoreboard: Boolean(value.detailedScoreboard),
      showIcons,
      showLastModifiedColor,
      maxColumns: this.normalizeMaxColumns(value.maxColumns),
      cellSize: this.normalizeCellSize(value.cellSize),
      makeNonDatWhite: showIcons ? false : Boolean(value.makeNonDatWhite),
      makeWarriorDatWhite: showLastModifiedColor ? false : Boolean(value.makeWarriorDatWhite)
    };
  }

  private normalizeInspectorViewSize(value: number): number {
    const numeric = Number.isFinite(value) ? Math.floor(value) : 1;
    return Math.max(1, Math.min(MAX_VIEW_SIZE, numeric));
  }

  private normalizeMaxColumns(value: number): number {
    const numeric = Number.isFinite(value) ? Math.floor(value) : 100;
    return Math.max(10, Math.min(10000, numeric));
  }

  private normalizeCellSize(value: number): number {
    const numeric = Number.isFinite(value) ? Math.floor(value) : 12;
    return Math.max(7, Math.min(48, numeric));
  }

  private readStorage(): CorewarViewSettings | null {
    try {
      const raw = window.sessionStorage?.getItem(STORAGE_KEY);
      if (!raw) {
        return null;
      }
      const parsed = JSON.parse(raw) as Partial<CorewarViewSettings> & { ts?: number; viewSize?: number };
      const timestamp = typeof parsed.ts === 'number' ? parsed.ts : null;
      const now = Date.now();
      if (timestamp === null || !Number.isFinite(timestamp) || now - timestamp > ONE_DAY_MS) {
        return null;
      }
      return {
        inspectorViewSize: Number(parsed.inspectorViewSize ?? parsed.viewSize ?? 1),
        detailedScoreboard: Boolean(parsed.detailedScoreboard),
        showIcons: Boolean(parsed.showIcons),
        showLastModifiedColor: Boolean(parsed.showLastModifiedColor),
        maxColumns: Number(parsed.maxColumns ?? 100),
        cellSize: Number(parsed.cellSize ?? 12),
        makeNonDatWhite: parsed.makeNonDatWhite === undefined ? false : Boolean(parsed.makeNonDatWhite),
        makeWarriorDatWhite:
          parsed.makeWarriorDatWhite === undefined ? false : Boolean(parsed.makeWarriorDatWhite)
      };
    } catch {
      return null;
    }
  }

  private writeStorage(settings: CorewarViewSettings): void {
    try {
      const payload = {
        ...settings,
        ts: Date.now()
      };
      window.sessionStorage?.setItem(STORAGE_KEY, JSON.stringify(payload));
    } catch {
      // ignore storage failures
    }
  }
}
