// Audit issue 4: Create loses the draft on in-app navigation, and "Blank template" changes only
// the label while keeping the previous example and its compiled state.
import { expect, test, type Page } from '@playwright/test';
import {
  RUNTIME_TIMEOUT, STARTER_MARKER, compileAndWait, create, editorText, expectNotRunnable, gotoCreate, selectGame,
  setCode, settleCompile, slowPolicy
} from './helpers';

test.describe.configure({ timeout: RUNTIME_TIMEOUT * 2 });

test.beforeEach(async ({ page }) => {
  // a fix may confirm before discarding edits; accept so the action under test goes through
  page.on('dialog', (d) => void d.accept());
  await gotoCreate(page);
  await selectGame(page, 'Connect 4');
});

async function loadExample(page: Page, index: number): Promise<string> {
  const { example } = create(page);
  await expect(example.locator('option')).not.toHaveCount(1, { timeout: 60_000 });
  const value = await example.locator('option').nth(index).getAttribute('value');
  const before = await editorText(page);
  await example.selectOption(value!);
  await expect.poll(() => editorText(page), { timeout: 60_000 }).not.toBe(before);
  return editorText(page);
}

test('draft and game survive navigating Home and back', async ({ page }) => {
  const draft = `def policy(board):\n    return 3  # my unsaved draft\n`;
  await setCode(page, draft);
  await page.getByRole('navigation', { name: 'Main' }).getByRole('button', { name: 'Home' }).click();
  await page.getByRole('navigation', { name: 'Main' }).getByRole('button', { name: 'Create Automata' }).click();
  await expect(create(page).game).toHaveValue(/connect4/);
  await expect.poll(() => editorText(page)).toContain('my unsaved draft');
});

test('an explicit reset restores the starter template', async ({ page }) => {
  await setCode(page, `def policy(board):\n    return 3  # draft\n`);
  const reset = page.getByRole('button', { name: /reset/i });
  await expect(reset, 'Create needs an explicit reset action').toBeVisible({ timeout: 5_000 });
  await reset.click();
  await expect.poll(() => editorText(page)).toContain(STARTER_MARKER);
  await expectNotRunnable(page);
});

test('Blank after a successful compile restores the starter and blocks Run', async ({ page }) => {
  await loadExample(page, 1);
  await compileAndWait(page);
  await expect(create(page).run).toBeEnabled();
  await create(page).example.selectOption('');
  await expect(create(page).example).toHaveValue('');
  await expect.poll(() => editorText(page)).toContain(STARTER_MARKER);
  await expectNotRunnable(page);
});

test('Blank while compiling restores the starter and the late result is ignored', async ({ page }) => {
  await loadExample(page, 1);
  await setCode(page, slowPolicy('return 3'));
  await create(page).compileIdle.click();
  await create(page).example.selectOption('');
  await settleCompile(page);
  await expect.poll(() => editorText(page)).toContain(STARTER_MARKER);
  await expectNotRunnable(page);
});

test('switching examples replaces the code and invalidates the compile', async ({ page }) => {
  const first = await loadExample(page, 1);
  await compileAndWait(page);
  await expect(create(page).run).toBeEnabled();
  const second = await loadExample(page, 2);
  expect(second).not.toBe(first);
  await expectNotRunnable(page);
});
