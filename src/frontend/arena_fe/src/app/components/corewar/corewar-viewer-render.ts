import {
  GRID_BG,
  HOVER_OUTLINE,
  HOVER_OUTLINE_LOCKED,
  LAST_EXECUTED_COLOR,
  OWNER_COLORS,
} from './corewar.constants';

export function drawCorewarBaseFull(args: {
  ctx: CanvasRenderingContext2D;
  instructions: string[];
  owners: number[];
  cols: number;
  cellSize: number;
  originX: number;
  originY: number;
  axisPad: number;
  showLastModifiedColor: boolean;
  drawOpcodePixels: (
    ctx: CanvasRenderingContext2D,
    opcode: string,
    cellX: number,
    cellY: number,
    cellSize: number,
    color: string
  ) => void;
  getGlyphColor: (opcode: string, owner: number) => string;
}): void {
  const {
    ctx,
    instructions,
    owners,
    cols,
    cellSize,
    originX,
    originY,
    axisPad,
    showLastModifiedColor,
    drawOpcodePixels,
    getGlyphColor
  } = args;
  const size = instructions.length;
  const rows = Math.ceil(size / cols);
  ctx.clearRect(0, 0, cols * cellSize + axisPad, rows * cellSize + axisPad);
  ctx.fillStyle = GRID_BG;
  ctx.fillRect(0, 0, cols * cellSize + axisPad, rows * cellSize + axisPad);

  const cellMeta = instructions.map((instruction, index) => {
    const opcode = instruction.slice(0, 3).toUpperCase();
    const owner = owners[index] ?? -1;
    return { opcode, owner };
  });

  if (showLastModifiedColor) {
    ctx.lineWidth = 1;
    for (let i = 0; i < size; i += 1) {
      const { owner } = cellMeta[i];
      if (owner < 0) {
        continue;
      }
      const x = originX + (i % cols) * cellSize;
      const y = originY + Math.floor(i / cols) * cellSize;
      ctx.strokeStyle = OWNER_COLORS[owner % OWNER_COLORS.length];
      ctx.strokeRect(x + 0.5, y + 0.5, cellSize - 1, cellSize - 1);
    }

    const tokenSize = Math.max(2, cellSize * 0.45);
    const tokenOffset = (cellSize - tokenSize) / 2;
    for (let i = 0; i < size; i += 1) {
      const { owner, opcode } = cellMeta[i];
      if (owner < 0 || opcode !== 'DAT') {
        continue;
      }
      const x = originX + (i % cols) * cellSize + tokenOffset;
      const y = originY + Math.floor(i / cols) * cellSize + tokenOffset;
      ctx.fillStyle = OWNER_COLORS[owner % OWNER_COLORS.length];
      ctx.fillRect(x, y, tokenSize, tokenSize);
    }
  }

  for (let i = 0; i < size; i += 1) {
    const { opcode, owner } = cellMeta[i];
    if (!opcode) {
      continue;
    }
    const x = originX + (i % cols) * cellSize;
    const y = originY + Math.floor(i / cols) * cellSize;
    const glyphColor = getGlyphColor(opcode, owner);
    drawOpcodePixels(ctx, opcode, x, y, cellSize, glyphColor);
  }
}

export function drawCorewarBaseCell(args: {
  ctx: CanvasRenderingContext2D;
  index: number;
  instruction: string;
  owner: number;
  cols: number;
  cellSize: number;
  originX: number;
  originY: number;
  showLastModifiedColor: boolean;
  drawOpcodePixels: (
    ctx: CanvasRenderingContext2D,
    opcode: string,
    cellX: number,
    cellY: number,
    cellSize: number,
    color: string
  ) => void;
  getGlyphColor: (opcode: string, owner: number) => string;
}): void {
  const {
    ctx,
    index,
    instruction,
    owner,
    cols,
    cellSize,
    originX,
    originY,
    showLastModifiedColor,
    drawOpcodePixels,
    getGlyphColor
  } = args;
  const opcode = instruction.slice(0, 3).toUpperCase();
  const x = originX + (index % cols) * cellSize;
  const y = originY + Math.floor(index / cols) * cellSize;
  ctx.fillStyle = GRID_BG;
  ctx.fillRect(x, y, cellSize, cellSize);

  if (showLastModifiedColor && owner >= 0) {
    ctx.lineWidth = 1;
    ctx.strokeStyle = OWNER_COLORS[owner % OWNER_COLORS.length];
    ctx.strokeRect(x + 0.5, y + 0.5, cellSize - 1, cellSize - 1);
  }

  if (showLastModifiedColor && owner >= 0 && opcode === 'DAT') {
    const tokenSize = Math.max(2, cellSize * 0.45);
    const tokenOffset = (cellSize - tokenSize) / 2;
    ctx.fillStyle = OWNER_COLORS[owner % OWNER_COLORS.length];
    ctx.fillRect(x + tokenOffset, y + tokenOffset, tokenSize, tokenSize);
  }

  if (opcode) {
    const glyphColor = getGlyphColor(opcode, owner);
    drawOpcodePixels(ctx, opcode, x, y, cellSize, glyphColor);
  }
}

export function drawCorewarLastExecutedHighlights(args: {
  ctx: CanvasRenderingContext2D;
  cols: number;
  cellSize: number;
  offsetX: number;
  offsetY: number;
  lastExecutedByWarrior: Array<number | null>;
  addressIndex: Map<number, number>;
}): void {
  const {
    ctx,
    cols,
    cellSize,
    offsetX,
    offsetY,
    lastExecutedByWarrior,
    addressIndex
  } = args;
  if (!lastExecutedByWarrior || lastExecutedByWarrior.length === 0) {
    return;
  }
  const lineWidth = Math.max(2, cellSize * 0.14);
  ctx.lineWidth = lineWidth;
  lastExecutedByWarrior.forEach((address) => {
    if (address === null || address === undefined) {
      return;
    }
    const highlightIndex = addressIndex.get(address);
    if (highlightIndex === undefined) {
      return;
    }
    const x = offsetX + (highlightIndex % cols) * cellSize;
    const y = offsetY + Math.floor(highlightIndex / cols) * cellSize;
    ctx.strokeStyle = LAST_EXECUTED_COLOR;
    ctx.strokeRect(x + 1, y + 1, cellSize - 2, cellSize - 2);
  });
  ctx.lineWidth = 1;
}

export function drawCorewarHoverWindow(args: {
  ctx: CanvasRenderingContext2D;
  cols: number;
  size: number;
  cellSize: number;
  originX: number;
  originY: number;
  width: number;
  height: number;
  range: { start: number; length: number; selectedIndex: number | null; locked: boolean } | null;
}): void {
  const { ctx, cols, size, cellSize, originX, originY, width, height, range } = args;
  ctx.clearRect(0, 0, width, height);
  if (!range || size <= 0) {
    return;
  }
  const baseIndex = range.selectedIndex ?? range.start;
  if (baseIndex < 0 || baseIndex >= size) {
    return;
  }
  const drawRowRect = (row: number, colStart: number, colEnd: number) => {
    if (colEnd < colStart) {
      return;
    }
    const rectWidth = (colEnd - colStart + 1) * cellSize;
    const x = originX + colStart * cellSize;
    const y = originY + row * cellSize;
    ctx.strokeStyle = range.locked ? HOVER_OUTLINE_LOCKED : HOVER_OUTLINE;
    ctx.lineWidth = Math.max(2, cellSize * (range.locked ? 0.28 : 0.18));
    ctx.strokeRect(x + 0.5, y + 0.5, rectWidth - 1, cellSize - 1);
  };
  const drawSegment = (segmentStart: number, segmentLength: number) => {
    if (segmentLength <= 0) {
      return;
    }
    const segmentEnd = segmentStart + segmentLength - 1;
    const startRow = Math.floor(segmentStart / cols);
    const startCol = segmentStart % cols;
    const endRow = Math.floor(segmentEnd / cols);
    const endCol = segmentEnd % cols;
    if (startRow === endRow) {
      drawRowRect(startRow, startCol, endCol);
      return;
    }
    drawRowRect(startRow, startCol, cols - 1);
    for (let row = startRow + 1; row < endRow; row += 1) {
      drawRowRect(row, 0, cols - 1);
    }
    drawRowRect(endRow, 0, endCol);
  };
  ctx.save();
  if (range.start + range.length > size) {
    const firstLength = size - range.start;
    drawSegment(range.start, firstLength);
    drawSegment(0, range.length - firstLength);
  } else {
    drawSegment(range.start, range.length);
  }
  ctx.restore();
}

export function drawCorewarProcessIndicators(args: {
  ctx: CanvasRenderingContext2D;
  cellSize: number;
  offsetX: number;
  offsetY: number;
  colorToRgba: (hex: string, alpha: number) => string;
  color: string;
  rowFlags: Uint8Array;
  colFlags: Uint8Array;
}): void {
  const { ctx, cellSize, offsetX, offsetY, colorToRgba, color, rowFlags, colFlags } = args;
  if (rowFlags.length === 0 && colFlags.length === 0) {
    return;
  }
  const markSize = Math.max(2, Math.round(cellSize * 0.18));
  const edgeInset = 2;
  const rowMarkX = Math.max(1, edgeInset);
  const colMarkY = Math.max(1, edgeInset);
  ctx.save();
  ctx.fillStyle = colorToRgba(color, 0.85);
  for (let row = 0; row < rowFlags.length; row += 1) {
    if (!rowFlags[row]) {
      continue;
    }
    const y = offsetY + row * cellSize + (cellSize - markSize) / 2;
    ctx.fillRect(rowMarkX, Math.round(y), markSize, markSize);
  }
  for (let col = 0; col < colFlags.length; col += 1) {
    if (!colFlags[col]) {
      continue;
    }
    const x = offsetX + col * cellSize + (cellSize - markSize) / 2;
    ctx.fillRect(Math.round(x), colMarkY, markSize, markSize);
  }
  ctx.restore();
}

export function drawCorewarProcessHighlights(args: {
  ctx: CanvasRenderingContext2D;
  cols: number;
  cellSize: number;
  offsetX: number;
  offsetY: number;
  indices: number[];
  cellX: number[];
  cellY: number[];
  sprite: HTMLCanvasElement | null;
}): void {
  const { ctx, cols, cellSize, offsetX, offsetY, indices, cellX, cellY, sprite } = args;
  if (!sprite || indices.length === 0) {
    return;
  }
  ctx.save();
  for (let i = 0; i < indices.length; i += 1) {
    const idx = indices[i] as number;
    const x = cellX[idx] ?? (offsetX + (idx % cols) * cellSize);
    const y = cellY[idx] ?? (offsetY + Math.floor(idx / cols) * cellSize);
    ctx.drawImage(sprite, x, y);
  }
  ctx.restore();
}
