// Keyboard hints on go, hex, havannah, othello and battleships. The big boards pick a column
// letter, then a row letter on that column, go's Pass button gets 0. Othello uses square names.
import { expect, test, type Page } from '@playwright/test';
import { RUNTIME_TIMEOUT, board, gotoPlay, keyboardMode } from './helpers';

test.describe.configure({ timeout: RUNTIME_TIMEOUT });

const hints = (page: Page) => page.locator('arena-output .kbd-hint');

async function hintTexts(page: Page): Promise<string[]> {
  return (await hints(page).allInnerTexts()).map((text) => text.trim()).sort();
}

const OWNED = /^(black|white)$/;

test('go: column letter, then row letter on that column, 0 passes', async ({ page }) => {
  await gotoPlay(page, 'go', 'world1', 'Human vs Human');
  const cells = board(page, '.go-cell');
  await expect(cells).toHaveCount(361);
  const letters = [...'abcdefghijklmnopqrs'];
  const rows = letters;
  await keyboardMode(page);
  // one hint per column and Pass, not one per point
  await expect.poll(() => hintTexts(page)).toEqual([...letters, '0'].sort());
  await page.keyboard.press('a');
  await expect.poll(() => hintTexts(page)).toEqual(rows);
  await expect(board(page, '.go-cell[data-kbd]')).toHaveCount(19);
  await page.keyboard.press('Backspace');
  await expect.poll(() => hintTexts(page)).toEqual([...letters, '0'].sort());
  await page.keyboard.type('aa');
  // aa is the bottom-left point: last row, first column
  await expect(cells.nth(18 * 19)).toHaveAttribute('data-owner', 'black');
  await expect(page.locator('arena-output .go-head')).toContainText('Human B');
  // the mode stays on for white, back at the column pick, and aa is taken
  await expect.poll(() => hintTexts(page)).toEqual([...letters, '0'].sort());
  await page.keyboard.press('a');
  await expect.poll(() => hintTexts(page)).toEqual(rows.slice(1));
  await page.keyboard.press('Backspace');
  await page.keyboard.press('0');
  await expect(page.locator('arena-output .go-head')).toContainText('Human A');
  await expect(board(page, '.go-cell[data-owner]')).toHaveCount(1);
});

test('hex: column letter, then row letter on that column', async ({ page }) => {
  await gotoPlay(page, 'hex', 'world1', 'Human vs Human');
  const cells = board(page, '.hex-cell');
  await expect(cells).toHaveCount(121);
  const letters = [...'abcdefghijk'];
  await keyboardMode(page);
  // one hint per column, on its top edge
  await expect.poll(() => hintTexts(page)).toEqual(letters);
  await page.keyboard.press('b');
  await expect(board(page, '.hex-cell[data-kbd]')).toHaveCount(11);
  await expect.poll(() => hintTexts(page)).toEqual(letters);
  await page.keyboard.press('Backspace');
  await expect(board(page, '.hex-cell[data-kbd]')).toHaveCount(0);
  await page.keyboard.type('bc');
  // column b, 3rd row from the bottom (row 8 from the top)
  await expect(cells.nth(8 * 11 + 1)).toHaveAttribute('data-owner', OWNED);
  await expect(board(page, '.hex-cell[data-owner]')).toHaveCount(1);
  // the other player starts at the column pick, column b has one cell fewer
  await expect.poll(() => hintTexts(page)).toEqual(letters);
  await page.keyboard.press('b');
  await expect(board(page, '.hex-cell[data-kbd]')).toHaveCount(10);
  await page.keyboard.press('Escape');
});

test('havannah: column letter, then row letter on that column', async ({ page }) => {
  await gotoPlay(page, 'havannah', 'world1', 'Human vs Human');
  const cells = board(page, '.havannah-cell');
  await expect(cells).toHaveCount(169);
  await keyboardMode(page);
  // 15 columns, hints along the top and upper-right edges
  await expect.poll(() => hintTexts(page)).toEqual([...'abcdefghijklmno']);
  // column c runs from the top row down 10 cells, rows o (top) to f
  await page.keyboard.press('c');
  await expect.poll(() => hintTexts(page)).toEqual([...'fghijklmno']);
  await page.keyboard.press('m');
  // 3rd row from the top, 3rd cell: its aria-label uses the top-row notation
  await expect(page.locator('arena-output .havannah-cell[aria-label="c3"]')).toHaveAttribute('data-owner', OWNED);
  await expect(board(page, '.havannah-cell[data-owner]')).toHaveCount(1);
  // the mode stays on for the other player
  await expect.poll(() => hintTexts(page)).toEqual([...'abcdefghijklmno']);
});

test('othello: legal squares only', async ({ page }) => {
  await gotoPlay(page, 'othello', 'world1', 'Human vs Human');
  const cells = board(page, '.othello-cell');
  await expect(cells).toHaveCount(64);
  await keyboardMode(page);
  await expect(hints(page)).toHaveCount(4);
  await expect.poll(() => hintTexts(page)).toEqual(['c5', 'd6', 'e3', 'f4']);
  await page.keyboard.type('d6');
  // d6 is the 3rd row from the top, 4th column
  await expect(cells.nth(2 * 8 + 3)).toHaveAttribute('data-owner', OWNED);
  // the mode stays on for the other player
  await expect.poll(() => hintTexts(page)).toEqual(['c4', 'c6', 'e6']);
  await page.keyboard.press('Escape');
  await expect(hints(page)).toHaveCount(0);
});

test('battleships: column letter, then row letter, on the active board only', async ({ page }) => {
  await gotoPlay(page, 'battleships', 'world1', 'Human vs Human');
  const cards = page.locator('arena-output .battleships-board-card');
  await expect(cards).toHaveCount(2);
  await expect(cards.nth(0).locator('.battleships-cell')).toHaveCount(100);
  const letters = [...'abcdefghij'];
  await keyboardMode(page);
  await expect.poll(() => hintTexts(page)).toEqual(letters);
  await expect(cards.nth(0).locator('[data-kbd]')).toHaveCount(10);
  await expect(cards.nth(1).locator('[data-kbd]')).toHaveCount(0);
  await page.keyboard.press('e');
  await expect(cards.nth(0).locator('.battleships-cell[data-kbd]')).toHaveCount(10);
  await page.keyboard.press('e');
  // column e, 5th row from the bottom (6th from the top)
  await expect(cards.nth(0).locator('.battleships-cell').nth(5 * 10 + 4)).not.toHaveAttribute('data-status', 'unknown');
  // the other player's board takes over
  await expect(cards.nth(0).locator('[data-kbd]')).toHaveCount(0);
  await expect(cards.nth(1).locator('[data-kbd]')).toHaveCount(10);
  await expect.poll(() => hintTexts(page)).toEqual(letters);
  await page.keyboard.press('Escape');
});
