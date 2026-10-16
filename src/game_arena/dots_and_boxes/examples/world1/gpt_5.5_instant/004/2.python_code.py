
import numpy as np
from typing import List, Tuple

# Dots and Boxes policy for a 4x4 box grid.
# Move format: "row,col,H" or "row,col,V"


Move = Tuple[int, int, str]


def _legal_moves(horizontal: np.ndarray, vertical: np.ndarray) -> List[Move]:
    moves = []
    # In the provided representation arrays are 5x5, but only:
    # horizontal rows 0..4, cols 0..3 are real box edges
    # vertical rows 0..3, cols 0..4 are real box edges
    for r in range(5):
        for c in range(4):
            if horizontal[r, c] == 0:
                moves.append((r, c, "H"))
    for r in range(4):
        for c in range(5):
            if vertical[r, c] == 0:
                moves.append((r, c, "V"))
    return moves


def _box_sides(horizontal: np.ndarray, vertical: np.ndarray, r: int, c: int) -> int:
    """Number of drawn sides around box (r,c), where r,c in 0..3."""
    return int(horizontal[r, c] != 0) + int(horizontal[r + 1, c] != 0) + \
           int(vertical[r, c] != 0) + int(vertical[r, c + 1] != 0)


def _adjacent_boxes(move: Move) -> List[Tuple[int, int]]:
    r, c, d = move
    boxes = []
    if d == "H":
        # box above
        if r > 0 and c < 4:
            boxes.append((r - 1, c))
        # box below
        if r < 4 and c < 4:
            boxes.append((r, c))
    else:
        # box left
        if c > 0 and r < 4:
            boxes.append((r, c - 1))
        # box right
        if c < 4 and r < 4:
            boxes.append((r, c))
    return boxes


def _captures(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray, move: Move) -> int:
    """How many currently unclaimed boxes this move completes."""
    count = 0
    for br, bc in _adjacent_boxes(move):
        if capture[br, bc] == 0:
            if _box_sides(horizontal, vertical, br, bc) == 3:
                count += 1
    return count


def _apply_move(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray, move: Move):
    """Return copied state after applying our move and claiming completed boxes."""
    h = horizontal.copy()
    v = vertical.copy()
    cap = capture.copy()
    r, c, d = move
    if d == "H":
        h[r, c] = 1
    else:
        v[r, c] = 1

    for br, bc in _adjacent_boxes(move):
        if cap[br, bc] == 0 and _box_sides(h, v, br, bc) == 4:
            cap[br, bc] = 1
    return h, v, cap


def _creates_three_boxes(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray, move: Move) -> int:
    """
    Number of adjacent unclaimed boxes that would have exactly 3 sides after this move,
    excluding boxes captured by the move.
    """
    h, v, cap = _apply_move(horizontal, vertical, capture, move)
    count = 0
    for br, bc in _adjacent_boxes(move):
        if cap[br, bc] == 0 and _box_sides(h, v, br, bc) == 3:
            count += 1
    return count


def _total_three_boxes(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> int:
    n = 0
    for r in range(4):
        for c in range(4):
            if capture[r, c] == 0 and _box_sides(horizontal, vertical, r, c) == 3:
                n += 1
    return n


def _immediate_capture_potential(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> int:
    """Maximum boxes opponent could take with one immediate move."""
    best = 0
    for m in _legal_moves(horizontal, vertical):
        best = max(best, _captures(horizontal, vertical, capture, m))
    return best


def _safe_score(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray, move: Move) -> float:
    """
    Score a non-capturing safe move.
    Prefer edges adjacent to boxes with more existing sides, but never creating 3-sides.
    Also mildly prefer boundary edges to reduce dangerous shared-edge effects.
    """
    score = 0.0
    adj = _adjacent_boxes(move)

    for br, bc in adj:
        if capture[br, bc] == 0:
            score += _box_sides(horizontal, vertical, br, bc)

    r, c, d = move
    if d == "H":
        if r == 0 or r == 4:
            score += 0.25
    else:
        if c == 0 or c == 4:
            score += 0.25

    # Prefer central-ish play slightly when otherwise equal.
    if d == "H":
        score -= 0.01 * (abs(r - 2) + abs(c - 1.5))
    else:
        score -= 0.01 * (abs(r - 1.5) + abs(c - 2))

    return score


def _sacrifice_score(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray, move: Move) -> float:
    """
    Lower-risk scoring for forced unsafe moves.
    We simulate the move and estimate how much it gives away.
    Higher is better.
    """
    h, v, cap = _apply_move(horizontal, vertical, capture, move)

    opp_best = _immediate_capture_potential(h, v, cap)
    three_count = _total_three_boxes(h, v, cap)
    created = _creates_three_boxes(horizontal, vertical, capture, move)

    # Prefer giving one box over two; prefer fewer 3-sided boxes overall.
    score = -10.0 * opp_best - 2.0 * created - 0.5 * three_count

    # If all sacrifices are bad, prefer opening on boundary, often limits damage.
    r, c, d = move
    if d == "H" and (r == 0 or r == 4):
        score += 0.2
    if d == "V" and (c == 0 or c == 4):
        score += 0.2

    return score


def _chain_capture_score(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray, move: Move) -> float:
    """
    Score capturing moves. Usually taking boxes is best. Prefer double captures.
    If there are many captures, prefer moves that keep capture opportunities alive.
    """
    cap_count = _captures(horizontal, vertical, capture, move)
    h, v, cap = _apply_move(horizontal, vertical, capture, move)

    # Since capture grants another turn, immediate future captures are valuable.
    future = _immediate_capture_potential(h, v, cap)
    remaining_three = _total_three_boxes(h, v, cap)

    return 100.0 * cap_count + 5.0 * future + 0.5 * remaining_three


def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    legal = _legal_moves(horizontal, vertical)

    # Absolute fallback if representation is unusual.
    if not legal:
        for r in range(5):
            for c in range(5):
                if horizontal[r, c] == 0:
                    return f"{r},{c},H"
                if vertical[r, c] == 0:
                    return f"{r},{c},V"
        return "0,0,H"

    # 1. Take any available capture, choosing the best.
    capturing = [m for m in legal if _captures(horizontal, vertical, capture, m) > 0]
    if capturing:
        best = max(capturing, key=lambda m: _chain_capture_score(horizontal, vertical, capture, m))
        return f"{best[0]},{best[1]},{best[2]}"

    # 2. Choose a safe non-capturing move: one that does not create a 3-sided box.
    safe = [m for m in legal if _creates_three_boxes(horizontal, vertical, capture, m) == 0]
    if safe:
        best = max(safe, key=lambda m: _safe_score(horizontal, vertical, capture, m))
        return f"{best[0]},{best[1]},{best[2]}"

    # 3. Forced sacrifice: minimize opponent's immediate gain.
    best = max(legal, key=lambda m: _sacrifice_score(horizontal, vertical, capture, m))
    return f"{best[0]},{best[1]},{best[2]}"
