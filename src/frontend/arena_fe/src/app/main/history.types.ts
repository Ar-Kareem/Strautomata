/** Types mirroring the files written by `src/frontend/export_history.py` (public/history/). */

export type Stage = 'quals' | 'tourney';
/** What the page lets the user pick: the two exported stages plus the "top-1 bot per model" view of the tourney. */
export type ViewStage = 'tourney' | 'models' | 'quals';

export type PlayerResult =
  | 'win'
  | 'loss'
  | 'draw'
  | 'error'
  | 'enemy_error'
  | 'timeout'
  | 'enemy_timeout'
  | 'unknown';
export type MatchReason = 'win' | 'draw' | 'error' | 'timeout' | 'unknown';

export interface HistoryIndexGame {
  id: string;
  game: string;
  world: string;
  label: string;
  column: string;
  replayable: boolean;
  stages: Partial<Record<Stage, { matches: number; bots: number }>>;
  qualified: number;
  models: number;
  /** CI rank of each model in this game (1 + models whose whole 95% CI is above; ties share a rank) */
  model_ranks?: Record<string, number>;
}

export interface HistoryIndexModel {
  id: string;
  family: string;
  bots: string[];
}

export interface HistoryIndexFamily {
  id: string;
  models: string[];
}

export interface HistoryIndex {
  generated: string;
  source: Record<string, unknown>;
  stages: Record<string, string>;
  games: HistoryIndexGame[];
  models: HistoryIndexModel[];
  families: HistoryIndexFamily[];
}

export interface RatingRow {
  rating: number | null;
  q975: number | null;
  q025: number | null;
  variance: number | null;
  n: number;
  rank: number;
}

export interface ModelRating extends RatingRow {
  top_bot: string | null;
  family: string;
}

export interface BotRating extends RatingRow {
  model: string;
  family: string;
}

export interface BotRecord {
  n: number;
  win: number;
  loss: number;
  draw: number;
  error: number;
  enemy_error: number;
  timeout: number;
  enemy_timeout: number;
  unknown: number;
  avg_moves: number;
  avg_secs: number;
}

/** [n, aWins, bWins, draws, aErrors, bErrors, aTimeouts, bTimeouts] for the pair "a|b" with a < b. */
export type PairwiseCounts = [number, number, number, number, number, number, number, number];

export interface QualsRanking {
  bot: string;
  rating: number | null;
  q975: number | null;
  q025: number | null;
  n: number;
  rank: number;
  qualified: boolean;
}

export interface StageSummary {
  bots: string[];
  records: Record<string, BotRecord>;
  pairwise: Record<string, PairwiseCounts>;
  n_matches: number;
  config: Record<string, unknown> | null;
  qualified?: string[];
  rankings?: Record<string, QualsRanking[]>;
}

export interface GameSummary {
  game: string;
  world: string;
  label: string;
  column: string;
  replayable: boolean;
  rating_system: string | null;
  models: Record<string, ModelRating>;
  bots: Record<string, BotRating>;
  stages: Partial<Record<Stage, StageSummary>>;
}

export interface MatchesTable {
  game: string;
  world: string;
  stage: Stage;
  bots: string[];
  columns: string[];
  result_codes: Record<PlayerResult, number>;
  reason_codes: Record<MatchReason, number>;
  rows: number[][];
}

/** One decoded row of matches.json. */
export interface MatchRow {
  index: number;
  a: string;
  b: string;
  resA: PlayerResult;
  resB: PlayerResult;
  reason: MatchReason;
  winner: 0 | 1 | null;
  moveCount: number | null;
  secs: number | null;
  seed: number | null;
  /** slot of this match among the replays of its bot pair, or -1 when no move list was exported */
  detail: number;
}

export interface FailedMove {
  index: number;
  player: number | null;
  action: unknown;
  why: string;
}

export interface MatchDetail {
  i: number;
  a: string;
  b: string;
  seed: number | null;
  reason: MatchReason;
  winner: 0 | 1 | null;
  result: [PlayerResult, PlayerResult];
  move_count: number | null;
  secs: number | null;
  moves: [number, unknown][];
  think: (number | null)[];
  exception: string | null;
  timeout_hit: unknown;
  returns: unknown;
  other: unknown;
  started: string | null;
}

export interface ReplayFrame {
  state: unknown;
  player: number | null;
}

export interface ReplayResult {
  ok: boolean;
  why?: string;
  frames: ReplayFrame[];
  applied: number;
  total: number;
  failed_move?: FailedMove | null;
  final?: Record<string, unknown> | null;
  done?: boolean;
}

/** A row of the leaderboard table (either a bot or a model). */
export interface LeaderboardRow {
  id: string;
  label: string;
  sub: string | null;
  family: string;
  rating: number | null;
  q025: number | null;
  q975: number | null;
  rank: number;
  n: number;
  record: BotRecord | null;
  qualified: boolean | null;
  /** bot took part in qualification but did not reach this stage */
  dnq: boolean;
}

/** Head-to-head aggregate for one opponent of the selected bot. */
export interface OpponentSummary {
  id: string;
  label: string;
  family: string;
  rank: number | null;
  n: number;
  wins: number;
  losses: number;
  draws: number;
  ownErrors: number;
  ownTimeouts: number;
  oppErrors: number;
  oppTimeouts: number;
  score: number; // 0..1 share of points for the selected bot
}

/** history/models/<model>.json: one model across every game */
export interface ModelStanding {
  rank: number;
  rating: number | null;
  q025: number | null;
  q975: number | null;
  n: number;
}

export interface ModelAutomaton {
  bot: string;
  quals: ModelStanding | null;
  quals_record: BotRecord | null;
  qualified: boolean;
  tourney: ModelStanding | null;
  tourney_record: BotRecord | null;
}

export interface ModelGame {
  id: string;
  rating: ModelStanding | null;
  top_bot: string | null;
  /** rated models in this game */
  models: number;
  /** automata in this game's tournament */
  tourney_bots: number;
  automata: ModelAutomaton[];
}

export interface ModelPage {
  model: string;
  family: string;
  games: ModelGame[];
}

/** public/leaderboard_models.csv: each model's Elo per game column and the median over games */
export interface OverallBoard {
  columns: string[];
  rows: { model: string; median: number; byGame: Record<string, number | null> }[];
}

/** history/strategies/<game>/<model>.json: each automaton's strategy text, null when it gave none */
export type StrategyMap = Record<string, string | null>;
