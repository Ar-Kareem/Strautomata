
import numpy as np
from typing import List, Tuple

# weight matrix for static evaluation
_WEIGHT = np.array([
    [120, -20,  20,   5,   5,  20, -20, 120],
    [-20, -40,  -5,  -5,  -5,  -5, -40, -20],
    [ 20,  -5,  15,   3,   3,  15,  -5,  20],
    [  5,  -5,   3,   3,   3,   3,  -5,   5],
    [  5,  -5,   3,   3,   3,   3,  -5,   5],
    [ 20,  -5,  15,   3,   3,  15,  -5,  20],
    [-20, -40,  -5,  -5,  -5,  -5, -40, -20],
    [120, -20,  20,   5,   5,  20, -20, 120],
], dtype=int)

_DIRECTIONS = [(-1, -1), (-1, 0), (-1, 1),
               (0, -1),          (0, 1),
               (1, -1),  (1, 0), (1, 1)]

def _in_bounds(r: int, c: int) -> bool:
    return 0 <= r < 8 and 0 <= c < 8

def _flippable_cells(r: int, c: int,
                     you: np.ndarray,
                     opp: np.ndarray) -> List[Tuple[int, int]]:
    """Return a list of opponent cells that would be flipped if we place at (r,c)."""
    flips = []
    for dr, dc in _DIRECTIONS:
        rr, cc = r + dr, c + dc
        line = []
        while _in_bounds(rr, cc) and opp[rr, cc] == 1:
            line.append((rr, cc))
            rr += dr
            cc += dc
        if line and _in_bounds(rr, cc) and you[rr, cc] == 1:
            flips.extend(line)
    return flips

def _legal_moves(you: np.ndarray, opp: np.ndarray) -> List[Tuple[int, int, List[Tuple[int, int]]]]:
    """Return a list of (r,c, flips) for every legal move."""
    moves = []
    empty = np.where((you == 0) & (opp == 0))
    for r, c in zip(empty[0], empty[1]):
        flips = _flippable_cells(r, c, you, opp)
        if flips:                     # at least one direction flips
            moves.append((r, c, flips))
    return moves

def _apply_move(you: np.ndarray, opp: np.ndarray,
                r: int, c: int,
                flips: List[Tuple[int, int]]) -> Tuple[np.ndarray, np.ndarray]:
    """Return new (you, opp) after placing at (r,c) and flipping."""
    new_you = you.copy()
    new_opp = opp.copy()
    new_you[r, c] = 1
    for fr, fc in flips:
        new_you[fr, fc] = 1
        new_opp[fr, fc] = 0
    return new_you, new_opp

def _score(you: np.ndarray, opp: np.ndarray) -> int:
    """Static evaluation using the weighted square table."""
    # we treat your discs as +weight, opponent discs as -weight
    return int(np.sum(_WEIGHT * you) - np.sum(_WEIGHT * opp))

def _coord_to_string(r: int, c: int) -> str:
    """Convert board indices to algebraic notation (e.g., a1)."""
    file_letter = chr(ord('a') + c)
    rank_digit = str(r + 1)               # rows are 0..7 → ranks 1..8
    return file_letter + rank_digit

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """
    Choose the best legal move according to a weighted‑square evaluation.
    Returns a move like "d3" or "pass" when no move is possible.
    """
    moves = _legal_moves(you, opponent)

    if not moves:
        return "pass"

    best_score = -10**9
    best_move = None

    for r, c, flips in moves:
        new_you, new_opp = _apply_move(you, opponent, r, c, flips)
        s = _score(new_you, new_opp)
        if s > best_score:
            best_score = s
            best_move = (r, c)

    # best_move is guaranteed to be set because moves list is non‑empty
    return _coord_to_string(best_move[0], best_move[1])
