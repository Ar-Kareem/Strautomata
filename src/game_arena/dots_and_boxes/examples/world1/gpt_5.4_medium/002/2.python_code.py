
import numpy as np
from functools import lru_cache

# ============================================================
# Board model for a 4x4-box Dots and Boxes game
# Legal edges:
#   Horizontal: rows 0..4, cols 0..3  -> 20 edges
#   Vertical:   rows 0..3, cols 0..4  -> 20 edges
# Arrays are 5x5, with the extra row/col unused for standard play.
# ============================================================

EDGE_INFO = []          # eid -> (row, col, 'H'/'V')
EDGE_ID = {}            # ('H'/'V', row, col) -> eid

# Horizontal edges: 5 x 4
for r in range(5):
    for c in range(4):
        eid = len(EDGE_INFO)
        EDGE_INFO.append((r, c, 'H'))
        EDGE_ID[('H', r, c)] = eid

# Vertical edges: 4 x 5
for r in range(4):
    for c in range(5):
        eid = len(EDGE_INFO)
        EDGE_INFO.append((r, c, 'V'))
        EDGE_ID[('V', r, c)] = eid

NUM_EDGES = len(EDGE_INFO)  # 40
FULL_MASK = (1 << NUM_EDGES) - 1

# Boxes: 4 x 4 = 16
BOX_MASKS = []              # bid -> bitmask of its 4 edges
ADJ_BOXES = [[] for _ in range(NUM_EDGES)]  # eid -> list of adjacent box ids

for r in range(4):
    for c in range(4):
        top = EDGE_ID[('H', r, c)]
        bot = EDGE_ID[('H', r + 1, c)]
        left = EDGE_ID[('V', r, c)]
        right = EDGE_ID[('V', r, c + 1)]
        eids = (top, bot, left, right)

        bid = len(BOX_MASKS)
        bm = 0
        for e in eids:
            bm |= (1 << e)
            ADJ_BOXES[e].append(bid)
        BOX_MASKS.append(bm)

ADJ_BOXES = tuple(tuple(lst) for lst in ADJ_BOXES)
BOUNDARY_EDGE = tuple(1 if len(ADJ_BOXES[e]) == 1 else 0 for e in range(NUM_EDGES))

EXACT_ALL_THRESHOLD = 18
EXACT_TACTICAL_THRESHOLD = 20


# ============================================================
# Utility functions
# ============================================================

def arrays_to_mask(horizontal: np.ndarray, vertical: np.ndarray) -> int:
    mask = 0

    for r in range(5):
        for c in range(4):
            if int(horizontal[r, c]) != 0:
                mask |= (1 << EDGE_ID[('H', r, c)])

    for r in range(4):
        for c in range(5):
            if int(vertical[r, c]) != 0:
                mask |= (1 << EDGE_ID[('V', r, c)])

    return mask


def move_to_str(eid: int) -> str:
    r, c, d = EDGE_INFO[eid]
    return f"{r},{c},{d}"


def legal_moves(mask: int):
    return [e for e in range(NUM_EDGES) if ((mask >> e) & 1) == 0]


def completed_count(mask: int, eid: int) -> int:
    """How many boxes are completed by adding edge eid to mask?"""
    newmask = mask | (1 << eid)
    cnt = 0
    for bid in ADJ_BOXES[eid]:
        if (newmask & BOX_MASKS[bid]) == BOX_MASKS[bid]:
            cnt += 1
    return cnt


def box_degree(mask: int, bid: int) -> int:
    return (mask & BOX_MASKS[bid]).bit_count()


def is_safe_move(mask: int, eid: int) -> bool:
    """Safe means:
    - it does not capture a box now
    - it does not create any 3-sided box for the opponent
    """
    if completed_count(mask, eid) > 0:
        return False
    for bid in ADJ_BOXES[eid]:
        if box_degree(mask, bid) == 2:
            return False
    return True


def capture_moves(mask: int):
    return [e for e in range(NUM_EDGES) if ((mask >> e) & 1) == 0 and completed_count(mask, e) > 0]


def safe_moves(mask: int):
    return [e for e in range(NUM_EDGES) if ((mask >> e) & 1) == 0 and is_safe_move(mask, e)]


def count_safe_moves(mask: int) -> int:
    cnt = 0
    for e in range(NUM_EDGES):
        if ((mask >> e) & 1) == 0 and is_safe_move(mask, e):
            cnt += 1
    return cnt


def count_box_degrees(mask: int):
    d1 = d2 = d3 = 0
    for bm in BOX_MASKS:
        d = (mask & bm).bit_count()
        if d == 1:
            d1 += 1
        elif d == 2:
            d2 += 1
        elif d == 3:
            d3 += 1
    return d1, d2, d3


def state_heuristic(mask: int) -> float:
    """Static eval from the current player's perspective."""
    s = count_safe_moves(mask)
    d1, d2, d3 = count_box_degrees(mask)
    caps = len(capture_moves(mask))
    return 5.0 * s + 3.0 * caps + 1.0 * d1 - 2.0 * d2 + 1.5 * d3


# ============================================================
# Exact endgame solver
# Returns net future boxes (current player - opponent)
# ============================================================

@lru_cache(maxsize=500000)
def solve(mask: int) -> int:
    if mask == FULL_MASK:
        return 0

    best = -100
    found_capture = False

    # Try captures first
    for eid in range(NUM_EDGES):
        if (mask >> eid) & 1:
            continue
        gain = completed_count(mask, eid)
        if gain > 0:
            found_capture = True
            val = gain + solve(mask | (1 << eid))
            if val > best:
                best = val

    if found_capture:
        return best

    # No capture available: turn passes after move
    for eid in range(NUM_EDGES):
        if (mask >> eid) & 1:
            continue
        val = -solve(mask | (1 << eid))
        if val > best:
            best = val

    return best


def exact_best_move(mask: int, legal):
    best_e = None
    best_v = -10**9
    best_t = -10**9

    for eid in legal:
        gain = completed_count(mask, eid)
        newmask = mask | (1 << eid)
        if gain > 0:
            v = gain + solve(newmask)
        else:
            v = -solve(newmask)

        # Tie-breaker
        t = 100 * gain
        if is_safe_move(mask, eid):
            t += 10
        t += BOUNDARY_EDGE[eid]

        if v > best_v or (v == best_v and t > best_t):
            best_v = v
            best_t = t
            best_e = eid

    return best_e


# ============================================================
# Greedy capture-run simulator
# Used as a heuristic for sacrifice estimation and capture choice
# ============================================================

def greedy_capture_run(mask: int):
    """
    Assume the player to move greedily keeps taking available captures.
    Returns: (boxes_taken_in_run, resulting_mask)
    """
    total = 0
    cur = mask

    while True:
        best_e = None
        best_key = None

        for eid in range(NUM_EDGES):
            if (cur >> eid) & 1:
                continue
            gain = completed_count(cur, eid)
            if gain <= 0:
                continue

            nxt = cur | (1 << eid)
            next_caps = 0
            for e2 in range(NUM_EDGES):
                if ((nxt >> e2) & 1) == 0 and completed_count(nxt, e2) > 0:
                    next_caps += 1

            key = (gain, next_caps, BOUNDARY_EDGE[eid])
            if best_e is None or key > best_key:
                best_e = eid
                best_key = key

        if best_e is None:
            break

        total += completed_count(cur, best_e)
        cur |= (1 << best_e)

    return total, cur


# ============================================================
# Heuristic move pickers
# ============================================================

def choose_best_safe(mask: int, safes):
    best_e = None
    best_score = -10**18

    for eid in safes:
        newmask = mask | (1 << eid)

        safe_after = count_safe_moves(newmask)
        d1, d2, _ = count_box_degrees(newmask)

        adj_bonus = 0
        for bid in ADJ_BOXES[eid]:
            d = box_degree(mask, bid)
            if d == 0:
                adj_bonus += 4
            elif d == 1:
                adj_bonus += 2

        score = (
            100 * safe_after
            - 8 * d2
            + 2 * d1
            + 3 * BOUNDARY_EDGE[eid]
            + adj_bonus
        )

        if score > best_score:
            best_score = score
            best_e = eid

    return best_e


def choose_best_capture(mask: int, captures, remaining: int):
    best_e = None
    best_score = -10**18

    for eid in captures:
        gain = completed_count(mask, eid)
        newmask = mask | (1 << eid)

        # If tactical enough, solve exactly from here
        if remaining - 1 <= EXACT_TACTICAL_THRESHOLD:
            score = gain + solve(newmask)
        else:
            extra_boxes, after = greedy_capture_run(newmask)
            total_now = gain + extra_boxes
            safe_after = count_safe_moves(after)
            _, d2, _ = count_box_degrees(after)

            score = (
                1000 * total_now
                + 10 * safe_after
                - 3 * d2
                + 2 * BOUNDARY_EDGE[eid]
            )

        if score > best_score:
            best_score = score
            best_e = eid

    return best_e


def choose_best_sacrifice(mask: int, legal):
    """
    No safe move exists. Open the line that seems to give away the least.
    """
    best_e = None
    best_score = -10**18

    for eid in legal:
        newmask = mask | (1 << eid)

        # Opponent's turn: estimate how many boxes they can greedily take
        opp_boxes, after = greedy_capture_run(newmask)
        remaining_after = NUM_EDGES - after.bit_count()

        if remaining_after <= EXACT_ALL_THRESHOLD:
            future = solve(after)  # our turn at 'after'
        else:
            future = state_heuristic(after)

        score = -1000 * opp_boxes + future + BOUNDARY_EDGE[eid]

        if score > best_score:
            best_score = score
            best_e = eid

    return best_e


# ============================================================
# Policy
# ============================================================

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    mask = arrays_to_mask(horizontal, vertical)
    legal = legal_moves(mask)

    if legal:
        remaining = len(legal)
        caps = [e for e in legal if completed_count(mask, e) > 0]

        if remaining <= EXACT_ALL_THRESHOLD:
            eid = exact_best_move(mask, legal)
            if eid is not None:
                return move_to_str(eid)

        if caps and remaining <= EXACT_TACTICAL_THRESHOLD:
            eid = exact_best_move(mask, legal)
            if eid is not None:
                return move_to_str(eid)

        if caps:
            eid = choose_best_capture(mask, caps, remaining)
            if eid is not None:
                return move_to_str(eid)

        safes = [e for e in legal if is_safe_move(mask, e)]

        if (not caps) and (not safes) and remaining <= EXACT_TACTICAL_THRESHOLD:
            eid = exact_best_move(mask, legal)
            if eid is not None:
                return move_to_str(eid)

        if safes:
            eid = choose_best_safe(mask, safes)
            if eid is not None:
                return move_to_str(eid)

        eid = choose_best_sacrifice(mask, legal)
        if eid is not None:
            return move_to_str(eid)

    # --------------------------------------------------------
    # Guaranteed legal fallbacks
    # --------------------------------------------------------
    # First scan the standard 40 real edges
    for r in range(5):
        for c in range(4):
            if int(horizontal[r, c]) == 0:
                return f"{r},{c},H"

    for r in range(4):
        for c in range(5):
            if int(vertical[r, c]) == 0:
                return f"{r},{c},V"

    # If the environment uses all 5x5 entries as valid, fall back further
    for r in range(horizontal.shape[0]):
        for c in range(horizontal.shape[1]):
            if int(horizontal[r, c]) == 0:
                return f"{r},{c},H"

    for r in range(vertical.shape[0]):
        for c in range(vertical.shape[1]):
            if int(vertical[r, c]) == 0:
                return f"{r},{c},V"

    # Terminal-state fallback; should normally never be reached
    return "0,0,H"
