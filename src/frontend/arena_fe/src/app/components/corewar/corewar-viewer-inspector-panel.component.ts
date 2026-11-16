import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  HostListener,
  Input,
  OnChanges,
  OnInit,
  SimpleChanges,
  inject,
} from '@angular/core';
import { TooltipModule } from 'primeng/tooltip';
import { ScrollerModule } from 'primeng/scroller';
import { CorewarHoverRange, CorewarInspectorRow } from './corewar-inspector-interaction.store';
import {
  INSPECTOR_TEXT_DARK,
  INSPECTOR_TEXT_LIGHT,
  OUTLINE_DIM,
  OWNER_COLORS,
  buildInstructionTooltip,
} from './corewar.constants';

type ProcessHoverMeta = {
  count: number;
  color: string | null;
  tooltip: string;
};

@Component({
  selector: 'corewar-viewer-inspector-panel',
  standalone: true,
  imports: [TooltipModule, ScrollerModule],
  templateUrl: './corewar-viewer-inspector-panel.component.html',
  styleUrl: './corewar-viewer-inspector-panel.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CorewarViewerInspectorPanelComponent implements OnInit, OnChanges {
  private readonly cdr = inject(ChangeDetectorRef);

  @Input() hoverRange: CorewarHoverRange | null = null;
  @Input() instructions: string[] = [];
  @Input() addresses: number[] = [];
  @Input() owners: number[] = [];
  @Input() showLastModifiedColor = false;
  @Input() processMetaForAddress: ((address: number) => ProcessHoverMeta | undefined) | null = null;
  @Input() hoverListVersion = 0;
  @Input() lockedIndex: number | null = null;
  @Input() lockedRange: { start: number; end: number } | null = null;

  readonly inspectorRowHeight = 36;
  hoverList: CorewarInspectorRow[] = [];
  mobileInspectorTooltipEnabled = false;
  mobileInspectorTooltipLines: string[] = [];

  ngOnInit(): void {
    this.updateMobileInspectorTooltipMode();
    this.rebuildHoverList();
  }

  ngOnChanges(_changes: SimpleChanges): void {
    this.rebuildHoverList();
  }

  @HostListener('window:resize')
  onWindowResize(): void {
    this.updateMobileInspectorTooltipMode();
  }

  onInspectorRowTap(event: Event, description: string): void {
    if (!this.mobileInspectorTooltipEnabled) {
      return;
    }
    event.stopPropagation?.();
    event.preventDefault?.();
    this.mobileInspectorTooltipLines = this.tooltipHtmlToLines(description);
    this.flush();
  }

  closeMobileInspectorTooltip(): void {
    if (this.mobileInspectorTooltipLines.length === 0) {
      return;
    }
    this.mobileInspectorTooltipLines = [];
    this.flush();
  }

  private updateMobileInspectorTooltipMode(): void {
    if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') {
      return;
    }
    const enabled =
      window.matchMedia('(max-width: 1100px)').matches
      || window.matchMedia('(hover: none), (pointer: coarse)').matches;
    if (this.mobileInspectorTooltipEnabled === enabled) {
      return;
    }
    this.mobileInspectorTooltipEnabled = enabled;
    if (!enabled) {
      this.mobileInspectorTooltipLines = [];
    }
    this.flush();
  }

  private tooltipHtmlToLines(tooltipHtml: string): string[] {
    if (!tooltipHtml) {
      return [];
    }
    if (typeof document === 'undefined') {
      return tooltipHtml
        .replace(/<\/div>\s*<div[^>]*>/g, '\n')
        .replace(/<[^>]*>/g, '')
        .split('\n')
        .map((line) => line.replace(/\s+$/g, ''))
        .filter((line) => line.length > 0);
    }
    const container = document.createElement('div');
    container.innerHTML = tooltipHtml;
    const lines = Array.from(container.querySelectorAll('.corewar-opcode-tooltip-line'))
      .map((line) => (line.textContent ?? '').replace(/\s+$/g, ''))
      .filter((line) => line.length > 0);
    if (lines.length > 0) {
      return lines;
    }
    const text = (container.textContent ?? '').trim();
    return text ? [text] : [];
  }

  private rebuildHoverList(): void {
    const range = this.hoverRange;
    const size = this.instructions.length;
    if (!range || size <= 0 || range.length <= 0) {
      this.hoverList = [];
      this.flush();
      return;
    }
    const windowSize = Math.max(1, Math.min(range.length, size));
    const indices: number[] = [];
    const rawInstructions: string[] = [];
    for (let offset = 0; offset < windowSize; offset += 1) {
      const idx = (range.start + offset + size) % size;
      indices.push(idx);
      rawInstructions.push(this.instructions[idx] ?? '');
    }
    let formattedInstructions = rawInstructions;
    try {
      formattedInstructions = this.formatCoreSlice(rawInstructions, 0, windowSize);
    } catch {
      formattedInstructions = rawInstructions;
    }
    const items: CorewarInspectorRow[] = [];
    for (let offset = 0; offset < windowSize; offset += 1) {
      const idx = indices[offset];
      const instruction = formattedInstructions[offset] ?? rawInstructions[offset] ?? '';
      const opcode = (rawInstructions[offset] ?? '').slice(0, 3).toUpperCase();
      const address = this.addresses[idx] ?? idx;
      const owner = this.owners[idx] ?? -1;
      const processMeta = this.processMetaForAddress?.(address);
      const processCount = processMeta?.count ?? 0;
      const isProcess = processCount > 0;
      const processColor = processMeta?.color ?? null;
      const showOwnerColor = owner >= 0 && this.showLastModifiedColor;
      const showProcessColor = !this.showLastModifiedColor && isProcess && !!processColor;
      const color = showOwnerColor
        ? OWNER_COLORS[owner % OWNER_COLORS.length]
        : showProcessColor
          ? processColor
          : OUTLINE_DIM;
      const textColor = showOwnerColor || showProcessColor ? INSPECTOR_TEXT_DARK : INSPECTOR_TEXT_LIGHT;
      items.push({
        address,
        addressLabel: String(address).padStart(4, '0'),
        instruction,
        isSelected: range.selectedIndex !== null && idx === range.selectedIndex,
        isLockedCenter: range.lockMarkerIndex !== null && idx === range.lockMarkerIndex,
        isDat: opcode === 'DAT',
        opcodeDescription: buildInstructionTooltip(rawInstructions[offset] ?? ''),
        color,
        textColor,
        isProcess,
        processCount,
        processColor,
        processTooltip: isProcess ? (processMeta?.tooltip ?? null) : null
      });
    }
    this.hoverList = items;
    this.flush();
  }

  private formatCoreSlice(cells: string[], start: number, end: number): string[] {
    const slice = cells.slice(start, end);
    if (slice.length === 0) {
      return [];
    }
    const parts = slice.map((cell) => cell.trim().split(/\s+/).filter(Boolean));
    const maxLen = Math.max(...parts.map((chunk) => chunk.length));
    const widths = new Array<number>(maxLen).fill(0);
    for (const chunk of parts) {
      for (let i = 0; i < chunk.length; i += 1) {
        widths[i] = Math.max(widths[i], chunk[i]?.length ?? 0);
      }
    }
    return parts.map((chunk) =>
      chunk
        .map((token, index) => token.padEnd(widths[index] ?? token.length, ' '))
        .join(' ')
        .replace(/\s+$/g, '')
    );
  }

  private flush(): void {
    this.cdr.markForCheck();
  }
}
