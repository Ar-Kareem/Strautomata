// Audit issue 2: NumPy integer moves are recorded as strings ("0"), so the replay of a match the
// user just played flags the first move illegal and stays at turn 0/0.
import { expect, test, type Page } from '@playwright/test';
import { RUNTIME_TIMEOUT, TTT_FIRST_EMPTY, TTT_NUMPY, compileAndWait, create, gotoCreate, selectGame, setCode, waitForQualification } from './helpers';

test.describe.configure({ timeout: RUNTIME_TIMEOUT * 3 });

async function openFirstFinishedReplay(page: Page, code: string) {
  await gotoCreate(page);
  await selectGame(page, 'Tic Tac Toe (3x3)');
  await create(page).lanes.fill('2');
  await create(page).lanes.dispatchEvent('change');
  await setCode(page, code);
  await compileAndWait(page);
  await create(page).run.click();
  await waitForQualification(page);
  const proceed = page.getByRole('button', { name: 'Proceed to tournament' });
  if (await proceed.isVisible()) {
    await proceed.click();
  }
  const finished = create(page).heatCells.and(page.locator(':is([data-outcome="win"],[data-outcome="loss"],[data-outcome="draw"])'));
  await expect(finished.first()).toBeVisible({ timeout: RUNTIME_TIMEOUT });
  await finished.first().click();
  const replay = page.locator('matches-replay');
  await expect(replay).toBeVisible();
  await expect(replay.locator('.rp-turn')).toBeVisible({ timeout: 60_000 });
  return replay;
}

for (const [name, code] of [['native ints', TTT_FIRST_EMPTY], ['numpy ints', TTT_NUMPY]] as const) {
  test(`replay of a just-played match with ${name}`, async ({ page }) => {
    const replay = await openFirstFinishedReplay(page, code);
    await expect(replay).not.toContainText('Replay failed');
    await expect(replay.locator('.rp-move-flag')).toHaveCount(0);
    const turn = (await replay.locator('.rp-turn').innerText()).match(/turn\s+(\d+)\s*\/\s*(\d+)/);
    expect(turn, 'turn counter').not.toBeNull();
    expect(Number(turn![2]), 'a finished 3x3 game has at least 5 moves').toBeGreaterThanOrEqual(5);
  });
}
