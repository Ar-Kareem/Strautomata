
import time
from functools import lru_cache
import numpy as np

try:
    _popcount = int.bit_count
except AttributeError:  # very old Python fallback
    _popcount = lambda x: bin(x).count("1")

# Real edges for 4x4 boxes: H rows 0..4 cols 0..3, V rows 0..3 cols 0..4.
H_MASK = 0
V_MASK = 0
EDGE_IDS = []
for r in range(5):
    for c in range(4):
        e = r * 5 + c
        H_MASK |= 1 << e
        EDGE_IDS.append(e)
for r in range(4):
    for c in range(5):
        e = r * 5 + c
        V_MASK |= 1 << e
        EDGE_IDS.append(25 + e)

BOX_H = []
BOX_V = []
BOX_EDGES = []
EDGE_BOXES = [[] for _ in range(50)]
for r in range(4):
    for c in range(4):
        b = r * 4 + c
        top = r * 5 + c
        bottom = (r + 1) * 5 + c
        left = r * 5 + c
        right = r * 5 + (c + 1)
        bh = (1 << top) | (1 << bottom)
        bv = (1 << left) | (1 << right)
        BOX_H.append(bh)
        BOX_V.append(bv)
        BOX_EDGES.append((top, bottom, 25 + left, 25 + right))
        EDGE_BOXES[top].append(b)
        EDGE_BOXES[bottom].append(b)
        EDGE_BOXES[25 + left].append(b)
        EDGE_BOXES[25 + right].append(b)

INF = 10 ** 9


def _to_bits(horizontal, vertical):
    H = np.asarray(horizontal)
    V = np.asarray(vertical)
    h = 0
    v = 0
    for r in range(5):
        for c in range(4):
            if int(H[r, c]) != 0:
                h |= 1 << (r * 5 + c)
    for r in range(4):
        for c in range(5):
            if int(V[r, c]) != 0:
                v |= 1 << (r * 5 + c)
    return h, v


def _any_empty_move(horizontal, vertical):
    # Emergency fallback; normally unused unless the game is already over.
    H = np.asarray(horizontal)
    V = np.asarray(vertical)
    if H.ndim == 2:
        for r in range(min(5, H.shape[0])):
            for c in range(min(5, H.shape[1])):
                if int(H[r, c]) == 0:
                    return f"{r},{c},H"
    if V.ndim == 2:
        for r in range(min(5, V.shape[0])):
            for c in range(min(5, V.shape[1])):
                if int(V[r, c]) == 0:
                    return f"{r},{c},V"
    return "0,0,H"


@lru_cache(maxsize=200000)
def _closure_captures(h, v):
    # Number of boxes obtained by repeatedly capturing every currently
    # three-sided box until none remain. Used for ordering/danger estimates.
    hh = h
    vv = v
    done = 0
    cnt = 0
    while True:
        found = -1
        for b in range(16):
            if (done >> b) & 1:
                continue
            if _popcount(BOX_H[b] & hh) + _popcount(BOX_V[b] & vv) == 3:
                found = b
                break
        if found < 0:
            return cnt
        for eid in BOX_EDGES[found]:
            if eid < 25:
                bit = 1 << eid
                if not (hh & bit):
                    hh |= bit
                    break
            else:
                bit = 1 << (eid - 25)
                if not (vv & bit):
                    vv |= bit
                    break
        done |= 1 << found
        cnt += 1


def _ordered_moves(h, v):
    moves = []
    for eid in EDGE_IDS:
        if eid < 25:
            bit = 1 << eid
            if h & bit:
                continue
            h2 = h | bit
            v2 = v
        else:
            bit = 1 << (eid - 25)
            if v & bit:
                continue
            h2 = h
            v2 = v | bit

        captures = 0
        makes_three = 0
        reaches_two = 0
        side_sum = 0
        for b in EDGE_BOXES[eid]:
            before = _popcount(BOX_H[b] & h) + _popcount(BOX_V[b] & v)
            after = before + 1
            if after == 4:
                captures += 1
            elif after == 3:
                makes_three += 1
            elif after == 2:
                reaches_two += 1
            side_sum += after

        if captures:
            key = (0, -(captures + _closure_captures(h2, v2)), -captures, eid)
        elif makes_three == 0:
            # Safe move: prefer edges that create the fewest two-sided boxes.
            key = (1, reaches_two, side_sum, eid)
        else:
            # Forced to open something: give away the shortest forced closure.
            key = (2, makes_three, _closure_captures(h2, v2), side_sum, eid)
        moves.append((key, eid, h2, v2, captures))

    moves.sort(key=lambda x: x[0])
    return moves


def _exact_solver(deadline):
    tt = {}
    nodes = 0

    class _Timeout(Exception):
        pass

    def search(h, v, player, alpha, beta):
        nonlocal nodes
        nodes += 1
        if (nodes & 255) == 0 and time.perf_counter() > deadline:
            raise _Timeout()

        if h == H_MASK and v == V_MASK:
            return 0

        key = (h << 26) | (v << 1) | (1 if player == 1 else 0)
        ent = tt.get(key)
        if ent is not None:
            val, flag = ent
            if flag == 0:
                return val
            if flag == 1 and val > alpha:      # lower bound
                alpha = val
            elif flag == 2 and val < beta:     # upper bound
                beta = val
            if alpha >= beta:
                return val

        a0, b0 = alpha, beta
        moves = _ordered_moves(h, v)
        if not moves:
            return 0

        if player == 1:
            best = -INF
            for _, eid, h2, v2, c in moves:
                val = c + search(
                    h2, v2, player if c else -player,
                    alpha - c, beta - c
                )
                if val > best:
                    best = val
                if best > alpha:
                    alpha = best
                if alpha >= beta:
                    break
        else:
            best = INF
            for _, eid, h2, v2, c in moves:
                val = -c + search(
                    h2, v2, player if c else -player,
                    alpha + c, beta + c
                )
                if val < best:
                    best = val
                if best < beta:
                    beta = best
                if alpha >= beta:
                    break

        if best <= a0:
            flag = 2
        elif best >= b0:
            flag = 1
        else:
            flag = 0
        tt[key] = (best, flag)
        return best

    return search, _Timeout


def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    h, v = _to_bits(horizontal, vertical)
    moves = _ordered_moves(h, v)
    if not moves:
        return _any_empty_move(horizontal, vertical)

    best_eid = moves[0][1]
    remaining = 40 - (_popcount(h) + _popcount(v))
    category = moves[0][0][0]

    # Exact search for late positions and for forced capture/chain positions.
    if remaining <= 24 or (remaining <= 30 and category != 1):
        max_future = 0
        for b in range(16):
            if _popcount(BOX_H[b] & h) + _popcount(BOX_V[b] & v) < 4:
                max_future += 1

        deadline = time.perf_counter() + 0.88
        search, timeout_exc = _exact_solver(deadline)
        alpha = -INF
        try:
            for _, eid, h2, v2, c in moves:
                val = c + search(h2, v2, 1 if c else -1, alpha - c, INF - c)
                if val > alpha:
                    alpha = val
                    best_eid = eid
                if alpha >= max_future:
                    break
        except timeout_exc:
            pass

    if best_eid < 25:
        return f"{best_eid // 5},{best_eid % 5},H"
    e = best_eid - 25
    return f"{e // 5},{e % 5},V"
