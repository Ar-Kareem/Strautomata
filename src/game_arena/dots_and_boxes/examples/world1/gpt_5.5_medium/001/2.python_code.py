
import numpy as np
from functools import lru_cache

# 4x4 boxes:
# Horizontal playable edges: rows 0..4, cols 0..3  -> 20
# Vertical playable edges:   rows 0..3, cols 0..4  -> 20
# Total playable edges: 40

H_COUNT = 20
V_COUNT = 20
EDGE_COUNT = 40
FULL_MASK = (1 << EDGE_COUNT) - 1

# Exact solve is used when, after our candidate move, at most this many edges remain.
# This keeps runtime safe while still solving most tactical/endgame positions exactly.
EXACT_CHILD_LIMIT = 18

IDX_TO_MOVE = []
MOVE_TO_IDX = {}

# Horizontal edge indices: 0..19
for r in range(5):
    for c in range(4):
        idx = r * 4 + c
        IDX_TO_MOVE.append((r, c, "H"))
        MOVE_TO_IDX[(r, c, "H")] = idx

# Vertical edge indices: 20..39
for r in range(4):
    for c in range(5):
        idx = 20 + r * 5 + c
        IDX_TO_MOVE.append((r, c, "V"))
        MOVE_TO_IDX[(r, c, "V")] = idx

# Box masks and edge adjacency.
BOX_MASKS = []
EDGE_BOXES = [[] for _ in range(EDGE_COUNT)]

for br in range(4):
    for bc in range(4):
        top = MOVE_TO_IDX[(br, bc, "H")]
        bottom = MOVE_TO_IDX[(br + 1, bc, "H")]
        left = MOVE_TO_IDX[(br, bc, "V")]
        right = MOVE_TO_IDX[(br, bc + 1, "V")]
        mask = (1 << top) | (1 << bottom) | (1 << left) | (1 << right)
        box_idx = br * 4 + bc
        BOX_MASKS.append(mask)
        for e in (top, bottom, left, right):
            EDGE_BOXES[e].append(box_idx)


def _state_to_mask(horizontal: np.ndarray, vertical: np.ndarray) -> int:
    """Convert occupied playable edges to a 40-bit mask."""
    mask = 0

    for r in range(5):
        for c in range(4):
            if horizontal[r, c] != 0:
                mask |= 1 << MOVE_TO_IDX[(r, c, "H")]

    for r in range(4):
        for c in range(5):
            if vertical[r, c] != 0:
                mask |= 1 << MOVE_TO_IDX[(r, c, "V")]

    return mask


def _move_string(idx: int) -> str:
    r, c, d = IDX_TO_MOVE[idx]
    return f"{r},{c},{d}"


def _box_side_count(mask: int, box_idx: int) -> int:
    return (mask & BOX_MASKS[box_idx]).bit_count()


def _capture_count(mask: int, edge_idx: int) -> int:
    """How many boxes are completed by playing edge_idx?"""
    bit = 1 << edge_idx
    if mask & bit:
        return -1

    new_mask = mask | bit
    made = 0

    for b in EDGE_BOXES[edge_idx]:
        bm = BOX_MASKS[b]
        if (mask & bm) != bm and (new_mask & bm) == bm:
            made += 1

    return made


def _danger_count(mask: int, edge_idx: int) -> int:
    """
    Number of adjacent boxes that become 3-sided after this non-capturing move.
    These are boxes likely handed to the opponent.
    """
    bit = 1 << edge_idx
    if mask & bit:
        return 99

    danger = 0
    for b in EDGE_BOXES[edge_idx]:
        before = _box_side_count(mask, b)
        if before == 2:
            danger += 1
    return danger


def _legal_indices(mask: int):
    empty = (~mask) & FULL_MASK
    while empty:
        bit = empty & -empty
        idx = bit.bit_length() - 1
        yield idx
        empty ^= bit


def _safe_move_count(mask: int) -> int:
    count = 0
    for idx in _legal_indices(mask):
        if _capture_count(mask, idx) == 0 and _danger_count(mask, idx) == 0:
            count += 1
    return count


def _capturing_move_count(mask: int) -> int:
    count = 0
    for idx in _legal_indices(mask):
        if _capture_count(mask, idx) > 0:
            count += 1
    return count


def _count_boxes_with_sides(mask: int, sides: int) -> int:
    total = 0
    for b in range(16):
        if _box_side_count(mask, b) == sides:
            total += 1
    return total


def _greedy_opponent_gain(mask: int) -> int:
    """
    Estimate how many boxes the opponent can immediately collect after we make
    a sacrificial move. This is not exact game theory, but it is a good chain
    opening heuristic when exact minimax is too expensive.
    """
    gained = 0
    m = mask

    while True:
        best_idx = None
        best_score = -10**9
        best_cap = 0

        for idx in _legal_indices(m):
            cap = _capture_count(m, idx)
            if cap <= 0:
                continue

            nm = m | (1 << idx)
            # Prefer larger immediate captures, then continuations.
            score = cap * 100 + _capturing_move_count(nm) * 5 - _count_boxes_with_sides(nm, 2)
            if score > best_score:
                best_score = score
                best_idx = idx
                best_cap = cap

        if best_idx is None:
            break

        m |= 1 << best_idx
        gained += best_cap

        if gained >= 16:
            break

    return gained


def _heuristic_score(mask: int, idx: int) -> float:
    """
    Heuristic tie-break / early-game evaluation for one move.
    Higher is better for the player to move.
    """
    cap = _capture_count(mask, idx)
    nm = mask | (1 << idx)

    if cap > 0:
        # Capturing is usually mandatory/good. Prefer double captures and moves
        # that keep a capture sequence alive.
        return (
            10000.0 * cap
            + 80.0 * _capturing_move_count(nm)
            - 4.0 * _count_boxes_with_sides(nm, 2)
            - 0.001 * idx
        )

    danger = _danger_count(mask, idx)

    if danger == 0:
        # Safe move. Try to reduce the opponent's safe options, while avoiding
        # too many 2-sided boxes.
        safe_after = _safe_move_count(nm)
        twos = _count_boxes_with_sides(nm, 2)
        ones = _count_boxes_with_sides(nm, 1)
        adjacency_bonus = len(EDGE_BOXES[idx])  # interior edges are often more flexible

        return (
            -8.0 * safe_after
            -3.0 * twos
            -0.4 * ones
            +0.25 * adjacency_bonus
            -0.001 * idx
        )

    # Forced unsafe move: open the least costly chain.
    opp_gain = _greedy_opponent_gain(nm)
    threes = _count_boxes_with_sides(nm, 3)

    return (
        -1000.0 * opp_gain
        -40.0 * danger
        -2.0 * threes
        -0.001 * idx
    )


@lru_cache(maxsize=None)
def _solve_exact(mask: int) -> int:
    """
    Exact future margin from this position for the player to move.

    Return value:
      maximum future boxes for current player minus future boxes for opponent.

    Extra-turn rule:
      If a move captures boxes, the same player moves again:
          value = captured + solve(new_state)
      Otherwise turn passes:
          value = -solve(new_state)
    """
    if mask == FULL_MASK:
        return 0

    best = -1000

    # Move ordering: captures first helps cache usefulness in practice.
    capturing = []
    others = []

    for idx in _legal_indices(mask):
        cap = _capture_count(mask, idx)
        if cap > 0:
            capturing.append((idx, cap))
        else:
            others.append((idx, cap))

    moves = capturing + others

    for idx, cap in moves:
        nm = mask | (1 << idx)
        if cap > 0:
            val = cap + _solve_exact(nm)
        else:
            val = -_solve_exact(nm)

        if val > best:
            best = val

    return best


def _choose_exact(mask: int):
    """Choose an exact minimax move if the remaining edge count is small enough."""
    remaining = EDGE_COUNT - mask.bit_count()

    # After one candidate move, exact search must have at most EXACT_CHILD_LIMIT edges.
    if remaining - 1 > EXACT_CHILD_LIMIT:
        return None

    best_idx = None
    best_val = -1000
    best_h = -10**18

    for idx in _legal_indices(mask):
        cap = _capture_count(mask, idx)
        nm = mask | (1 << idx)

        if cap > 0:
            val = cap + _solve_exact(nm)
        else:
            val = -_solve_exact(nm)

        h = _heuristic_score(mask, idx)

        if val > best_val or (val == best_val and h > best_h):
            best_val = val
            best_h = h
            best_idx = idx

    return best_idx


def _choose_heuristic(mask: int) -> int:
    """
    Main non-exact policy:
      1. Capture if possible.
      2. Otherwise play a safe move if possible.
      3. Otherwise sacrifice the least damaging edge.
    """
    capturing = []
    safe = []
    unsafe = []

    for idx in _legal_indices(mask):
        cap = _capture_count(mask, idx)
        if cap > 0:
            capturing.append(idx)
        else:
            danger = _danger_count(mask, idx)
            if danger == 0:
                safe.append(idx)
            else:
                unsafe.append(idx)

    if capturing:
        candidates = capturing
    elif safe:
        candidates = safe
    else:
        candidates = unsafe

    best_idx = candidates[0]
    best_score = -10**18

    for idx in candidates:
        score = _heuristic_score(mask, idx)
        if score > best_score:
            best_score = score
            best_idx = idx

    return best_idx


def _fallback_legal(horizontal: np.ndarray, vertical: np.ndarray) -> str:
    """
    Defensive fallback. Prefer real 4x4 playable edges; then any empty array slot.
    This should almost never be needed.
    """
    for r in range(5):
        for c in range(4):
            if horizontal[r, c] == 0:
                return f"{r},{c},H"

    for r in range(4):
        for c in range(5):
            if vertical[r, c] == 0:
                return f"{r},{c},V"

    # If the arena treats the full 5x5 arrays as legal, try padding entries.
    for r in range(5):
        for c in range(5):
            if horizontal[r, c] == 0:
                return f"{r},{c},H"

    for r in range(5):
        for c in range(5):
            if vertical[r, c] == 0:
                return f"{r},{c},V"

    # Game should be over if this happens.
    return "0,0,H"


def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    Return the next move as 'row,col,dir'.

    horizontal, vertical, capture are 5x5 numpy arrays.
    The player to move is always us.
    """
    try:
        mask = _state_to_mask(horizontal, vertical)

        if mask == FULL_MASK:
            return _fallback_legal(horizontal, vertical)

        exact_idx = _choose_exact(mask)
        if exact_idx is not None:
            return _move_string(exact_idx)

        idx = _choose_heuristic(mask)
        return _move_string(idx)

    except Exception:
        # Never fail to return a legal-looking move.
        return _fallback_legal(horizontal, vertical)
