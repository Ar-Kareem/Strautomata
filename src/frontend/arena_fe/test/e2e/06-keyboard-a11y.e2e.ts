// Audit issue 6: core workflows cannot be completed with the keyboard and lack accessible names.
import { expect, test, type Locator, type Page } from '@playwright/test';
import { RUNTIME_TIMEOUT, board, gotoMatchup, gotoPlay, tabStops } from './helpers';

test.describe.configure({ timeout: RUNTIME_TIMEOUT });

async function accessibleNames(cells: Locator): Promise<string[]> {
  return cells.evaluateAll((els) =>
    els.map((el) => {
      const labelledBy = el.getAttribute('aria-labelledby');
      const fromIds = labelledBy
        ? labelledBy.split(/\s+/).map((id) => document.getElementById(id)?.textContent ?? '').join(' ')
        : '';
      return (el.getAttribute('aria-label') || fromIds || el.getAttribute('title') || el.textContent || '').trim();
    })
  );
}

async function activeIsOneOf(page: Page, selector: string): Promise<boolean> {
  return page.evaluate((sel) => !!document.activeElement?.matches(sel), selector);
}

// ---- game picker ------------------------------------------------------------------------------
test.describe('game picker', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/#/matches?stage=tourney');
    await expect(page.locator('.gpk-trigger')).toBeVisible({ timeout: 60_000 });
  });

  test('a game can be chosen with Enter and the arrow keys', async ({ page }) => {
    const trigger = page.locator('.gpk-trigger');
    const before = await trigger.innerText();
    await trigger.focus();
    await page.keyboard.press('Enter');
    const listbox = page.getByRole('listbox', { name: 'Game' });
    await expect(listbox).toBeVisible();
    await page.keyboard.press('ArrowDown');
    await page.keyboard.press('ArrowDown');
    const active = await page.evaluate(() => {
      const el = document.activeElement;
      const id = el?.getAttribute('aria-activedescendant');
      const target = id ? document.getElementById(id) : el;
      return target?.getAttribute('role') === 'option' ? target.textContent?.trim() ?? '' : null;
    });
    expect(active, 'ArrowDown should move to an option').not.toBeNull();
    await page.keyboard.press('Enter');
    await expect(listbox).toBeHidden();
    await expect(page).toHaveURL(/[?&]game=/);
    await expect(trigger).not.toHaveText(before);
    await expect(trigger).toBeFocused();
  });

  test('Escape closes the picker and returns focus to it', async ({ page }) => {
    const trigger = page.locator('.gpk-trigger');
    await trigger.focus();
    await page.keyboard.press('Enter');
    await expect(page.getByRole('listbox', { name: 'Game' })).toBeVisible();
    await page.keyboard.press('Escape');
    await expect(page.getByRole('listbox', { name: 'Game' })).toBeHidden();
    await expect(trigger).toBeFocused();
  });

  test('decorative previews add no tab stops', async ({ page }) => {
    await page.locator('.gpk-trigger').click();
    const previews = page.locator('.gpk-popup game-preview');
    await expect(previews.first()).toBeVisible();
    let stops = 0;
    for (const preview of await previews.all()) {
      stops += await tabStops(preview);
    }
    expect(stops).toBe(0);
  });
});

// ---- human boards -----------------------------------------------------------------------------
async function expectKeyboardMove(page: Page, cells: Locator): Promise<void> {
  const before = await accessibleNames(cells);
  expect(before.filter((n) => !n), 'every cell needs an accessible name').toHaveLength(0);
  const target = cells.first();
  await target.focus();
  await expect(target).toBeFocused();
  await page.keyboard.press('Enter');
  await expect.poll(async () => (await accessibleNames(cells)).some((n, i) => n !== before[i]), {
    message: 'a keyboard move should change the board state that assistive tech reads'
  }).toBe(true);
}

test('Tic Tac Toe cells are named and playable with the keyboard', async ({ page }) => {
  await gotoPlay(page, 'tic_tac_toe', 'world1', 'Human vs Human');
  const cells = board(page, '.tic-tac-toe-cell');
  await expect(cells).toHaveCount(9);
  await expectKeyboardMove(page, cells);
});

test('Tic Tac Toe marks are exposed to assistive tech', async ({ page }) => {
  await gotoPlay(page, 'tic_tac_toe', 'world1', 'Human vs Human');
  const cells = board(page, '.tic-tac-toe-cell');
  await cells.first().click();
  await expect(cells.first()).toHaveAccessibleName(/\b(x|o|red|blue)\b/i);
});

test('Connect 4 cells are named and playable with the keyboard', async ({ page }) => {
  await gotoPlay(page, 'connect4', 'world1', 'Human vs Human');
  const cells = board(page, '.connect4-cell');
  await expect(cells.first()).toBeVisible();
  await expectKeyboardMove(page, cells);
});

test('Hex cells are named and playable with the keyboard', async ({ page }) => {
  await gotoPlay(page, 'hex', 'world1', 'Human vs Human');
  const cells = board(page, '.hex-cell');
  await expect(cells.first()).toBeVisible();
  await expectKeyboardMove(page, cells);
});

test('Chess squares are named and reachable with the keyboard', async ({ page }) => {
  await gotoPlay(page, 'chess', 'worlduci1', 'Human vs Human');
  const cells = board(page, '.chess-cell');
  await expect(cells).toHaveCount(64);
  expect((await accessibleNames(cells)).filter((n) => !n)).toHaveLength(0);
  expect(await tabStops(page.locator('arena-output arena-chess-gui').first())).toBeGreaterThan(0);
});

// ---- heatmap ----------------------------------------------------------------------------------
test.describe('heatmap', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/#/matches?stage=tourney&game=tic_tac_toe_world1');
    await expect(page.locator('.hm-cell').first()).toBeVisible({ timeout: 60_000 });
  });

  test('every cell has an accessible name', async ({ page }) => {
    const cells = page.locator('.hm-cell:not([disabled])');
    const names = await accessibleNames(cells);
    expect(names.length).toBeGreaterThan(0);
    expect(names.filter((n) => !n).length, 'unnamed heatmap cells').toBe(0);
  });

  test('the matrix is not one tab stop per cell', async ({ page }) => {
    const rows = await page.locator('.hm-row-text').count();
    const stops = await tabStops(page.locator('matches-heatmap'));
    expect(stops, `${stops} tab stops for ${rows} rows`).toBeLessThanOrEqual(rows);
  });

  test('keyboard focus shows the matchup details and arrows move between cells', async ({ page }) => {
    const first = page.locator('.hm-cell:not([disabled])').first();
    await first.focus();
    await expect(page.locator('.hm-tip, [role="tooltip"]').first()).toBeVisible();
    await page.keyboard.press('ArrowRight');
    expect(await activeIsOneOf(page, '.hm-cell')).toBe(true);
    expect(await first.evaluate((el) => el === document.activeElement)).toBe(false);
  });
});

// ---- matchup replays --------------------------------------------------------------------------
test('a replay can be opened from the matchup list with the keyboard', async ({ page }) => {
  await gotoMatchup(page, 'tourney', 'tic_tac_toe_world1', 'gpt_5.4_nano/001', 'claude_fable_5.1_high/002');
  const control = page.locator('.mu-table').getByRole('button', { name: /replay/i })
    .or(page.locator('.mu-table').getByRole('link', { name: /replay/i }))
    .first();
  await expect(control).toBeVisible();
  await control.focus();
  await expect(control).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(page).toHaveURL(/[?&]m=\d+/);
  await expect(page.locator('matches-replay')).toBeVisible();
});
