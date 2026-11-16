// Audit issue 1: policies' moves are converted back into engine objects before get_move, so
// valid policies fail to compile and the random baseline "faults" in qualification.
import { expect, test } from '@playwright/test';
import {
  FIRST_LEGAL, NIM_AUDIT, RUNTIME_TIMEOUT, TTT_CONSTANT, TTT_FIRST_EMPTY,
  compileAndWait, create, gotoCreate, selectGame, setCode, waitForQualification
} from './helpers';

test.describe.configure({ timeout: RUNTIME_TIMEOUT * 2 });

const VALID: { game: string; code: string }[] = [
  { game: 'Tic Tac Toe (3x3)', code: TTT_FIRST_EMPTY },
  { game: 'Tic Tac Toe (4x4)', code: TTT_FIRST_EMPTY },
  { game: 'Tic Tac Toe 3D', code: FIRST_LEGAL },
  { game: 'Battleships', code: FIRST_LEGAL },
  { game: 'Mancala', code: FIRST_LEGAL },
  { game: 'Clobber', code: FIRST_LEGAL },
  { game: 'Nim', code: NIM_AUDIT },
  { game: 'Dots and Boxes', code: FIRST_LEGAL },
  { game: 'Connect 4', code: FIRST_LEGAL } // control: integer actions always worked
];

test.describe('valid policies compile', () => {
  for (const { game, code } of VALID) {
    test(game, async ({ page }) => {
      await gotoCreate(page);
      await selectGame(page, game);
      await setCode(page, code);
      await compileAndWait(page);
      const c = create(page);
      await expect(c.fault).toHaveCount(0);
      await expect(c.ok).toBeVisible();
      await expect(c.run).toBeEnabled();
    });
  }
});

test.describe('qualification against random', () => {
  test.beforeEach(async ({ page }) => {
    await gotoCreate(page);
    await selectGame(page, 'Tic Tac Toe (3x3)');
    await create(page).lanes.fill('2');
    await create(page).lanes.dispatchEvent('change');
  });

  test('a legal policy never sees the baseline fault', async ({ page }) => {
    await setCode(page, TTT_FIRST_EMPTY);
    await compileAndWait(page);
    await create(page).run.click();
    const outcomes = await waitForQualification(page);
    expect(outcomes.filter((o) => o === 'gift'), `outcomes: ${outcomes}`).toHaveLength(0);
    expect(outcomes.filter((o) => o === 'fault'), `outcomes: ${outcomes}`).toHaveLength(0);
  });

  test('a policy that replays an occupied cell is faulted, never gifted', async ({ page }) => {
    await setCode(page, TTT_CONSTANT);
    await compileAndWait(page);
    await create(page).run.click();
    const outcomes = await waitForQualification(page);
    expect(outcomes, 'every game ends on the user replaying (0, 0)').toEqual(Array(10).fill('fault'));
  });

  test('qualification moves are more than a single ply', async ({ page }) => {
    await setCode(page, TTT_FIRST_EMPTY);
    await compileAndWait(page);
    await create(page).run.click();
    await waitForQualification(page);
    const moves = await create(page).qualCells.locator('.cr-qual-meta').allInnerTexts();
    const counts = moves.map((t) => Number(t.match(/(\d+)\s*mv/)?.[1] ?? 0));
    expect(Math.min(...counts), `move counts: ${counts}`).toBeGreaterThanOrEqual(5); // 3x3 needs >= 5 plies to end
  });
});
