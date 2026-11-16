import { Injectable } from '@angular/core';

type ProcessHoverMeta = {
  count: number;
  color: string | null;
  breakdown: Map<number, number>;
  tooltip: string;
};

type EnsureProcessBackgroundArgs = {
  processQueues: Array<number[]>;
  size: number;
  cols: number;
  cellSize: number;
  originX: number;
  originY: number;
  width: number;
  height: number;
  addressIdentity: boolean;
  addressIndex: Map<number, number>;
  currentInstructions: string[];
  currentOwners: number[];
  ownerColors: string[];
  showLastModifiedColor: boolean;
  cellX: number[];
  cellY: number[];
  drawOpcodePixels: (
    ctx: CanvasRenderingContext2D,
    opcode: string,
    cellX: number,
    cellY: number,
    cellSize: number,
    color: string
  ) => void;
  getGlyphColor: (opcode: string, owner: number) => string;
};

type EnsureSelectedProcessCacheArgs = {
  size: number;
  rows: number;
  cols: number;
  selectedWarriorIndex: number | null;
  selectedProcessQueue: number[];
  addressIdentity: boolean;
  addressIndex: Map<number, number>;
  cellRow: number[];
  cellCol: number[];
};

@Injectable()
export class CorewarProcessOverlayStore {
  private processHoverMap = new Map<number, ProcessHoverMeta>();
  private processBackgroundCanvas: HTMLCanvasElement | null = null;
  private processBackgroundCtx: CanvasRenderingContext2D | null = null;
  private processBackgroundKey = 0;
  private processBackgroundDirty = true;
  private backgroundSeen = new Uint32Array(0);
  private backgroundSeenToken = 1;
  private selectedProcessIndices: number[] = [];
  private selectedRowFlags = new Uint8Array(0);
  private selectedColFlags = new Uint8Array(0);
  private selectedCacheDirty = true;
  private processSeen = new Uint32Array(0);
  private processSeenToken = 1;

  clearState(): void {
    this.processHoverMap.clear();
    this.selectedProcessIndices = [];
    this.selectedRowFlags = new Uint8Array(0);
    this.selectedColFlags = new Uint8Array(0);
    this.selectedCacheDirty = true;
    this.processBackgroundDirty = true;
    this.processBackgroundKey = 0;
  }

  markBackgroundDirty(): void {
    this.processBackgroundDirty = true;
  }

  markSelectedCacheDirty(): void {
    this.selectedCacheDirty = true;
  }

  getBackgroundCanvas(): HTMLCanvasElement | null {
    return this.processBackgroundCanvas;
  }

  getSelectedProcessIndices(): number[] {
    return this.selectedProcessIndices;
  }

  getSelectedRowFlags(): Uint8Array {
    return this.selectedRowFlags;
  }

  getSelectedColFlags(): Uint8Array {
    return this.selectedColFlags;
  }

  getProcessHoverMeta(address: number): ProcessHoverMeta | undefined {
    return this.processHoverMap.get(address);
  }

  rebuildProcessHoverMap(processQueues: Array<number[]>, ownerColors: string[], glyphColor: string): void {
    this.processHoverMap.clear();
    if (!processQueues.length) {
      return;
    }
    processQueues.forEach((queue, warriorIndex) => {
      if (!queue || queue.length === 0) {
        return;
      }
      const color = ownerColors[warriorIndex % ownerColors.length];
      for (const addr of queue) {
        if (!Number.isFinite(addr)) {
          continue;
        }
        const key = addr as number;
        const existing = this.processHoverMap.get(key);
        if (!existing) {
          const breakdown = new Map<number, number>();
          breakdown.set(warriorIndex, 1);
          this.processHoverMap.set(key, {
            count: 1,
            color,
            breakdown,
            tooltip: `1x Warrior #${warriorIndex + 1}`
          });
          continue;
        }
        existing.count += 1;
        existing.breakdown.set(warriorIndex, (existing.breakdown.get(warriorIndex) ?? 0) + 1);
        if (existing.color && existing.color !== color) {
          existing.color = glyphColor;
        }
      }
    });
    this.processHoverMap.forEach((entry) => {
      if (entry.breakdown.size === 0) {
        entry.tooltip = '';
        return;
      }
      const lines = Array.from(entry.breakdown.entries())
        .sort((a, b) => a[0] - b[0])
        .map(([warriorIndex, count]) => `${count}x Warrior #${warriorIndex + 1}`);
      entry.tooltip = lines.join('\n');
    });
  }

  ensureBackgroundCanvas(widthPx: number, heightPx: number, ratio: number): void {
    if (!this.processBackgroundCanvas) {
      this.processBackgroundCanvas = document.createElement('canvas');
      this.processBackgroundCtx = this.processBackgroundCanvas.getContext('2d');
    }
    if (this.processBackgroundCanvas && this.processBackgroundCtx) {
      this.processBackgroundCanvas.width = Math.floor(widthPx * ratio);
      this.processBackgroundCanvas.height = Math.floor(heightPx * ratio);
      this.processBackgroundCtx.setTransform(ratio, 0, 0, ratio, 0, 0);
      this.processBackgroundCtx.imageSmoothingEnabled = false;
      this.processBackgroundDirty = true;
    }
  }

  ensureProcessBackground(args: EnsureProcessBackgroundArgs): void {
    const ctx = this.processBackgroundCtx;
    const canvas = this.processBackgroundCanvas;
    if (!ctx || !canvas) {
      return;
    }
    if (!args.processQueues.length || args.size <= 0) {
      if (this.processBackgroundDirty || this.processBackgroundKey !== 0) {
        ctx.clearRect(0, 0, args.width, args.height);
        this.processBackgroundKey = 0;
        this.processBackgroundDirty = false;
      }
      return;
    }
    const key = this.computeProcessBackgroundKey(args);
    if (!this.processBackgroundDirty && key === this.processBackgroundKey) {
      return;
    }
    this.processBackgroundKey = key;
    this.processBackgroundDirty = false;
    ctx.clearRect(0, 0, args.width, args.height);
    this.drawProcessBackgrounds(args, ctx);
  }

  ensureSelectedProcessCache(args: EnsureSelectedProcessCacheArgs): void {
    if (!this.selectedCacheDirty) {
      return;
    }
    this.selectedCacheDirty = false;
    this.selectedProcessIndices = [];
    if (args.selectedWarriorIndex === null || args.selectedProcessQueue.length === 0 || args.size <= 0) {
      this.selectedRowFlags = new Uint8Array(args.rows);
      this.selectedColFlags = new Uint8Array(args.cols);
      return;
    }
    if (this.processSeen.length !== args.size) {
      this.processSeen = new Uint32Array(args.size);
    }
    this.processSeenToken = (this.processSeenToken + 1) >>> 0;
    if (this.processSeenToken === 0) {
      this.processSeenToken = 1;
      this.processSeen.fill(0);
    }
    if (this.selectedRowFlags.length !== args.rows) {
      this.selectedRowFlags = new Uint8Array(args.rows);
    } else {
      this.selectedRowFlags.fill(0);
    }
    if (this.selectedColFlags.length !== args.cols) {
      this.selectedColFlags = new Uint8Array(args.cols);
    } else {
      this.selectedColFlags.fill(0);
    }
    const token = this.processSeenToken;
    for (const addr of args.selectedProcessQueue) {
      if (!Number.isFinite(addr)) {
        continue;
      }
      const idx = args.addressIdentity
        ? (addr >= 0 && addr < args.size ? (addr as number) : undefined)
        : args.addressIndex.get(addr as number);
      if (idx === undefined || this.processSeen[idx] === token) {
        continue;
      }
      this.processSeen[idx] = token;
      this.selectedProcessIndices.push(idx);
      const row = args.cellRow[idx] ?? Math.floor(idx / args.cols);
      const col = args.cellCol[idx] ?? (idx % args.cols);
      if (row >= 0 && row < args.rows) {
        this.selectedRowFlags[row] = 1;
      }
      if (col >= 0 && col < args.cols) {
        this.selectedColFlags[col] = 1;
      }
    }
  }

  colorToRgba(hex: string, alpha: number): string {
    if (!hex.startsWith('#') || (hex.length !== 7 && hex.length !== 4)) {
      return `rgba(255, 255, 255, ${alpha})`;
    }
    const normalized = hex.length === 4
      ? `#${hex[1]}${hex[1]}${hex[2]}${hex[2]}${hex[3]}${hex[3]}`
      : hex;
    const r = parseInt(normalized.slice(1, 3), 16);
    const g = parseInt(normalized.slice(3, 5), 16);
    const b = parseInt(normalized.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }

  private computeProcessBackgroundKey(args: EnsureProcessBackgroundArgs): number {
    let hash = 2166136261 >>> 0;
    for (let w = 0; w < args.processQueues.length; w += 1) {
      const queue = args.processQueues[w];
      if (!queue || queue.length === 0) {
        hash = this.hashMix(hash, w + 1);
        continue;
      }
      hash = this.hashMix(hash, w + 1);
      hash = this.hashMix(hash, queue.length);
      for (const addr of queue) {
        if (!Number.isFinite(addr)) {
          continue;
        }
        const idx = args.addressIdentity
          ? (addr >= 0 && addr < args.size ? (addr as number) : undefined)
          : args.addressIndex.get(addr as number);
        if (idx === undefined) {
          continue;
        }
        hash = this.hashMix(hash, idx + 1);
        const instruction = args.currentInstructions[idx] ?? '';
        hash = this.hashMix(hash, instruction.charCodeAt(0) || 0);
        hash = this.hashMix(hash, instruction.charCodeAt(1) || 0);
        hash = this.hashMix(hash, instruction.charCodeAt(2) || 0);
      }
    }
    return hash >>> 0;
  }

  private hashMix(hash: number, value: number): number {
    return Math.imul(hash ^ value, 16777619) >>> 0;
  }

  private drawProcessBackgrounds(args: EnsureProcessBackgroundArgs, ctx: CanvasRenderingContext2D): void {
    if (!args.processQueues.length) {
      return;
    }
    if (!args.size) {
      return;
    }
    if (this.backgroundSeen.length !== args.size) {
      this.backgroundSeen = new Uint32Array(args.size);
      this.backgroundSeenToken = 1;
    }
    const showQueueOutline = args.showLastModifiedColor;
    const pad = showQueueOutline ? Math.max(1, Math.round(args.cellSize * 0.1)) : 0;
    const fillSize = Math.max(1, args.cellSize - pad * 2);
    let token = this.backgroundSeenToken;
    args.processQueues.forEach((queue, warriorIndex) => {
      if (!queue || queue.length === 0) {
        return;
      }
      token = (token + 1) >>> 0;
      if (token === 0) {
        this.backgroundSeen.fill(0);
        token = 1;
      }
      const baseColor = args.ownerColors[warriorIndex % args.ownerColors.length];
      const fill = this.colorToRgba(baseColor, 0.55);
      const stroke = this.colorToRgba(baseColor, 0.95);
      if (showQueueOutline) {
        ctx.lineWidth = Math.max(1, Math.round(args.cellSize * 0.12));
      }
      for (const addr of queue) {
        if (!Number.isFinite(addr)) {
          continue;
        }
        const idx = args.addressIdentity
          ? (addr >= 0 && addr < args.size ? (addr as number) : undefined)
          : args.addressIndex.get(addr as number);
        if (idx === undefined) {
          continue;
        }
        if (this.backgroundSeen[idx] === token) {
          continue;
        }
        this.backgroundSeen[idx] = token;
        const baseX = args.cellX[idx] ?? (args.originX + (idx % args.cols) * args.cellSize);
        const baseY = args.cellY[idx] ?? (args.originY + Math.floor(idx / args.cols) * args.cellSize);
        const x = baseX + pad;
        const y = baseY + pad;
        ctx.fillStyle = fill;
        ctx.fillRect(x, y, fillSize, fillSize);
        if (showQueueOutline) {
          ctx.strokeStyle = stroke;
          ctx.strokeRect(x + 0.5, y + 0.5, fillSize - 1, fillSize - 1);
        }
        const opcode = (args.currentInstructions[idx] ?? '').slice(0, 3).toUpperCase();
        if (opcode) {
          const owner = args.currentOwners[idx] ?? -1;
          const glyphColor = args.getGlyphColor(opcode, owner);
          args.drawOpcodePixels(ctx, opcode, baseX, baseY, args.cellSize, glyphColor);
        }
      }
    });
    this.backgroundSeenToken = token;
  }
}
