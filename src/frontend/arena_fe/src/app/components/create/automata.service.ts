import { Injectable, inject } from '@angular/core';
import { ArenaMatchRunner } from '../../controllers/arena-match-runner';
import { HistoryService } from '../matches/history.service';
import { modelOf } from '../matches/history-format';
import { MatchLane, MatchLanePool } from './match-lane-pool';

export type FullMatchReason = 'win' | 'draw' | 'error' | 'illegal' | 'timeout' | 'setup' | 'hung';

export interface FullMatchResult {
  winner: 0 | 1 | null;
  reason: FullMatchReason;
  culprit: number | null;
  culprit_name?: string;
  error?: string | null;
  traceback?: string | null;
  moves: number;
  /** [player, engine move (string, tuple-as-list or action id), think seconds] */
  history?: [number, unknown, number][];
  secs: number;
  final?: Record<string, unknown> | null;
}

export interface CompileResult {
  ok: boolean;
  /** which step failed: the code itself, the runtime (engine import), or the first call on the initial board */
  stage?: 'compile' | 'runtime' | 'smoke';
  error?: string;
  traceback?: string;
  /** 1-based line in the user's code where the error originated, when known */
  line?: number | null;
  /** on success: the move returned on the initial board and how long it took */
  move?: string;
  secs?: number;
}

export interface Opponent {
  id: string;
  model: string;
  family: string;
  rating: number;
  /** 95% interval bounds from the tournament bootstrap (fall back to the rating when missing) */
  low: number;
  high: number;
  rank: number;
}

export const USER_BOT = 'user';
/** slack on top of the move time limit before a lane is assumed hung (engine step + observation overhead) */
const MOVE_GRACE_MS = 1_000;
/** allowance before the first move: game construction and, on first use, fetching the opponent's code */
const MATCH_SETUP_GRACE_MS = 10_000;
/** wall-clock guard for loading the code itself (module-level statements run here; a loop there hangs) */
const COMPILE_WALL_LIMIT_MS = 60_000;
/** slack added to the move time limit for the initial-board call, to cover game construction */
const SMOKE_GRACE_MS = 1_000;

const hungResult = (
  moveTimeout: number,
  history: [number, unknown, number][],
  player: number | null,
  names: [string, string]
): FullMatchResult => {
  const who = player === null ? 'A policy' : player === 0 ? `${names[0]} (first)` : `${names[1]} (second)`;
  const moves = history.length;
  return {
    winner: player === null ? null : ((1 - player) as 0 | 1),
    reason: 'hung',
    culprit: player,
    culprit_name: player === null ? undefined : names[player],
    error: `${who} did not return a move within ${moveTimeout}s at move ${moves + 1}, so it loses; its Python runtime was restarted. That policy is probably stuck in a loop.`,
    moves,
    history, // every move that completed before the hang, streamed out by the heartbeat
    secs: history.reduce((sum, [, , dt]) => sum + (typeof dt === 'number' ? dt : 0), 0)
  };
};

@Injectable({ providedIn: 'root' })
export class AutomataService {
  private readonly runner = inject(ArenaMatchRunner);
  private readonly history = inject(HistoryService);
  private readonly pool = new MatchLanePool();

  private toAppUrl(path: string): string {
    return new URL(path.replace(/^\/+/, ''), document.baseURI).toString();
  }

  /** Tournament opponents for a game, strongest first, with their exported ratings. */
  async loadOpponents(gameKey: string): Promise<Opponent[]> {
    const summary = await this.history.loadSummary(gameKey);
    const list: Opponent[] = [];
    for (const [id, row] of Object.entries(summary.bots)) {
      if (row.rating === null || id === 'random') {
        continue;
      }
      list.push({
        id,
        model: modelOf(id),
        family: row.family,
        rating: row.rating,
        low: row.q025 ?? row.rating,
        high: row.q975 ?? row.rating,
        rank: row.rank
      });
    }
    list.sort((a, b) => b.rating - a.rating || a.id.localeCompare(b.id));
    return list;
  }

  async loadBotCode(gameId: string, worldId: string, botId: string): Promise<string> {
    const response = await fetch(this.toAppUrl(`py/game_arena/${gameId}/examples/${worldId}/${botId}/2.python_code.py`));
    if (!response.ok) {
      throw new Error(`Could not load the code of ${botId}`);
    }
    return response.text();
  }

  async loadPrompt(gameId: string, worldId: string): Promise<string> {
    const config = await this.history.loadGameConfig(gameId, worldId);
    const result = await this.runner.getGamePrompt<{ prompt?: string; error?: string } | null>(gameId, worldId, config);
    if (!result || result.error) {
      throw new Error(result?.error ?? 'No prompt available');
    }
    return result.prompt ?? '';
  }

  /** race a runtime call against a wall-clock limit; on timeout stop the main runtime and return `onTimeout` */
  private async guarded<T>(call: Promise<T>, limitMs: number, onTimeout: () => T): Promise<T> {
    let timer: number | null = null;
    const guard = new Promise<T>((resolve) => {
      timer = window.setTimeout(() => {
        resolve(onTimeout()); // first, so the race reports the timeout rather than the dropped request
        this.runner.restartRuntime();
      }, limitMs);
    });
    try {
      return await Promise.race([call, guard]);
    } finally {
      if (timer !== null) {
        window.clearTimeout(timer);
      }
    }
  }

  /**
   * Compile the user's code in the main runtime, then call the policy once on the initial board.
   * The initial-board call is guarded by the move time limit (plus a second of slack for game
   * construction); loading the module has its own generous limit since it should be instant.
   */
  async compile(gameId: string, worldId: string, code: string, moveTimeout: number): Promise<CompileResult> {
    const config = await this.history.loadGameConfig(gameId, worldId);
    const loaded = await this.guarded(
      this.runner
        .setUserPolicy<CompileResult | null>(gameId, worldId, code, config)
        .then((result) => result ?? { ok: false, stage: 'compile' as const, error: 'Empty response from the runtime' }),
      COMPILE_WALL_LIMIT_MS,
      () => ({
        ok: false,
        stage: 'compile' as const,
        error: `Loading your code did not finish within ${COMPILE_WALL_LIMIT_MS / 1000}s; it was stopped. Module-level code is probably stuck in a loop.`
      })
    );
    if (!loaded.ok) {
      return loaded;
    }
    const limitMs = Math.max(1, moveTimeout) * 1000 + SMOKE_GRACE_MS;
    return this.guarded(
      this.runner
        .smokeTestUserPolicy<CompileResult | null>(gameId, worldId, config, moveTimeout)
        .then((result) => result ?? { ok: false, stage: 'smoke' as const, error: 'Empty response from the runtime' }),
      limitMs,
      () => ({
        ok: false,
        stage: 'smoke' as const,
        error: `Your policy did not return within the move time limit of ${moveTimeout}s on the initial board, so it was stopped. It is probably stuck in a loop.`
      })
    );
  }

  // ---- parallel match lanes ----------------------------------------------------------------

  /** Make sure exactly `count` lanes exist and return them (existing lanes keep their loaded code). */
  ensureLanes(count: number): MatchLane[] {
    return this.pool.setSize(count);
  }

  /**
   * Load the runtime and the user's code into a lane (no-op if that exact code is already loaded).
   * A runtime that fails to come up (e.g. the OpenSpiel module fails to load while many runtimes
   * start at once) is restarted and retried; errors in the user's code are not retried.
   */
  async prepareLane(lane: MatchLane, gameId: string, worldId: string, code: string): Promise<void> {
    const key = `${gameId}/${worldId}\n${code}`;
    if (lane.prepared === key) {
      return;
    }
    const config = await this.history.loadGameConfig(gameId, worldId);
    const attempts = 3;
    let result: CompileResult | null = null;
    for (let attempt = 1; ; attempt += 1) {
      try {
        await lane.request<void>({ type: 'ensureRunner' });
        result = await lane.request<CompileResult | null>({ type: 'setUserPolicy', gameId, worldId, code, config, smoke: false });
        break;
      } catch (err) {
        if (attempt >= attempts) {
          throw err;
        }
        console.warn(`Match runtime ${lane.index + 1} failed to start (attempt ${attempt}), restarting`, err);
        lane.restart();
        await new Promise((resolve) => setTimeout(resolve, 600 * attempt));
      }
    }
    if (!result?.ok) {
      throw new Error(result?.error ?? 'Could not load your code into the match runtime');
    }
    lane.prepared = key;
  }

  /**
   * Play one whole match on a lane. The runtime reports before every move; if no move completes
   * within the move time limit (plus a little grace) the lane is stopped and the player who was
   * on move loses by "hung". Match length itself is unlimited, so long games are fine.
   */
  async playOnLane(
    lane: MatchLane,
    gameId: string,
    worldId: string,
    botA: string,
    botB: string,
    seed: number,
    moveTimeout: number
  ): Promise<FullMatchResult> {
    const config = await this.history.loadGameConfig(gameId, worldId);
    const perMoveMs = Math.max(1, moveTimeout) * 1000 + MOVE_GRACE_MS;
    let timer: number | null = null;
    const history: [number, unknown, number][] = [];
    let player: number | null = null;
    let onHang: (() => void) | null = null;
    let hung = false;
    const arm = (ms: number) => {
      if (timer !== null) {
        window.clearTimeout(timer);
      }
      timer = window.setTimeout(() => onHang?.(), ms);
    };
    const guard = new Promise<FullMatchResult>((resolve) => {
      onHang = () => {
        hung = true;
        // settle the lane before reporting, so the caller sees whether its code is still loaded
        void lane.stop().then(() => resolve(hungResult(moveTimeout, history, player, [botA, botB])));
      };
    });
    arm(perMoveMs + MATCH_SETUP_GRACE_MS);
    try {
      const played = lane
        .request<FullMatchResult | null>(
          { type: 'playFullMatch', payload: { gameId, worldId, config, botA, botB, seed, moveTimeout } },
          (_moves, p, last) => {
            if (last) {
              history.push(last);
            }
            player = p;
            arm(perMoveMs);
          }
        )
        .then((result) => {
          if (!result) {
            throw new Error('Empty response from the match runtime');
          }
          return result;
        })
        // the interrupted match rejects before the lane has settled: report the hang instead
        .catch((err) => (hung ? guard : Promise.reject(err)));
      return await Promise.race([played, guard]);
    } finally {
      if (timer !== null) {
        window.clearTimeout(timer);
      }
    }
  }

  /** Kill every lane (and any match in flight). */
  disposeLanes(): void {
    this.pool.dispose();
  }

  warmRuntime(): void {
    this.runner.warmRuntime();
  }
}
