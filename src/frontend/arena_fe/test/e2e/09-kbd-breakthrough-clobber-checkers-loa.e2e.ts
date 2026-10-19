// Keyboard hints on the piece-moving boards: keyboard mode shows the movable pieces as squares, typing one
// selects it and shows its targets, Backspace goes back, typing a target plays the move.
import { expect, test, type Page } from '@playwright/test';
import { RUNTIME_TIMEOUT, board, gotoPlay, keyboardMode } from './helpers';

test.describe.configure({ timeout: RUNTIME_TIMEOUT });

const hints = (page: Page) => page.locator('arena-output .kbd-hint');

async function hintTexts(page: Page): Promise<string[]> {
  return (await hints(page).allInnerTexts()).map((text) => text.trim()).sort();
}

const sorted = (labels: string[]) => [...labels].sort();

test('breakthrough: piece square then direction', async ({ page }) => {
  await gotoPlay(page, 'breakthrough', 'world1', 'Human vs Human');
  const cells = board(page, '.breakthrough-cell');
  await expect(cells).toHaveCount(64);
  const firstRow = ['a7', 'b7', 'c7', 'd7', 'e7', 'f7', 'g7', 'h7'];
  await keyboardMode(page);
  await expect.poll(() => hintTexts(page)).toEqual(sorted(firstRow));
  // green moves down the screen, a corner pawn has two steps
  await page.keyboard.type('a7');
  await expect.poll(() => hintTexts(page)).toEqual(['c', 's']);
  await page.keyboard.press('Backspace');
  await expect.poll(() => hintTexts(page)).toEqual(sorted(firstRow));
  await page.keyboard.type('b7');
  await expect.poll(() => hintTexts(page)).toEqual(['c', 's', 'z']);
  await page.keyboard.press('s');
  // b6 is row 2 from the top
  await expect(cells.nth(2 * 8 + 1)).toHaveAttribute('data-owner', 'black');
  await expect(cells.nth(1 * 8 + 1)).not.toHaveAttribute('data-owner', 'black');
  // the mode stays on for the other player
  await expect(hints(page)).not.toHaveCount(0);
});

test('clobber: piece square then w/a/s/d', async ({ page }) => {
  await gotoPlay(page, 'clobber', 'world1', 'Human vs Human');
  const cells = board(page, '.clobber-cell');
  await expect(cells).toHaveCount(30);
  const pieces = ['a5', 'c5', 'e5', 'b4', 'd4', 'f4', 'a3', 'c3', 'e3', 'b2', 'd2', 'f2', 'a1', 'c1', 'e1'];
  await keyboardMode(page);
  await expect.poll(() => hintTexts(page)).toEqual(sorted(pieces));
  await page.keyboard.type('a5');
  await expect.poll(() => hintTexts(page)).toEqual(['d', 's']);
  await page.keyboard.press('Backspace');
  await expect.poll(() => hintTexts(page)).toEqual(sorted(pieces));
  await page.keyboard.type('c3');
  await expect.poll(() => hintTexts(page)).toEqual(['a', 'd', 's', 'w']);
  await page.keyboard.press('w');
  // 6 columns: c4 is row 1, c3 is row 2 from the top
  await expect(cells.nth(1 * 6 + 2)).toHaveAttribute('data-owner', 'black');
  await expect(cells.nth(2 * 6 + 2)).not.toHaveAttribute('data-owner', /./);
  // the mode stays on for the other player
  await expect(hints(page)).not.toHaveCount(0);
});

test('checkers: piece square then landing square', async ({ page }) => {
  await gotoPlay(page, 'checkers', 'world1', 'Human vs Human');
  const cells = board(page, '.checkers-cell');
  await expect(cells).toHaveCount(64);
  await keyboardMode(page);
  await expect.poll(() => hintTexts(page)).toEqual(['a3', 'c3', 'e3', 'g3']);
  await page.keyboard.type('c3');
  await expect.poll(() => hintTexts(page)).toEqual(['b4', 'd4']);
  await page.keyboard.press('Backspace');
  await expect.poll(() => hintTexts(page)).toEqual(['a3', 'c3', 'e3', 'g3']);
  await page.keyboard.type('g3');
  await expect.poll(() => hintTexts(page)).toEqual(['f4', 'h4']);
  await page.keyboard.type('h4');
  // h4 is row 4 from the top, g3 row 5
  await expect(cells.nth(4 * 8 + 7)).toHaveAttribute('data-owner', 'white');
  await expect(cells.nth(5 * 8 + 6)).not.toHaveAttribute('data-owner', /./);
  // the mode stays on for the other player
  await expect(hints(page)).not.toHaveCount(0);
});

test('lines of action: piece square then destination square', async ({ page }) => {
  await gotoPlay(page, 'lines_of_action', 'world1', 'Human vs Human');
  const cells = board(page, '.loa-cell');
  await expect(cells).toHaveCount(64);
  const pieces = ['b1', 'c1', 'd1', 'e1', 'f1', 'g1', 'b8', 'c8', 'd8', 'e8', 'f8', 'g8'];
  await keyboardMode(page);
  await expect.poll(() => hintTexts(page)).toEqual(sorted(pieces));
  // b8 jumps its own row to h8 or moves two squares down
  await page.keyboard.type('b8');
  await expect.poll(() => hintTexts(page)).toEqual(['b6', 'd6', 'h8']);
  await page.keyboard.press('Backspace');
  await expect.poll(() => hintTexts(page)).toEqual(sorted(pieces));
  await page.keyboard.type('c1');
  await expect.poll(() => hintTexts(page)).toEqual(['a3', 'c3', 'e3']);
  await page.keyboard.type('c3');
  // c3 is row 5 from the top, c1 row 7
  await expect(cells.nth(5 * 8 + 2)).toHaveAttribute('data-owner', 'p1');
  await expect(cells.nth(7 * 8 + 2)).not.toHaveAttribute('data-owner', /./);
  // the mode stays on for the other player
  await expect(hints(page)).not.toHaveCount(0);
});
