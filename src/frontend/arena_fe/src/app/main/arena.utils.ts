import { GAME_DESCRIPTIONS, GAME_WORLD_LABELS } from './arena.constants';
import type { BotOption, EloByColumn, GameWorldOption, MatchPayload } from './arena.constants';

type ActiveGameState = {
  catalog: { games: GameWorldOption[] };
  selection: { gameId: string | null; worldId: string | null };
};

type HashRouteState = {
  path: string;
  params: URLSearchParams;
};

const BOT_LABELS: Record<string, string> = {
  human: 'Human',
  random: 'Random Scout',
  first: 'First Legal',
  last: 'Last Legal'
};

const BOT_BLURBS: Record<string, string> = {
  human: 'Moves are provided by the player.',
  random: 'Picks any legal move at random.',
  first: 'Always grabs the first available move.',
  last: 'Always selects the final legal move.'
};

export const includeGameInDropdown = (gameId: string, worldId: string): boolean => {
  return !!GAME_WORLD_LABELS[gameId]?.[worldId];
};

export const formatGameLabel = (gameId: string, worldId: string): string =>
  GAME_WORLD_LABELS[gameId]?.[worldId] ?? `??? ${gameId} / ${worldId}`;

export const formatGameDescription = (gameId: string, worldId: string): string =>
  GAME_DESCRIPTIONS[gameId] ?? `Arena match for ${formatGameLabel(gameId, worldId)}.`;

export const getActiveGame = (state: ActiveGameState): GameWorldOption | null =>
  state.catalog.games.find((game) => game.gameId === state.selection.gameId && game.worldId === state.selection.worldId) ?? null;

export const formatBotLabel = (id: string): string => BOT_LABELS[id] ?? id;

export const resolveBotLabel = (
  bots: BotOption[],
  botId: string | null,
  fallback: string
): string => (botId ? bots.find((candidate) => candidate.id === botId)?.label ?? formatBotLabel(botId) : fallback);

export const formatBotBlurb = (id: string): string =>
  BOT_BLURBS[id] ?? 'Arena bot from examples.';

export const buildBotOptions = (botIds: string[], includeHuman: boolean): BotOption[] => {
  const preferredOrder = includeHuman
    ? ['human', 'random', 'first', 'last']
    : ['random', 'first', 'last'];
  const unique = new Set(botIds.map((id) => String(id)));
  for (const id of preferredOrder) {
    unique.add(id);
  }
  const rest = [...unique].filter((id) => !preferredOrder.includes(id)).sort();
  const ordered = [...preferredOrder, ...rest];
  return ordered.map((id) => ({
    id,
    label: formatBotLabel(id),
    blurb: formatBotBlurb(id)
  }));
};

export const normalizeLogs = (logs: MatchPayload['logs']): string[] =>
  Array.isArray(logs) ? logs.map((item) => String(item)) : [];

export const formatErrorLines = (detail: string): string[] =>
  detail
    .split('\n')
    .map((line) => line.trimEnd())
    .filter((line) => line.length > 0)
    .slice(0, 12);

export const collectGameIdsFromManifest = (manifestFiles: string[]): string[] => {
  const ids: string[] = [];
  const seen = new Set<string>();
  for (const file of manifestFiles) {
    if (!file.startsWith('game_arena/')) {
      continue;
    }
    const parts = file.split('/');
    if (parts.length < 3) {
      continue;
    }
    const gameId = parts[1];
    if (!gameId || gameId.startsWith('__') || seen.has(gameId)) {
      continue;
    }
    seen.add(gameId);
    ids.push(gameId);
  }
  return ids;
};

export const toJsValue = <T>(value: unknown): T | null => {
  if (value && typeof (value as { toJs?: (options?: unknown) => unknown }).toJs === 'function') {
    const proxy = value as {
      toJs: (options?: unknown) => unknown;
      destroy?: () => void;
    };
    let converted: unknown;
    try {
      converted = proxy.toJs({ dict_converter: Object.fromEntries });
    } catch {
      converted = proxy.toJs();
    }
    proxy.destroy?.();
    if (converted instanceof Map) {
      return Object.fromEntries(converted) as T;
    }
    return converted as T;
  }
  return value as T;
};

export const parseEloCsv = (text: string): EloByColumn | null => {
  const lines = text.split(/\r?\n/).filter((line) => line.trim().length > 0);
  if (lines.length < 2) {
    return null;
  }
  const header = lines[0].split(',').map((cell) => cell.trim());
  if (header.length < 2) {
    return null;
  }
  const columns = header.slice(1).filter((column) => column.length > 0);
  if (columns.length === 0) {
    return null;
  }
  const table: EloByColumn = {};
  for (const column of columns) {
    table[column] = {};
  }
  let found = 0;
  for (const line of lines.slice(1)) {
    const cells = line.split(',');
    const botId = cells[0]?.trim();
    if (!botId) {
      continue;
    }
    for (let i = 0; i < columns.length; i += 1) {
      const column = columns[i];
      const raw = cells[i + 1]?.trim();
      if (!raw) {
        continue;
      }
      const value = Number(raw);
      if (!Number.isFinite(value)) {
        continue;
      }
      table[column][botId] = value;
      found += 1;
    }
  }
  return found > 0 ? table : null;
};

const normalizeHashPath = (path: string): string => {
  const trimmed = (path ?? '').trim();
  if (!trimmed || trimmed === '#') {
    return '/';
  }
  const withoutHash = trimmed.startsWith('#') ? trimmed.slice(1) : trimmed;
  const clean = withoutHash.startsWith('/') ? withoutHash : `/${withoutHash}`;
  return clean.replace(/\/+$/, '') || '/';
};

export const getHashRouteState = (): HashRouteState => {
  const hashRaw = window.location.hash.startsWith('#')
    ? window.location.hash.slice(1)
    : window.location.hash;
  if (!hashRaw) {
    return { path: '/', params: new URLSearchParams() };
  }
  const [pathPart, queryPart] = hashRaw.split('?', 2);
  return {
    path: normalizeHashPath(pathPart),
    params: new URLSearchParams(queryPart ?? '')
  };
};

/**
 * Moving to another page adds a browser history entry; changing params within a page replaces it,
 * unless `push` asks for an entry anyway (a view inside a page that Back should return from).
 */
export const setHashRouteState = (path: string, params?: URLSearchParams, push = false): void => {
  const url = new URL(window.location.href);
  const cleanPath = normalizeHashPath(path);
  const query = params?.toString() ?? '';
  url.hash = `${cleanPath}${query ? `?${query}` : ''}`;
  if (url.toString() === window.location.href) {
    return;
  }
  if (push || cleanPath !== getHashRouteState().path) {
    window.history.pushState({}, '', url.toString());
  } else {
    window.history.replaceState({}, '', url.toString());
  }
};

const GAME_ELO_COLUMNS: Record<string, string> = {
  amazons: 'Amazons',
  backgammon: 'Backgammon',
  battleships: 'Battleships',
  blackjack: 'Blackjack',
  breakthrough: 'Breakthrough',
  checkers: 'Checkers',
  chess: 'Chess UCI',
  clobber: 'Clobber',
  connect4: 'Connect4',
  dots_and_boxes: 'Dots&B',
  go: 'Go',
  havannah: 'Havannah',
  hex: 'Hex',
  lines_of_action: 'LoA',
  mancala: 'Mancala',
  nim: 'Nim',
  othello: 'Othello',
  pentago: 'Pentago',
  tic_tac_toe_3d: '3D TTT'
};

/** Column of elos_all_bots.csv holding the ratings for a game/world. */
export const resolveEloColumn = (gameId: string | null, worldId: string | null): string | null => {
  if (!gameId) {
    return null;
  }
  if (gameId === 'tic_tac_toe') {
    return worldId === 'world2' ? '4x4 TTT' : '3x3 TTT';
  }
  return GAME_ELO_COLUMNS[gameId] ?? null;
};

const MODEL_LOGOS: [RegExp, string][] = [
  [/^claude/, 'claude'],
  [/^(gpt|o\d|chatgpt)/, 'openai'],
  [/^gemini/, 'gemini'],
  [/^(deepseek|tng)/, 'deepseek'],
  [/^(devstral|ministral|mistral|magistral|codestral)/, 'mistral'],
  [/^glm/, 'zhipu'],
  [/^grok/, 'grok'],
  [/^kat_/, 'kwaipilot'],
  [/^kimi/, 'kimi'],
  [/^mimo/, 'xiaomimimo'],
  [/^minimax/, 'minimax'],
  [/^nemotron/, 'nvidia'],
  [/^qwen/, 'qwen'],
  [/^solar/, 'upstage'],
  [/^trinity/, 'arcee'],
  [/^(llama|muse)/, 'meta']
];

/** URL of the provider logo for a bot id like "gpt_5.5_high/003" (public/logos/), or null. */
export const resolveBotLogo = (botId: string): string | null => {
  const model = botId.split('/')[0];
  const logo = MODEL_LOGOS.find(([pattern]) => pattern.test(model))?.[1];
  return logo ? `logos/${logo}.svg` : null;
};

const FAMILY_LOGOS: Record<string, string> = {
  Claude: 'claude',
  GPT: 'openai',
  Gemini: 'gemini',
  DeepSeek: 'deepseek',
  Mistral: 'mistral',
  GLM: 'zhipu',
  Grok: 'grok',
  KAT: 'kwaipilot',
  Kimi: 'kimi',
  MiMo: 'xiaomimimo',
  MiniMax: 'minimax',
  Nemotron: 'nvidia',
  Qwen: 'qwen',
  Solar: 'upstage',
  Trinity: 'arcee',
  Llama: 'meta',
  Meta: 'meta'
};

/** URL of the provider logo for a model family name ("GPT", "Claude", ...), or null. */
export const resolveFamilyLogo = (family: string | null | undefined): string | null => {
  const logo = family ? FAMILY_LOGOS[family] : undefined;
  return logo ? `logos/${logo}.svg` : null;
};
