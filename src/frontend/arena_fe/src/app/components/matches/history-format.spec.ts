// @ts-expect-error node builtin typings are not installed in this project; vitest runs in node
import { existsSync, readFileSync } from 'node:fs';
// @ts-expect-error node builtin typings are not installed in this project; vitest runs in node
import { resolve } from 'node:path';
// @ts-expect-error node builtin typings are not installed in this project; vitest runs in node
import { gunzipSync } from 'node:zlib';
declare const process: { cwd(): string };
import { describe, expect, it } from 'vitest';
import type { GameSummary, MatchesTable } from '@main/history.types';
import { decodeMatchesTable, pairKey, pairScore, safeBotName } from './history-format';
import { ReplayFile } from './replay-format';

const HISTORY = resolve(process.cwd(), 'public/history');
const readJson = <T>(path: string): T => JSON.parse(readFileSync(resolve(HISTORY, path), 'utf8')) as T;

describe('history export decoding (real exported data)', () => {
  const summary = readJson<GameSummary>('games/nim_world1/summary.json');
  const table = readJson<MatchesTable>('games/nim_world1/tourney/matches.json');
  const rows = decodeMatchesTable(table);

  it('decodes every row with known bots and outcomes', () => {
    expect(rows.length).toBe(table.rows.length);
    expect(rows.length).toBe(summary.stages.tourney!.n_matches);
    const bots = new Set(table.bots);
    for (const row of rows) {
      expect(bots.has(row.a)).toBe(true);
      expect(bots.has(row.b)).toBe(true);
      expect(row.reason).not.toBe('unknown');
    }
  });

  it('per-bot records in summary.json match the decoded rows', () => {
    const records = summary.stages.tourney!.records;
    const counts = new Map<string, { win: number; loss: number; draw: number; error: number; timeout: number; n: number }>();
    for (const row of rows) {
      for (const [bot, res] of [[row.a, row.resA], [row.b, row.resB]] as const) {
        const c = counts.get(bot) ?? { win: 0, loss: 0, draw: 0, error: 0, timeout: 0, n: 0 };
        c.n += 1;
        if (res === 'win') c.win += 1;
        if (res === 'loss') c.loss += 1;
        if (res === 'draw') c.draw += 1;
        if (res === 'error') c.error += 1;
        if (res === 'timeout') c.timeout += 1;
        counts.set(bot, c);
      }
    }
    for (const [bot, rec] of Object.entries(records)) {
      const c = counts.get(bot)!;
      expect(c.n).toBe(rec.n);
      expect(c.win).toBe(rec.win);
      expect(c.loss).toBe(rec.loss);
      expect(c.draw).toBe(rec.draw);
      expect(c.error).toBe(rec.error);
      expect(c.timeout).toBe(rec.timeout);
    }
  });

  it('pairwise table agrees with the decoded rows and pairScore', () => {
    const pairwise = summary.stages.tourney!.pairwise;
    const a = table.bots[0];
    const b = table.bots[1];
    const mine = rows.filter((r) => pairKey(r.a, r.b) === pairKey(a, b));
    const counts = pairwise[pairKey(a, b)];
    expect(counts[0]).toBe(mine.length);
    const { share } = pairScore(pairwise, a, b);
    let points = 0;
    for (const r of mine) {
      const my = r.a === a ? r.resA : r.resB;
      if (my === 'win' || my === 'enemy_error' || my === 'enemy_timeout') points += 1;
      if (my === 'draw') points += 0.5;
    }
    expect(share).toBeCloseTo(points / mine.length, 6);
  });

  // replays/ is gitignored and only present after a local export
  it.skipIf(!existsSync(resolve(HISTORY, 'replays/nim_world1/tourney')))('every row decodes to its replay', () => {
    const vocab = readJson<unknown[]>('replays/nim_world1/tourney/vocab.json');
    const cache = new Map<string, ReplayFile>();
    expect(rows.every((r) => r.detail >= 0)).toBe(true);
    for (const row of rows.slice(0, 2000)) {
      const lo = row.a <= row.b ? row.a : row.b;
      const hi = row.a <= row.b ? row.b : row.a;
      let file = cache.get(lo);
      if (!file) {
        const raw = readFileSync(resolve(HISTORY, `replays/nim_world1/tourney/${safeBotName(lo)}.rpl`));
        file = new ReplayFile(new Uint8Array(gunzipSync(raw)), vocab);
        cache.set(lo, file);
      }
      const entry = file.entry(hi, row.detail);
      expect(entry).not.toBeNull();
      expect(entry!.think.length).toBe(entry!.moves.length);
      for (const [, move] of entry!.moves) {
        expect(move).not.toBeNull();
      }
    }
  });
});
