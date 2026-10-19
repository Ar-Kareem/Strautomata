import { describe, expect, it } from 'vitest';
import { kbdDirection, kbdGrid, kbdLayerGrid, kbdList, kbdNimTake, kbdNumber, kbdRankLetter, kbdSquare, kbdSquareFromTop } from './arena-kbd-keys';
import { matchKbd } from './arena-kbd-layer.component';

describe('keyboard hint labels', () => {
  it('names squares from the bottom-left as drawn', () => {
    expect(kbdSquare(0, 0, 8)).toBe('a1');
    expect(kbdSquare(4, 3, 8)).toBe('e4');
    expect(kbdSquareFromTop(0, 0, 8)).toBe('a8');
    expect(kbdSquareFromTop(7, 7, 8)).toBe('h1');
    // go picks the row as a letter too
    expect([kbdRankLetter(0), kbdRankLetter(18)]).toEqual(['a', 's']);
  });

  it('pads numbers so no full label starts a longer one', () => {
    expect(kbdSquare(10, 0, 11)).toBe('k01');
    expect(kbdSquare(10, 10, 11)).toBe('k11');
    expect(kbdNumber(0, 7)).toBe('1');
    expect(kbdNumber(0, 12)).toBe('01');
    expect(kbdNimTake(0, 3, 4, 7)).toBe('13');
    expect(kbdNimTake(0, 3, 11, 12)).toBe('0103');
  });

  it('lays small grids out like the keyboard', () => {
    const rows = (size: number) =>
      Array.from({ length: size }, (_, r) => Array.from({ length: size }, (_, c) => kbdGrid(c, r, size)).join(''));
    expect(rows(3)).toEqual(['qwe', 'asd', 'zxc']);
    expect(rows(4)).toEqual(['1234', 'qwer', 'asdf', 'zxcv']);
    expect(kbdGrid(0, 0, 5)).toBe('a5');
    expect(kbdGrid(0, 0, 11)).toBe('a11');
    // 3D layers keep the digits for layer numbers
    expect(kbdLayerGrid(0, 0, 4)).toBe('a4');
  });

  it('maps one-step moves to wasd and the diagonals around them', () => {
    expect([kbdDirection(-1, 0), kbdDirection(1, 0), kbdDirection(0, -1), kbdDirection(0, 1)]).toEqual(['w', 's', 'a', 'd']);
    expect([kbdDirection(-1, -1), kbdDirection(-1, 1), kbdDirection(1, -1), kbdDirection(1, 1)]).toEqual(['q', 'e', 'z', 'c']);
  });

  it('gives lists prefix-free labels without b or o', () => {
    for (const count of [1, 5, 24, 25, 600]) {
      const labels = kbdList(count);
      expect(new Set(labels).size).toBe(count);
      expect(labels.some((a) => labels.some((b) => a !== b && b.startsWith(a)))).toBe(false);
      expect(labels.join('')).not.toMatch(/[bo]/);
    }
  });
});

describe('matchKbd', () => {
  const labels = ['a1', 'a10', 'a2', 'b1'];

  it('narrows to the labels that start with what was typed', () => {
    expect(matchKbd(labels, 'a').visible).toEqual([0, 1, 2]);
    expect(matchKbd(labels, 'x').visible).toEqual([]);
  });

  it('picks a full label only when nothing longer starts with it', () => {
    expect(matchKbd(labels, 'a2').pick).toBe(2);
    expect(matchKbd(labels, 'a1')).toEqual({ visible: [0, 1], exact: 0, pick: null });
    expect(matchKbd(labels, 'a10').pick).toBe(1);
  });
});
