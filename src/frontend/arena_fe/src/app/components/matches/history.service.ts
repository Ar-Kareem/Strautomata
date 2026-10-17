import { Injectable, inject } from '@angular/core';
import { ArenaMatchRunner } from '../../controllers/arena-match-runner';
import type {
  GameSummary,
  HistoryIndex,
  MatchDetail,
  MatchRow,
  MatchesTable,
  ModelPage,
  OverallBoard,
  ReplayResult,
  StrategyMap,
  Stage
} from '@main/history.types';
import { decodeMatchesTable, safeBotName } from './history-format';
import { ReplayFile, gunzip } from './replay-format';

type GameWorldsFile = {
  configs?: Record<string, { gameId: string; worldId: string; config: string | null }>;
};

/**
 * Loads the static files exported by `export_history.py` (public/history/) with an in-memory
 * cache, decodes the columnar match table and binary replay files, and replays move lists
 * through the Pyodide engine.
 */
@Injectable({ providedIn: 'root' })
export class HistoryService {
  private readonly runner = inject(ArenaMatchRunner);
  private readonly cache = new Map<string, Promise<unknown>>();
  private readonly decodedRows = new Map<MatchesTable, MatchRow[]>();
  private gameWorlds: Promise<GameWorldsFile> | null = null;

  private toAppUrl(path: string): string {
    return new URL(path.replace(/^\/+/, ''), document.baseURI).toString();
  }

  private cached<T>(key: string, load: () => Promise<T>): Promise<T> {
    const hit = this.cache.get(key);
    if (hit) {
      return hit as Promise<T>;
    }
    const promise = load();
    promise.catch(() => this.cache.delete(key));
    this.cache.set(key, promise);
    return promise;
  }

  private fetchOk(path: string): Promise<Response> {
    return fetch(this.toAppUrl(path)).then((response) => {
      if (!response.ok) {
        throw new Error(`${response.status} while loading ${path}`);
      }
      return response;
    });
  }

  private fetchJson<T>(path: string): Promise<T> {
    return this.cached(path, async () => (await (await this.fetchOk(path)).json()) as T);
  }

  loadIndex(): Promise<HistoryIndex> {
    return this.fetchJson<HistoryIndex>('history/index.json');
  }

  loadSummary(gameKey: string): Promise<GameSummary> {
    return this.fetchJson<GameSummary>(`history/games/${encodeURIComponent(gameKey)}/summary.json`);
  }

  loadModel(model: string): Promise<ModelPage> {
    return this.fetchJson<ModelPage>(`history/models/${encodeURIComponent(model)}.json`);
  }

  loadStrategies(gameKey: string, model: string): Promise<StrategyMap> {
    return this.fetchJson<StrategyMap>(`history/strategies/${encodeURIComponent(gameKey)}/${encodeURIComponent(model)}.json`);
  }

  /** An automaton's source, as deployed with the site (py/game_arena/<game>/examples/<world>/<bot>/). */
  loadBotCode(gameId: string, worldId: string, bot: string): Promise<string> {
    const path = `py/game_arena/${gameId}/examples/${worldId}/${bot}/2.python_code.py`;
    return this.cached(path, async () => (await this.fetchOk(path)).text());
  }

  /** Overall leaderboard (public/leaderboard_models.csv): rows without a median are dropped. */
  loadOverall(): Promise<OverallBoard> {
    return this.cached('leaderboard_models.csv', async () => {
      const [header, ...lines] = (await (await this.fetchOk('leaderboard_models.csv')).text()).trim().split(/\r?\n/);
      const names = header.split(',');
      const median = names.indexOf('Median ELO');
      const columns = names.slice(1).filter((_, i) => i + 1 !== median);
      const rows = lines.map((line) => {
        const cells = line.split(',');
        const value = (i: number): number | null => (cells[i] === undefined || cells[i] === '' ? null : Number(cells[i]));
        return {
          model: cells[0],
          median: value(median) ?? NaN,
          byGame: Object.fromEntries(columns.map((column) => [column, value(names.indexOf(column))]))
        };
      });
      return { columns, rows: rows.filter((row) => !Number.isNaN(row.median)) };
    });
  }

  loadMatches(gameKey: string, stage: Stage): Promise<MatchesTable> {
    return this.fetchJson<MatchesTable>(`history/games/${encodeURIComponent(gameKey)}/${stage}/matches.json`);
  }

  /** All matches of `bot` against bots sorting after it, from replays/<game>/<stage>/<bot>.rpl */
  loadReplayFile(gameKey: string, stage: Stage, bot: string): Promise<ReplayFile> {
    const dir = `history/replays/${encodeURIComponent(gameKey)}/${stage}`;
    const path = `${dir}/${encodeURIComponent(safeBotName(bot))}.rpl`;
    return this.cached(path, async () => {
      try {
        const [vocab, response] = await Promise.all([this.fetchJson<unknown[]>(`${dir}/vocab.json`), this.fetchOk(path)]);
        return new ReplayFile(await gunzip(new Uint8Array(await response.arrayBuffer())), vocab);
      } catch (err) {
        console.warn(`Replay data unavailable (${path}); re-run export_history.py.`, err);
        throw new Error('Replay data is not available in this build.');
      }
    });
  }

  /** Detail entry for a decoded row, or null when the exporter did not keep its move list. */
  async loadDetail(gameKey: string, stage: Stage, row: MatchRow): Promise<MatchDetail | null> {
    if (row.detail < 0) {
      return null;
    }
    const lo = row.a <= row.b ? row.a : row.b;
    const hi = row.a <= row.b ? row.b : row.a;
    const file = await this.loadReplayFile(gameKey, stage, lo);
    const entry = file.entry(hi, row.detail);
    if (!entry) {
      return null;
    }
    return {
      i: row.index,
      a: row.a,
      b: row.b,
      seed: row.seed,
      reason: row.reason,
      winner: row.winner,
      result: [row.resA, row.resB],
      move_count: row.moveCount,
      secs: row.secs,
      moves: entry.moves,
      think: entry.think,
      exception: entry.exception ?? null,
      timeout_hit: entry.timeout_hit ?? null,
      returns: entry.returns ?? null,
      other: entry.other ?? null,
      started: null
    };
  }

  decodeRows(table: MatchesTable): MatchRow[] {
    const cached = this.decodedRows.get(table);
    if (cached) {
      return cached;
    }
    const rows = decodeMatchesTable(table);
    this.decodedRows.set(table, rows);
    return rows;
  }

  async loadGameConfig(gameId: string, worldId: string): Promise<Record<string, unknown>> {
    if (!this.gameWorlds) {
      this.gameWorlds = fetch(this.toAppUrl('py/game_worlds.json')).then(async (response) => {
        if (!response.ok) {
          throw new Error('Failed to load game_worlds.json');
        }
        return (await response.json()) as GameWorldsFile;
      });
      this.gameWorlds.catch(() => {
        this.gameWorlds = null;
      });
    }
    const worlds = await this.gameWorlds;
    const entry = worlds.configs?.[`${gameId}/${worldId}`];
    if (!entry?.config) {
      return {};
    }
    try {
      const parsed = JSON.parse(entry.config) as unknown;
      return parsed && typeof parsed === 'object' ? (parsed as Record<string, unknown>) : {};
    } catch {
      return {};
    }
  }

  warmRuntime(): void {
    this.runner.warmRuntime();
  }

  /** Replay a recorded move list through the engine running in the Pyodide worker. */
  async replay(gameId: string, worldId: string, seed: number | null, moves: [number, unknown][]): Promise<ReplayResult> {
    const config = await this.loadGameConfig(gameId, worldId);
    const result = await this.runner.replayMoves<ReplayResult | null>({
      gameId,
      worldId,
      config,
      seed,
      moves
    });
    if (!result) {
      return { ok: false, why: 'Empty response from the engine', frames: [], applied: 0, total: moves.length };
    }
    return result;
  }
}
