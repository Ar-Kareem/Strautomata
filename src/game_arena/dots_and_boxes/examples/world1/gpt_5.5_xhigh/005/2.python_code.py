
import time
from functools import lru_cache
import numpy as np

# 4x4 boxes: 20 horizontal edges + 20 vertical edges = 40 real edges.
N = 4
NUM_BOXES = N * N


def _h_index(r, c):
    return r * N + c


def _v_index(r, c):
    return (N + 1) * N + r * (N + 1) + c


_EDGE_TO_MOVE = []
for _r in range(N + 1):
    for _c in range(N):
        _EDGE_TO_MOVE.append((_r, _c, "H"))
for _r in range(N):
    for _c in range(N + 1):
        _EDGE_TO_MOVE.append((_r, _c, "V"))

_NUM_EDGES = len(_EDGE_TO_MOVE)
_ALL_EDGES_MASK = (1 << _NUM_EDGES) - 1
_MOVE_STR = [f"{r},{c},{d}" for (r, c, d) in _EDGE_TO_MOVE]

_BOX_EDGES = []
_BOX_MASKS = []
for r in range(N):
    for c in range(N):
        edges = (
            _h_index(r, c),
            _h_index(r + 1, c),
            _v_index(r, c),
            _v_index(r, c + 1),
        )
        _BOX_EDGES.append(edges)
        m = 0
        for e in edges:
            m |= 1 << e
        _BOX_MASKS.append(m)

_EDGE_BOXES_LIST = [[] for _ in range(_NUM_EDGES)]
for b, edges in enumerate(_BOX_EDGES):
    for e in edges:
        _EDGE_BOXES_LIST[e].append(b)
_EDGE_BOXES = tuple(tuple(x) for x in _EDGE_BOXES_LIST)

# Static centrality ordering, used only as a tie-breaker.
_STATIC_SCORE = []
for e, (r, c, d) in enumerate(_EDGE_TO_MOVE):
    if d == "H":
        mr, mc = float(r), c + 0.5
    else:
        mr, mc = r + 0.5, float(c)
    dist = abs(mr - 2.0) + abs(mc - 2.0)
    score = -dist
    if len(_EDGE_BOXES[e]) == 1:
        score += 0.20
    _STATIC_SCORE.append(score)

_STATIC_ORDER = sorted(range(_NUM_EDGES), key=lambda e: (-_STATIC_SCORE[e], e))
_STATIC_RANK = [0] * _NUM_EDGES
for rank, e in enumerate(_STATIC_ORDER):
    _STATIC_RANK[e] = rank


# Transposition table for exact search.
# flag: 0 exact, 1 lower bound, 2 upper bound
_TT = {}
_SEARCH_DEADLINE = 0.0
_SEARCH_NODES = 0

_LIMIT_DEADLINE = 0.0
_LIMIT_NODES = 0
_LIMIT_TT = {}


def _array_fallback(horizontal, vertical):
    """Last-resort legal move from the raw arrays."""
    try:
        for r in range(N + 1):
            for c in range(N):
                if int(horizontal[r, c]) == 0:
                    return f"{r},{c},H"
        for r in range(N):
            for c in range(N + 1):
                if int(vertical[r, c]) == 0:
                    return f"{r},{c},V"
        # If the arena ever exposes extra array entries as legal, try those too.
        for r in range(5):
            for c in range(5):
                if int(horizontal[r, c]) == 0:
                    return f"{r},{c},H"
        for r in range(5):
            for c in range(5):
                if int(vertical[r, c]) == 0:
                    return f"{r},{c},V"
    except Exception:
        pass
    return "0,0,H"


def _state_to_masks(horizontal, vertical, capture):
    occ = 0

    for r in range(N + 1):
        for c in range(N):
            if int(horizontal[r, c]) != 0:
                occ |= 1 << _h_index(r, c)

    for r in range(N):
        for c in range(N + 1):
            if int(vertical[r, c]) != 0:
                occ |= 1 << _v_index(r, c)

    cap = 0
    for r in range(N):
        for c in range(N):
            if int(capture[r, c]) != 0:
                cap |= 1 << (r * N + c)

    # Be robust to inconsistent inputs: a geometrically complete box is no
    # longer available for future scoring.
    for b, bm in enumerate(_BOX_MASKS):
        if (occ & bm) == bm:
            cap |= 1 << b

    return occ, cap


def _first_legal_move_str(occ):
    legal = _ALL_EDGES_MASK ^ (occ & _ALL_EDGES_MASK)
    if legal:
        bit = legal & -legal
        e = bit.bit_length() - 1
        return _MOVE_STR[e]
    return None


def _box_sides(occ, b):
    return (occ & _BOX_MASKS[b]).bit_count()


def _capture_mask_for_edge(occ, cap, e):
    """Boxes captured by drawing edge e."""
    cm = 0
    for b in _EDGE_BOXES[e]:
        bb = 1 << b
        if (cap & bb) == 0 and _box_sides(occ, b) == 3:
            cm |= bb
    return cm


def _danger_count_for_edge(occ, cap, e):
    """Number of adjacent unclaimed boxes that would become 3-sided."""
    danger = 0
    for b in _EDGE_BOXES[e]:
        bb = 1 << b
        if (cap & bb) == 0 and _box_sides(occ, b) == 2:
            danger += 1
    return danger


def _classify_moves(occ, cap):
    captures = []
    safe = []
    unsafe = []

    legal = _ALL_EDGES_MASK ^ (occ & _ALL_EDGES_MASK)
    while legal:
        bit = legal & -legal
        e = bit.bit_length() - 1
        legal ^= bit

        cm = _capture_mask_for_edge(occ, cap, e)
        if cm:
            captures.append((e, cm, cm.bit_count(), 0))
        else:
            danger = _danger_count_for_edge(occ, cap, e)
            if danger == 0:
                safe.append((e, 0, 0, 0))
            else:
                unsafe.append((e, 0, 0, danger))

    return captures, safe, unsafe


def _capturable_boxes_mask(occ, cap):
    m = 0
    for b in range(NUM_BOXES):
        bb = 1 << b
        if (cap & bb) == 0 and _box_sides(occ, b) == 3:
            m |= bb
    return m


def _count_boxes_with_sides(occ, cap, sides):
    n = 0
    for b in range(NUM_BOXES):
        if (cap & (1 << b)) == 0 and _box_sides(occ, b) == sides:
            n += 1
    return n


def _sacrifice_size(occ, cap, e):
    """
    Approximate number of boxes in the chain/component opened by edge e.
    Used when no safe move exists.
    """
    seen = 0
    total = 0
    stack = []

    for b in _EDGE_BOXES[e]:
        if (cap & (1 << b)) == 0 and _box_sides(occ, b) == 2:
            stack.append(b)

    while stack:
        b = stack.pop()
        bb = 1 << b
        if seen & bb:
            continue
        seen |= bb
        total += 1

        for ed in _BOX_EDGES[b]:
            if occ & (1 << ed):
                continue
            for nb in _EDGE_BOXES[ed]:
                if nb != b and (cap & (1 << nb)) == 0 and _box_sides(occ, nb) == 2:
                    if (seen & (1 << nb)) == 0:
                        stack.append(nb)

    return max(1, total)


def _loony_components(occ, cap):
    """
    If the position is a pure loony endgame where every unclaimed box has
    exactly two sides, return components as positive chain lengths and negative
    loop lengths. Otherwise return None.
    """
    for b in range(NUM_BOXES):
        if (cap & (1 << b)) == 0 and _box_sides(occ, b) != 2:
            return None

    seen = 0
    comps = []

    for b in range(NUM_BOXES):
        bb = 1 << b
        if (cap & bb) or (seen & bb):
            continue

        stack = [b]
        seen |= bb
        size = 0
        boundary_ends = 0

        while stack:
            x = stack.pop()
            size += 1

            for ed in _BOX_EDGES[x]:
                if occ & (1 << ed):
                    continue

                adj = _EDGE_BOXES[ed]
                if len(adj) == 1:
                    boundary_ends += 1
                else:
                    nb = adj[1] if adj[0] == x else adj[0]
                    if cap & (1 << nb):
                        boundary_ends += 1
                    elif (seen & (1 << nb)) == 0:
                        seen |= 1 << nb
                        stack.append(nb)

        if size:
            if boundary_ends == 0 and size >= 4:
                comps.append(-size)  # loop
            else:
                comps.append(size)   # chain

    return tuple(sorted(comps))


@lru_cache(maxsize=10000)
def _loony_value(comps):
    """
    Value for the player to move/open in a pure chain-loop endgame.
    Positive is good for the player to move.
    """
    if not comps:
        return 0

    best = -1000
    for i, comp in enumerate(comps):
        rest = comps[:i] + comps[i + 1:]
        vr = _loony_value(rest)

        if comp > 0:
            n = comp
            responses = [-n - vr]       # controller takes all
            if n >= 3:
                responses.append(4 - n + vr)  # hard-hearted handout of 2
        else:
            n = -comp
            responses = [-n - vr]
            if n >= 4:
                responses.append(8 - n + vr)  # handout of 4 in a loop

        # The opponent/controller chooses the response worst for opener.
        val = min(responses)
        if val > best:
            best = val

    return best


def _heuristic_eval(occ, cap):
    """
    Fast approximate future margin for the player to move.
    Used only outside exact search.
    """
    legal = _ALL_EDGES_MASK ^ (occ & _ALL_EDGES_MASK)
    if legal == 0:
        return 0.0

    captures, safe, unsafe = _classify_moves(occ, cap)

    if captures:
        cb = _capturable_boxes_mask(occ, cap).bit_count()
        return 3.0 * cb + 0.20 * len(captures)

    if safe:
        n = len(safe)
        # With n safe moves and current player to move, odd n tends to make the
        # opponent open the first chain; even n tends to make current player open.
        mag = 1.0
        if n <= 12:
            mag = 1.6
        if n <= 6:
            mag = 2.4
        if n <= 2:
            mag = 3.2
        return mag if (n % 2 == 1) else -mag

    comps = _loony_components(occ, cap)
    if comps is not None:
        return float(_loony_value(comps))

    # Non-pure loony fallback: current player must open something, so prefer
    # positions where the smallest sacrifice is small.
    best = -50.0
    for e, _, _, _ in unsafe:
        val = -float(_sacrifice_size(occ, cap, e))
        if val > best:
            best = val
    return best


def _safe_move_score(occ, cap, e):
    new_occ = occ | (1 << e)

    # Opponent moves next after a safe move, so negate opponent evaluation.
    score = -55.0 * _heuristic_eval(new_occ, cap)

    made_twos = 0
    adj_sides = 0
    for b in _EDGE_BOXES[e]:
        if cap & (1 << b):
            continue
        s = _box_sides(occ, b)
        adj_sides += s
        if s == 1:
            made_twos += 1

    twos_after = _count_boxes_with_sides(new_occ, cap, 2)

    # Avoid creating 2-sided boxes too early unless parity/endgame says it is good.
    score -= 65.0 * made_twos
    score -= 2.0 * twos_after
    score -= 3.0 * adj_sides

    if len(_EDGE_BOXES[e]) == 1:
        score += 0.5
    score += _STATIC_SCORE[e]
    return score


def _capture_move_score(occ, cap, e, cm):
    new_occ = occ | (1 << e)
    new_cap = cap | cm
    k = cm.bit_count()
    # Captures keep the turn, so future heuristic is from our perspective.
    return 1000.0 * k + 60.0 * _heuristic_eval(new_occ, new_cap) + _STATIC_SCORE[e]


def _sacrifice_score(occ, cap, e):
    new_occ = occ | (1 << e)
    opp_eval = _heuristic_eval(new_occ, cap)
    size = _sacrifice_size(occ, cap, e)
    danger = _danger_count_for_edge(occ, cap, e)
    return -60.0 * opp_eval - 35.0 * size - 25.0 * danger + _STATIC_SCORE[e]


def _ordered_moves_for_search(occ, cap):
    captures, safe, unsafe = _classify_moves(occ, cap)
    captures.sort(key=lambda x: (-x[2], _STATIC_RANK[x[0]]))
    safe.sort(key=lambda x: _STATIC_RANK[x[0]])
    unsafe.sort(key=lambda x: (x[3], _STATIC_RANK[x[0]]))
    return captures + safe + unsafe


def _root_ordered_moves(occ, cap):
    captures, safe, unsafe = _classify_moves(occ, cap)

    if captures:
        captures.sort(key=lambda x: -_capture_move_score(occ, cap, x[0], x[1]))
        safe.sort(key=lambda x: -_safe_move_score(occ, cap, x[0]))
        unsafe.sort(key=lambda x: -_sacrifice_score(occ, cap, x[0]))
        return captures + safe + unsafe

    if safe:
        safe.sort(key=lambda x: -_safe_move_score(occ, cap, x[0]))
        unsafe.sort(key=lambda x: -_sacrifice_score(occ, cap, x[0]))
        return safe + unsafe

    unsafe.sort(key=lambda x: -_sacrifice_score(occ, cap, x[0]))
    return unsafe


def _negamax_exact(occ, cap, alpha, beta):
    global _SEARCH_NODES

    _SEARCH_NODES += 1
    if (_SEARCH_NODES & 2047) == 0 and time.perf_counter() > _SEARCH_DEADLINE:
        raise TimeoutError

    legal = _ALL_EDGES_MASK ^ (occ & _ALL_EDGES_MASK)
    if legal == 0:
        return 0

    key = (occ, cap)
    ent = _TT.get(key)
    if ent is not None:
        val, flag = ent
        if flag == 0:
            return val
        if flag == 1:
            alpha = max(alpha, val)
        else:
            beta = min(beta, val)
        if alpha >= beta:
            return val

    orig_alpha = alpha
    orig_beta = beta
    best = -1000

    for e, cm, k, _ in _ordered_moves_for_search(occ, cap):
        occ2 = occ | (1 << e)
        cap2 = cap | cm

        if k:
            val = k + _negamax_exact(occ2, cap2, alpha - k, beta - k)
        else:
            val = -_negamax_exact(occ2, cap2, -beta, -alpha)

        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    if best <= orig_alpha:
        flag = 2
    elif best >= orig_beta:
        flag = 1
    else:
        flag = 0
    _TT[key] = (best, flag)

    return best


def _choose_exact(occ, cap, deadline):
    global _SEARCH_DEADLINE, _SEARCH_NODES, _TT

    if len(_TT) > 700000:
        _TT.clear()

    _SEARCH_DEADLINE = deadline
    _SEARCH_NODES = 0

    moves = _root_ordered_moves(occ, cap)
    if not moves:
        return None

    best_e = None
    best_val = -1000
    alpha = -1000
    beta = 1000

    for e, cm, k, _ in moves:
        if time.perf_counter() > deadline:
            raise TimeoutError

        occ2 = occ | (1 << e)
        cap2 = cap | cm

        if k:
            val = k + _negamax_exact(occ2, cap2, alpha - k, beta - k)
        else:
            val = -_negamax_exact(occ2, cap2, -beta, -alpha)

        if val > best_val:
            best_val = val
            best_e = e
        if val > alpha:
            alpha = val

    return best_e


def _limited_moves(occ, cap, root=False):
    captures, safe, unsafe = _classify_moves(occ, cap)

    if captures:
        captures.sort(key=lambda x: -_capture_move_score(occ, cap, x[0], x[1]))
        if len(captures) + len(safe) + len(unsafe) <= 10:
            all_moves = captures + safe + unsafe
            all_moves.sort(
                key=lambda x: (
                    0 if x[2] else 1,
                    -_capture_move_score(occ, cap, x[0], x[1]) if x[2] else -_sacrifice_score(occ, cap, x[0]),
                )
            )
            return all_moves

        chosen = captures[:8]
        # Include possible handout/sacrifice moves only when no ordinary safe
        # move is available; exact search handles most such cases.
        if not safe and unsafe:
            unsafe.sort(key=lambda x: -_sacrifice_score(occ, cap, x[0]))
            chosen += unsafe[:2]
        return chosen

    if safe:
        safe.sort(key=lambda x: -_safe_move_score(occ, cap, x[0]))
        return safe[:14 if root else 8]

    unsafe.sort(key=lambda x: -_sacrifice_score(occ, cap, x[0]))
    return unsafe[:14 if root else 8]


def _limited_negamax(occ, cap, depth, alpha, beta):
    global _LIMIT_NODES

    _LIMIT_NODES += 1
    if (_LIMIT_NODES & 1023) == 0 and time.perf_counter() > _LIMIT_DEADLINE:
        raise TimeoutError

    legal = _ALL_EDGES_MASK ^ (occ & _ALL_EDGES_MASK)
    if legal == 0:
        return 0.0

    if depth <= 0:
        return _heuristic_eval(occ, cap)

    key = (occ, cap, depth)
    if key in _LIMIT_TT:
        return _LIMIT_TT[key]

    moves = _limited_moves(occ, cap, root=False)
    if not moves:
        return 0.0

    best = -1.0e9

    for e, cm, k, _ in moves:
        occ2 = occ | (1 << e)
        cap2 = cap | cm

        if k:
            val = k + _limited_negamax(occ2, cap2, depth - 1, alpha - k, beta - k)
        else:
            val = -_limited_negamax(occ2, cap2, depth - 1, -beta, -alpha)

        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    _LIMIT_TT[key] = best
    return best


def _choose_limited(occ, cap, depth, deadline):
    global _LIMIT_DEADLINE, _LIMIT_NODES, _LIMIT_TT

    _LIMIT_DEADLINE = deadline
    _LIMIT_NODES = 0
    _LIMIT_TT = {}

    moves = _limited_moves(occ, cap, root=True)
    if not moves:
        return None

    best_e = None
    best_val = -1.0e9
    alpha = -1.0e9
    beta = 1.0e9

    for e, cm, k, _ in moves:
        if time.perf_counter() > deadline:
            break

        occ2 = occ | (1 << e)
        cap2 = cap | cm

        try:
            if k:
                val = k + _limited_negamax(occ2, cap2, depth - 1, alpha - k, beta - k)
            else:
                val = -_limited_negamax(occ2, cap2, depth - 1, -beta, -alpha)
        except TimeoutError:
            break

        if val > best_val:
            best_val = val
            best_e = e
        if val > alpha:
            alpha = val

    if best_e is None:
        raise TimeoutError
    return best_e


def _choose_heuristic(occ, cap):
    captures, safe, unsafe = _classify_moves(occ, cap)

    if captures:
        captures.sort(key=lambda x: -_capture_move_score(occ, cap, x[0], x[1]))
        return captures[0][0]

    if safe:
        safe.sort(key=lambda x: -_safe_move_score(occ, cap, x[0]))
        return safe[0][0]

    if unsafe:
        unsafe.sort(key=lambda x: -_sacrifice_score(occ, cap, x[0]))
        return unsafe[0][0]

    return None


def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    start = time.perf_counter()

    try:
        occ, cap = _state_to_masks(horizontal, vertical, capture)
        fallback = _first_legal_move_str(occ)
        if fallback is None:
            return _array_fallback(horizontal, vertical)

        legal_mask = _ALL_EDGES_MASK ^ (occ & _ALL_EDGES_MASK)
        remaining = legal_mask.bit_count()
        captures, safe, unsafe = _classify_moves(occ, cap)

        # Exact search in positions where it is usually affordable and important:
        # late endgames, capture races, and low-safe-move chain transitions.
        exact_allowed = (
            remaining <= 20
            or (remaining <= 23 and (len(captures) > 0 or len(safe) <= 6))
            or (remaining <= 24 and len(safe) == 0)
        )

        if exact_allowed:
            try:
                e = _choose_exact(occ, cap, start + 0.80)
                if e is not None and (occ & (1 << e)) == 0:
                    return _MOVE_STR[e]
            except TimeoutError:
                pass
            except Exception:
                pass

        # Small selective search for midgame tactics.
        now = time.perf_counter()
        if remaining <= 32 and now < start + 0.55:
            try:
                if remaining <= 24:
                    depth = 8
                elif remaining <= 28:
                    depth = 7
                else:
                    depth = 5
                deadline = min(start + 0.88, now + 0.18)
                e = _choose_limited(occ, cap, depth, deadline)
                if e is not None and (occ & (1 << e)) == 0:
                    return _MOVE_STR[e]
            except TimeoutError:
                pass
            except Exception:
                pass

        # Guaranteed fast fallback.
        e = _choose_heuristic(occ, cap)
        if e is not None and (occ & (1 << e)) == 0:
            return _MOVE_STR[e]

        return fallback

    except Exception:
        return _array_fallback(horizontal, vertical)
