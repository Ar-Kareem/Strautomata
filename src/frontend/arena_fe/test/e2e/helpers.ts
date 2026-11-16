import { expect, type Locator, type Page } from '@playwright/test';

export const RUNTIME_TIMEOUT = 180_000;

// ---- policies ---------------------------------------------------------------------------------
export const FIRST_LEGAL = `def policy(_debug_legal_moves, **kw):
    m = _debug_legal_moves[0]
    return m.get_unparsed_str() if hasattr(m, "get_unparsed_str") else m
`;
export const TTT_FIRST_EMPTY = `def policy(board):
    for r in range(len(board)):
        for c in range(len(board[r])):
            if board[r][c] == 0:
                return (r, c)
`;
export const TTT_CONSTANT = `def policy(board):
    return (0, 0)
`;
export const TTT_NUMPY = `def policy(board):
    return tuple(np.argwhere(np.array(board) == 0)[0])
`;
export const NIM_AUDIT = `def policy(piles):
    return next(f'{i},1' for i, n in enumerate(piles) if n)
`;
/** sleeps on the initial board so the compile stays pending long enough to change things under it */
export const slowPolicy = (body: string, secs = 3): string => `import time
def policy(**kwargs):
    time.sleep(${secs})
    ${body}
`;
export const STARTER_MARKER = 'raise NotImplementedError("write your automaton here")';

// ---- Create page ------------------------------------------------------------------------------
export const create = (page: Page) => ({
  game: page.getByRole('combobox', { name: 'Game' }),
  example: page.getByRole('combobox', { name: 'Start from a tournament automaton' }),
  lanes: page.getByRole('spinbutton', { name: 'Parallel matches' }),
  editor: page.locator('.cm-content'),
  compile: page.getByRole('button', { name: /^(Compile|Compiling…)$/ }),
  compileIdle: page.getByRole('button', { name: 'Compile', exact: true }),
  run: page.getByRole('button', { name: 'Run', exact: true }),
  ok: page.locator('.cr-ok'),
  fault: page.locator('.cr-editor .cr-fault'),
  qualCells: page.locator('.cr-qual-cell'),
  heatCells: page.locator('.cr-heat-cell')
});

export async function gotoCreate(page: Page): Promise<void> {
  await page.goto('/#/create');
  await expect(create(page).game).toBeVisible();
}

export async function selectGame(page: Page, label: string): Promise<void> {
  await create(page).game.selectOption({ label });
}

/** replace the editor content with `code` verbatim (insertText bypasses auto-indent) */
export async function setCode(page: Page, code: string): Promise<void> {
  const { editor } = create(page);
  await editor.click();
  await page.keyboard.press('ControlOrMeta+a');
  await page.keyboard.insertText(code);
  await expect.poll(() => editorText(page)).toBe(code.trim());
}

export async function editorText(page: Page): Promise<string> {
  return (await create(page).editor.innerText()).replace(/ /g, ' ').trim();
}

export async function compileAndWait(page: Page): Promise<void> {
  const c = create(page);
  await c.compileIdle.click();
  await expect(c.compileIdle).toBeVisible({ timeout: RUNTIME_TIMEOUT });
}

/** wait for an in-flight compile (possibly stale) to resolve, plus a margin for late results */
export async function settleCompile(page: Page, marginMs = 4_000): Promise<void> {
  await expect(create(page).compileIdle).toBeVisible({ timeout: RUNTIME_TIMEOUT });
  await page.waitForTimeout(marginMs);
}

export async function expectNotRunnable(page: Page): Promise<void> {
  const c = create(page);
  await expect(c.run).toBeDisabled();
  await expect(c.ok).toHaveCount(0);
}

const SETTLED = ['win', 'loss', 'draw', 'fault', 'gift', 'error'];

/** every qualification cell finished; returns their outcomes */
export async function waitForQualification(page: Page): Promise<string[]> {
  const cells = create(page).qualCells;
  await expect(cells).toHaveCount(10, { timeout: RUNTIME_TIMEOUT });
  await expect
    .poll(async () => (await cells.evaluateAll((els) => els.map((e) => e.getAttribute('data-outcome')))).every((o) => SETTLED.includes(o ?? '')), {
      timeout: RUNTIME_TIMEOUT
    })
    .toBe(true);
  return cells.evaluateAll((els) => els.map((e) => e.getAttribute('data-outcome') ?? ''));
}

// ---- Matches page -----------------------------------------------------------------------------
export async function gotoMatchup(page: Page, stage: 'quals' | 'tourney', game: string, botA: string, botB?: string): Promise<void> {
  const params = new URLSearchParams({ stage, game, bot: botA });
  if (botB) {
    params.set('vs', botB);
  }
  await page.goto(`/#/matches?${params}`);
  await expect(page.locator('.mu-summary, .mu-table').first()).toBeVisible({ timeout: 60_000 });
}

export function pointsOf(chipText: string): number {
  const m = chipText.match(/([\d.]+)\s+points?/);
  if (!m) {
    throw new Error(`no points in "${chipText}"`);
  }
  return Number(m[1]);
}

// ---- Play page --------------------------------------------------------------------------------
export async function gotoPlay(page: Page, game: string, world: string, matchup: 'AI vs AI' | 'Human vs AI' | 'Human vs Human'): Promise<void> {
  await page.goto(`/#/arena?game=${game}&sub=${world}`);
  const radio = page.getByRole('radio', { name: matchup });
  await expect(radio).toBeEnabled({ timeout: RUNTIME_TIMEOUT });
  await radio.click();
}

/** cells of the live match board (the game picker renders a preview board with the same classes) */
export function board(page: Page, cellSelector: string): Locator {
  return page.locator('arena-output').locator(cellSelector);
}

/** elements in `scope` that the Tab key can reach */
export async function tabStops(scope: Locator): Promise<number> {
  return scope.evaluate((root) => {
    const sel = 'a[href],button,input,select,textarea,[tabindex],[contenteditable="true"]';
    return [...root.querySelectorAll<HTMLElement>(sel)].filter((el) => {
      if (el.tabIndex < 0 || (el as HTMLButtonElement).disabled || el.closest('[inert]')) {
        return false;
      }
      const s = getComputedStyle(el);
      return s.visibility !== 'hidden' && s.display !== 'none';
    }).length;
  });
}

/** turn keyboard mode on once the board has targets (Space does nothing before then) */
export async function keyboardMode(page: Page): Promise<void> {
  await expect(page.locator('arena-output [data-kbd]').first()).toBeAttached({ timeout: RUNTIME_TIMEOUT });
  await page.keyboard.press('Space');
}
