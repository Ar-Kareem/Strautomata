export const OWNER_COLORS = [
  '#2f7cff',
  '#2ed08f',
  '#f2b84b',
  '#f05d6b',
  '#b36bff',
  '#45b7ff',
  '#f36cf4',
  '#85f2a7',
  '#ff9b47',
  '#ff5ea3'
];

export const DEFAULT_COLUMNS = 100;
// entire grid background
export const GRID_BG = 'rgba(5, 7, 10, 0.98)';
// GLYPH COLOR for the initial DAT cells (i.e. DAT with owner == -1)
export const GLYPH_DIM_COLOR = 'rgba(120, 126, 132, 0.32)';
// GLYPH COLOR for all other glyphs
export const GLYPH_COLOR = '#f4f6f8';
// last-executed process outline
export const LAST_EXECUTED_COLOR = '#ffffff';
// on hover
export const HOVER_OUTLINE_LOCKED = 'rgba(255, 255, 255, 0.95)';
export const HOVER_OUTLINE = 'rgba(255, 255, 255, 0.4)';
// process highlights circles (when left scoreboard is clicked)
export const PROCESS_HIGHLIGHT_RING = 'rgba(255, 255, 255, 0.65)';
// legend
export const LEGEND_PANEL_BG = 'rgba(5, 8, 12, 0.35)';
export const LEGEND_TEXT_COLOR = 'rgba(220, 228, 236, 0.9)';
// right panel 
//   text/font colors
export const INSPECTOR_TEXT_DARK = '#060a07';
export const INSPECTOR_TEXT_LIGHT = '#f4f6f8';
//   row background color
export const OUTLINE_DIM = 'rgba(140, 148, 156, 0.35)';

export const OPCODE_DESCRIPTIONS: Record<string, string> = {
  DAT: 'DAT : data (kills the process)',
  MOV: 'MOV : move (copies data from one address to another)',
  ADD: 'ADD : add (adds one number to another)',
  SUB: 'SUB : subtract (subtracts one number from another)',
  MUL: 'MUL : multiply (multiplies one number with another)',
  DIV: 'DIV : divide (divides one number from another)',
  MOD: 'MOD : modulus (divides one number with another and gives the remainder)',
  JMP: 'JMP : jump (continues execution from another address)',
  JMZ: 'JMZ : jump if zero (tests a number and jumps to an address if it\'s 0)',
  JMN: 'JMN : jump if not zero (tests a number and jumps if it isn\'t 0)',
  DJN: 'DJN : decrement and jump if not zero (decrements a number by one, and jumps unless the result is 0)',
  SPL: 'SPL : split (starts a second process at another address)',
  CMP: 'CMP : skip if equal (compares two instructions, and skips the next instruction if they are equal)',
  SEQ: 'SEQ : same as CMP',
  SNE: 'SNE : skip if not equal (compares two instructions, and skips the next instruction if they aren\'t equal)',
  SLT: 'SLT : skip if lower than (compares two values, and skips the next instruction if the first is lower than the second)',
  LDP: 'LDP : load from p-space (loads a number from private storage space)',
  STP: 'STP : save to p-space (saves a number to private storage space)',
  NOP: 'NOP : no operation (does nothing)',
  '.A': ' .A : apply the source A-field to the destination A-field',
  '.B': ' .B : apply the source B-field to the destination B-field',
  '.AB': '.AB : apply the source A-field to the destination B-field',
  '.BA': '.BA : apply the source B-field to the destination A-field',
  '.F': ' .F : apply both source fields to the same fields in the destination',
  '.X': ' .X : apply both source fields to the opposite fields in the destination',
  '.I': ' .I : apply the entire source instruction to the destination',
  mods: 'Mods are ignored by JMP/SPL; unsupported mods fall back, and .I acts like .F except for MOV/SEQ/SNE (CMP=SEQ).',
  modes: 'Define the indirection and side effects used when evaluating operands.',
  '#': ' #  : immediate',
  '$': ' $  : direct (the $ may be omitted)',
  '*': ' *  : A-field indirect',
  '@': ' @  : B-field indirect',
  '{': ' {  : A-field indirect with predecrement',
  '<': ' <  : B-field indirect with predecrement',
  '}': ' }  : A-field indirect with postincrement',
  '>': ' >  : B-field indirect with postincrement',
};

export const DEFAULT_SIM_CONFIG = {
  rounds: 4,
  size: 8000,
  cycles: 80000,
  processes: 8000,
  length: 100,
  distance: 100,
  seed: 0
};

export type WarriorOption = {
  name: string;
  value: string;
  source: string;
  code: string;
  path?: string;
  codeLoaded?: boolean;
};

export type GroupedWarriorOption = {
  label: string;
  value: string;
  items: Array<{ label: string; value: number }>;
};

export type ScoreboardRow = {
  id: number;
  label: string;
  color: string;
  alive: boolean;
  isLastAlive: boolean;
  processes: number;
  lastExecutedLabel: string;
  roundsWon: number;
  score: number | null;
  aliveScore: number | null;
  spawned: number;
  coverage: number;
};

export type CorewarFrame = {
  instructions: string[];
  owners: number[];
  addresses?: number[];
};

export type CorewarSimConfig = {
  rounds: number;
  size: number;
  cycles: number;
  processes: number;
  length: number;
  distance: number;
  seed: number;
};

export type CorewarWarriorSpec = {
  source: string;
  code: string;
};

export type CorewarProcessState = {
  id?: number;
  queue?: number[];
};

export type CorewarWarriorState = {
  id: number;
  name: string;
  author: string;
  alive: boolean;
  n_processes: number;
  last_executed?: number | null;
};

export type CorewarMetrics = {
  score?: number[];
  alive_score?: number[];
  total_spawned_procs?: number[];
  memory_coverage?: number[];
};

export type CorewarStepState = {
  cycle?: number;
  total_cycles?: number;
  per_warrior?: CorewarWarriorState[];
  processes?: CorewarProcessState[];
  core_size?: number;
  metrics?: CorewarMetrics;
  round_index?: number;
  rounds?: number;
  n_alive?: number;
};

export type CorewarInitMatchPayload = {
  match_id?: number;
  error?: string;
  error_indices?: number[];
  state?: CorewarStepState;
  frame?: CorewarFrame;
};

export type CorewarStepPayload = {
  done?: boolean;
  match_done?: boolean;
  error?: string;
  state?: CorewarStepState;
  frame?: CorewarFrame;
};

export type CorewarNextRoundPayload = {
  done?: boolean;
  error?: string;
  state?: CorewarStepState;
  frame?: CorewarFrame;
};

export type CorewarMatchWinner = {
  name: string;
  roundsWon: number;
  color: string;
};

export function getCorewarMatchWinner(
  perWarrior: CorewarWarriorState[],
  roundWins: number[],
  matchDone: boolean
): CorewarMatchWinner | null {
  if (!matchDone || perWarrior.length === 0) {
    return null;
  }
  const maxWins = roundWins.length ? Math.max(...roundWins.map((wins) => wins ?? 0)) : 0;
  const winners = perWarrior
    .map((warrior, index) => ({
      name: warrior?.name?.trim() || `Warrior ${index + 1}`,
      roundsWon: roundWins[index] ?? 0,
      color: OWNER_COLORS[index % OWNER_COLORS.length]
    }))
    .filter((row) => row.roundsWon === maxWins && maxWins > 0);
  if (winners.length !== 1) {
    return null;
  }
  return winners[0];
}

export function escapeTooltipHtml(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

export function buildInstructionTooltip(rawInstruction: string): string {
  const trimmed = rawInstruction.trim();
  const match = trimmed.match(
    /^([A-Z]{3})(\.[A-Z]{1,2})?\s+([#$*@{}<>])\s*[+-]?\d+\s*,\s*([#$*@{}<>])\s*[+-]?\d+\s*$/
  );
  const opcode = match?.[1]?.toUpperCase() ?? trimmed.slice(0, 3).toUpperCase();
  const modifier = match?.[2]?.toUpperCase() ?? '';
  const aMode = match?.[3] ?? '';
  const bMode = match?.[4] ?? '';
  const opcodeDesc = OPCODE_DESCRIPTIONS[opcode] ?? opcode;
  const modDesc = modifier ? (OPCODE_DESCRIPTIONS[modifier] ?? modifier) : 'default modifier';
  const aModeDesc = aMode ? (OPCODE_DESCRIPTIONS[aMode] ?? aMode) : 'A-mode';
  const bModeDesc = bMode ? (OPCODE_DESCRIPTIONS[bMode] ?? bMode) : 'B-mode';
  return [opcodeDesc, modDesc, aModeDesc, bModeDesc]
    .map((line) => `<div class="corewar-opcode-tooltip-line">${escapeTooltipHtml(line)}</div>`)
    .join('');
}

export function normalizeCellSize(value: number): number {
  const numeric = Number.isFinite(value) ? Math.floor(value) : 12;
  return Math.max(7, Math.min(48, numeric));
}
