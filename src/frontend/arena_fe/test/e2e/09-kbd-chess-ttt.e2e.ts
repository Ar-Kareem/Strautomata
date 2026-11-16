// Keyboard hints: Space toggles keyboard mode, which shows a hint over every legal target, typing
// one clicks it, and a board that needs a second pick shows the next set.
import { expect, test, type Page } from '@playwright/test';
import { RUNTIME_TIMEOUT, board, gotoPlay, keyboardMode } from './helpers';

test.describe.configure({ timeout: RUNTIME_TIMEOUT });

const hints = (page: Page) => page.locator('arena-output .kbd-hint');

async function hintTexts(page: Page): Promise<string[]> {
  return (await hints(page).allInnerTexts()).map((text) => text.trim()).sort();
}

test('tic tac toe: qweasdzxc places a mark', async ({ page }) => {
  await gotoPlay(page, 'tic_tac_toe', 'world1', 'Human vs Human');
  const cells = board(page, '.tic-tac-toe-cell');
  await expect(cells).toHaveCount(9);
  await keyboardMode(page);
  await expect(hints(page)).toHaveCount(9);
  await expect.poll(() => hintTexts(page)).toEqual([...'acdeqswxz']);
  await page.keyboard.press('s');
  await expect(cells.nth(4)).toHaveAttribute('data-owner', 'p0');
  // the mode stays on for the next move
  await expect.poll(() => hintTexts(page)).toEqual([...'acdeqwxz']);
  await page.keyboard.press('q');
  await expect(cells.nth(0)).toHaveAttribute('data-owner', 'p1');
  await expect(hints(page)).toHaveCount(7);
  // Space turns it off and on again
  await page.keyboard.press('Space');
  await expect(hints(page)).toHaveCount(0);
  await page.keyboard.press('Space');
  await expect(hints(page)).toHaveCount(7);
  await page.keyboard.press('Escape');
  await expect(hints(page)).toHaveCount(0);
});

test('the mode stays on through the automaton\'s turn', async ({ page }) => {
  await gotoPlay(page, 'tic_tac_toe', 'world1', 'Human vs AI');
  const cells = board(page, '.tic-tac-toe-cell');
  await expect(cells.and(page.locator('[data-kbd]'))).toHaveCount(9, { timeout: RUNTIME_TIMEOUT });
  await keyboardMode(page);
  await expect(hints(page)).toHaveCount(9);
  await page.keyboard.press('s');
  await expect(cells.nth(4)).toHaveAttribute('data-owner', /p[01]/);
  // the automaton replies, then the hints come back for the remaining 7 squares without Space
  await expect(hints(page)).toHaveCount(7, { timeout: RUNTIME_TIMEOUT });
});

test('chess: piece square then destination square, Backspace goes back', async ({ page }) => {
  await gotoPlay(page, 'chess', 'worlduci1', 'Human vs Human');
  const cells = board(page, '.chess-cell');
  await expect(cells).toHaveCount(64);
  await keyboardMode(page);
  // 8 pawns and 2 knights can move
  await expect(hints(page)).toHaveCount(10);
  await expect.poll(() => hintTexts(page)).toContain('e2');
  await page.keyboard.press('e');
  // typing narrows to the hints that start with it
  await expect(hints(page)).toHaveCount(1);
  await page.keyboard.press('2');
  await expect.poll(() => hintTexts(page)).toEqual(['e3', 'e4']);
  await page.keyboard.press('Backspace');
  await expect(hints(page)).toHaveCount(10);
  await page.keyboard.press('g');
  await page.keyboard.press('1');
  await expect.poll(() => hintTexts(page)).toEqual(['f3', 'h3']);
  await page.keyboard.type('f3');
  await expect(page.locator('arena-output .chess-cell[aria-label="f3: white knight"]')).toHaveCount(1);
  // black's pieces get hints without pressing Space again
  await expect(hints(page)).toHaveCount(10, { timeout: 30_000 });
  // a whole move typed in one burst, before the second set of hints has drawn
  await page.keyboard.type('e7e5', { delay: 0 });
  await expect(page.locator('arena-output .chess-cell[aria-label="e5: black pawn"]')).toHaveCount(1);
  await expect.poll(() => hintTexts(page), { timeout: 30_000 }).toContain('f3');
});
