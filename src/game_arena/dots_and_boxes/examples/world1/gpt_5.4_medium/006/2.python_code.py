
import numpy as np
from functools import lru_cache

# ------------------------------------------------------------
# Precomputed geometry for a 4x4 boxes board:
# - Horizontal edges: (row 0..4, col 0..3) => 20 edges
# - Vertical edges:   (row 0..3, col 0..4) => 20 edges
# Total real edges = 40
# ------------------------------------------------------------

H_IDX = {}
V_IDX = {}
EDGE_INFO = []          # idx -> (row, col, 'H'/'V')
IS_BOUNDARY_EDGE = []   # idx -> bool

# Horizontal edges
for r in range(5):
    for c in range(4):
        idx = len(EDGE_INFO)
        H_IDX[(r, c)] = idx
        EDGE_INFO.append((r, c, 'H'))
        IS_BOUNDARY_EDGE.append(r == 0 or r == 4)

# Vertical edges
for r in range(4):
    for c in range(5):
        idx = len(EDGE_INFO)
        V_IDX[(r, c)] = idx
        EDGE_INFO.append((r, c, 'V'))
        IS_BOUNDARY_EDGE.append(c == 0 or c == 4)

EDGE_TO_BOXES = [[] for _ in range(40)]  # edge idx -> list of adjacent box ids
BOX_MASKS = []                           # box id -> bitmask of its 4 edges

for r in range(4):
    for c in range(4):
        b = r * 4 + c
        edges = [
            H_IDX[(r, c)],
            H_IDX[(r + 1, c)],
            V_IDX[(r, c)],
            V_IDX[(r, c + 1)],
        ]
        mask = 0
        for e in edges:
            mask |= (1 << e)
            EDGE_TO_BOXES[e].append(b)
        BOX_MASKS.append(mask)

FULL_EDGE_MASK = (1 << 40) - 1
EXACT_LIMIT = 19  # exact search when <= 19 real edges remain


def _encode_move(idx: int) -> str:
    r, c, d = EDGE_INFO[idx]
    return f"{r},{c},{d}"


def _cap_count(occ: int, idx: int) -> int:
    """How many boxes are completed by drawing edge idx into occupancy occ?"""
    k = 0
    for b in EDGE_TO_BOXES[idx]:
        # This move completes box b iff box b currently has exactly 3 sides.
        if (occ & BOX_MASKS[b]).bit_count() == 3:
            k += 1
    return k


def _legal_moves_from_occ(occ: int):
    moves = []
    rem = FULL_EDGE_MASK ^ occ
    while rem:
        lsb = rem & -rem
        moves.append(lsb.bit_length() - 1)
        rem ^= lsb
    return moves


def _box_side_counts(occ: int):
    return [(occ & mask).bit_count() for mask in BOX_MASKS]


def _max_capture_available(occ: int) -> int:
    best = 0
    rem = FULL_EDGE_MASK ^ occ
    while rem:
        lsb = rem & -rem
        idx = lsb.bit_length() - 1
        rem ^= lsb
        k = _cap_count(occ, idx)
        if k > best:
            best = k
    return best


def _greedy_capture_gain(occ: int) -> int:
    """
    Approximate how many boxes the side to move can immediately harvest
    by greedily following available captures.
    """
    gain = 0
    cur = occ

    while True:
        rem = FULL_EDGE_MASK ^ cur
        best_idx = None
        best_key = None

        while rem:
            lsb = rem & -rem
            idx = lsb.bit_length() - 1
            rem ^= lsb

            k = _cap_count(cur, idx)
            if k <= 0:
                continue

            nxt = cur | (1 << idx)
            follow = _max_capture_available(nxt)
            key = (k, follow, int(IS_BOUNDARY_EDGE[idx]), -idx)

            if best_key is None or key > best_key:
                best_key = key
                best_idx = idx

        if best_idx is None:
            break

        gain += best_key[0]
        cur |= (1 << best_idx)

    return gain


@lru_cache(maxsize=None)
def _exact_value(occ: int) -> int:
    """
    Exact game-theoretic value from this occupancy state, from the perspective
    of the player to move:
        future_boxes_you - future_boxes_opponent
    """
    if occ == FULL_EDGE_MASK:
        return 0

    best = -100
    rem = FULL_EDGE_MASK ^ occ

    while rem:
        lsb = rem & -rem
        idx = lsb.bit_length() - 1
        rem ^= lsb

        k = _cap_count(occ, idx)
        nxt = occ | lsb

        if k > 0:
            val = k + _exact_value(nxt)   # same player moves again
        else:
            val = -_exact_value(nxt)      # turn passes

        if val > best:
            best = val

    return best


def _choose_exact_move(occ: int, legal_moves):
    best_idx = legal_moves[0]
    best_key = None

    for idx in legal_moves:
        nxt = occ | (1 << idx)
        k = _cap_count(occ, idx)
        val = (k + _exact_value(nxt)) if k > 0 else (-_exact_value(nxt))

        # Tie-breakers: prefer more immediate capture, then boundary, then lower idx
        key = (val, k, int(IS_BOUNDARY_EDGE[idx]), -idx)
        if best_key is None or key > best_key:
            best_key = key
            best_idx = idx

    return best_idx


def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    # Build occupancy bitmask from the real 40 edges only.
    occ = 0

    for r in range(5):
        for c in range(4):
            if int(horizontal[r, c]) != 0:
                occ |= (1 << H_IDX[(r, c)])

    for r in range(4):
        for c in range(5):
            if int(vertical[r, c]) != 0:
                occ |= (1 << V_IDX[(r, c)])

    legal_moves = _legal_moves_from_occ(occ)

    # Emergency fallback: should almost never happen.
    if not legal_moves:
        for r in range(5):
            for c in range(4):
                if int(horizontal[r, c]) == 0:
                    return f"{r},{c},H"
        for r in range(4):
            for c in range(5):
                if int(vertical[r, c]) == 0:
                    return f"{r},{c},V"

        # Last-resort scan of whole arrays in case environment treats extras as legal.
        for r in range(min(5, horizontal.shape[0])):
            for c in range(min(5, horizontal.shape[1])):
                if int(horizontal[r, c]) == 0:
                    return f"{r},{c},H"
        for r in range(min(5, vertical.shape[0])):
            for c in range(min(5, vertical.shape[1])):
                if int(vertical[r, c]) == 0:
                    return f"{r},{c},V"

        return "0,0,H"

    remaining = len(legal_moves)

    # Exact solve for endgames.
    if remaining <= EXACT_LIMIT:
        return _encode_move(_choose_exact_move(occ, legal_moves))

    counts = _box_side_counts(occ)

    capture_moves = []
    safe_moves = []
    all_moves = []

    for idx in legal_moves:
        cap = 0
        danger = 0
        twos = 0
        sum_before = 0

        for b in EDGE_TO_BOXES[idx]:
            cnt = counts[b]
            sum_before += cnt
            if cnt == 3:
                cap += 1
            elif cnt == 2:
                danger += 1
            elif cnt == 1:
                twos += 1

        feat = (idx, cap, danger, twos, sum_before)
        all_moves.append(feat)

        if cap > 0:
            capture_moves.append(feat)
        elif danger == 0:
            safe_moves.append(feat)

    # 1) Always take captures in the middlegame.
    if capture_moves:
        best_idx = capture_moves[0][0]
        best_key = None

        for idx, cap, danger, twos, sum_before in capture_moves:
            nxt = occ | (1 << idx)
            follow = _max_capture_available(nxt)

            key = (
                cap,                         # immediate boxes
                follow,                      # continuation potential
                -danger,                     # avoid odd self-complications if tied
                int(IS_BOUNDARY_EDGE[idx]),
                -sum_before,
                -idx
            )

            if best_key is None or key > best_key:
                best_key = key
                best_idx = idx

        return _encode_move(best_idx)

    # 2) Prefer safe moves that do not create 3-sided boxes.
    if safe_moves:
        best_idx = safe_moves[0][0]
        best_key = None

        for idx, cap, danger, twos, sum_before in safe_moves:
            key = (
                -twos,                       # avoid making 2-sided boxes
                -sum_before,                 # touch low-count boxes
                int(IS_BOUNDARY_EDGE[idx]),  # slight preference for boundary
                -idx
            )

            if best_key is None or key > best_key:
                best_key = key
                best_idx = idx

        return _encode_move(best_idx)

    # 3) Forced to give something away: choose the move that seems to concede
    #    the smallest immediate capture sequence.
    best_idx = all_moves[0][0]
    best_key = None

    for idx, cap, danger, twos, sum_before in all_moves:
        nxt = occ | (1 << idx)
        opp_gain = _greedy_capture_gain(nxt)

        key = (
            -opp_gain,                      # minimize opponent harvest
            -danger,                        # fewer fresh 3-sided boxes
            -sum_before,
            int(IS_BOUNDARY_EDGE[idx]),
            -idx
        )

        if best_key is None or key > best_key:
            best_key = key
            best_idx = idx

    return _encode_move(best_idx)
