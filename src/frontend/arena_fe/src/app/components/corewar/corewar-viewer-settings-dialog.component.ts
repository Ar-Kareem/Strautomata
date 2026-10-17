import { ChangeDetectionStrategy, ChangeDetectorRef, Component, EventEmitter, Output, inject } from '@angular/core';
import { DialogModule } from 'primeng/dialog';
import { CorewarViewSettingsStore } from './corewar-view-settings.store';
import { CorewarViewSettings } from '@main/arena.store';

@Component({
  selector: 'corewar-viewer-settings-dialog',
  standalone: true,
  imports: [DialogModule],
  templateUrl: './corewar-viewer-settings-dialog.component.html',
  styleUrl: './corewar-viewer-settings-dialog.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CorewarViewerSettingsDialogComponent {
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly viewSettingsStore = inject(CorewarViewSettingsStore);

  @Output() settingsSaved = new EventEmitter<{ previous: CorewarViewSettings; next: CorewarViewSettings }>();

  readonly inspectorViewSizeMax = 35;

  get inspectorDialogOpen(): boolean {
    return this.viewSettingsStore.dialogOpen;
  }

  get inspectorViewSizeDraft(): number {
    return this.viewSettingsStore.draft.inspectorViewSize;
  }

  get detailedScoreboardDraft(): boolean {
    return this.viewSettingsStore.draft.detailedScoreboard;
  }

  get showIconsDraft(): boolean {
    return this.viewSettingsStore.draft.showIcons;
  }

  get showLastModifiedColorDraft(): boolean {
    return this.viewSettingsStore.draft.showLastModifiedColor;
  }

  get maxColumnsDraft(): number {
    return this.viewSettingsStore.draft.maxColumns;
  }

  get cellSizeSettingDraft(): number {
    return this.viewSettingsStore.draft.cellSize;
  }

  get makeNonDatWhiteDraft(): boolean {
    return this.viewSettingsStore.draft.makeNonDatWhite;
  }

  get makeWarriorDatWhiteDraft(): boolean {
    return this.viewSettingsStore.draft.makeWarriorDatWhite;
  }

  openInspectorDialog(): void {
    this.viewSettingsStore.openDialog();
    this.flush();
  }

  closeInspectorDialog(event?: Event): void {
    if (!this.inspectorDialogOpen) {
      return;
    }
    event?.preventDefault();
    event?.stopPropagation();
    this.viewSettingsStore.closeDialog();
    this.flush();
  }

  setInspectorViewSizeDraft(value: number): void {
    this.viewSettingsStore.setInspectorViewSizeDraft(value);
    this.flush();
  }

  onMaxColumnsInput(event: Event): void {
    const input = this.inputTarget(event);
    if (input) this.setMaxColumnsDraft(input.value);
  }

  onCellSizeInput(event: Event): void {
    const input = this.inputTarget(event);
    if (input) this.setCellSizeDraft(input.value);
  }

  onShowIconsChange(event: Event): void {
    const input = this.inputTarget(event);
    if (input) this.setShowIconsDraft(input.checked);
  }

  onMakeNonDatWhiteChange(event: Event): void {
    const input = this.inputTarget(event);
    if (input) this.setMakeNonDatWhiteDraft(input.checked);
  }

  onShowLastModifiedColorChange(event: Event): void {
    const input = this.inputTarget(event);
    if (input) this.setShowLastModifiedColorDraft(input.checked);
  }

  onMakeWarriorDatWhiteChange(event: Event): void {
    const input = this.inputTarget(event);
    if (input) this.setMakeWarriorDatWhiteDraft(input.checked);
  }

  onDetailedScoreboardChange(event: Event): void {
    const input = this.inputTarget(event);
    if (input) this.setDetailedScoreboardDraft(input.checked);
  }

  setDetailedScoreboardDraft(value: boolean): void {
    this.viewSettingsStore.setDetailedScoreboardDraft(value);
    this.flush();
  }

  setMaxColumnsDraft(value: number | string): void {
    this.viewSettingsStore.setMaxColumnsDraft(value);
    this.flush();
  }

  setCellSizeDraft(value: number | string): void {
    this.viewSettingsStore.setCellSizeDraft(value);
    this.flush();
  }

  setShowIconsDraft(value: boolean): void {
    this.viewSettingsStore.setShowIconsDraft(value);
    this.flush();
  }

  setShowLastModifiedColorDraft(value: boolean): void {
    this.viewSettingsStore.setShowLastModifiedColorDraft(value);
    this.flush();
  }

  setMakeNonDatWhiteDraft(value: boolean): void {
    this.viewSettingsStore.setMakeNonDatWhiteDraft(value);
    this.flush();
  }

  setMakeWarriorDatWhiteDraft(value: boolean): void {
    this.viewSettingsStore.setMakeWarriorDatWhiteDraft(value);
    this.flush();
  }

  resetInspectorDialog(): void {
    this.viewSettingsStore.resetDraft();
    this.flush();
  }

  saveInspectorDialog(event?: Event): void {
    if (!this.inspectorDialogOpen) {
      return;
    }
    event?.preventDefault();
    const payload = this.viewSettingsStore.saveDraft();
    this.settingsSaved.emit(payload);
    this.flush();
  }

  private inputTarget(event: Event): HTMLInputElement | null {
    return event.target instanceof HTMLInputElement ? event.target : null;
  }

  private flush(): void {
    this.cdr.markForCheck();
  }
}
