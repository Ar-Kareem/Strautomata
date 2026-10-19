// Audit issue 3: a compile that resolves after the game (or code) changed still reports its
// result and enables Run for the wrong game.
import { expect, test } from '@playwright/test';
import {
  FIRST_LEGAL, RUNTIME_TIMEOUT, compileAndWait, create, expectNotRunnable, gotoCreate, selectGame, setCode,
  settleCompile, slowPolicy
} from './helpers';

test.describe.configure({ timeout: RUNTIME_TIMEOUT * 2 });

test.beforeEach(async ({ page }) => {
  await gotoCreate(page);
  await selectGame(page, 'Tic Tac Toe (3x3)');
  // warm the runtime so the slow policy, not Pyodide start-up, decides when compile resolves
  await setCode(page, FIRST_LEGAL);
  await compileAndWait(page);
});

test('switching game while compiling discards the old success', async ({ page }) => {
  await setCode(page, slowPolicy('return (0, 0)'));
  await create(page).compileIdle.click();
  await selectGame(page, 'Chess');
  await settleCompile(page);
  await expectNotRunnable(page);
});

test('switching game while compiling discards the old error', async ({ page }) => {
  await setCode(page, slowPolicy('raise ValueError("stale-ttt-error")'));
  await create(page).compileIdle.click();
  await selectGame(page, 'Chess');
  await settleCompile(page);
  await expect(create(page).fault).toHaveCount(0); // the editor itself still contains the string
  await expectNotRunnable(page);
});

test('switching away and back while compiling still needs a new compile', async ({ page }) => {
  await setCode(page, slowPolicy('return (0, 0)'));
  await create(page).compileIdle.click();
  await selectGame(page, 'Chess');
  await selectGame(page, 'Tic Tac Toe (3x3)');
  await settleCompile(page);
  await expectNotRunnable(page);
});

test('editing code while compiling discards the old success', async ({ page }) => {
  await setCode(page, slowPolicy('return (0, 0)'));
  await create(page).compileIdle.click();
  await setCode(page, slowPolicy('return (1, 1)'));
  await settleCompile(page);
  await expectNotRunnable(page);
});

test('a newer compile for another game wins over the older one', async ({ page }) => {
  await setCode(page, slowPolicy('return (0, 0)'));
  await create(page).compileIdle.click();
  await selectGame(page, 'Connect 4');
  await setCode(page, FIRST_LEGAL);
  await expect(create(page).compileIdle).toBeEnabled({ timeout: RUNTIME_TIMEOUT });
  await compileAndWait(page);
  await settleCompile(page);
  const c = create(page);
  await expect(c.run).toBeEnabled();
  await expect(c.ok.locator('code')).toHaveText(/^\d+$/); // a Connect 4 column, not the (0, 0) of Tic Tac Toe
});

test('recompiling the Tic Tac Toe policy under Chess fails', async ({ page }) => {
  await setCode(page, `def policy(board):\n    return (0, 0)\n`);
  await selectGame(page, 'Chess');
  await compileAndWait(page);
  await expect(create(page).fault).toBeVisible();
  await expectNotRunnable(page);
});
