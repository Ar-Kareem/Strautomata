// Keyboard hints for connect4, nim, mancala, tic tac toe 3d and dots and boxes.
import { expect, test, type Page } from '@playwright/test';
import { RUNTIME_TIMEOUT, board, gotoPlay, keyboardMode } from './helpers';

test.describe.configure({ timeout: RUNTIME_TIMEOUT });

const hints = (page: Page) => page.locator('arena-output .kbd-hint');

async function hintTexts(page: Page): Promise<string[]> {
  return (await hints(page).allInnerTexts()).map((text) => text.trim()).sort();
}

/** every hint sits centred on its own target */
async function hintsOnTargets(page: Page): Promise<boolean> {
  return page.locator('arena-output').evaluate((root) => {
    const shown = [...root.querySelectorAll('.kbd-hint')];
    return shown.length > 0 && shown.every((hint) => {
      const target = root.querySelector(`[data-kbd="${hint.textContent?.trim()}"]`);
      if (!target) {
        return false;
      }
      const h = hint.getBoundingClientRect();
      const t = target.getBoundingClientRect();
      const dx = h.left + h.width / 2 - (t.left + t.width / 2);
      const dy = h.top + h.height / 2 - (t.top + t.height / 2);
      return Math.abs(dx) < 2 && Math.abs(dy) < 2;
    });
  });
}

test('connect4: column number on the landing cell drops a disc', async ({ page }) => {
  await gotoPlay(page, 'connect4', 'world1', 'Human vs Human');
  const cells = board(page, '.connect4-cell');
  await expect(cells).toHaveCount(42);
  await keyboardMode(page);
  await expect.poll(() => hintTexts(page)).toEqual(['1', '2', '3', '4', '5', '6', '7']);
  // hints sit on the bottom row, where the disc lands
  await expect(board(page, '.connect4-cell[data-kbd]')).toHaveCount(7);
  await expect(cells.nth(35)).toHaveAttribute('data-kbd', '1');
  await page.keyboard.press('4');
  await expect(cells.nth(38)).toHaveAttribute('data-owner', 'p0');
  // the mode stays on and the next hint in that column moves up a row
  await expect.poll(() => hintTexts(page)).toEqual(['1', '2', '3', '4', '5', '6', '7']);
  await expect(cells.nth(31)).toHaveAttribute('data-kbd', '4');
});

test('nim: pile number narrows, count takes', async ({ page }) => {
  await gotoPlay(page, 'nim', 'world1', 'Human vs Human');
  const counts = board(page, '.nim-pile-count');
  await expect(counts).toHaveText(['1', '3', '5', '7']);
  await keyboardMode(page);
  await expect.poll(() => hintTexts(page)).toEqual(
    ['11', '21', '22', '23', '31', '32', '33', '34', '35', '41', '42', '43', '44', '45', '46', '47']
  );
  await page.keyboard.press('4');
  await expect(hints(page)).toHaveCount(7);
  await page.keyboard.press('3');
  await expect(counts).toHaveText(['1', '3', '5', '4']);
  // the mode stays on for the other player: 1 + 3 + 5 + 4 tokens
  await expect(hints(page)).toHaveCount(13);
  // the tokens slide to their new places after a take, and the hints follow them
  await expect.poll(() => hintsOnTargets(page)).toBe(true);
});

test('nim: hints follow the tokens after the automaton takes', async ({ page }) => {
  await gotoPlay(page, 'nim', 'world1', 'Human vs AI');
  const counts = board(page, '.nim-pile-count');
  await expect(counts).toHaveText(['1', '3', '5', '7'], { timeout: RUNTIME_TIMEOUT });
  await keyboardMode(page);
  await expect(hints(page)).toHaveCount(16);
  await page.keyboard.type('41');
  // the automaton replies, its pile slides to the new count and the hints land on the tokens
  await expect.poll(async () => (await counts.allInnerTexts()).join(','), { timeout: RUNTIME_TIMEOUT }).not.toBe('1,3,5,6');
  await expect(hints(page).first()).toBeVisible({ timeout: RUNTIME_TIMEOUT });
  await expect.poll(() => hintsOnTargets(page)).toBe(true);
});

test('mancala: pit number as printed sows the pit', async ({ page }) => {
  await gotoPlay(page, 'mancala', 'world1', 'Human vs Human');
  const pits = board(page, '.mancala-row.bottom .mancala-pit');
  await expect(pits).toHaveCount(6);
  await keyboardMode(page);
  await expect.poll(() => hintTexts(page)).toEqual(['1', '2', '3', '4', '5', '6']);
  await expect(pits.nth(0)).toHaveAttribute('data-kbd', '1');
  await page.keyboard.press('1');
  await expect(pits.nth(0)).toHaveAttribute('data-seeds', '0');
  await expect(pits.nth(1)).toHaveAttribute('data-seeds', '5');
  // the mode stays on for the other player's pits
  await expect(board(page, '.mancala-row.top .mancala-pit[data-kbd]')).toHaveCount(6);
  await expect(hints(page)).toHaveCount(6);
});

test('tic tac toe 3d: layer number then small grid', async ({ page }) => {
  await gotoPlay(page, 'tic_tac_toe_3d', 'world1', 'Human vs Human');
  const chips = board(page, '.ttt3d-layer-chip');
  const cells = board(page, '.ttt3d-cell');
  await expect(chips).toHaveText([/L1/, /L2/, /L3/]);
  await keyboardMode(page);
  // layer chips show their printed number, the shown layer (L1) has no chip hint
  await expect.poll(() => hintTexts(page)).toEqual([...'23acdeqswxz'].sort());
  await page.keyboard.press('3');
  await expect(chips.nth(2)).toHaveClass(/is-active/);
  await expect.poll(() => hintTexts(page)).toEqual([...'12acdeqswxz'].sort());
  await page.keyboard.press('s');
  await expect(cells.nth(4)).toHaveAttribute('data-owner', 'p0');
  await expect(page.locator('arena-output .ttt3d-layer')).toHaveAttribute('data-layer', '2');
  // the mode stays on: two layer chips and the 8 free cells
  await expect(hints(page)).toHaveCount(10);
});

test('dots and boxes: line square on the grid of dots and lines', async ({ page }) => {
  await gotoPlay(page, 'dots_and_boxes', 'world1', 'Human vs Human');
  const lines = board(page, '.dots-cell.is-line-h, .dots-cell.is-line-v');
  await expect(lines).toHaveCount(40);
  await keyboardMode(page);
  await expect(hints(page)).toHaveCount(40);
  const texts = await hintTexts(page);
  expect(texts).toEqual(expect.arrayContaining(['b9', 'h9', 'a8', 'i8', 'd5', 'e4']));
  expect(texts).not.toContain('a9');
  await page.keyboard.type('b9');
  // b9 is the top-left horizontal line
  await expect(board(page, '.dots-cell').nth(1)).toHaveAttribute('data-owner', /black|white/);
  // the mode stays on for the other player
  await expect(hints(page)).toHaveCount(39);
});
