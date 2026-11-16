// Audit issue 5: the head-to-head "points" chips leave out draws, while the score percentage
// counts a draw as half a point.
import { expect, test, type Page } from '@playwright/test';
import { gotoMatchup, pointsOf } from './helpers';

const A_SCORES = new Set(['Win', 'Opp. error', 'Opp. timeout']);
const B_SCORES = new Set(['Loss', 'Error', 'Timeout']);

async function chips(page: Page) {
  const chip = page.locator('.mu-summary .mu-chip');
  await expect(chip.first()).toBeVisible();
  const texts = await chip.allInnerTexts();
  const games = Number(texts[0].match(/(\d+)\s+games?/)![1]);
  return { games, a: pointsOf(texts[1]), b: pointsOf(texts[2]) };
}

/** points recomputed from the per-game "Result for A" column: win = 1, draw = 0.5 */
async function expectedFromRows(page: Page) {
  const results = await page.locator('.mu-table tbody tr td:nth-child(3) .mu-chip').allInnerTexts();
  let a = 0;
  let b = 0;
  for (const r of results.map((t) => t.trim())) {
    if (r === 'Draw') {
      a += 0.5;
      b += 0.5;
    } else if (A_SCORES.has(r)) {
      a += 1;
    } else if (B_SCORES.has(r)) {
      b += 1;
    }
  }
  return { n: results.length, a, b };
}

test('all-draw matchup gives each side half a point per game', async ({ page }) => {
  await gotoMatchup(page, 'tourney', 'tic_tac_toe_world1', 'gpt_5.4_nano/001', 'claude_fable_5.1_high/002');
  const c = await chips(page);
  expect(c.games).toBe(20);
  expect(c.a).toBe(10);
  expect(c.b).toBe(10);
});

const MIXED: [string, string, string] = ['connect4_world1', 'gemini_2.0_flash_001/001', 'gpt_5.2/003']; // wins, draws, faults both ways

test('mixed matchup: chips match the per-game results', async ({ page }) => {
  const [game, a, b] = MIXED;
  await gotoMatchup(page, 'tourney', game, a, b);
  const c = await chips(page);
  const e = await expectedFromRows(page);
  expect(e.n).toBe(c.games);
  expect(c.a).toBe(e.a);
  expect(c.b).toBe(e.b);
  expect(c.a + c.b).toBe(c.games);
});

test('mixed matchup: swapping sides mirrors the points', async ({ page }) => {
  const [game, a, b] = MIXED;
  await gotoMatchup(page, 'tourney', game, a, b);
  const ab = await chips(page);
  await gotoMatchup(page, 'tourney', game, b, a);
  const ba = await chips(page);
  expect(ba.a).toBe(ab.b);
  expect(ba.b).toBe(ab.a);
});

test('points agree with the score percentage of the same matchup', async ({ page }) => {
  const [game, a, b] = MIXED;
  await gotoMatchup(page, 'tourney', game, a, b);
  const c = await chips(page);
  await gotoMatchup(page, 'tourney', game, a);
  const row = page.locator('.mu-opp-row').filter({ has: page.locator('.mu-opp-name[title="gpt_5.2 #3"]') });
  await expect(row).toHaveCount(1);
  const pct = Number((await row.locator('.mu-opp-pct').innerText()).replace('%', ''));
  expect(pct).toBe(Math.round((100 * c.a) / c.games));
});

test('empty matchup shows zero points', async ({ page }) => {
  await gotoMatchup(page, 'tourney', 'tic_tac_toe_world1', 'gpt_5.4_nano', 'claude_fable_5.1_high');
  const c = await chips(page);
  expect(c).toEqual({ games: 0, a: 0, b: 0 });
});
