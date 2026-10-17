import { AfterViewInit, ChangeDetectionStrategy, ChangeDetectorRef, Component, DestroyRef, ElementRef, Input, OnChanges, SimpleChanges, ViewChild, inject } from '@angular/core';
import { Store } from '@ngrx/store';
import {
  DEFAULT_COLUMNS,
  GLYPH_COLOR,
  GRID_BG,
  OWNER_COLORS,
  CorewarFrame,
  normalizeCellSize,
} from './corewar.constants';
import { CorewarViewSettingsStore } from './corewar-view-settings.store';
import { CorewarProcessOverlayStore } from './corewar-process-overlay.store';
import { CorewarHoverRange, CorewarInspectorInteractionStore } from './corewar-inspector-interaction.store';
import {
  drawCorewarOpcodePixels,
  getCorewarGlyphColor,
  getCorewarProcessHighlightSprite,
} from './corewar-viewer-glyphs';
import {
  drawCorewarBaseCell,
  drawCorewarBaseFull,
  drawCorewarHoverWindow,
  drawCorewarLastExecutedHighlights,
  drawCorewarProcessHighlights,
  drawCorewarProcessIndicators,
} from './corewar-viewer-render';
import { arenaActions, ArenaState, CorewarViewSettings } from '@main/arena.store';
import { CorewarViewerInspectorPanelComponent } from './corewar-viewer-inspector-panel.component';
import { CorewarViewerSettingsDialogComponent } from './corewar-viewer-settings-dialog.component';
import { CorewarViewerLegendPanelComponent } from './corewar-viewer-legend-panel.component';
import { CorewarViewerInputLayerComponent } from './corewar-viewer-input-layer.component';

type PendingFrame = { instructions: string[]; owners: number[]; addresses: number[] | null };
@Component({
  selector: 'corewar-viewer',
  standalone: true,
  imports: [
    CorewarViewerInspectorPanelComponent,
    CorewarViewerSettingsDialogComponent,
    CorewarViewerLegendPanelComponent,
    CorewarViewerInputLayerComponent
  ],
  providers: [CorewarViewSettingsStore, CorewarProcessOverlayStore, CorewarInspectorInteractionStore],
  templateUrl: './corewar-viewer.component.html',
  styleUrl: './corewar-viewer.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  inputs: ['lastExecutedByWarrior']
})
export class CorewarViewerComponent implements AfterViewInit, OnChanges {
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly destroyRef = inject(DestroyRef);
  private readonly store = inject(Store<{ arena: ArenaState }>);
  private readonly arenaState = this.store.selectSignal((root: { arena: ArenaState }) => root.arena);
  private readonly viewSettingsStore = inject(CorewarViewSettingsStore);
  private readonly processOverlayStore = inject(CorewarProcessOverlayStore);
  private readonly inspectorStore = inject(CorewarInspectorInteractionStore);

  @Input() coreSize: number | null = null;
  @Input() frame: CorewarFrame | null = null;
  @Input() lastExecutedByWarrior: Array<number | null> = [];
  @Input() selectedProcessQueue: number[] = [];
  @Input() selectedWarriorIndex: number | null = null;
  @Input() processQueues: Array<number[]> = [];

  @ViewChild(CorewarViewerInputLayerComponent) inputLayerRef?: CorewarViewerInputLayerComponent;
  @ViewChild('coreCanvasSlot', { static: true }) coreCanvasSlotRef!: ElementRef<HTMLDivElement>;
  @ViewChild('coreCanvasShell', { static: true }) coreCanvasShellRef!: ElementRef<HTMLDivElement>;
  @ViewChild('overlayCanvas', { static: true }) overlayCanvasRef!: ElementRef<HTMLCanvasElement>;
  @ViewChild('hoverCanvas', { static: true }) hoverCanvasRef!: ElementRef<HTMLCanvasElement>;
  @ViewChild(CorewarViewerLegendPanelComponent) legendPanelRef?: CorewarViewerLegendPanelComponent;

  get lockedIndex(): number | null {
    return this.inspectorStore.lockedIndex;
  }

  get lockedRange(): { start: number; end: number } | null {
    return this.inspectorStore.lockedRange;
  }

  get inspectorViewSize(): number {
    return this.viewSettingsStore.settings().inspectorViewSize;
  }

  get showIcons(): boolean {
    return this.viewSettingsStore.settings().showIcons;
  }

  get showLastModifiedColor(): boolean {
    return this.viewSettingsStore.settings().showLastModifiedColor;
  }

  get maxColumns(): number {
    return this.viewSettingsStore.settings().maxColumns;
  }

  get cellSizeSetting(): number {
    return this.viewSettingsStore.settings().cellSize;
  }

  get makeNonDatWhite(): boolean {
    return this.viewSettingsStore.settings().makeNonDatWhite;
  }

  get makeWarriorDatWhite(): boolean {
    return this.viewSettingsStore.settings().makeWarriorDatWhite;
  }

  readonly inspectorViewSizeMax = 35;
  readonly legendOpcodeDrawer = (
    ctx: CanvasRenderingContext2D,
    opcode: string,
    cellX: number,
    cellY: number,
    cellSize: number,
    color: string
  ) => this.drawOpcodePixels(ctx, opcode, cellX, cellY, cellSize, color);
  readonly processHoverMetaForAddress = (address: number) => this.processOverlayStore.getProcessHoverMeta(address);
  hoverRange: CorewarHoverRange | null = null;
  hoverListVersion = 0;
  private pendingFrame: PendingFrame | null = null;
  private drawScheduled = false;
  private drawing = false;
  canvasSize = 0;
  coreColumns = DEFAULT_COLUMNS;
  private ctx: CanvasRenderingContext2D | null = null;
  private overlayCtx: CanvasRenderingContext2D | null = null;
  private hoverCtx: CanvasRenderingContext2D | null = null;
  cellSize = 14;
  private pixelRatio = 1;
  currentInstructions: string[] = [];
  currentOwners: number[] = [];
  currentAddresses: number[] = [];
  private addressIndex = new Map<number, number>();
  private addressIdentity = false;
  private cellX: number[] = [];
  private cellY: number[] = [];
  private cellRow: number[] = [];
  private cellCol: number[] = [];
  private cellCoordCols = 0;
  private cellCoordSize = 0;
  private cellCoordPad = 0;
  private cellCoordCellSize = 0;

  private readonly resizeListener = () => {
    this.resizeCanvas();
  };

  constructor() {
    this.destroyRef.onDestroy(() => {
      window.removeEventListener('resize', this.resizeListener);
    });
  }

  ngAfterViewInit(): void {
    const canvas = this.inputLayerRef?.canvasElement;
    if (!canvas) {
      return;
    }
    this.ctx = canvas.getContext('2d');
    this.overlayCtx = this.overlayCanvasRef.nativeElement.getContext('2d');
    this.hoverCtx = this.hoverCanvasRef.nativeElement.getContext('2d');
    this.viewSettingsStore.ensureLoadedFromStorage();
    this.resizeCanvas();
    this.clearCanvas();
    this.redrawLegend();
    window.addEventListener('resize', this.resizeListener);
    if (this.frame?.instructions?.length) {
      this.queueFrame(this.frame);
    }
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['coreSize'] && this.coreSize) {
      this.ensureCanvas(this.coreSize);
      this.clearCanvas();
    }
    if (changes['frame'] && this.frame?.instructions?.length) {
      this.queueFrame(this.frame);
    }
    if (
      changes['selectedProcessQueue']
      || changes['selectedWarriorIndex']
      || changes['lastExecutedByWarrior']
      || changes['processQueues']
    ) {
      if (changes['selectedProcessQueue'] || changes['selectedWarriorIndex']) {
        this.processOverlayStore.markSelectedCacheDirty();
      }
      if (changes['processQueues']) {
        this.rebuildProcessHoverMap();
        if (this.inspectorStore.hoverIndex !== null) {
          this.updateHover(this.inspectorStore.hoverIndex, true);
        }
      }
      this.redrawOverlay();
    }
  }

  clear(): void {
    this.pendingFrame = null;
    this.drawScheduled = false;
    this.drawing = false;
    this.currentInstructions = [];
    this.currentOwners = [];
    this.currentAddresses = [];
    this.addressIndex.clear();
    this.hoverRange = null;
    this.hoverListVersion = 0;
    this.inspectorStore.clear();
    this.processOverlayStore.clearState();
    this.clearCanvas();
    this.flush();
  }

  forceFullRedraw(): void {
    this.redrawCurrentFrame(true);
  }

  onCanvasInteractionChanged(): void {
    this.rebuildHoverList();
    this.flush();
  }

  onSettingsSaved({ previous, next }: { previous: CorewarViewSettings; next: CorewarViewSettings }): void {
    if (next.inspectorViewSize !== previous.inspectorViewSize) {
      this.rebuildHoverList();
    }
    if (next.showIcons !== previous.showIcons) {
      this.processOverlayStore.markBackgroundDirty();
      this.redrawCurrentFrame(true);
      this.redrawLegend();
    }
    if (next.showLastModifiedColor !== previous.showLastModifiedColor) {
      this.processOverlayStore.markBackgroundDirty();
      this.rebuildHoverList();
      this.redrawCurrentFrame(true);
    }
    if (next.maxColumns !== previous.maxColumns || next.cellSize !== previous.cellSize) {
      this.resizeCanvas();
    }
    if (
      next.makeNonDatWhite !== previous.makeNonDatWhite
      || next.makeWarriorDatWhite !== previous.makeWarriorDatWhite
    ) {
      this.processOverlayStore.markBackgroundDirty();
      this.redrawCurrentFrame(true);
    }
    this.flush();
  }

  private queueFrame(frame: CorewarFrame): void {
    this.pendingFrame = {
      instructions: frame.instructions ?? [],
      owners: frame.owners ?? [],
      addresses: frame.addresses ?? null
    };
    this.scheduleDraw();
  }

  private scheduleDraw(): void {
    if (this.drawing || this.drawScheduled) {
      return;
    }
    this.drawScheduled = true;
    requestAnimationFrame(() => {
      this.drawScheduled = false;
      this.drawPendingFrame();
    });
  }

  private drawPendingFrame(): void {
    if (this.drawing) {
      return;
    }
    const frame = this.pendingFrame;
    if (!frame) {
      return;
    }
    this.pendingFrame = null;
    this.drawing = true;
    this.drawFrame(frame.instructions, frame.owners, frame.addresses ?? undefined);
    this.drawing = false;
    if (this.pendingFrame) {
      this.scheduleDraw();
    }
  }

  private redrawCurrentFrame(forceFull = false): void {
    if (!this.currentInstructions.length || !this.ctx) {
      return;
    }
    this.drawFrame(this.currentInstructions, this.currentOwners, this.currentAddresses, forceFull);
  }

  private drawFrame(
    instructions: string[],
    owners: number[],
    addresses?: number[],
    forceFull = false
  ): void {
    this.ensureCanvas(instructions.length);
    if (!this.ctx) {
      return;
    }
    const ctx = this.ctx;
    const cols = this.coreColumns;
    const size = instructions.length;
    const cellSize = this.cellSize;
    const axisPad = this.getAxisPadding();
    const originX = axisPad;
    const originY = axisPad;
    const normalizedOwners = this.normalizeOwners(owners, size);
    const prevInstructions = this.currentInstructions;
    const prevOwners = this.currentOwners;
    const prevSize = this.currentInstructions.length;
    const prevAddressIdentity = this.addressIdentity;
    let needsFull = forceFull || prevInstructions.length !== size || prevOwners.length !== size;
    let changedIndices: number[] = [];

    if (!needsFull) {
      for (let i = 0; i < size; i += 1) {
        if (prevInstructions[i] !== instructions[i] || prevOwners[i] !== normalizedOwners[i]) {
          changedIndices.push(i);
        }
      }
      if (changedIndices.length > size * 0.35) {
        needsFull = true;
        changedIndices = [];
      }
    }

    this.currentInstructions = instructions;
    this.currentOwners = normalizedOwners;
    if (addresses && addresses.length === size) {
      this.currentAddresses = addresses;
      this.addressIdentity = false;
    } else {
      this.currentAddresses = instructions.map((_, index) => index);
      this.addressIdentity = true;
    }
    this.addressIndex.clear();
    for (let i = 0; i < this.currentAddresses.length; i += 1) {
      this.addressIndex.set(this.currentAddresses[i], i);
    }
    if (prevSize !== size || prevAddressIdentity !== this.addressIdentity) {
      this.processOverlayStore.markSelectedCacheDirty();
    }
    this.ensureCellCoords(size);
    if (this.inspectorStore.hoverIndex !== null) {
      this.updateHover(this.inspectorStore.hoverIndex, true);
    }
    if (needsFull) {
      this.drawBaseFull(ctx, instructions, normalizedOwners, cols, cellSize, originX, originY);
    } else {
      for (const index of changedIndices) {
        this.drawBaseCell(ctx, index, instructions[index] ?? '', normalizedOwners[index] ?? -1, cols, cellSize, originX, originY);
      }
    }
    this.drawOverlay();
  }

  private redrawOverlay(): void {
    if (!this.overlayCtx || !this.currentInstructions.length) {
      return;
    }
    this.drawOverlay();
  }

  private drawOverlay(): void {
    if (!this.overlayCtx) {
      return;
    }
    const ctx = this.overlayCtx;
    const cols = this.coreColumns;
    const size = this.currentInstructions.length;
    const rows = Math.ceil(size / cols);
    const cellSize = this.cellSize;
    const axisPad = this.getAxisPadding();
    const originX = axisPad;
    const originY = axisPad;
    const width = cols * cellSize + axisPad;
    const height = rows * cellSize + axisPad;
    this.processOverlayStore.ensureSelectedProcessCache({
      size,
      rows,
      cols,
      selectedWarriorIndex: this.selectedWarriorIndex,
      selectedProcessQueue: this.selectedProcessQueue,
      addressIdentity: this.addressIdentity,
      addressIndex: this.addressIndex,
      cellRow: this.cellRow,
      cellCol: this.cellCol
    });
    this.processOverlayStore.ensureProcessBackground({
      processQueues: this.processQueues,
      size,
      cols,
      cellSize,
      originX,
      originY,
      width,
      height,
      addressIdentity: this.addressIdentity,
      addressIndex: this.addressIndex,
      currentInstructions: this.currentInstructions,
      currentOwners: this.currentOwners,
      ownerColors: OWNER_COLORS,
      showLastModifiedColor: this.showLastModifiedColor,
      cellX: this.cellX,
      cellY: this.cellY,
      drawOpcodePixels: (overlayCtx, opcode, x, y, sizePx, color) =>
        this.drawOpcodePixels(overlayCtx, opcode, x, y, sizePx, color),
      getGlyphColor: (opcode, owner) => this.getGlyphColor(opcode, owner)
    });
    ctx.clearRect(0, 0, width, height);
    const processBackgroundCanvas = this.processOverlayStore.getBackgroundCanvas();
    if (processBackgroundCanvas) {
      ctx.save();
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.drawImage(processBackgroundCanvas, 0, 0);
      ctx.restore();
    }
    this.drawLastExecutedHighlights(ctx, cols, cellSize, originX, originY);
    this.drawProcessHighlights(
      ctx,
      cols,
      cellSize,
      originX,
      originY,
      this.processOverlayStore.getSelectedProcessIndices()
    );
    this.drawProcessIndicators(ctx, cols, rows, cellSize, originX, originY);
    this.drawHoverWindow();
  }

  private drawBaseFull(
    ctx: CanvasRenderingContext2D,
    instructions: string[],
    owners: number[],
    cols: number,
    cellSize: number,
    originX: number,
    originY: number
  ): void {
    drawCorewarBaseFull({
      ctx,
      instructions,
      owners,
      cols,
      cellSize,
      originX,
      originY,
      axisPad: this.getAxisPadding(),
      showLastModifiedColor: this.showLastModifiedColor,
      drawOpcodePixels: (baseCtx, opcode, cellX, cellY, sizePx, color) =>
        this.drawOpcodePixels(baseCtx, opcode, cellX, cellY, sizePx, color),
      getGlyphColor: (opcode, owner) => this.getGlyphColor(opcode, owner)
    });
  }

  private drawBaseCell(
    ctx: CanvasRenderingContext2D,
    index: number,
    instruction: string,
    owner: number,
    cols: number,
    cellSize: number,
    originX: number,
    originY: number
  ): void {
    drawCorewarBaseCell({
      ctx,
      index,
      instruction,
      owner,
      cols,
      cellSize,
      originX,
      originY,
      showLastModifiedColor: this.showLastModifiedColor,
      drawOpcodePixels: (baseCtx, opcode, cellX, cellY, sizePx, color) =>
        this.drawOpcodePixels(baseCtx, opcode, cellX, cellY, sizePx, color),
      getGlyphColor: (opcode, opcodeOwner) => this.getGlyphColor(opcode, opcodeOwner)
    });
  }

  private ensureCellCoords(size: number): void {
    if (size <= 0) {
      this.cellX = [];
      this.cellY = [];
      this.cellRow = [];
      this.cellCol = [];
      this.cellCoordCols = 0;
      this.cellCoordSize = 0;
      this.cellCoordPad = 0;
      this.cellCoordCellSize = 0;
      return;
    }
    const cols = this.coreColumns;
    const axisPad = this.getAxisPadding();
    if (
      this.cellCoordSize === size
      && this.cellCoordCols === cols
      && this.cellCoordPad === axisPad
      && this.cellCoordCellSize === this.cellSize
      && this.cellCoordSize > 0
    ) {
      return;
    }
    this.cellCoordSize = size;
    this.cellCoordCols = cols;
    this.cellCoordPad = axisPad;
    this.cellCoordCellSize = this.cellSize;
    this.cellX = new Array<number>(size);
    this.cellY = new Array<number>(size);
    this.cellRow = new Array<number>(size);
    this.cellCol = new Array<number>(size);
    for (let i = 0; i < size; i += 1) {
      const row = Math.floor(i / cols);
      const col = i % cols;
      this.cellRow[i] = row;
      this.cellCol[i] = col;
      this.cellX[i] = axisPad + col * this.cellSize;
      this.cellY[i] = axisPad + row * this.cellSize;
    }
    this.processOverlayStore.markSelectedCacheDirty();
    this.processOverlayStore.markBackgroundDirty();
  }

  private drawLastExecutedHighlights(
    ctx: CanvasRenderingContext2D,
    cols: number,
    cellSize: number,
    offsetX: number,
    offsetY: number
  ): void {
    drawCorewarLastExecutedHighlights({
      ctx,
      cols,
      cellSize,
      offsetX,
      offsetY,
      lastExecutedByWarrior: this.lastExecutedByWarrior,
      addressIndex: this.addressIndex
    });
  }

  private drawHoverWindow(): void {
    if (!this.hoverCtx) {
      return;
    }
    const ctx = this.hoverCtx;
    const cols = this.coreColumns;
    const size = this.currentInstructions.length;
    const rows = Math.ceil(size / cols);
    const cellSize = this.cellSize;
    const axisPad = this.getAxisPadding();
    const originX = axisPad;
    const originY = axisPad;
    const width = cols * cellSize + axisPad;
    const height = rows * cellSize + axisPad;
    this.hoverListVersion += 1;
    this.setHoverRange(this.getHoverRange());
    drawCorewarHoverWindow({
      ctx,
      cols,
      size,
      cellSize,
      originX,
      originY,
      width,
      height,
      range: this.hoverRange
    });
  }

  private getGlyphColor(opcode: string, owner: number): string {
    return getCorewarGlyphColor({
      opcode,
      owner,
      showIcons: this.showIcons,
      showLastModifiedColor: this.showLastModifiedColor,
      makeNonDatWhite: this.makeNonDatWhite,
      makeWarriorDatWhite: this.makeWarriorDatWhite
    });
  }

  private drawOpcodePixels(
    ctx: CanvasRenderingContext2D,
    opcode: string,
    cellX: number,
    cellY: number,
    cellSize: number,
    color: string
  ): void {
    drawCorewarOpcodePixels({
      ctx,
      opcode,
      cellX,
      cellY,
      cellSize,
      color,
      showIcons: this.showIcons
    });
  }

  private drawProcessHighlights(
    ctx: CanvasRenderingContext2D,
    cols: number,
    cellSize: number,
    offsetX: number,
    offsetY: number,
    indices: number[]
  ): void {
    if (this.selectedWarriorIndex === null || indices.length === 0) {
      return;
    }
    const color = OWNER_COLORS[this.selectedWarriorIndex % OWNER_COLORS.length];
    const sprite = getCorewarProcessHighlightSprite(color, cellSize, (hex, alpha) =>
      this.colorToRgba(hex, alpha)
    );
    drawCorewarProcessHighlights({
      ctx,
      cols,
      cellSize,
      offsetX,
      offsetY,
      indices,
      cellX: this.cellX,
      cellY: this.cellY,
      sprite
    });
  }

  private drawProcessIndicators(
    ctx: CanvasRenderingContext2D,
    cols: number,
    rows: number,
    cellSize: number,
    offsetX: number,
    offsetY: number
  ): void {
    const selectedProcessIndices = this.processOverlayStore.getSelectedProcessIndices();
    if (this.selectedWarriorIndex === null || selectedProcessIndices.length === 0) {
      return;
    }
    const rowFlags = this.processOverlayStore.getSelectedRowFlags();
    const colFlags = this.processOverlayStore.getSelectedColFlags();
    if (rowFlags.length === 0 && colFlags.length === 0) {
      return;
    }
    const color = OWNER_COLORS[this.selectedWarriorIndex % OWNER_COLORS.length];
    drawCorewarProcessIndicators({
      ctx,
      cellSize,
      offsetX,
      offsetY,
      colorToRgba: (hex, alpha) => this.colorToRgba(hex, alpha),
      color,
      rowFlags,
      colFlags
    });
  }

  private colorToRgba(hex: string, alpha: number): string {
    return this.processOverlayStore.colorToRgba(hex, alpha);
  }

  private ensureCanvas(size: number | null): void {
    if (!size || size <= 0) {
      return;
    }
    if (this.canvasSize === size && this.ctx) {
      return;
    }
    this.canvasSize = size;
    this.resizeCanvas();
  }

  private resizeCanvas(): void {
    if (!this.ctx) {
      return;
    }
    const shell = this.coreCanvasShellRef?.nativeElement;
    const slot = this.coreCanvasSlotRef?.nativeElement;
    let shellWidth = slot?.clientWidth ?? shell?.clientWidth ?? 0;
    const framePad = 12;
    if (slot) {
      const styles = window.getComputedStyle(slot);
      const padX = parseFloat(styles.paddingLeft || '0') + parseFloat(styles.paddingRight || '0');
      shellWidth = Math.max(0, shellWidth - padX - framePad * 2);
    }
    if (shellWidth > 0) {
      const axisPad = this.getAxisPadding();
      this.cellSize = normalizeCellSize(this.cellSizeSetting);
      const usableWidth = Math.max(0, shellWidth - axisPad);
      const computed = Math.floor(usableWidth / this.cellSize);
      this.coreColumns = Math.max(1, Math.min(this.maxColumns, computed || 1));
    }
    let cols = this.coreColumns;
    let rows = Math.ceil((this.canvasSize || 1) / cols);
    if (rows > 400) {
      rows = 400;
      cols = Math.max(1, Math.ceil((this.canvasSize || 1) / rows));
    }
    const canvas = this.inputLayerRef?.canvasElement;
    if (!canvas) {
      return;
    }
    const overlayCanvas = this.overlayCanvasRef?.nativeElement;
    const hoverCanvas = this.hoverCanvasRef?.nativeElement;
    const ratio = window.devicePixelRatio || 1;
    this.pixelRatio = ratio;
    const axisPad = this.getAxisPadding();
    const widthPx = Math.max(1, cols * this.cellSize + axisPad);
    const heightPx = Math.max(1, rows * this.cellSize + axisPad);
    const safeWidth = Math.min(widthPx, 8000);
    const safeHeight = Math.min(heightPx, 8000);
    const safeWidthRatio = Math.min(widthPx * ratio, 8000);
    const safeHeightRatio = Math.min(heightPx * ratio, 8000);
    canvas.width = Math.floor(safeWidthRatio);
    canvas.height = Math.floor(safeHeightRatio);
    canvas.style.width = `${safeWidth}px`;
    canvas.style.height = `${safeHeight}px`;
    this.ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    this.ctx.imageSmoothingEnabled = false;
    if (overlayCanvas && this.overlayCtx) {
      overlayCanvas.width = Math.floor(safeWidthRatio);
      overlayCanvas.height = Math.floor(safeHeightRatio);
      overlayCanvas.style.width = `${safeWidth}px`;
      overlayCanvas.style.height = `${safeHeight}px`;
      this.overlayCtx.setTransform(ratio, 0, 0, ratio, 0, 0);
      this.overlayCtx.imageSmoothingEnabled = false;
    }
    if (hoverCanvas && this.hoverCtx) {
      hoverCanvas.width = Math.floor(safeWidthRatio);
      hoverCanvas.height = Math.floor(safeHeightRatio);
      hoverCanvas.style.width = `${safeWidth}px`;
      hoverCanvas.style.height = `${safeHeight}px`;
      this.hoverCtx.setTransform(ratio, 0, 0, ratio, 0, 0);
      this.hoverCtx.imageSmoothingEnabled = false;
    }
    this.processOverlayStore.ensureBackgroundCanvas(widthPx, heightPx, ratio);
    this.emitGrid(cols, rows);
    if (this.currentInstructions.length > 0) {
      this.redrawCurrentFrame(true);
    }
    this.redrawLegend();
  }

  private clearCanvas(): void {
    if (!this.ctx) {
      return;
    }
    const cols = this.coreColumns;
    const rows = Math.ceil((this.canvasSize || 1) / cols);
    const axisPad = this.getAxisPadding();
    // clear base grid background; once per clear
    this.ctx.fillStyle = GRID_BG;
    this.ctx.fillRect(0, 0, cols * this.cellSize + axisPad, rows * this.cellSize + axisPad);
    this.clearOverlay();
  }

  private clearOverlay(): void {
    if (!this.overlayCtx) {
      return;
    }
    const canvas = this.overlayCanvasRef.nativeElement;
    const width = canvas.width / this.pixelRatio;
    const height = canvas.height / this.pixelRatio;
    this.overlayCtx.clearRect(0, 0, width, height);
    if (this.hoverCtx) {
      this.hoverCtx.clearRect(0, 0, width, height);
    }
  }

  private updateHover(index: number | null, force = false): void {
    const changed = this.inspectorStore.setHover(index);
    if (!changed && !force) {
      return;
    }
    this.rebuildHoverList();
    this.flush();
  }

  private rebuildHoverList(): void {
    this.drawHoverWindow();
  }

  private getHoverRange(): CorewarHoverRange | null {
    const size = this.currentInstructions.length;
    if (!size) {
      return null;
    }
    const windowSize = this.normalizeInspectorViewSize(this.inspectorViewSize);
    return this.inspectorStore.getHoverRange(size, windowSize);
  }

  private setHoverRange(next: CorewarHoverRange | null): void {
    const current = this.hoverRange;
    if (current === next) {
      return;
    }
    if (!current || !next) {
      this.hoverRange = next;
      return;
    }
    if (
      current.start === next.start
      && current.length === next.length
      && current.selectedIndex === next.selectedIndex
      && current.lockMarkerIndex === next.lockMarkerIndex
      && current.locked === next.locked
    ) {
      return;
    }
    this.hoverRange = next;
  }

  private normalizeInspectorViewSize(value: number): number {
    const maxSize = this.inspectorViewSizeMax;
    const clamped = Math.max(1, Math.min(maxSize, Math.floor(value)));
    return clamped;
  }

  private rebuildProcessHoverMap(): void {
    this.processOverlayStore.rebuildProcessHoverMap(this.processQueues, OWNER_COLORS, GLYPH_COLOR);
    this.processOverlayStore.markBackgroundDirty();
    this.processOverlayStore.markSelectedCacheDirty();
  }

  private getAxisPadding(): number {
    return Math.max(8, Math.round(this.cellSize * 0.6));
  }

  private emitGrid(cols: number, rows: number): void {
    const current = this.arenaState().corewar.grid;
    if (current.cols === cols && current.rows === rows) {
      return;
    }
    this.store.dispatch(arenaActions.updateCorewarGrid({ grid: { cols, rows } }));
  }

  private normalizeOwners(owners: number[] | null | undefined, size: number): number[] {
    const normalized = new Array<number>(size);
    for (let i = 0; i < size; i += 1) {
      const value = owners?.[i];
      normalized[i] = Number.isFinite(value) ? (value as number) : -1;
    }
    return normalized;
  }

  private redrawLegend(): void {
    this.legendPanelRef?.redraw();
  }

  private flush(): void {
    this.cdr.markForCheck();
  }
}
