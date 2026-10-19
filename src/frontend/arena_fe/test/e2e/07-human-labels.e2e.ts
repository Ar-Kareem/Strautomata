// Audit issue 7: in Human vs Human Tic Tac Toe both players are "Human" in the turn label, the
// scoreboard and the winner banner.
import { expect, test } from '@playwright/test';
import { RUNTIME_TIMEOUT, board, gotoPlay } from './helpers';

test.describe.configure({ timeout: RUNTIME_TIMEOUT });

test.beforeEach(async ({ page }) => {
  await gotoPlay(page, 'tic_tac_toe', 'world1', 'Human vs Human');
  await expect(board(page, '.tic-tac-toe-cell')).toHaveCount(9);
});

test('the turn label names the side to move', async ({ page }) => {
  const label = page.locator('arena-output .tic-tac-toe-head p');
  const first = (await label.innerText()).trim();
  await board(page, '.tic-tac-toe-cell').nth(0).click();
  await expect(label).not.toHaveText(first);
  const second = (await label.innerText()).trim();
  for (const text of [first, second]) {
    expect(text, 'should say which side moves, not just "Human"').toMatch(/\b(x|o|red|blue|player [12])\b/i);
  }
});

test('the scoreboard distinguishes the two humans', async ({ page }) => {
  const labels = await page.locator('arena-output .versus-name').allInnerTexts();
  expect(labels).toHaveLength(2);
  expect(labels[0].trim()).not.toBe(labels[1].trim());
});

test('the winner banner names the winning side', async ({ page }) => {
  const cells = board(page, '.tic-tac-toe-cell');
  for (const i of [0, 3, 1, 4, 2]) {
    // first player takes the top row
    await cells.nth(i).click();
    await page.waitForTimeout(300);
  }
  const banner = page.locator('arena-output .tic-tac-toe-banner');
  await expect(banner).toBeVisible();
  await expect(banner).not.toHaveText(/^\s*human won\s*$/i);
  await expect(banner).toHaveText(/\b(x|o|red|blue|player [12])\b/i);
});
