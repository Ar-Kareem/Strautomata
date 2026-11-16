/**
 * Keyboard hint labels for every game board. Space toggles keyboard mode, which shows a hint over
 * each legal target, typing a hint clicks it, and a board that needs a second pick shows the next
 * set of hints. Boards put the label in a `data-kbd` attribute and mark the selected piece with
 * `data-kbd-back` so Backspace can step back. All labels come from this file so the boards can be checked against each other.
 *
 * Rules
 * - Square boards: file letter + rank number, a1 is the bottom-left square as drawn (chess).
 * - Big boards (10+ rows): column letter, then row letter on that column only (a is the bottom
 *   row), so the board isn't covered in hints. The column hint sits on the column's top edge.
 * - Small grids: the block of keys shaped like the board, qwe/asd/zxc or 1234/qwer/asdf/zxcv.
 * - One-step moves: the direction from the piece, w up, s down, a left, d right, q e z c diagonals.
 * - A row of choices: the number printed on the board, else the position counted from 1.
 * - Unnumbered lists: kbdList, home row first.
 * - Pass 0, bar b, bear off o.
 * - Numbers are padded to the board's widest one (k01 next to k11, 05 next to 23), so a full label
 *   never starts a longer one and always picks at once.
 *
 * Game            | First pick              | Second pick            | Third pick
 * ----------------|-------------------------|------------------------|-------------
 * amazons         | queen square            | destination square     | arrow square
 * backgammon      | point number, b bar     | point number, o off    |
 *                 | or a move from the list | or a move from the list|
 * battleships     | column letter           | row letter             |
 * breakthrough    | piece square            | direction              |
 * checkers        | piece square            | landing square         |
 * chess           | piece square            | destination square     |
 * clobber         | piece square            | direction              |
 * connect4        | column number           |                        |
 * dots_and_boxes  | line square on the grid of dots and lines         |
 * go              | column letter, 0 pass   | row letter             |
 * havannah        | column letter           | row letter             |
 * hex             | column letter           | row letter             |
 * lines_of_action | piece square            | destination square     |
 * mancala         | pit number as printed   |                        |
 * nim             | pile number + count, 13 takes 3 from pile 1      |
 * othello         | square                  |                        |
 * pentago         | square                  | quadrant q e z c + a (counterclockwise) or d (clockwise)
 * tic_tac_toe     | small grid, else square |                        |
 * tic_tac_toe_3d  | layer number, then small grid (else square) on the shown layer
 */

const FILES = 'abcdefghijklmnopqrstuvwxyz';

/** `value` with leading zeros to the width of `max` */
function padded(value: number, max: number): string {
  return String(value).padStart(String(max).length, '0');
}

/** Column letter of a square name. */
export function kbdFile(col: number): string {
  return FILES[col] ?? '?';
}

/** Row number of a square name. `rankFromBottom` is 0 for the bottom row as drawn. */
export function kbdRank(rankFromBottom: number, rows: number): string {
  return padded(rankFromBottom + 1, rows);
}

/** Row as a letter, a for the bottom row, for boards picked column then row (go). */
export function kbdRankLetter(rankFromBottom: number): string {
  return FILES[rankFromBottom] ?? '?';
}

/** Chess-style square name. `rankFromBottom` is 0 for the bottom row as drawn. */
export function kbdSquare(col: number, rankFromBottom: number, rows: number): string {
  return `${kbdFile(col)}${kbdRank(rankFromBottom, rows)}`;
}

/** Square name for a board drawn with row 0 at the top. */
export function kbdSquareFromTop(col: number, rowFromTop: number, rows: number): string {
  return kbdSquare(col, rows - 1 - rowFromTop, rows);
}

const SMALL_GRIDS: Record<number, string[]> = {
  2: ['qw', 'as'],
  3: ['qwe', 'asd', 'zxc'],
  4: ['1234', 'qwer', 'asdf', 'zxcv']
};

/** Small square grids get the matching block of keys, larger ones fall back to square names. */
export function kbdGrid(col: number, rowFromTop: number, size: number): string {
  return SMALL_GRIDS[size]?.[rowFromTop]?.[col] ?? kbdSquareFromTop(col, rowFromTop, size);
}

/** A layer of the 3D board: the small grid while it leaves the digits free for layer numbers. */
export function kbdLayerGrid(col: number, rowFromTop: number, size: number): string {
  return size <= 3 ? kbdGrid(col, rowFromTop, size) : kbdSquareFromTop(col, rowFromTop, size);
}

/** Direction of a one-step move as drawn on screen. */
export function kbdDirection(dRowDown: number, dCol: number): string {
  const vertical = Math.sign(dRowDown);
  const horizontal = Math.sign(dCol);
  return [
    ['q', 'w', 'e'],
    ['a', '', 'd'],
    ['z', 's', 'c']
  ][vertical + 1][horizontal + 1];
}

/** 1-based position in a row of `count` choices. */
export function kbdNumber(index: number, count: number): string {
  return padded(index + 1, count);
}

/** A number printed on the board, out of numbers up to `max`. */
export function kbdPrinted(value: number, max: number): string {
  return padded(value, max);
}

export const KBD_PASS = '0';
export const KBD_BAR = 'b';
export const KBD_OFF = 'o';

/** Nim: pile number then how many to take. */
export function kbdNimTake(pileIndex: number, take: number, piles: number, maxTake: number): string {
  return `${padded(pileIndex + 1, piles)}${padded(take, maxTake)}`;
}

const PENTAGO_QUADRANTS = ['q', 'e', 'z', 'c'];

/** Pentago rotation: quadrant (q e z c, laid out like the board) then a for left (counterclockwise) or d for right. */
export function kbdPentagoRotation(quadrant: number, direction: 'L' | 'R'): string {
  return `${PENTAGO_QUADRANTS[quadrant] ?? '?'}${direction === 'L' ? 'a' : 'd'}`;
}

// skips b and o so a list can sit next to the bar and bear-off hints
const LIST_KEYS = 'asdfghjklqwertyuipzxcvnm';

/** Labels for an unnumbered list. Every label has the same length so none is a prefix of another. */
export function kbdList(count: number): string[] {
  const keys = LIST_KEYS;
  let length = 1;
  while (keys.length ** length < count) {
    length += 1;
  }
  const labels: string[] = [];
  for (let i = 0; i < count; i += 1) {
    let label = '';
    let rest = i;
    for (let j = 0; j < length; j += 1) {
      label = keys[rest % keys.length] + label;
      rest = Math.floor(rest / keys.length);
    }
    labels.push(label);
  }
  return labels;
}
