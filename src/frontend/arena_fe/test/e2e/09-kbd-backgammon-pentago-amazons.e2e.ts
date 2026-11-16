// Keyboard hints on backgammon, pentago and amazons: every stage of a move by keyboard.
import { expect, test, type Page } from '@playwright/test';
import { kbdList } from '../../src/app/components/arena-gui-helpers/arena-kbd-keys';
import { RUNTIME_TIMEOUT, board, gotoPlay, keyboardMode } from './helpers';

test.describe.configure({ timeout: RUNTIME_TIMEOUT });

const hints = (page: Page) => page.locator('arena-output .kbd-hint');

async function hintTexts(page: Page): Promise<string[]> {
  return (await hints(page).allInnerTexts()).map((text) => text.trim()).sort();
}

test('backgammon: point number then destination or move letter, Backspace goes back', async ({ page }) => {
  await gotoPlay(page, 'backgammon', 'world1', 'Human vs Human');
  const point = (n: string) =>
    board(page, '.bg-point').filter({ has: page.locator('.point-num', { hasText: new RegExp(`^${n}$`) }) });
  const numbers = (selector: string) => board(page, `${selector} .point-num`).allInnerTexts();
  // hints pad the printed point number to two digits
  const labels = (printed: string[]) => printed.map((n) => n.padStart(2, '0'));
  const chips = board(page, '.move-chip');
  // dice and the first player are random, so the expected hints come from the board itself
  await expect(chips.first()).toBeVisible();
  const sources = await numbers('.bg-point.is-legal-from');
  expect(sources.length).toBeGreaterThan(0);
  const source = sources[0];
  const stack = await point(source).locator('.point-stack').innerHTML();
  await keyboardMode(page);
  await expect.poll(() => hintTexts(page)).toEqual([...labels(sources), ...kbdList(await chips.count())].sort());
  await page.keyboard.type(labels([source])[0]);
  // destinations of the source plus the moves that start there
  await expect(board(page, '.bg-point.is-selected .point-num')).toHaveText(source);
  const destinations = await numbers('.bg-point.is-legal-to');
  expect(destinations.length).toBeGreaterThan(0);
  await expect.poll(async () => hintTexts(page)).toEqual([...labels(destinations), ...kbdList(await chips.count())].sort());
  await page.keyboard.press('Backspace');
  await expect(board(page, '.bg-point.is-selected')).toHaveCount(0);
  await expect.poll(() => hintTexts(page)).toEqual(expect.arrayContaining(labels(sources)));
  await page.keyboard.type(labels([source])[0]);
  await expect.poll(() => hintTexts(page)).toEqual(expect.arrayContaining(labels(destinations)));
  // the first listed move from the source
  await page.keyboard.type('a');
  await expect.poll(() => point(source).locator('.point-stack').innerHTML()).not.toBe(stack);
});

test('pentago: square then quadrant rotation', async ({ page }) => {
  await gotoPlay(page, 'pentago', 'world1', 'Human vs Human');
  const cells = board(page, '.pentago-cell');
  await expect(cells).toHaveCount(36);
  await keyboardMode(page);
  await expect(hints(page)).toHaveCount(36);
  await expect.poll(() => hintTexts(page)).toEqual(expect.arrayContaining(['a1', 'a6', 'f1', 'f6']));
  await page.keyboard.type('a1');
  await expect.poll(() => hintTexts(page)).toEqual(['ca', 'cd', 'ea', 'ed', 'qa', 'qd', 'za', 'zd']);
  await page.keyboard.press('Backspace');
  await expect(hints(page)).toHaveCount(36);
  await page.keyboard.type('a1');
  await expect(hints(page)).toHaveCount(8);
  // rotate the top-left quadrant clockwise, a1 sits in the bottom-left one
  await page.keyboard.type('qd');
  await expect(cells.nth(30)).toHaveAttribute('data-owner', 'black');
  // the mode stays on for the other player's 35 free squares
  await expect(hints(page)).toHaveCount(35);
});

test('amazons: queen, destination, arrow, Backspace steps back one stage', async ({ page }) => {
  await gotoPlay(page, 'amazons', 'world1', 'Human vs Human');
  const cells = board(page, '.amazons-cell');
  await expect(cells).toHaveCount(36);
  await keyboardMode(page);
  await expect.poll(() => hintTexts(page)).toEqual(['a5', 'b6', 'e6', 'f5']);
  await page.keyboard.type('b6');
  await expect.poll(() => hintTexts(page)).toEqual(expect.arrayContaining(['a6', 'b5', 'c6', 'c5']));
  await page.keyboard.type('b5');
  // the arrow can land on the square the queen left
  await expect.poll(() => hintTexts(page)).toEqual(expect.arrayContaining(['b6', 'b4', 'c5']));
  await expect.poll(() => hintTexts(page)).not.toContain('b5');
  await page.keyboard.press('Backspace');
  await expect.poll(() => hintTexts(page)).toEqual(expect.arrayContaining(['a6', 'b5', 'c6']));
  await page.keyboard.press('Backspace');
  await expect.poll(() => hintTexts(page)).toEqual(['a5', 'b6', 'e6', 'f5']);
  await page.keyboard.type('b6');
  await expect.poll(() => hintTexts(page)).toContain('b5');
  await page.keyboard.type('b5');
  await expect.poll(() => hintTexts(page)).toContain('b6');
  await page.keyboard.type('b6');
  await expect(cells.nth(7)).toHaveAttribute('data-owner', 'white');
  await expect(cells.nth(1).locator('.amazons-arrow')).toHaveCount(1);
  // the mode stays on for the other player's queens
  await expect(hints(page)).toHaveCount(4);
});
