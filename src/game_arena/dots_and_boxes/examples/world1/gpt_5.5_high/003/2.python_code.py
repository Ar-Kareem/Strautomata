
import time
from functools import lru_cache
import numpy as np


_INITIALIZED = False

_EDGES = []
_EDGE_BITS = []
_BOX_MASKS = []
_EDGE_BOXES = []
_EDGE_PREF = []
_FULL_MASK = 0


class _SearchTimeout(Exception):
    pass


def _init():
    global _INITIALIZED, _EDGES, _EDGE_BITS, _BOX_MASKS, _EDGE_BOXES, _EDGE_PREF, _FULL_MASK
    if _INITIALIZED:
        return

    _EDGES = []

    # Horizontal edges: rows 0..4, cols 0..3  => indices 0..19
    for r in range(5):
        for c in range(4):
            _EDGES.append((r, c, "H"))

    # Vertical edges: rows 0..3, cols 0..4 => indices 20..39
    for r in range(4):
        for c in range(5):
            _EDGES.append((r, c, "V"))

    _EDGE_BITS = [1 << i for i in range(40)]
    _FULL_MASK = (1 << 40) - 1

    _BOX_MASKS = []
    _EDGE_BOXES = [[] for _ in range(40)]

    for r in range(4):
        for c in range(4):
            # Box (r,c): top H(r,c), bottom H(r+1,c), left V(r,c), right V(r,c+1)
            top = r * 4 + c
            bottom = (r + 1) * 4 + c
            left = 20 + r * 5 + c
            right = 20 + r * 5 + (c + 1)
            mask = (1 << top) | (1 << bottom) | (1 << left) | (1 << right)
            b = r * 4 + c
            _BOX_MASKS.append(mask)
            _EDGE_BOXES[top].append(b)
            _EDGE_BOXES[bottom].append(b)
            _EDGE_BOXES[left].append(b)
            _EDGE_BOXES[right].append(b)

    # Deterministic final tiebreaker.
    _EDGE_PREF = list(range(40))

    _INITIALIZED = True


def _occupied_mask(horizontal, vertical):
    occ = 0

    # Valid horizontal edges only: 5 x 4
    for r in range(5):
        for c in range(4):
            if int(horizontal[r, c]) != 0:
                occ |= 1 << (r * 4 + c)

    # Valid vertical edges only: 4 x 5
    for r in range(4):
        for c in range(5):
            if int(vertical[r, c]) != 0:
                occ |= 1 << (20 + r * 5 + c)

    return occ


def _move_to_str(e):
    r, c, d = _EDGES[e]
    return f"{r},{c},{d}"


def _legal_edges(occ):
    out = []
    rem = _FULL_MASK ^ occ
    while rem:
        bit = rem & -rem
        out.append(bit.bit_length() - 1)
        rem ^= bit
    return out


def _capture_count(occ, e):
    # Drawing e captures each adjacent box that already has its other 3 sides.
    cnt = 0
    for b in _EDGE_BOXES[e]:
        if (occ & _BOX_MASKS[b]).bit_count() == 3:
            cnt += 1
    return cnt


def _danger_count(occ, e):
    # Non-capturing danger: how many adjacent boxes are changed from 2 sides to 3 sides.
    cnt = 0
    for b in _EDGE_BOXES[e]:
        if (occ & _BOX_MASKS[b]).bit_count() == 2:
            cnt += 1
    return cnt


def _safe_penalty(occ, e):
    # Lower is better. Prefer not to create many 2-sided boxes.
    p = len(_EDGE_BOXES[e])
    for b in _EDGE_BOXES[e]:
        s = (occ & _BOX_MASKS[b]).bit_count()
        ns = s + 1
        if ns >= 3:
            p += 20
        elif ns == 2:
            p += 4
    return p


def _unsafe_penalty(occ, e):
    # Cheap ordering for bad forced moves.
    p = 0
    for b in _EDGE_BOXES[e]:
        p += (occ & _BOX_MASKS[b]).bit_count()
    return p


def _ordered_moves(occ):
    captures = []
    safe = []
    unsafe = []

    rem = _FULL_MASK ^ occ
    while rem:
        bit = rem & -rem
        e = bit.bit_length() - 1
        rem ^= bit

        k = _capture_count(occ, e)
        if k:
            captures.append((-k, _safe_penalty(occ, e), _EDGE_PREF[e], e))
        else:
            d = _danger_count(occ, e)
            if d == 0:
                safe.append((_safe_penalty(occ, e), _EDGE_PREF[e], e))
            else:
                unsafe.append((d, _unsafe_penalty(occ, e), _EDGE_PREF[e], e))

    captures.sort()
    safe.sort()
    unsafe.sort()

    return [x[-1] for x in captures] + [x[-1] for x in safe] + [x[-1] for x in unsafe]


@lru_cache(maxsize=200000)
def _max_capture_run_cached(occ):
    _init()
    best = 0
    rem = _FULL_MASK ^ occ
    while rem:
        bit = rem & -rem
        e = bit.bit_length() - 1
        rem ^= bit

        k = _capture_count(occ, e)
        if k:
            val = k + _max_capture_run_cached(occ | bit)
            if val > best:
                best = val
    return best


@lru_cache(maxsize=200000)
def _static_value_cached(occ):
    """
    Approximate future score from the viewpoint of the player to move.
    Positive means good for the side to move.
    """
    _init()

    if occ == _FULL_MASK:
        return 0.0

    best_capture = -1
    safe_count = 0
    min_giveaway = 99
    any_move = False

    rem = _FULL_MASK ^ occ
    while rem:
        bit = rem & -rem
        e = bit.bit_length() - 1
        rem ^= bit
        any_move = True

        k = _capture_count(occ, e)
        if k:
            val = k + _max_capture_run_cached(occ | bit)
            if val > best_capture:
                best_capture = val
        else:
            d = _danger_count(occ, e)
            if d == 0:
                safe_count += 1
            else:
                give = _max_capture_run_cached(occ | bit)
                if give < min_giveaway:
                    min_giveaway = give

    if not any_move:
        return 0.0

    # If boxes are immediately available, the current player can usually profit.
    if best_capture >= 0:
        return float(best_capture)

    # No safe moves: current player must open something.
    if safe_count == 0:
        if min_giveaway == 99:
            min_giveaway = 0
        return -float(min_giveaway)

    # Quiet phase approximation: parity of safe moves often matters.
    return (0.40 if (safe_count & 1) else -0.25) + min(0.15, safe_count * 0.005)


def _transition_static_value(occ, e):
    bit = _EDGE_BITS[e]
    k = _capture_count(occ, e)
    if k:
        return k + _static_value_cached(occ | bit)
    return -_static_value_cached(occ | bit)


def _tie_score(occ, e):
    k = _capture_count(occ, e)
    d = _danger_count(occ, e)
    score = 1000.0 * k - 100.0 * d - 10.0 * _safe_penalty(occ, e)

    # When forced to give boxes, prefer the smallest immediate capture run.
    if k == 0 and d > 0:
        score -= 5.0 * _max_capture_run_cached(occ | _EDGE_BITS[e])

    score -= 0.001 * _EDGE_PREF[e]
    return score


def _static_best_move(occ):
    moves = _ordered_moves(occ)
    if not moves:
        return None

    best_e = moves[0]
    best_v = -10**9
    best_t = -10**9

    for e in moves:
        v = _transition_static_value(occ, e)
        t = _tie_score(occ, e)
        if v > best_v + 1e-9 or (abs(v - best_v) <= 1e-9 and t > best_t):
            best_v = v
            best_t = t
            best_e = e

    return best_e


def _exact_best_move(occ, deadline):
    """
    Exact negamax search from occ.
    Value is future boxes for player to move minus future boxes for opponent.
    Capturing keeps the turn; non-capturing switches turn.
    """
    tt = {}
    nodes = [0]
    INF = 1000

    def search(pos, alpha, beta):
        nodes[0] += 1
        if (nodes[0] & 2047) == 0 and time.perf_counter() > deadline:
            raise _SearchTimeout()

        if pos == _FULL_MASK:
            return 0

        cached = tt.get(pos)
        if cached is not None:
            return cached

        best = -INF
        cutoff = False
        moves = _ordered_moves(pos)

        if not moves:
            return 0

        for e in moves:
            bit = _EDGE_BITS[e]
            k = _capture_count(pos, e)
            child = pos | bit

            if k:
                val = k + search(child, alpha - k, beta - k)
            else:
                val = -search(child, -beta, -alpha)

            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                cutoff = True
                break

        if not cutoff:
            tt[pos] = best
        return best

    moves = _ordered_moves(occ)
    if not moves:
        return None

    best_e = moves[0]
    best_v = -INF
    best_t = -10**9
    alpha = -INF
    beta = INF

    for e in moves:
        if time.perf_counter() > deadline:
            raise _SearchTimeout()

        bit = _EDGE_BITS[e]
        k = _capture_count(occ, e)
        child = occ | bit

        if k:
            val = k + search(child, alpha - k, beta - k)
        else:
            val = -search(child, -beta, -alpha)

        t = _tie_score(occ, e)
        if val > best_v or (val == best_v and t > best_t):
            best_v = val
            best_t = t
            best_e = e

        if val > alpha:
            alpha = val

    return best_e


def _shallow_value(pos, depth, alpha, beta, deadline, nodes):
    nodes[0] += 1
    if (nodes[0] & 511) == 0 and time.perf_counter() > deadline:
        raise _SearchTimeout()

    if pos == _FULL_MASK:
        return 0.0

    if depth <= 0:
        return _static_value_cached(pos)

    moves = _ordered_moves(pos)
    if not moves:
        return 0.0

    # Limit branching in the heuristic search.
    branch = 14 if depth >= 3 else 18
    if len(moves) > branch:
        moves = moves[:branch]

    best = -1000.0

    for e in moves:
        bit = _EDGE_BITS[e]
        k = _capture_count(pos, e)
        child = pos | bit

        if k:
            val = k + _shallow_value(child, depth, alpha - k, beta - k, deadline, nodes)
        else:
            val = -_shallow_value(child, depth - 1, -beta, -alpha, deadline, nodes)

        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    return best


def _shallow_best_move(occ, depth, deadline):
    moves = _ordered_moves(occ)
    if not moves:
        return None

    nodes = [0]
    best_e = moves[0]
    best_v = -1000.0
    best_t = -10**9
    alpha = -1000.0
    beta = 1000.0

    # Evaluate every root move; pruning/branch limiting happens below.
    for e in moves:
        if time.perf_counter() > deadline:
            raise _SearchTimeout()

        bit = _EDGE_BITS[e]
        k = _capture_count(occ, e)
        child = occ | bit

        if k:
            val = k + _shallow_value(child, depth, alpha - k, beta - k, deadline, nodes)
        else:
            val = -_shallow_value(child, depth - 1, -beta, -alpha, deadline, nodes)

        t = _tie_score(occ, e)
        if val > best_v + 1e-9 or (abs(val - best_v) <= 1e-9 and t > best_t):
            best_v = val
            best_t = t
            best_e = e

        if val > alpha:
            alpha = val

    return best_e


def _emergency_legal(horizontal, vertical):
    # Valid horizontal edges.
    try:
        for r in range(5):
            for c in range(4):
                if int(horizontal[r, c]) == 0:
                    return f"{r},{c},H"

        # Valid vertical edges.
        for r in range(4):
            for c in range(5):
                if int(vertical[r, c]) == 0:
                    return f"{r},{c},V"
    except Exception:
        pass

    # Should only happen if the game is already over.
    return "0,0,H"


def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    try:
        _init()
        occ = _occupied_mask(horizontal, vertical)
        moves = _legal_edges(occ)

        if not moves:
            return _emergency_legal(horizontal, vertical)

        if len(moves) == 1:
            return _move_to_str(moves[0])

        start = time.perf_counter()
        rem = len(moves)

        cap_exists = False
        safe_exists = False
        for e in moves:
            k = _capture_count(occ, e)
            if k:
                cap_exists = True
            elif _danger_count(occ, e) == 0:
                safe_exists = True

        # Try exact search in late or forced-looking positions.
        try_exact = rem <= 22 or (rem <= 26 and (cap_exists or not safe_exists))
        if try_exact:
            budget = 0.72 if rem <= 22 else 0.55
            try:
                e = _exact_best_move(occ, start + budget)
                if e is not None:
                    return _move_to_str(e)
            except _SearchTimeout:
                pass
            except Exception:
                pass

        # Tactical shallow search.
        try:
            if time.perf_counter() < start + 0.90:
                depth = 4 if rem <= 24 else 3
                e = _shallow_best_move(occ, depth, start + 0.92)
                if e is not None:
                    return _move_to_str(e)
        except _SearchTimeout:
            pass
        except Exception:
            pass

        # Static safe fallback.
        e = _static_best_move(occ)
        if e is not None:
            return _move_to_str(e)

        return _emergency_legal(horizontal, vertical)

    except Exception:
        return _emergency_legal(horizontal, vertical)
