
import time
from functools import lru_cache
import numpy as np

# ----------------------------
# Board precomputation
# ----------------------------

EDGE_TO_MOVE = []
H_INDEX = {}
V_INDEX = {}

idx = 0
for r in range(5):
    for c in range(4):
        H_INDEX[(r, c)] = idx
        EDGE_TO_MOVE.append((r, c, "H"))
        idx += 1

for r in range(4):
    for c in range(5):
        V_INDEX[(r, c)] = idx
        EDGE_TO_MOVE.append((r, c, "V"))
        idx += 1

EDGE_COUNT = 40
BIT = [1 << i for i in range(EDGE_COUNT)]
BIT_TO_INDEX = {BIT[i]: i for i in range(EDGE_COUNT)}
FULL_MASK = (1 << EDGE_COUNT) - 1

BOX_MASKS = [0] * 16
EDGE_ADJ = [[] for _ in range(EDGE_COUNT)]

for r in range(4):
    for c in range(4):
        b = 4 * r + c
        e_top = H_INDEX[(r, c)]
        e_bottom = H_INDEX[(r + 1, c)]
        e_left = V_INDEX[(r, c)]
        e_right = V_INDEX[(r, c + 1)]
        mask = BIT[e_top] | BIT[e_bottom] | BIT[e_left] | BIT[e_right]
        BOX_MASKS[b] = mask
        EDGE_ADJ[e_top].append(b)
        EDGE_ADJ[e_bottom].append(b)
        EDGE_ADJ[e_left].append(b)
        EDGE_ADJ[e_right].append(b)

EDGE_OTHERMASKS = [
    tuple(BOX_MASKS[b] ^ BIT[e] for b in EDGE_ADJ[e]) for e in range(EDGE_COUNT)
]
ADJ_LEN = [len(EDGE_ADJ[e]) for e in range(EDGE_COUNT)]

# Search tuning
SEARCH_TIME_BUDGET = 0.55
FULL_SEARCH_THRESHOLD = 18
TACTICAL_SEARCH_THRESHOLD = 21
LOONY_SEARCH_THRESHOLD = 23

_search_deadline = 0.0
_search_nodes = 0


class _Timeout(Exception):
    pass


# ----------------------------
# Basic helpers
# ----------------------------

def emergency_legal_move(horizontal: np.ndarray, vertical: np.ndarray) -> str:
    for r in range(5):
        for c in range(4):
            if horizontal[r, c] == 0:
                return f"{r},{c},H"
    for r in range(4):
        for c in range(5):
            if vertical[r, c] == 0:
                return f"{r},{c},V"
    return "0,0,H"  # should never be needed unless board is full


def arrays_to_mask(horizontal: np.ndarray, vertical: np.ndarray) -> int:
    mask = 0
    idx = 0
    for r in range(5):
        for c in range(4):
            if horizontal[r, c] != 0:
                mask |= BIT[idx]
            idx += 1

    base = 20
    for r in range(4):
        for c in range(5):
            if vertical[r, c] != 0:
                mask |= BIT[base + c]
        base += 5

    return mask


def move_to_str(idx: int) -> str:
    r, c, d = EDGE_TO_MOVE[idx]
    return f"{r},{c},{d}"


def capture_count(mask: int, idx: int) -> int:
    total = 0
    for othermask in EDGE_OTHERMASKS[idx]:
        if (mask & othermask) == othermask:
            total += 1
    return total


def is_safe_noncapture(mask: int, idx: int) -> bool:
    # Safe means: it does not capture, and it does not create a 3-sided box.
    for othermask in EDGE_OTHERMASKS[idx]:
        if (mask & othermask).bit_count() >= 2:
            return False
    return True


def classify_moves(mask: int):
    legal = []
    caps = []
    safes = []
    unsafe = []

    avail = FULL_MASK ^ mask
    while avail:
        bit = avail & -avail
        avail ^= bit
        idx = BIT_TO_INDEX[bit]
        legal.append(idx)
        k = capture_count(mask, idx)
        if k:
            caps.append((idx, k))
        elif is_safe_noncapture(mask, idx):
            safes.append(idx)
        else:
            unsafe.append(idx)

    return legal, caps, safes, unsafe


def count_two_sided(mask: int) -> int:
    total = 0
    for bm in BOX_MASKS:
        if (mask & bm).bit_count() == 2:
            total += 1
    return total


# ----------------------------
# Fast tactical evaluators
# ----------------------------

@lru_cache(maxsize=100000)
def max_capture_run(mask: int) -> int:
    # Maximum number of boxes the current player can take in one uninterrupted
    # capture sequence starting from this occupancy mask.
    best = 0
    avail = FULL_MASK ^ mask
    while avail:
        bit = avail & -avail
        avail ^= bit
        idx = BIT_TO_INDEX[bit]
        k = capture_count(mask, idx)
        if k:
            v = k + max_capture_run(mask | bit)
            if v > best:
                best = v
    return best


@lru_cache(maxsize=100000)
def heuristic_state_value(mask: int, turn: int) -> float:
    # turn = 1 if it's our turn, -1 if opponent's turn.
    legal, caps, safes, unsafe = classify_moves(mask)

    if not legal:
        return 0.0

    # If current player can immediately start taking boxes, that's big.
    if caps:
        run = max_capture_run(mask)
        return (12.0 + run) if turn == 1 else (-12.0 - run)

    # Safe phase heuristic: parity + avoid many 2-sided boxes.
    if safes:
        val = 0.10 * len(safes) - 0.18 * count_two_sided(mask)
        if turn == 1:
            val += 0.8 if (len(safes) % 2 == 1) else -0.8
        else:
            val += 0.8 if (len(safes) % 2 == 0) else -0.8
        return val

    # No captures, no safe moves: current player must open something.
    if turn == 1:
        best = -1e9
        for idx in unsafe:
            v = heuristic_state_value(mask | BIT[idx], -1)
            if v > best:
                best = v
        return best
    else:
        best = 1e9
        for idx in unsafe:
            v = heuristic_state_value(mask | BIT[idx], 1)
            if v < best:
                best = v
        return best


def local_safe_bonus(mask: int, idx: int) -> float:
    score = 0.0
    for othermask in EDGE_OTHERMASKS[idx]:
        t = (mask & othermask).bit_count()
        if t == 0:
            score += 0.7
        elif t == 1:
            score -= 0.5
    if ADJ_LEN[idx] == 1:
        score += 0.1
    return score


def safe_move_value(mask: int, idx: int) -> float:
    # Evaluate a safe move by assuming opponent will answer with their best safe reply.
    mask2 = mask | BIT[idx]
    bonus = local_safe_bonus(mask, idx)

    _, caps2, safes2, _ = classify_moves(mask2)

    # If opponent already has no safe reply, that's excellent.
    if caps2 or not safes2:
        return bonus + heuristic_state_value(mask2, -1)

    worst_for_us = 1e9
    for j in safes2:
        v = heuristic_state_value(mask2 | BIT[j], 1)
        if v < worst_for_us:
            worst_for_us = v

    return bonus + worst_for_us


# ----------------------------
# Exact late-game solver
# ----------------------------

@lru_cache(maxsize=300000)
def solve_future(mask: int, turn: int) -> int:
    global _search_deadline, _search_nodes

    _search_nodes += 1
    if (_search_nodes & 2047) == 0 and time.perf_counter() > _search_deadline:
        raise _Timeout

    if mask == FULL_MASK:
        return 0

    avail = FULL_MASK ^ mask

    if turn == 1:
        best = -99
        while avail:
            bit = avail & -avail
            avail ^= bit
            idx = BIT_TO_INDEX[bit]
            k = capture_count(mask, idx)
            nxt_turn = 1 if k else -1
            v = k + solve_future(mask | bit, nxt_turn)
            if v > best:
                best = v
        return best
    else:
        best = 99
        while avail:
            bit = avail & -avail
            avail ^= bit
            idx = BIT_TO_INDEX[bit]
            k = capture_count(mask, idx)
            nxt_turn = -1 if k else 1
            v = -k + solve_future(mask | bit, nxt_turn)
            if v < best:
                best = v
        return best


# ----------------------------
# Main policy
# ----------------------------

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    # capture is not needed for move selection because current score is a constant
    # offset across all candidate moves.
    _ = capture

    fallback = emergency_legal_move(horizontal, vertical)

    try:
        mask = arrays_to_mask(horizontal, vertical)
        legal, caps, safes, unsafe = classify_moves(mask)

        if not legal:
            return fallback

        fallback = move_to_str(legal[0])
        cap_map = {i: k for i, k in caps}
        safe_set = set(safes)

        remaining = EDGE_COUNT - mask.bit_count()
        try_exact = (
            remaining <= FULL_SEARCH_THRESHOLD
            or (caps and remaining <= TACTICAL_SEARCH_THRESHOLD)
            or ((not safes) and remaining <= LOONY_SEARCH_THRESHOLD)
        )

        # Exact search when feasible/tactical.
        if try_exact:
            global _search_deadline, _search_nodes
            _search_deadline = time.perf_counter() + SEARCH_TIME_BUDGET
            _search_nodes = 0

            try:
                root_order = []
                for idx in legal:
                    bit = BIT[idx]
                    if idx in cap_map:
                        rough = cap_map[idx] + heuristic_state_value(mask | bit, 1)
                    elif idx in safe_set:
                        rough = safe_move_value(mask, idx)
                    else:
                        rough = heuristic_state_value(mask | bit, -1)
                    root_order.append((rough, idx))
                root_order.sort(key=lambda x: (x[0], -x[1]), reverse=True)

                best_idx = legal[0]
                best_val = -10**9

                for _, idx in root_order:
                    bit = BIT[idx]
                    k = cap_map.get(idx, 0)
                    nxt_turn = 1 if k else -1
                    val = k + solve_future(mask | bit, nxt_turn)
                    if val > best_val or (val == best_val and idx < best_idx):
                        best_val = val
                        best_idx = idx

                return move_to_str(best_idx)

            except _Timeout:
                pass  # fall back to heuristic move selection

        # Heuristic move selection
        best_idx = legal[0]
        best_val = -1e18

        for idx in legal:
            bit = BIT[idx]

            if idx in cap_map:
                val = cap_map[idx] + heuristic_state_value(mask | bit, 1)
            elif idx in safe_set:
                val = safe_move_value(mask, idx)
            else:
                val = heuristic_state_value(mask | bit, -1)

            if val > best_val or (abs(val - best_val) <= 1e-12 and idx < best_idx):
                best_val = val
                best_idx = idx

        return move_to_str(best_idx)

    except Exception:
        # Never risk returning an illegal move due to an internal error.
        return fallback
