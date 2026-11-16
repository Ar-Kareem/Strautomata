import { ChangeDetectionStrategy, ChangeDetectorRef, Component, DestroyRef, EventEmitter, HostListener, Input, OnChanges, Output, SimpleChanges, inject } from '@angular/core';

import { CorewarConsoleRunner } from '../../controllers/corewar-console-runner';
import { DEFAULT_COLUMNS, ScoreboardRow } from './corewar.constants';

@Component({
  selector: 'corewar-roster',
  standalone: true,
  templateUrl: './corewar-roster.component.html',
  styleUrl: './corewar-roster.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class CorewarRosterComponent implements OnChanges {
  private readonly runner = inject(CorewarConsoleRunner);
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly destroyRef = inject(DestroyRef);
  private destroyed = false;

  constructor() {
    this.destroyRef.onDestroy(() => {
      this.destroyed = true;
    });
  }

  @Input() matchId: number | null = null;
  @Input() rows: ScoreboardRow[] = [];
  @Input() activeWarriorCodes: string[] = [];
  @Input() gridCols: number | null = null;
  @Input() resetToken = 0;
  @Input() detailedScoreboard = false;

  @Output() selectionChange = new EventEmitter<{ warriorIndex: number | null; queue: number[] }>();
  @Output() error = new EventEmitter<string>();

  selectedWarriorId: number | null = null;
  selectedProcessQueue: number[] = [];
  selectedProcessQueueText = '';
  selectedUniqueCount = 0;
  selectedRowCount = 0;
  selectedColCount = 0;

  isPreviewOpen = false;
  previewName = '';
  previewCode = '';

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['matchId'] && !changes['matchId'].firstChange) {
      this.clearSelection();
    }
    if (changes['rows'] && this.rows.length === 0) {
      this.clearSelection();
    }
    if (changes['resetToken'] && !changes['resetToken'].firstChange) {
      this.clearSelection();
    }
    if (changes['gridCols'] && this.selectedProcessQueue.length > 0) {
      this.updateProcessStats();
    }
  }

  openPreview(index: number): void {
    const row = this.rows[index];
    if (!row) {
      return;
    }
    this.previewName = row.label;
    this.previewCode = this.activeWarriorCodes[index] ?? 'No source available.';
    this.isPreviewOpen = true;
    this.flush();
  }

  requestClosePreview(): void {
    this.isPreviewOpen = false;
    this.previewName = '';
    this.previewCode = '';
    this.flush();
  }

  @HostListener('document:keydown', ['$event'])
  handlePreviewKey(event: Event): void {
    if (!this.isPreviewOpen) {
      return;
    }
    const keyEvent = event as KeyboardEvent;
    const isSpace = keyEvent.key === ' ' || keyEvent.code === 'Space';
    if (keyEvent.key !== 'Escape' && keyEvent.key !== 'Enter' && !isSpace) {
      return;
    }
    keyEvent.preventDefault();
    keyEvent.stopPropagation();
    this.requestClosePreview();
  }

  async selectWarriorProcesses(index: number): Promise<void> {
    if (!this.matchId || this.destroyed) {
      return;
    }
    const row = this.rows[index];
    if (!row) {
      return;
    }
    if (this.selectedWarriorId === row.id) {
      this.clearSelection();
      return;
    }
    this.selectedWarriorId = row.id;
    this.selectedProcessQueue = [];
    this.selectedProcessQueueText = '';
    this.updateProcessStats();
    this.selectionChange.emit({ warriorIndex: index, queue: [] });
    this.flush();
    try {
      const result = await this.runner.getProcesses(this.matchId);
      const payload = result as { processes?: Array<{ id: number; queue?: number[] }>; error?: string };
      if (payload.error) {
        throw new Error(payload.error);
      }
      const selectedEntry = (payload.processes ?? []).find((entry) => entry.id === row.id);
      this.selectedProcessQueue = selectedEntry?.queue ?? [];
      this.selectedProcessQueueText = this.selectedProcessQueue.join(', ');
      this.updateProcessStats();
      this.selectionChange.emit({ warriorIndex: index, queue: this.selectedProcessQueue });
    } catch (error) {
      this.error.emit(error instanceof Error ? error.message : String(error));
      this.selectionChange.emit({ warriorIndex: index, queue: [] });
    } finally {
      this.flush();
    }
  }

  clearSelection(): void {
    this.selectedWarriorId = null;
    this.selectedProcessQueue = [];
    this.selectedProcessQueueText = '';
    this.selectedUniqueCount = 0;
    this.selectedRowCount = 0;
    this.selectedColCount = 0;
    this.selectionChange.emit({ warriorIndex: null, queue: [] });
    this.flush();
  }

  private updateProcessStats(): void {
    const queue = this.selectedProcessQueue;
    if (!queue || queue.length === 0) {
      this.selectedUniqueCount = 0;
      this.selectedRowCount = 0;
      this.selectedColCount = 0;
      return;
    }
    const cols = this.gridCols && this.gridCols > 0 ? this.gridCols : DEFAULT_COLUMNS;
    const unique = new Set<number>();
    const rows = new Set<number>();
    const colsSet = new Set<number>();
    for (const addr of queue) {
      if (!Number.isFinite(addr)) {
        continue;
      }
      unique.add(addr);
      const row = Math.floor(addr / cols);
      const col = addr % cols;
      if (row >= 0) {
        rows.add(row);
      }
      if (col >= 0) {
        colsSet.add(col);
      }
    }
    this.selectedUniqueCount = unique.size;
    this.selectedRowCount = rows.size;
    this.selectedColCount = colsSet.size;
  }

  formatMetric(value: number | null | undefined, digits = 3): string {
    if (value === null || value === undefined || Number.isNaN(value)) {
      return '-';
    }
    return value.toFixed(digits);
  }

  private flush(): void {
    this.cdr.markForCheck();
  }
}
