
import numpy as np
from functools import lru_cache

# ---------------------------------------------------------------------
# Board constants for a 4x4 box grid:
#   Horizontal edges: rows 0..4, cols 0..3  -> bits 0..19
#   Vertical edges:   rows 0..3, cols 0..4  -> bits 20..39
# ---------------------------------------------------------------------

_EDGE_STR = []
_EDGE_INFO = []

for r in range(5):
    for c in range(4):
        _EDGE_STR.append(f"{r},{c},H")
        _EDGE_INFO.append(("H", r, c))

for r in range(4):
    for c in range(5):
        _EDGE_STR.append(f"{r},{c},V")
        _EDGE_INFO.append(("V", r, c))

_FULL_MASK = (1 << 40) - 1

_BOX_MASKS = []
_ADJ = [[] for _ in range(40)]

for r in range(4):
    for c in range(4):
        top = r * 4 + c
        bottom = (r + 1) * 4 + c
        left = 20 + r * 5 + c
        right = 20 + r * 5 + (c + 1)

        m = (1 << top) | (1 << bottom) | (1 << left) | (1 << right)
        box_index = r * 4 + c
        _BOX_MASKS.append(m)

        _ADJ[top].append(box_index)
        _ADJ[bottom].append(box_index)
        _ADJ[left].append(box_index)
        _ADJ[right].append(box_index)

_ADJ = [tuple(x) for x in _ADJ]
_BOX_MASKS = tuple(_BOX_MASKS)

# Small positional tie-breaker: internal/central edges are mildly preferred
# when all other strategic features are equal.
_EDGE_BONUS = []
for i, (kind, r, c) in enumerate(_EDGE_INFO):
    bonus = 2.0 * len(_ADJ[i])
    if kind == "H":
        dist = abs(r - 2.0) + abs((c + 0.5) - 2.0)
    else:
        dist = abs((r + 0.5) - 2.0) + abs(c - 2.0)
    bonus += max(0.0, 3.0 - dist)
    _EDGE_BONUS.append(bonus)

_EXACT_THRESHOLD = 18


def _mask_from_arrays(horizontal, vertical):
    m = 0

    for r in range(5):
        for c in range(4):
            if horizontal[r, c] != 0:
                m |= 1 << (r * 4 + c)

    for r in range(4):
        for c in range(5):
            if vertical[r, c] != 0:
                m |= 1 << (20 + r * 5 + c)

    return m


def _capture_count(mask, idx):
    n = 0
    for b in _ADJ[idx]:
        if (mask & _BOX_MASKS[b]).bit_count() == 3:
            n += 1
    return n


def _creates_three(mask, idx):
    for b in _ADJ[idx]:
        if (mask & _BOX_MASKS[b]).bit_count() == 2:
            return True
    return False


def _count_boxes_with_sides(mask, sides):
    n = 0
    for bm in _BOX_MASKS:
        if (mask & bm).bit_count() == sides:
            n += 1
    return n


def _safe_count(mask):
    n = 0
    avail = _FULL_MASK & ~mask

    while avail:
        lsb = avail & -avail
        idx = lsb.bit_length() - 1

        if _capture_count(mask, idx) == 0 and not _creates_three(mask, idx):
            n += 1

        avail ^= lsb

    return n


@lru_cache(maxsize=500000)
def _exact_value(mask):
    """
    Exact future box differential from this mask, from the viewpoint of
    the player to move.

    If a move captures k boxes, the same player moves again:
        value = k + value(child)

    If a move captures no boxes, the turn passes:
        value = -value(child)
    """
    if mask == _FULL_MASK:
        return 0

    best = -100
    avail = _FULL_MASK & ~mask

    while avail:
        lsb = avail & -avail
        idx = lsb.bit_length() - 1
        new_mask = mask | lsb

        k = _capture_count(mask, idx)
        if k:
            val = k + _exact_value(new_mask)
        else:
            val = -_exact_value(new_mask)

        if val > best:
            best = val

        avail ^= lsb

    return best


@lru_cache(maxsize=100000)
def _greedy_capture_gain(mask):
    """
    Estimate how many boxes the player to move can collect by continuing
    to take available captures. This is not a full solve, but it is useful
    for evaluating chains when the board is still too large for exact search.
    """
    best = 0
    avail = _FULL_MASK & ~mask

    while avail:
        lsb = avail & -avail
        idx = lsb.bit_length() - 1
        k = _capture_count(mask, idx)

        if k:
            val = k + _greedy_capture_gain(mask | lsb)
            if val > best:
                best = val

        avail ^= lsb

    return best


def _fallback(horizontal, vertical):
    """
    Always return some empty edge if one exists.

    Real 4x4-board edges are tried first. The final 5x5-array scan is only
    a last-resort guard for unusual engines that consider every array entry
    playable.
    """
    for r in range(5):
        for c in range(4):
            if horizontal[r, c] == 0:
                return f"{r},{c},H"

    for r in range(4):
        for c in range(5):
            if vertical[r, c] == 0:
                return f"{r},{c},V"

    for r in range(5):
        for c in range(5):
            if horizontal[r, c] == 0:
                return f"{r},{c},H"

    for r in range(5):
        for c in range(5):
            if vertical[r, c] == 0:
                return f"{r},{c},V"

    # Should only happen after the game is over.
    return "0,0,H"


def _choose_exact(mask):
    best_idx = None
    best_val = -100
    best_tie = -10**9

    avail = _FULL_MASK & ~mask

    while avail:
        lsb = avail & -avail
        idx = lsb.bit_length() - 1
        new_mask = mask | lsb

        k = _capture_count(mask, idx)
        if k:
            val = k + _exact_value(new_mask)
        else:
            val = -_exact_value(new_mask)

        tie = _EDGE_BONUS[idx]
        if _capture_count(mask, idx) == 0 and not _creates_three(mask, idx):
            tie += 10.0

        if val > best_val or (val == best_val and tie > best_tie):
            best_val = val
            best_tie = tie
            best_idx = idx

        avail ^= lsb

    return best_idx


def _choose_heuristic(mask):
    legal = []
    captures = []
    safe = []

    avail = _FULL_MASK & ~mask

    while avail:
        lsb = avail & -avail
        idx = lsb.bit_length() - 1
        k = _capture_count(mask, idx)

        legal.append((idx, lsb, k))

        if k:
            captures.append((idx, lsb, k))
        elif not _creates_three(mask, idx):
            safe.append((idx, lsb, k))

        avail ^= lsb

    if not legal:
        return None

    # 1. Take captures. Prefer moves that take more boxes and continue a
    # capturing sequence.
    if captures:
        best_idx = captures[0][0]
        best_score = -10**9

        for idx, lsb, k in captures:
            new_mask = mask | lsb
            score = (
                1000.0 * (k + _greedy_capture_gain(new_mask))
                + 20.0 * _safe_count(new_mask)
                + _EDGE_BONUS[idx]
            )

            if score > best_score:
                best_score = score
                best_idx = idx

        return best_idx

    # 2. If possible, play a safe move that does not create a 3-sided box.
    if safe:
        best_idx = safe[0][0]
        best_score = -10**9

        for idx, lsb, _ in safe:
            new_mask = mask | lsb

            score = (
                50.0 * _safe_count(new_mask)
                - 3.0 * _count_boxes_with_sides(new_mask, 2)
                - 20.0 * _count_boxes_with_sides(new_mask, 3)
                + _EDGE_BONUS[idx]
            )

            if score > best_score:
                best_score = score
                best_idx = idx

        return best_idx

    # 3. No safe move exists: we must open something. Choose the move that
    # appears to give the opponent the smallest immediate chain.
    best_idx = legal[0][0]
    best_score = -10**9

    for idx, lsb, _ in legal:
        new_mask = mask | lsb

        opened_threes = 0
        for b in _ADJ[idx]:
            if (mask & _BOX_MASKS[b]).bit_count() == 2:
                opened_threes += 1

        opponent_gain = _greedy_capture_gain(new_mask)

        score = (
            -1000.0 * opponent_gain
            - 50.0 * opened_threes
            - 2.0 * _count_boxes_with_sides(new_mask, 3)
            + _EDGE_BONUS[idx]
        )

        if score > best_score:
            best_score = score
            best_idx = idx

    return best_idx


def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    try:
        mask = _mask_from_arrays(horizontal, vertical)

        if mask == _FULL_MASK:
            return _fallback(horizontal, vertical)

        remaining = 40 - mask.bit_count()

        if remaining <= _EXACT_THRESHOLD:
            idx = _choose_exact(mask)
        else:
            idx = _choose_heuristic(mask)

        if idx is None:
            return _fallback(horizontal, vertical)

        move = _EDGE_STR[idx]

        # Final legality guard against inconsistent inputs.
        kind, r, c = _EDGE_INFO[idx]
        if kind == "H":
            if horizontal[r, c] == 0:
                return move
        else:
            if vertical[r, c] == 0:
                return move

        return _fallback(horizontal, vertical)

    except Exception:
        return _fallback(horizontal, vertical)
