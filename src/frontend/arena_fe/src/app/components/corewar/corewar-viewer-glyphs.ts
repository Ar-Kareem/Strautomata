import { GLYPH_COLOR, GLYPH_DIM_COLOR, PROCESS_HIGHLIGHT_RING } from './corewar.constants';

const OPCODE_PIXEL_MAP: Record<string, string[]> = {
  DAT: [
    'wwwwwwwww',
    'wwbbbbbww',
    'wwbwwwbww',
    'wwbwwwbww',
    'wwbwwwbww',
    'wwbbbbbww',
    'wwwwwwwww',
    'wwwwwwwww',
    'wwwwwwwww',
  ],
  MOV: [
    'wwwwbwwww',
    'wwwwwbwww',
    'wwwwwwbww',
    'wbbbbbbbw',
    'wwwwwwbww',
    'wwwwwbwww',
    'wwwwbwwww',
    'wwwwwwwww',
    'wwwwwwwww',
  ],
  ADD: [
    'wwwwwwwww',
    'wwwwbwwww',
    'wwwwbwwww',
    'wwbbbbbww',
    'wwwwbwwww',
    'wwwwbwwww',
    'wwwwwwwww',
    'wwwwwwwww',
    'wwwwwwwww',
  ],
  SUB: [
    'wwwwwwwww',
    'wwwwwwwww',
    'wwwwwwwww',
    'wwbbbbbww',
    'wwwwwwwww',
    'wwwwwwwww',
    'wwwwwwwww',
    'wwwwwwwww',
    'wwwwwwwww',
  ],
  MUL: [
    'wwwwwwwww',
    'wwbwwwbww',
    'wwwbwbwww',
    'wwwwbwwww',
    'wwwbwbwww',
    'wwbwwwbww',
    'wwwwwwwww',
    'wwwwwwwww',
    'wwwwwwwww',
  ],
  DIV: [
    'wwwwwwwww',
    'wwwwbwwww',
    'wwwwwwwww',
    'wwbbbbbww',
    'wwwwwwwww',
    'wwwwbwwww',
    'wwwwwwwww',
    'wwwwwwwww',
    'wwwwwwwww',
  ],
  MOD: [
    'wwbwwwwbw',
    'wbwbwwbww',
    'wwbwwbwww',
    'wwwwbwwww',
    'wwwbwwbww',
    'wwbwwbwbw',
    'wbwwwwbww',
    'wwwwwwwww',
    'wwwwwwwww',
  ],
  JMP: [
    'wbbbbbbbw',
    'wwwwwwwbw',
    'wwwwwwwbw',
    'wwwwwwwbw',
    'wwwwwwwbw',
    'wwwwwwwbw',
    'wwwwwwwbw',
    'wwwwwwwww',
    'wwwwwwwww',
  ],
  JMZ: [
    'wbbbbbbbw',
    'wwwwwwwbw',
    'wwwbbwwbw',
    'wwbwwbwbw',
    'wwbwwbwbw',
    'wwbwwbwbw',
    'wwwbbwwbw',
    'wwwwwwwww',
    'wwwwwwwww',
  ],
  JMN: [
    'wbbbbbbbw',
    'wwwwwwwbw',
    'wwwbbwwbw',
    'wwbbbbwbw',
    'wwbbbbwbw',
    'wwbbbbwbw',
    'wwwbbwwbw',
    'wwwwwwwww',
    'wwwwwwwww',
  ],
  DJN: [
    'wbbbbbbbw',
    'wwwwwwwbw',
    'wwwbbwwbw',
    'wwbbbbwbw',
    'wwwwwwwbw',
    'wwbbbbwbw',
    'wwwbbwwbw',
    'wwwwwwwww',
    'wwwwwwwww',
  ],
  SPL: [
    'wwwbbbbbw',
    'wwwwwwwbw',
    'wbwwwwwbw',
    'wbwwwwwbw',
    'wbwwwwwbw',
    'wbwwwwwww',
    'wbbbbbwww',
    'wwwwwwwww',
    'wwwwwwwww',
  ],
  SLT: [
    'wwwwwwwww',
    'wwwwwbbww',
    'wwwbbwwww',
    'wwbwwwwww',
    'wwwbbwwww',
    'wwwwwbbww',
    'wwwwwwwww',
    'wwwwwwwww',
    'wwwwwwwww',
  ],
  CMP: [
    'wwwwwwwww',
    'wwwwwwwww',
    'wwbbbbbww',
    'wwwwwwwww',
    'wwbbbbbww',
    'wwwwwwwww',
    'wwwwwwwww',
    'wwwwwwwww',
    'wwwwwwwww',
  ],
  SEQ: [
    'wwwwwwwww',
    'wwwwwwwww',
    'wwbbbbbww',
    'wwwwwwwww',
    'wwbbbbbww',
    'wwwwwwwww',
    'wwwwwwwbw',
    'wwwwwwwww',
    'wwwwwwwww',
  ],
  SNE: [
    'wwwwwwwww',
    'wwwwwbwww',
    'wwbbbbbww',
    'wwwwbwwww',
    'wwbbbbbww',
    'wwwbwwwww',
    'wwwwwwwww',
    'wwwwwwwww',
    'wwwwwwwww',
  ],
  NOP: [
    'wwwwwwwww',
    'wwwwwwwww',
    'wwbbwwbww',
    'wwbwbwbww',
    'wwbwwbbww',
    'wwwwwwwww',
    'wwwwwwwww',
    'wwwwwwwww',
    '.........',
  ],
  GEN: [
    'wwwwwwwww',
    'wwwwwwwww',
    'wwwwwwwww',
    'wwwwwwwww',
    'wwwwbwwww',
    'wwwwwwwww',
    'wwwwwwwww',
    'wwwwwwwww',
    'wwwwwwwww',
  ],
};

type OpcodePixelCache = {
  size: number;
  runs: Array<{ x: number; y: number; len: number }>;
  minX: number;
  minY: number;
  width: number;
  height: number;
};

const OPCODE_PIXEL_CACHE: Record<string, OpcodePixelCache> = (() => {
  const cache: Record<string, OpcodePixelCache> = {};
  for (const [opcode, pattern] of Object.entries(OPCODE_PIXEL_MAP)) {
    const size = pattern.length;
    const runs: Array<{ x: number; y: number; len: number }> = [];
    let minX = size;
    let minY = size;
    let maxX = -1;
    let maxY = -1;
    for (let y = 0; y < size; y += 1) {
      const row = pattern[y] ?? '';
      let runStart = -1;
      let runLength = 0;
      for (let x = 0; x < row.length; x += 1) {
        if (row[x] === 'b') {
          if (runStart < 0) {
            runStart = x;
            runLength = 1;
          } else {
            runLength += 1;
          }
        } else if (runStart >= 0) {
          runs.push({ x: runStart, y, len: runLength });
          if (runStart < minX) minX = runStart;
          if (y < minY) minY = y;
          if (runStart + runLength - 1 > maxX) maxX = runStart + runLength - 1;
          if (y > maxY) maxY = y;
          runStart = -1;
          runLength = 0;
        }
      }
      if (runStart >= 0) {
        runs.push({ x: runStart, y, len: runLength });
        if (runStart < minX) minX = runStart;
        if (y < minY) minY = y;
        if (runStart + runLength - 1 > maxX) maxX = runStart + runLength - 1;
        if (y > maxY) maxY = y;
      }
    }
    if (!runs.length) {
      cache[opcode] = { size, runs: [], minX: 0, minY: 0, width: 0, height: 0 };
      continue;
    }
    cache[opcode] = {
      size,
      runs,
      minX,
      minY,
      width: maxX - minX + 1,
      height: maxY - minY + 1
    };
  }
  return cache;
})();

const OPCODE_SPRITE_CACHE = new Map<string, HTMLCanvasElement>();
const PROCESS_HIGHLIGHT_CACHE = new Map<string, HTMLCanvasElement>();

export function getCorewarGlyphColor(args: {
  opcode: string;
  owner: number;
  showIcons: boolean;
  showLastModifiedColor: boolean;
  makeNonDatWhite: boolean;
  makeWarriorDatWhite: boolean;
}): string {
  const { opcode, owner, showIcons, showLastModifiedColor, makeNonDatWhite, makeWarriorDatWhite } = args;
  if (opcode === 'DAT') {
    if (owner < 0) {
      return GLYPH_DIM_COLOR;
    }
    if (!showLastModifiedColor && !makeWarriorDatWhite) {
      return GLYPH_DIM_COLOR;
    }
    return GLYPH_COLOR;
  }
  if (!showIcons && !makeNonDatWhite) {
    return GLYPH_DIM_COLOR;
  }
  return GLYPH_COLOR;
}

export function drawCorewarOpcodePixels(args: {
  ctx: CanvasRenderingContext2D;
  opcode: string;
  cellX: number;
  cellY: number;
  cellSize: number;
  color: string;
  showIcons: boolean;
}): void {
  const iconKey = args.showIcons ? args.opcode : (args.opcode === 'DAT' ? 'DAT' : 'GEN');
  const sprite = getOpcodeSprite(iconKey, args.color, args.cellSize);
  if (!sprite) {
    return;
  }
  args.ctx.drawImage(sprite, args.cellX, args.cellY);
}

function getOpcodeSprite(opcode: string, color: string, cellSize: number): CanvasImageSource | null {
  const cached = OPCODE_PIXEL_CACHE[opcode];
  if (!cached || cached.runs.length === 0) {
    return null;
  }
  const size = Math.max(1, Math.round(cellSize));
  const key = `${opcode}|${color}|${size}`;
  const existing = OPCODE_SPRITE_CACHE.get(key);
  if (existing) {
    return existing;
  }
  const canvas = document.createElement('canvas');
  canvas.width = size;
  canvas.height = size;
  const spriteCtx = canvas.getContext('2d');
  if (!spriteCtx) {
    return null;
  }
  spriteCtx.imageSmoothingEnabled = true;
  const scale = (size * 0.72) / cached.size;
  const activeWidth = cached.width * scale;
  const activeHeight = cached.height * scale;
  const offsetX = (size - activeWidth) / 2 - cached.minX * scale;
  const offsetY = (size - activeHeight) / 2 - cached.minY * scale;
  spriteCtx.fillStyle = color;
  for (const run of cached.runs) {
    spriteCtx.fillRect(
      offsetX + run.x * scale,
      offsetY + run.y * scale,
      run.len * scale,
      scale
    );
  }
  OPCODE_SPRITE_CACHE.set(key, canvas);
  return canvas;
}

export function getCorewarProcessHighlightSprite(
  color: string,
  cellSize: number,
  colorToRgba: (hex: string, alpha: number) => string
): HTMLCanvasElement | null {
  const size = Math.max(1, Math.round(cellSize));
  const key = `${color}|${size}`;
  const existing = PROCESS_HIGHLIGHT_CACHE.get(key);
  if (existing) {
    return existing;
  }
  const canvas = document.createElement('canvas');
  canvas.width = size;
  canvas.height = size;
  const spriteCtx = canvas.getContext('2d');
  if (!spriteCtx) {
    return null;
  }
  spriteCtx.imageSmoothingEnabled = false;
  const radius = Math.max(3, size * 0.24);
  const center = size / 2;
  spriteCtx.fillStyle = colorToRgba(color, 0.2);
  spriteCtx.beginPath();
  spriteCtx.arc(center, center, radius * 0.7, 0, Math.PI * 2);
  spriteCtx.fill();
  spriteCtx.strokeStyle = PROCESS_HIGHLIGHT_RING;
  spriteCtx.lineWidth = Math.max(1, size * 0.16) + 1;
  spriteCtx.beginPath();
  spriteCtx.arc(center, center, radius, 0, Math.PI * 2);
  spriteCtx.stroke();
  PROCESS_HIGHLIGHT_CACHE.set(key, canvas);
  return canvas;
}
