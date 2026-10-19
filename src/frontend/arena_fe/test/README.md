# Frontend regression tests (pre-release audit)

One file per audit issue. Each test fails on the audited behaviour and passes once it is fixed.

| Issue | Python runner (`python/`) | Browser (`e2e/`) |
|---|---|---|
| 1. Move conversion, false qualification results | `test_arena_runner.py` | `01-move-conversion.e2e.ts` |
| 2. NumPy move serialization and replay | `test_arena_runner.py` | `02-numpy-replay.e2e.ts` |
| 3. Stale compile results | | `03-stale-compile.e2e.ts` |
| 4. Drafts and Blank template | | `04-drafts-and-blank.e2e.ts` |
| 5. Draws missing from matchup points | | `05-matchup-points.e2e.ts` |
| 6. Keyboard accessibility | | `06-keyboard-a11y.e2e.ts` |
| 7. Human vs Human labels | | `07-human-labels.e2e.ts` |
| v1.9 retest: Backgammon H/L replay, stale opponents/prompt, runtime errors scored as faults, replay move order and move list, Connect 4 human labels | `test_arena_runner.py` (Backgammon) | `08-retest.e2e.ts` |
| Keyboard hints on every board (labels in `arena-kbd-keys.ts`, unit tests in `arena-kbd.spec.ts`) | | `09-kbd-*.e2e.ts` |

## Python runner tests

`public/arena.runner.py` is the Python the browser runs in Pyodide. These tests run that same file under CPython against `src/game_arena`, covering all 20 game-worlds in seconds.

```bash
npm run test:runner
# same as: cd src && ../env3.12/bin/python -m pytest frontend/arena_fe/test/python -q
```

## Browser tests (Playwright)

```bash
# against a dev server that is already running
E2E_BASE_URL=http://127.0.0.1:4299 npm run test:e2e -- --project=chromium

# or let Playwright start `ng serve` on port 4320 (E2E_PORT to change)
npm run test:e2e -- --project=chromium

# one issue
npm run test:e2e -- --project=chromium 03
```

Tests run in parallel on half the CPU cores (`E2E_WORKERS=n` to change). The full Chromium suite takes about 1 minute on 32 workers and about 7 minutes on 1. Each test boots its own Pyodide, which takes 4-6s, most of it CPU: Pyodide 0.26 cannot snapshot a runtime that has numpy and pyspiel loaded.

Projects: `chromium`, `firefox`, `webkit` (Safari engine), `mobile-chrome`. `@playwright/test` is pinned to 1.58.0 because it matches the Chromium build already cached in `~/.cache/ms-playwright`. The other browsers need `npx playwright install firefox webkit` first.

Reports go to `e2e/playwright-report/`.

## Choices a fix has to satisfy

- **Issue 1:** if the random baseline itself cannot play, the match must not come back as a user win with `culprit_name == "random"`. How the infrastructure error is reported is up to the fix.
- **Issue 3:** a compile started before a game switch, a code edit, or a switch away and back must never enable Run, and its error must not be shown.
- **Issue 4:** drafts survive in-app navigation, and a button whose name matches `/reset/i` restores the starter template. Native confirm dialogs are accepted automatically.
- **Issue 6:**
  - Picker options get focus either directly or through `aria-activedescendant`.
  - Board cells keep their current classes (`.tic-tac-toe-cell`, `.connect4-cell`, `.hex-cell`, `.chess-cell`), and a cell's accessible name changes when a piece is placed.
  - The heatmap has at most one tab stop per row and supports arrow-key movement.
- **Issue 7:** turn, scoreboard and winner labels name the side (X/O, red/blue, or player 1/2).
