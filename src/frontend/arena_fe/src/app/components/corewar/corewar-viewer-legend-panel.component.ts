import {
  AfterViewInit,
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  ElementRef,
  Input,
  OnChanges,
  SimpleChanges,
  ViewChild,
  inject,
} from '@angular/core';
import { GLYPH_COLOR, LEGEND_PANEL_BG, LEGEND_TEXT_COLOR, OPCODE_DESCRIPTIONS } from './corewar.constants';

type AddressingLegendEntry = { symbol: string; label: string };
type CorewarLegendEntry = { key: string; x: number; y: number; width: number; height: number };

const OPCODE_LEGEND_ORDER = [
  'DAT', 'MOV', 'ADD', 'SUB', 'MUL', 'DIV', 'MOD', 'JMP', 'JMZ',
  'JMN', 'DJN', 'SPL', 'SLT', 'CMP', 'SEQ', 'SNE', 'NOP',
];

const ADDRESSING_LEGEND: AddressingLegendEntry[] = [
  { symbol: '#', label: 'immediate' },
  { symbol: '$', label: 'direct (the $ may be omitted)' },
  { symbol: '*', label: 'A-field indirect' },
  { symbol: '@', label: 'B-field indirect' },
  { symbol: '{', label: 'A-field indirect with predecrement' },
  { symbol: '<', label: 'B-field indirect with predecrement' },
  { symbol: '}', label: 'A-field indirect with postincrement' },
  { symbol: '>', label: 'B-field indirect with postincrement' },
];

const MODIFIER_LEGEND = ['.A', '.B', '.AB', '.BA', '.F', '.X', '.I'];

@Component({
  selector: 'corewar-viewer-legend-panel',
  standalone: true,
  templateUrl: './corewar-viewer-legend-panel.component.html',
  styleUrl: './corewar-viewer-legend-panel.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CorewarViewerLegendPanelComponent implements AfterViewInit, OnChanges {
  private readonly cdr = inject(ChangeDetectorRef);

  @Input() boardCanvas: HTMLCanvasElement | null = null;
  @Input() canvasShell: HTMLDivElement | null = null;
  @Input() cellSize = 14;
  @Input() showIcons = false;
  @Input() drawOpcodePixels: ((
    ctx: CanvasRenderingContext2D,
    opcode: string,
    x: number,
    y: number,
    size: number,
    color: string
  ) => void) | null = null;

  @ViewChild('legendCanvas', { static: true }) legendCanvasRef!: ElementRef<HTMLCanvasElement>;

  legendTooltip: { text: string; x: number; y: number } | null = null;
  private legendCtx: CanvasRenderingContext2D | null = null;
  private legendEntries: CorewarLegendEntry[] = [];

  ngAfterViewInit(): void {
    this.legendCtx = this.legendCanvasRef.nativeElement.getContext('2d');
    this.redraw();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['showIcons'] && !this.showIcons) {
      this.legendTooltip = null;
    }
    this.redraw();
  }

  redraw(): void {
    if (!this.legendCtx || !this.drawOpcodePixels) {
      return;
    }
    const result = drawCorewarLegend({
      legendCtx: this.legendCtx,
      legendCanvas: this.legendCanvasRef?.nativeElement ?? null,
      canvasShell: this.canvasShell,
      boardCanvas: this.boardCanvas,
      cellSize: this.cellSize,
      showIcons: this.showIcons,
      drawOpcodePixels: this.drawOpcodePixels
    });
    this.legendEntries = result.entries;
    if (result.cleared) {
      this.legendTooltip = null;
    }
    this.flush();
  }

  onLegendMove(event: MouseEvent): void {
    if (!this.showIcons || !this.legendEntries.length) {
      if (this.legendTooltip) {
        this.legendTooltip = null;
        this.flush();
      }
      return;
    }
    const shell = this.canvasShell;
    if (!shell) {
      return;
    }
    const canvas = this.legendCanvasRef.nativeElement;
    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    const entry = this.legendEntries.find(
      (item) => x >= item.x && x <= item.x + item.width && y >= item.y && y <= item.y + item.height
    );
    if (!entry) {
      if (this.legendTooltip) {
        this.legendTooltip = null;
        this.flush();
      }
      return;
    }
    const description = OPCODE_DESCRIPTIONS[entry.key] ?? '';
    if (!description) {
      return;
    }
    const shellRect = shell.getBoundingClientRect();
    const localX = rect.left - shellRect.left + x;
    const localY = rect.top - shellRect.top + y;
    const tooltipWidth = 240;
    const tooltipHeight = 42;
    const offset = 12;
    let tooltipX = localX + offset;
    let tooltipY = localY - tooltipHeight - offset;
    if (tooltipX + tooltipWidth > shellRect.width - 6) {
      tooltipX = shellRect.width - tooltipWidth - 6;
    }
    if (tooltipX < 6) {
      tooltipX = 6;
    }
    if (tooltipY < 6) {
      tooltipY = localY + offset;
    }
    if (tooltipY + tooltipHeight > shellRect.height - 6) {
      tooltipY = shellRect.height - tooltipHeight - 6;
    }
    this.legendTooltip = { text: description, x: tooltipX, y: tooltipY };
    this.flush();
  }

  onLegendLeave(): void {
    if (!this.showIcons) {
      return;
    }
    if (this.legendTooltip) {
      this.legendTooltip = null;
      this.flush();
    }
  }

  private flush(): void {
    this.cdr.markForCheck();
  }
}

function drawCorewarLegend(args: {
  legendCtx: CanvasRenderingContext2D | null;
  legendCanvas: HTMLCanvasElement | null;
  canvasShell: HTMLDivElement | null;
  boardCanvas: HTMLCanvasElement | null;
  cellSize: number;
  showIcons: boolean;
  drawOpcodePixels: (
    ctx: CanvasRenderingContext2D,
    opcode: string,
    x: number,
    y: number,
    size: number,
    color: string
  ) => void;
}): { entries: CorewarLegendEntry[]; cleared: boolean } {
  const {
    legendCtx,
    legendCanvas,
    canvasShell,
    boardCanvas,
    cellSize,
    showIcons,
    drawOpcodePixels
  } = args;
  if (!legendCtx || !legendCanvas) {
    return { entries: [], cleared: false };
  }
  if (!showIcons) {
    legendCanvas.width = 0;
    legendCanvas.height = 0;
    legendCanvas.style.width = '0px';
    legendCanvas.style.height = '0px';
    return { entries: [], cleared: true };
  }

  let shellWidth = canvasShell?.clientWidth ?? 0;
  if (canvasShell) {
    const styles = window.getComputedStyle(canvasShell);
    const padX = parseFloat(styles.paddingLeft || '0') + parseFloat(styles.paddingRight || '0');
    shellWidth = Math.max(0, shellWidth - padX);
  }
  const boardWidth = boardCanvas?.getBoundingClientRect().width ?? 0;
  const legendWidth = boardWidth > 0 ? boardWidth : shellWidth;
  if (legendWidth <= 0) {
    return { entries: [], cleared: false };
  }

  const ctx = legendCtx;
  const ratio = window.devicePixelRatio || 1;
  const baseGlyph = Math.max(16, Math.round(cellSize * 1.9));
  const baseFont = Math.max(14, Math.round(cellSize * 1.25));
  let glyphSize = baseGlyph;
  let fontSize = baseFont;
  let gap = 22;
  let glyphGap = 8;
  const fontFamily = 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace';

  const measureOpcodeRow = (ops: string[]) => {
    let total = 0;
    ops.forEach((op, index) => {
      total += glyphSize + glyphGap + ctx.measureText(op).width;
      if (index < ops.length - 1) {
        total += gap;
      }
    });
    return total;
  };

  const measureSymbolRow = () => {
    let total = 0;
    const pad = Math.max(6, Math.round(fontSize * 0.4));
    const modesWidth = ctx.measureText('MODES:').width;
    total += modesWidth + gap;
    ADDRESSING_LEGEND.forEach((entry, index) => {
      const boxWidth = ctx.measureText(entry.symbol).width + pad * 2;
      total += boxWidth;
      if (index < ADDRESSING_LEGEND.length - 1) {
        total += gap;
      }
    });
    return total;
  };

  const measureModifierRow = () => {
    let total = 0;
    const pad = Math.max(6, Math.round(fontSize * 0.4));
    const modsWidth = ctx.measureText('MODS:').width;
    total += modsWidth + gap;
    MODIFIER_LEGEND.forEach((modifier, index) => {
      const boxWidth = ctx.measureText(modifier).width + pad * 2;
      total += boxWidth;
      if (index < MODIFIER_LEGEND.length - 1) {
        total += gap;
      }
    });
    return total;
  };

  const measureLayout = () => {
    ctx.font = `600 ${fontSize}px ${fontFamily}`;
    const firstRow = OPCODE_LEGEND_ORDER.slice(0, 9);
    const secondRow = OPCODE_LEGEND_ORDER.slice(9);
    const row1 = measureOpcodeRow(firstRow);
    const row2 = measureOpcodeRow(secondRow);
    const row3 = measureModifierRow();
    const row4 = measureSymbolRow();
    return Math.max(row1, row2, row3, row4);
  };

  let totalWidth = measureLayout();
  if (totalWidth > legendWidth) {
    const scale = legendWidth / totalWidth;
    glyphSize = Math.max(6, Math.floor(baseGlyph * scale));
    fontSize = Math.max(7, Math.floor(baseFont * scale));
    gap = Math.max(8, Math.round(18 * scale));
    glyphGap = Math.max(3, Math.round(6 * scale));
    totalWidth = measureLayout();
    if (totalWidth > legendWidth) {
      const squeeze = legendWidth / totalWidth;
      gap = Math.max(6, Math.floor(gap * squeeze));
      glyphGap = Math.max(3, Math.floor(glyphGap * squeeze));
      totalWidth = measureLayout();
    }
  }

  const rowHeight = Math.max(24, glyphSize + 12);
  const rowGap = 6;
  const height = rowHeight * 4 + rowGap * 3;
  legendCanvas.width = Math.floor(legendWidth * ratio);
  legendCanvas.height = Math.floor(height * ratio);
  legendCanvas.style.width = `${legendWidth}px`;
  legendCanvas.style.height = `${height}px`;
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  const borderInset = 8;
  const contentWidth = Math.max(1, legendWidth - borderInset * 2);
  ctx.clearRect(0, 0, legendWidth, height);
  ctx.fillStyle = LEGEND_PANEL_BG;
  ctx.fillRect(borderInset, 0, contentWidth, height);
  ctx.font = `600 ${fontSize}px ${fontFamily}`;
  ctx.fillStyle = LEGEND_TEXT_COLOR;
  ctx.textBaseline = 'middle';

  const firstRow = OPCODE_LEGEND_ORDER.slice(0, 9);
  const secondRow = OPCODE_LEGEND_ORDER.slice(9);
  const entries: CorewarLegendEntry[] = [];

  const drawRow = (ops: string[], baseY: number) => {
    let x = borderInset;
    const y = baseY + Math.round((rowHeight - glyphSize) / 2);
    const textY = baseY + rowHeight / 2;
    for (const op of ops) {
      const textWidth = ctx.measureText(op).width;
      const entryWidth = glyphSize + glyphGap + textWidth;
      drawOpcodePixels(ctx, op, x, y, glyphSize, GLYPH_COLOR);
      const textX = x + glyphSize + glyphGap;
      ctx.fillText(op, textX, textY);
      entries.push({ key: op, x, y: baseY, width: entryWidth, height: rowHeight });
      x += entryWidth + gap;
    }
  };

  drawRow(firstRow, 0);
  drawRow(secondRow, rowHeight + rowGap);

  const modifierRowY = (rowHeight + rowGap) * 2;
  let x = borderInset;
  const modifierTextY = modifierRowY + rowHeight / 2;
  const pad = Math.max(6, Math.round(fontSize * 0.4));
  const modsLabel = 'MODS:';
  const modsLabelWidth = ctx.measureText(modsLabel).width;
  ctx.fillText(modsLabel, x, modifierTextY);
  entries.push({ key: 'mods', x, y: modifierRowY, width: modsLabelWidth, height: rowHeight });
  x += modsLabelWidth + gap;
  for (const modifier of MODIFIER_LEGEND) {
    const textWidth = ctx.measureText(modifier).width;
    const boxWidth = textWidth + pad * 2;
    ctx.fillText(modifier, x + pad, modifierTextY);
    entries.push({ key: modifier, x, y: modifierRowY, width: boxWidth, height: rowHeight });
    x += boxWidth + gap;
  }

  const symbolRowY = (rowHeight + rowGap) * 3;
  x = borderInset;
  const symbolTextY = symbolRowY + rowHeight / 2;
  const modesLabel = 'MODES:';
  const modesLabelWidth = ctx.measureText(modesLabel).width;
  ctx.fillText(modesLabel, x, symbolTextY);
  entries.push({ key: 'modes', x, y: symbolRowY, width: modesLabelWidth, height: rowHeight });
  x += modesLabelWidth + gap;
  for (const entry of ADDRESSING_LEGEND) {
    const textWidth = ctx.measureText(entry.symbol).width;
    const boxWidth = textWidth + pad * 2;
    ctx.fillText(entry.symbol, x + pad, symbolTextY);
    entries.push({ key: entry.symbol, x, y: symbolRowY, width: boxWidth, height: rowHeight });
    x += boxWidth + gap;
  }

  return { entries, cleared: false };
}
