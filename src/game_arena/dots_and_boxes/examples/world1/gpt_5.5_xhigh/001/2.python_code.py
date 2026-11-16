
import time
import numpy as np

# Dots and Boxes: 4x4 boxes => 5x4 horizontal + 4x5 vertical = 40 real edges.
# Edge numbering:
#   0..19   : H(row 0..4, col 0..3), index = row*4 + col
#   20..39  : V(row 0..3, col 0..4), index = 20 + row*5 + col

_EDGE_COUNT = 40
_FULL_MASK = (1 << _EDGE_COUNT) - 1
_GLOBAL_EXACT = {}
_GLOBAL_EXACT_MAX = 250000


def _h_index(r, c):
    return r * 4 + c


def _v_index(r, c):
    return 20 + r * 5 + c


_EDGE_STRINGS = []
_EDGE_BOXES = []
_EDGE_CENTER_WEIGHT = []

for r in range(5):
    for c in range(4):
        _EDGE_STRINGS.append(f"{r},{c},H")
        adj = []
        if r > 0:
            adj.append((r - 1) * 4 + c)
        if r < 4:
            adj.append(r * 4 + c)
        _EDGE_BOXES.append(tuple(adj))

        y = float(r)
        x = float(c) + 0.5
        _EDGE_CENTER_WEIGHT.append(-((y - 2.0) ** 2 + (x - 2.0) ** 2))

for r in range(4):
    for c in range(5):
        _EDGE_STRINGS.append(f"{r},{c},V")
        adj = []
        if c > 0:
            adj.append(r * 4 + (c - 1))
        if c < 4:
            adj.append(r * 4 + c)
        _EDGE_BOXES.append(tuple(adj))

        y = float(r) + 0.5
        x = float(c)
        _EDGE_CENTER_WEIGHT.append(-((y - 2.0) ** 2 + (x - 2.0) ** 2))

_EDGE_BOXES = tuple(_EDGE_BOXES)
_EDGE_CENTER_WEIGHT = tuple(_EDGE_CENTER_WEIGHT)
_EDGE_BITS = tuple(1 << i for i in range(_EDGE_COUNT))

_BOX_MASKS = []
for r in range(4):
    for c in range(4):
        top = _h_index(r, c)
        bottom = _h_index(r + 1, c)
        left = _v_index(r, c)
        right = _v_index(r, c + 1)
        _BOX_MASKS.append(
            _EDGE_BITS[top] | _EDGE_BITS[bottom] | _EDGE_BITS[left] | _EDGE_BITS[right]
        )
_BOX_MASKS = tuple(_BOX_MASKS)


class _SearchTimeout(Exception):
    pass


def _state_to_mask(horizontal, vertical):
    occ = 0
    for r in range(5):
        for c in range(4):
            if horizontal[r, c] != 0:
                occ |= _EDGE_BITS[_h_index(r, c)]
    for r in range(4):
        for c in range(5):
            if vertical[r, c] != 0:
                occ |= _EDGE_BITS[_v_index(r, c)]
    return occ


def _first_legal_from_arrays(horizontal, vertical):
    """Emergency legal move fallback. Prefer real 4x4-board edges."""
    try:
        for r in range(5):
            for c in range(4):
                if horizontal[r, c] == 0:
                    return f"{r},{c},H"
        for r in range(4):
            for c in range(5):
                if vertical[r, c] == 0:
                    return f"{r},{c},V"

        # If an arena treats the unused 5x5 fringe as playable, this may still save us.
        for r in range(5):
            for c in range(5):
                if horizontal[r, c] == 0:
                    return f"{r},{c},H"
        for r in range(5):
            for c in range(5):
                if vertical[r, c] == 0:
                    return f"{r},{c},V"
    except Exception:
        pass

    # Should only happen if called after the game is already over.
    return "0,0,H"


def _iter_legal(occ):
    m = _FULL_MASK ^ (occ & _FULL_MASK)
    while m:
        bit = m & -m
        e = bit.bit_length() - 1
        yield e
        m ^= bit


def _capture_count(occ, e):
    cnt = 0
    for b in _EDGE_BOXES[e]:
        if (occ & _BOX_MASKS[b]).bit_count() == 3:
            cnt += 1
    return cnt


def _creates_count(occ, e):
    """Number of adjacent boxes that would become 3-sided but not captured."""
    cnt = 0
    for b in _EDGE_BOXES[e]:
        if (occ & _BOX_MASKS[b]).bit_count() == 2:
            cnt += 1
    return cnt


def _safe_features(occ, e):
    # For safe moves, c==1 means this move creates a 2-sided box, which is
    # usually more committal than playing around untouched boxes.
    twos_created = 0
    side_sum = 0
    adj_len = len(_EDGE_BOXES[e])
    for b in _EDGE_BOXES[e]:
        c = (occ & _BOX_MASKS[b]).bit_count()
        side_sum += c
        if c == 1:
            twos_created += 1
    return twos_created, side_sum, adj_len


def _safe_harm(occ, e):
    twos_created, side_sum, adj_len = _safe_features(occ, e)
    return 10 * twos_created + side_sum - adj_len


def _side_distribution(occ):
    dist = [0, 0, 0, 0, 0]
    for mask in _BOX_MASKS:
        dist[(occ & mask).bit_count()] += 1
    return dist


def _categorized_moves(occ):
    captures = []
    safe = []
    danger = []
    for e in _iter_legal(occ):
        k = _capture_count(occ, e)
        if k:
            captures.append((e, k))
        else:
            cr = _creates_count(occ, e)
            if cr:
                danger.append((e, cr))
            else:
                safe.append(e)
    return captures, safe, danger


def _max_capture_run(occ, memo):
    """Maximum boxes capturable by taking only capturing moves until none remain."""
    if occ in memo:
        return memo[occ]

    best = 0
    for e in _iter_legal(occ):
        k = _capture_count(occ, e)
        if k:
            v = k + _max_capture_run(occ | _EDGE_BITS[e], memo)
            if v > best:
                best = v

    memo[occ] = best
    return best


def _best_open_cost(occ, danger=None):
    """If forced to open, estimate how many boxes the opponent can immediately harvest."""
    if danger is None:
        _, _, danger = _categorized_moves(occ)

    if not danger:
        return 0

    capmemo = {}
    best = 99
    for e, _ in danger:
        cost = _max_capture_run(occ | _EDGE_BITS[e], capmemo)
        if cost < best:
            best = cost
    return 0 if best == 99 else best


def _static_no_capture_value(occ, safe=None, danger=None):
    """Approximate value for side to move when there are no immediate captures."""
    if occ == _FULL_MASK:
        return 0.0

    if safe is None or danger is None:
        _, safe, danger = _categorized_moves(occ)

    if safe:
        sc = len(safe)
        dist = _side_distribution(occ)

        # In the safe-move phase, odd safe-move count is generally good for the
        # player to move: they may be able to make the opponent open first.
        val = 0.60 if (sc & 1) else -0.60

        # Many 2-sided boxes mean the loony phase is near; amplify parity a bit.
        if sc & 1:
            val += 0.04 * dist[2]
        else:
            val -= 0.04 * dist[2]

        val += 0.004 * sc
        return val

    if danger:
        return -float(_best_open_cost(occ, danger))

    return 0.0


def _capture_rank(occ, item):
    e, k = item
    return (-k, -_creates_count(occ, e), _safe_harm(occ, e), -_EDGE_CENTER_WEIGHT[e], e)


def _danger_rank(occ, e, capmemo):
    nocc = occ | _EDGE_BITS[e]
    cost = _max_capture_run(nocc, capmemo)
    cr = _creates_count(occ, e)
    dist = _side_distribution(nocc)
    return (cost, cr, dist[2], -_EDGE_CENTER_WEIGHT[e], e)


def _capture_phase_value(occ, memo, depth):
    """Approximate tactical value while boxes are available, including handout moves."""
    if occ == _FULL_MASK:
        return 0.0

    caps, safe, danger = _categorized_moves(occ)

    if depth <= 0:
        if caps:
            return float(_max_capture_run(occ, {}))
        return _static_no_capture_value(occ, safe, danger)

    key = (occ, depth)
    if key in memo:
        return memo[key]

    if not caps:
        val = _static_no_capture_value(occ, safe, danger)
        memo[key] = val
        return val

    best = -100.0

    for e, k in sorted(caps, key=lambda item: _capture_rank(occ, item)):
        v = float(k) + _capture_phase_value(occ | _EDGE_BITS[e], memo, depth - 1)
        if v > best:
            best = v

    # Hard-hearted handout approximation: sometimes a non-capturing move while
    # captures exist is correct. Such moves normally create capturable boxes.
    if danger:
        capmemo = {}
        handouts = sorted(danger, key=lambda item: _danger_rank(occ, item[0], capmemo))[:4]
        for e, _ in handouts:
            v = -_capture_phase_value(occ | _EDGE_BITS[e], memo, depth - 1)
            if v > best:
                best = v

    memo[key] = best
    return best


def _static_value(occ):
    caps, safe, danger = _categorized_moves(occ)
    if caps:
        return _capture_phase_value(occ, {}, 10)
    return _static_no_capture_value(occ, safe, danger)


def _safe_rank(occ, e):
    nocc = occ | _EDGE_BITS[e]
    caps, safe, danger = _categorized_moves(nocc)
    opp_val = _static_value(nocc) if caps else _static_no_capture_value(nocc, safe, danger)
    twos_created, side_sum, adj_len = _safe_features(occ, e)
    return (opp_val, twos_created, -adj_len, -_EDGE_CENTER_WEIGHT[e], side_sum, e)


def _candidate_moves(occ, root=False):
    caps, safe, danger = _categorized_moves(occ)

    if caps:
        moves = sorted(caps, key=lambda item: _capture_rank(occ, item))

        # Include a few plausible handout/double-cross moves.
        if danger:
            capmemo = {}
            extra = sorted(danger, key=lambda item: _danger_rank(occ, item[0], capmemo))[:6]
            moves += [(e, 0) for e, _ in extra]
        return moves

    if safe:
        limit = 18 if root else 8
        s = sorted(safe, key=lambda e: _safe_rank(occ, e))
        return [(e, 0) for e in s[:limit]]

    if danger:
        limit = 18 if root else 8
        capmemo = {}
        d = sorted(danger, key=lambda item: _danger_rank(occ, item[0], capmemo))
        return [(e, 0) for e, _ in d[:limit]]

    return []


def _ordered_moves(occ):
    """Move ordering for exact search. Includes every legal move."""
    arr = []
    for e in _iter_legal(occ):
        k = _capture_count(occ, e)
        if k:
            key = (0, -k, -_creates_count(occ, e), _safe_harm(occ, e), e)
        else:
            cr = _creates_count(occ, e)
            if cr == 0:
                key = (1, _safe_harm(occ, e), -_EDGE_CENTER_WEIGHT[e], e)
            else:
                key = (2, cr, _safe_harm(occ, e), -_EDGE_CENTER_WEIGHT[e], e)
        arr.append((key, e, k))

    arr.sort(key=lambda x: x[0])
    return [(e, k) for _, e, k in arr]


def _store_exact(occ, val, memo):
    memo[occ] = val
    if len(_GLOBAL_EXACT) < _GLOBAL_EXACT_MAX:
        _GLOBAL_EXACT[occ] = val


def _exact_negamax(occ, alpha, beta, memo, deadline, nodes):
    # Value is future box margin for the player to move.
    if occ == _FULL_MASK:
        return 0

    if occ in memo:
        return memo[occ]
    gv = _GLOBAL_EXACT.get(occ)
    if gv is not None:
        return gv

    nodes[0] += 1
    if (nodes[0] & 2047) == 0 and time.perf_counter() > deadline:
        raise _SearchTimeout()

    moves = _ordered_moves(occ)
    if not moves:
        return 0

    best = -100
    for e, k in moves:
        nocc = occ | _EDGE_BITS[e]
        if k:
            # Capturing keeps the move.
            v = k + _exact_negamax(nocc, alpha - k, beta - k, memo, deadline, nodes)
        else:
            # Non-capture passes the turn.
            v = -_exact_negamax(nocc, -beta, -alpha, memo, deadline, nodes)

        if v > best:
            best = v
        if v > alpha:
            alpha = v
        if alpha >= beta:
            return best

    _store_exact(occ, best, memo)
    return best


def _root_tiebreak(occ, e):
    k = _capture_count(occ, e)
    nocc = occ | _EDGE_BITS[e]

    if k:
        return (
            10.0 * k
            + 0.10 * _creates_count(occ, e)
            + 0.001 * _EDGE_CENTER_WEIGHT[e]
        )

    cr = _creates_count(occ, e)
    if cr == 0:
        caps, safe, danger = _categorized_moves(nocc)
        opp_val = _static_value(nocc) if caps else _static_no_capture_value(nocc, safe, danger)
        twos_created, side_sum, adj_len = _safe_features(occ, e)
        return (
            -opp_val
            - 0.25 * twos_created
            - 0.01 * side_sum
            + 0.04 * adj_len
            + 0.001 * _EDGE_CENTER_WEIGHT[e]
        )

    return -float(_max_capture_run(nocc, {})) - 0.02 * cr + 0.001 * _EDGE_CENTER_WEIGHT[e]


def _choose_exact(occ, deadline):
    moves = _ordered_moves(occ)
    if not moves:
        return None, 0

    memo = {}
    nodes = [0]
    best_e = None
    best_v = -100
    best_tie = -1e100
    alpha = -64
    beta = 64

    for e, k in moves:
        if time.perf_counter() > deadline:
            raise _SearchTimeout()

        nocc = occ | _EDGE_BITS[e]
        if k:
            v = k + _exact_negamax(nocc, alpha - k, beta - k, memo, deadline, nodes)
        else:
            v = -_exact_negamax(nocc, -beta, -alpha, memo, deadline, nodes)

        tie = _root_tiebreak(occ, e)
        if v > best_v or (v == best_v and tie > best_tie):
            best_v = v
            best_e = e
            best_tie = tie

        if v > alpha:
            alpha = v

    return best_e, best_v


def _quick_value(occ, depth, alpha, beta, memo, deadline, nodes):
    if occ == _FULL_MASK:
        return 0.0

    nodes[0] += 1
    if (nodes[0] & 511) == 0 and time.perf_counter() > deadline:
        raise _SearchTimeout()

    if depth <= 0:
        return _static_value(occ)

    key = (occ, depth)
    if key in memo:
        return memo[key]

    moves = _candidate_moves(occ, root=False)
    if not moves:
        return 0.0

    best = -100.0
    for e, k in moves:
        nocc = occ | _EDGE_BITS[e]
        if k:
            v = float(k) + _quick_value(nocc, depth - 1, alpha - k, beta - k, memo, deadline, nodes)
        else:
            v = -_quick_value(nocc, depth - 1, -beta, -alpha, memo, deadline, nodes)

        if v > best:
            best = v
        if v > alpha:
            alpha = v
        if alpha >= beta:
            return best

    memo[key] = best
    return best


def _choose_quick(occ, depth, deadline):
    moves = _candidate_moves(occ, root=True)
    if not moves:
        return None

    memo = {}
    nodes = [0]
    best_e = None
    best_v = -1e100
    best_tie = -1e100
    alpha = -64.0
    beta = 64.0

    for e, k in moves:
        if time.perf_counter() > deadline:
            raise _SearchTimeout()

        nocc = occ | _EDGE_BITS[e]
        if k:
            v = float(k) + _quick_value(nocc, depth - 1, alpha - k, beta - k, memo, deadline, nodes)
        else:
            v = -_quick_value(nocc, depth - 1, -beta, -alpha, memo, deadline, nodes)

        tie = _root_tiebreak(occ, e)
        if v > best_v + 1e-9 or (abs(v - best_v) <= 1e-9 and tie > best_tie):
            best_v = v
            best_e = e
            best_tie = tie

        if v > alpha:
            alpha = v

    return best_e


def _estimate_move_value(occ, e):
    k = _capture_count(occ, e)
    nocc = occ | _EDGE_BITS[e]
    if k:
        return float(k) + _static_value(nocc)
    return -_static_value(nocc)


def _choose_heuristic(occ):
    caps, safe, danger = _categorized_moves(occ)

    if caps:
        candidates = list(caps)

        # Also consider a handful of handout moves; exact/quick search usually
        # handles these, but this keeps the final fallback from being naive.
        if danger:
            capmemo = {}
            d = sorted(danger, key=lambda item: _danger_rank(occ, item[0], capmemo))[:6]
            candidates += [(e, 0) for e, _ in d]

    elif safe:
        candidates = [(e, 0) for e in safe]

    else:
        candidates = [(e, 0) for e, _ in danger]

    if not candidates:
        candidates = [(e, _capture_count(occ, e)) for e in _iter_legal(occ)]

    best_e = None
    best_v = -1e100
    best_tie = -1e100

    for e, _ in candidates:
        v = _estimate_move_value(occ, e)
        tie = _root_tiebreak(occ, e)
        if v > best_v + 1e-9 or (abs(v - best_v) <= 1e-9 and tie > best_tie):
            best_v = v
            best_e = e
            best_tie = tie

    return best_e


def _uncompleted_boxes(occ):
    return sum(1 for mask in _BOX_MASKS if (occ & mask).bit_count() < 4)


def _policy_impl(horizontal, vertical, capture):
    # capture is not needed for move legality or future-margin decisions; the
    # current score is constant across candidate moves.
    _ = capture

    occ = _state_to_mask(horizontal, vertical)
    remaining_mask = _FULL_MASK ^ (occ & _FULL_MASK)
    if remaining_mask == 0:
        return _first_legal_from_arrays(horizontal, vertical)

    start = time.perf_counter()
    rem = remaining_mask.bit_count()
    caps, safe, _ = _categorized_moves(occ)
    uncompleted = _uncompleted_boxes(occ)

    # Exact search in late/tactical/loony positions.
    attempt_exact = (
        rem <= 20
        or ((caps or not safe) and rem <= 27)
        or (uncompleted <= 8 and rem <= 28)
    )

    if attempt_exact:
        try:
            important = bool(caps) or not safe or rem <= 16
            budget = 0.78 if important else 0.55
            e, _v = _choose_exact(occ, start + budget)
            if e is not None:
                return _EDGE_STRINGS[e]
        except _SearchTimeout:
            pass

    # Candidate-limited tactical search for the middle game.
    try:
        if time.perf_counter() < start + 0.86:
            if caps or not safe:
                depth = 10
            elif rem <= 28:
                depth = 5
            else:
                depth = 4

            e = _choose_quick(occ, depth, start + 0.88)
            if e is not None:
                return _EDGE_STRINGS[e]
    except _SearchTimeout:
        pass

    # Fast always-legal fallback.
    e = _choose_heuristic(occ)
    if e is not None:
        return _EDGE_STRINGS[e]

    return _first_legal_from_arrays(horizontal, vertical)


def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    try:
        return _policy_impl(horizontal, vertical, capture)
    except Exception:
        # Absolute safety net: never fail to return a move string.
        return _first_legal_from_arrays(horizontal, vertical)
