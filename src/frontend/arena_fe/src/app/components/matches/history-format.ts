import type { MatchReason, MatchRow, MatchesTable, PairwiseCounts, PlayerResult } from '@main/history.types';

const FAMILY_COLORS: Record<string, string> = {
  Claude: '#f0a35e',
  GPT: '#4ea8ff',
  Gemini: '#b388ff',
  DeepSeek: '#2dd4bf',
  Qwen: '#ff6f8d',
  Kimi: '#ffd166',
  GLM: '#7bd389',
  Grok: '#c9d1d9',
  MiniMax: '#ff9f43',
  Mistral: '#ff7f50',
  KAT: '#5eead4',
  MiMo: '#f472b6',
  Nemotron: '#84cc16',
  Solar: '#fbbf24',
  Trinity: '#38bdf8',
  Llama: '#a3e635',
  Baseline: '#8a97ad',
  Other: '#9aa5b8'
};

export const familyColor = (family: string | null | undefined): string => {
  if (!family) {
    return FAMILY_COLORS['Other'];
  }
  if (FAMILY_COLORS[family]) {
    return FAMILY_COLORS[family];
  }
  let hash = 0;
  for (const ch of family) {
    hash = (hash * 31 + ch.charCodeAt(0)) >>> 0;
  }
  return `hsl(${hash % 360} 70% 62%)`;
};

export const modelOf = (bot: string): string => bot.split('/')[0];

export const botNumber = (bot: string): string | null => {
  const parts = bot.split('/');
  return parts.length > 1 ? parts[parts.length - 1] : null;
};

/** "gpt_5.5_high/002" -> "gpt_5.5_high #002" */
export const botLabel = (bot: string): string => {
  const num = botNumber(bot);
  if (!num) {
    return bot;
  }
  const short = /^\d+$/.test(num) ? String(parseInt(num, 10)) : num;
  return `${modelOf(bot)} #${short}`;
};

/** "gpt_5.5_high/002" -> "#2" (for views already scoped to one model) */
export const botShortLabel = (bot: string): string => {
  const num = botNumber(bot);
  if (!num) {
    return bot;
  }
  return `#${/^\d+$/.test(num) ? String(parseInt(num, 10)) : num}`;
};

export const pairKey = (a: string, b: string): string => (a <= b ? `${a}|${b}` : `${b}|${a}`);

export const safeBotName = (bot: string): string => bot.replace(/\//g, '__');

export const formatRating = (value: number | null | undefined): string =>
  value === null || value === undefined || Number.isNaN(value) ? '–' : Math.round(value).toString();

export const formatSecs = (value: number | null | undefined): string => {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return '–';
  }
  if (value < 10) {
    return `${value.toFixed(2)}s`;
  }
  if (value < 100) {
    return `${value.toFixed(1)}s`;
  }
  return `${Math.round(value)}s`;
};

export const RESULT_LABEL: Record<PlayerResult, string> = {
  win: 'Win',
  loss: 'Loss',
  draw: 'Draw',
  error: 'Error',
  enemy_error: 'Opp. error',
  timeout: 'Timeout',
  enemy_timeout: 'Opp. timeout',
  unknown: 'Unknown'
};

export type ResultTone = 'win' | 'loss' | 'draw' | 'fault' | 'gift' | 'neutral';

export const resultTone = (result: PlayerResult): ResultTone => {
  switch (result) {
    case 'win':
      return 'win';
    case 'loss':
      return 'loss';
    case 'draw':
      return 'draw';
    case 'error':
    case 'timeout':
      return 'fault';
    case 'enemy_error':
    case 'enemy_timeout':
      return 'gift';
    default:
      return 'neutral';
  }
};

export const REASON_LABEL: Record<MatchReason, string> = {
  win: 'Decisive',
  draw: 'Draw',
  error: 'Illegal move / crash',
  timeout: 'Timeout',
  unknown: 'Unknown'
};

/** Human sentence describing a match from bot A's point of view. */
export const describeMatch = (row: MatchRow, labelA: string, labelB: string): string => {
  switch (row.reason) {
    case 'win':
      return row.winner === 0 ? `${labelA} won` : `${labelB} won`;
    case 'draw':
      return 'Draw';
    case 'error':
      if (row.winner === null) {
        return 'Both players errored';
      }
      return row.winner === 0 ? `${labelB} made an illegal move / crashed` : `${labelA} made an illegal move / crashed`;
    case 'timeout':
      if (row.winner === null) {
        return 'Timeout';
      }
      return row.winner === 0 ? `${labelB} timed out` : `${labelA} timed out`;
    default:
      return 'Unknown outcome';
  }
};

/** Points share for `row` bot against `col` bot from the exported pairwise counts (0..1, or null when no games). */
export const pairScore = (
  pairwise: Record<string, PairwiseCounts>,
  row: string,
  col: string
): { share: number | null; counts: PairwiseCounts | null; rowIsA: boolean } => {
  const key = pairKey(row, col);
  const counts = pairwise[key] ?? null;
  const rowIsA = row <= col;
  if (!counts || counts[0] === 0) {
    return { share: null, counts, rowIsA };
  }
  const [n, aWins, bWins, draws, aErr, bErr, aTo, bTo] = counts;
  const rowWins = rowIsA ? aWins : bWins;
  const oppFaults = rowIsA ? bErr + bTo : aErr + aTo;
  const share = (rowWins + oppFaults + 0.5 * draws) / n;
  return { share: Math.max(0, Math.min(1, share)), counts, rowIsA };
};

export const shareColor = (share: number | null): string => {
  if (share === null) {
    return 'rgba(255, 255, 255, 0.04)';
  }
  // 0 -> red, 0.5 -> neutral, 1 -> teal
  if (share >= 0.5) {
    const t = (share - 0.5) * 2;
    return `rgba(45, 212, 191, ${0.12 + t * 0.75})`;
  }
  const t = (0.5 - share) * 2;
  return `rgba(255, 111, 141, ${0.12 + t * 0.75})`;
};

export const moveToText = (move: unknown): string => {
  if (move === null || move === undefined) {
    return '–';
  }
  if (typeof move === 'string') {
    return move;
  }
  if (typeof move === 'number') {
    return String(move);
  }
  try {
    return JSON.stringify(move);
  } catch {
    return String(move);
  }
};

/** Decode the columnar matches.json rows into typed objects. */
export const decodeMatchesTable = (table: MatchesTable): MatchRow[] => {
  const resultByCode = new Map<number, PlayerResult>();
  for (const [name, code] of Object.entries(table.result_codes)) {
    resultByCode.set(code, name as PlayerResult);
  }
  const reasonByCode = new Map<number, MatchReason>();
  for (const [name, code] of Object.entries(table.reason_codes)) {
    reasonByCode.set(code, name as MatchReason);
  }
  const col = (name: string): number => table.columns.indexOf(name);
  const iA = col('a');
  const iB = col('b');
  const iResA = col('res_a');
  const iResB = col('res_b');
  const iReason = col('reason');
  const iWinner = col('winner');
  const iMoves = col('move_count');
  const iSecs = col('secs');
  const iSeed = col('seed');
  const iDetail = col('detail');
  return table.rows.map((raw, index) => {
    const winnerRaw = raw[iWinner];
    const moves = raw[iMoves];
    const secs = raw[iSecs];
    const seed = raw[iSeed];
    return {
      index,
      a: table.bots[raw[iA]] ?? String(raw[iA]),
      b: table.bots[raw[iB]] ?? String(raw[iB]),
      resA: resultByCode.get(raw[iResA]) ?? 'unknown',
      resB: resultByCode.get(raw[iResB]) ?? 'unknown',
      reason: reasonByCode.get(raw[iReason]) ?? 'unknown',
      winner: winnerRaw === 0 || winnerRaw === 1 ? winnerRaw : null,
      moveCount: typeof moves === 'number' && moves >= 0 ? moves : null,
      secs: typeof secs === 'number' && secs >= 0 ? secs : null,
      seed: typeof seed === 'number' && seed >= 0 ? seed : null,
      detail: typeof raw[iDetail] === 'number' ? raw[iDetail] : -1
    };
  });
};
