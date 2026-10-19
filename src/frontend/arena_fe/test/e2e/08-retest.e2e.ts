// v1.9 wide retest: Backgammon H/L replay, stale game data on Create, runtime errors scored as
// user faults, replay move order and move list keyboard access, Human vs Human board labels.
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { expect, test, type Page } from '@playwright/test';
import {
  RUNTIME_TIMEOUT, TTT_FIRST_EMPTY, board, compileAndWait, create, gotoCreate, gotoMatchup, gotoPlay, selectGame, setCode,
  waitForQualification
} from './helpers';

test.describe.configure({ timeout: RUNTIME_TIMEOUT * 3 });

/** answers in Backgammon's documented H/L format, which the engine parses against the current dice */
const BACKGAMMON_HL = String.raw`import re
def policy(state, _debug_legal_moves, **kw):
    d = state["dice"]
    for m in _debug_legal_moves:
        toks = str(m).split(" - ")[-1].split()
        if len(toks) != 2 or not all(re.fullmatch(r"\d+/\d+", t) for t in toks):
            continue
        (f1, t1), (f2, t2) = [tuple(int(x) for x in t.split("/")) for t in toks]
        if f1 - t1 == d[1]:
            return f"H:A{f1-1},A{f2-1}"
        if f1 - t1 == d[0]:
            return f"L:A{f1-1},A{f2-1}"
    return _debug_legal_moves[0]
`;

/** wins its own games but breaks the random baseline, so every qualification game is a runtime error */
const BREAKS_BASELINE = `import random as _r
_r.choice = lambda seq: (_ for _ in ()).throw(RuntimeError("baseline sabotaged"))
${TTT_FIRST_EMPTY}`;

async function startRun(page: Page, game: string, code: string): Promise<void> {
  await gotoCreate(page);
  await selectGame(page, game);
  await create(page).lanes.fill('2');
  await create(page).lanes.dispatchEvent('change');
  await setCode(page, code);
  await compileAndWait(page);
  await create(page).run.click();
}

test('a fresh Backgammon match with H/L moves replays to the end', async ({ page }) => {
  await startRun(page, 'Backgammon', BACKGAMMON_HL);
  await waitForQualification(page);
  const proceed = page.getByRole('button', { name: 'Proceed to tournament' });
  if (await proceed.isVisible()) {
    await proceed.click();
  }
  const finished = create(page).heatCells.and(page.locator(':is([data-outcome="win"],[data-outcome="loss"],[data-outcome="draw"])'));
  await expect(finished.first()).toBeVisible({ timeout: RUNTIME_TIMEOUT });
  await finished.first().click();
  const replay = page.locator('matches-replay');
  await expect(replay.locator('.rp-turn')).toBeVisible({ timeout: 60_000 });
  await expect(replay.locator('.rp-move-flag')).toHaveCount(0);
  await expect(replay.locator('.rp-move code', { hasText: /^[HL]:/ }).first()).toBeVisible();
  const [, turn, last] = (await replay.locator('.rp-turn').innerText()).match(/turn\s+(\d+)\s*\/\s*(\d+)/)!;
  expect(Number(turn)).toBe(0);
  expect(Number(last), 'every recorded move replays').toBe(await replay.locator('.rp-move').count());

  // the opening line names whoever actually made move 1 (Backgammon's first roll decides it)
  const firstSeat = (await replay.locator('.rp-move').first().locator('.rp-move-player').innerText()).trim();
  const firstName = (await replay.locator('.rp-move').first().locator('.rp-move-player').getAttribute('title'))!;
  expect(['A', 'B']).toContain(firstSeat);
  await expect(replay.locator('.rp-current')).toContainText(`${firstName} move`);
});

test('a runtime error is shown as an error, not as the user\'s fault', async ({ page }) => {
  await startRun(page, 'Tic Tac Toe (3x3)', BREAKS_BASELINE);
  const outcomes = await waitForQualification(page);
  expect(outcomes, `outcomes: ${outcomes}`).toEqual(Array(10).fill('error'));
  await expect(create(page).qualCells.first()).toContainText('Error');
  await expect(page.locator('.cr-qual-cell', { hasText: 'Your fault' })).toHaveCount(0);
  await expect(page.locator('.cr-error', { hasText: 'not counted' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Proceed to tournament' })).toHaveCount(0);
});

test('a late opponent list for the previous game is dropped', async ({ page }) => {
  await page.route('**/history/games/tic_tac_toe_world1/summary.json', async (route) => {
    await new Promise((r) => setTimeout(r, 4_000));
    await route.continue();
  });
  await gotoCreate(page);
  await selectGame(page, 'Tic Tac Toe (3x3)');
  await selectGame(page, 'Chess');
  const options = create(page).example.locator('option');
  await expect(options.nth(1)).toBeAttached({ timeout: 30_000 });
  await page.waitForTimeout(6_000); // past the delayed Tic Tac Toe response
  const chess = Object.keys(JSON.parse(readFileSync(join(__dirname, '../../public/history/games/chess_worlduci1/summary.json'), 'utf8')).bots);
  const ttt = Object.keys(JSON.parse(readFileSync(join(__dirname, '../../public/history/games/tic_tac_toe_world1/summary.json'), 'utf8')).bots);
  const shown = (await options.evaluateAll((els) => els.map((e) => (e as HTMLOptionElement).value))).filter(Boolean);
  expect(shown.length).toBeGreaterThan(0);
  expect(shown.filter((id) => !chess.includes(id)), 'only Chess opponents').toEqual([]);
  expect(chess.some((id) => !ttt.includes(id) && shown.includes(id))).toBe(true);
});

test('the open prompt follows the selected game', async ({ page }) => {
  await gotoCreate(page);
  await selectGame(page, 'Tic Tac Toe (3x3)');
  await page.getByRole('button', { name: 'Show prompt' }).click();
  await selectGame(page, 'Chess'); // while the Tic Tac Toe prompt is still loading
  const prompt = page.locator('.cr-prompt pre');
  await expect(prompt).toContainText(/chess/i, { timeout: RUNTIME_TIMEOUT });
  await page.waitForTimeout(3_000);
  await expect(prompt).toContainText(/chess/i);
  await expect(prompt).not.toContainText(/tic.?tac.?toe/i);
});

test('replay moves can be chosen with the keyboard', async ({ page }) => {
  await gotoMatchup(page, 'tourney', 'tic_tac_toe_world1', 'gpt_5.4_nano/001', 'claude_fable_5.1_high/002');
  await page.locator('.mu-table').getByRole('button', { name: /replay/i }).first().click();
  const replay = page.locator('matches-replay');
  await expect(replay.locator('.rp-turn')).toBeVisible({ timeout: 60_000 });
  const second = replay.locator('.rp-move').nth(1);
  await second.focus();
  await expect(second).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(replay.locator('.rp-turn')).toHaveText(/turn 2 \//);
  await expect(second).toHaveAttribute('aria-current', 'step');
});

test('Human vs Human Connect 4 names the side to move', async ({ page }) => {
  await gotoPlay(page, 'connect4', 'world1', 'Human vs Human');
  const label = page.locator('arena-output .connect4-head p');
  await expect(label).toHaveText(/Human A/);
  await board(page, '.connect4-cell').first().click();
  await expect(label).toHaveText(/Human B/);
});
