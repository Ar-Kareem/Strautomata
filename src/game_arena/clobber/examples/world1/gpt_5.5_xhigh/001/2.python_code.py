
from __future__ import annotations
import time

_ROWS = 5
_COLS = 6
_N = _ROWS * _COLS

_MATE = 100_000_000
_INF = 1_000_000_000
_TIME_LIMIT = 0.90

_EXACT, _LOWER, _UPPER = 0, 1, 2
_TT_LIMIT = 350_000

_NEI = [0] * _N
_CELL_SCORE = [0] * _N
_HAS_LEFT = _HAS_RIGHT = _HAS_UP = _HAS_DOWN = 0

for r in range(_ROWS):
    for c in range(_COLS):
        i = r * _COLS + c
        b = 1 << i

        if c > 0:
            _HAS_LEFT |= b
        if c + 1 < _COLS:
            _HAS_RIGHT |= b
        if r > 0:
            _HAS_UP |= b
        if r + 1 < _ROWS:
            _HAS_DOWN |= b

        m = 0
        if r > 0:
            m |= 1 << (i - _COLS)
        if c + 1 < _COLS:
            m |= 1 << (i + 1)
        if r + 1 < _ROWS:
            m |= 1 << (i + _COLS)
        if c > 0:
            m |= 1 << (i - 1)
        _NEI[i] = m

        # Small deterministic tie-breaker: central squares are usually more flexible.
        _CELL_SCORE[i] = 20 - (abs(r - 2) * 4 + abs(2 * c - 5) * 2)

_TT = {}
_HISTORY = [0] * (_N * _N)
_KILLERS = [[-1, -1] for _ in range(64)]

_DEADLINE = 0.0
_NODES = 0


class _SearchTimeout(Exception):
    pass


def _check_time() -> None:
    if time.perf_counter() >= _DEADLINE:
        raise _SearchTimeout()


def _mask_from_array(a) -> int:
    """Accepts either a numpy-like 5x6/flat array or Python nested/flat lists."""
    try:
        flat = a.ravel()
        m = 0
        for i in range(_N):
            if flat[i]:
                m |= 1 << i
        return m
    except Exception:
        pass

    try:
        if len(a) == _N:
            m = 0
            for i in range(_N):
                if a[i]:
                    m |= 1 << i
            return m
    except Exception:
        pass

    m = 0
    for r in range(_ROWS):
        row = a[r]
        for c in range(_COLS):
            if row[c]:
                m |= 1 << (r * _COLS + c)
    return m


def _neighbor_bits(mask: int) -> int:
    return (
        ((mask & _HAS_LEFT) >> 1)
        | ((mask & _HAS_RIGHT) << 1)
        | ((mask & _HAS_UP) >> _COLS)
        | ((mask & _HAS_DOWN) << _COLS)
    )


def _cut_edges(a: int, b: int) -> int:
    """Number of adjacent opposite-colour edges."""
    return (
        (((a & _HAS_RIGHT) << 1) & b).bit_count()
        + (((b & _HAS_RIGHT) << 1) & a).bit_count()
        + (((a & _HAS_DOWN) << _COLS) & b).bit_count()
        + (((b & _HAS_DOWN) << _COLS) & a).bit_count()
    )


def _terminal_score(us: int, them: int) -> int:
    # No legal move: side to move loses.  The occupied-count term prefers
    # faster wins / slower losses without compromising mate dominance.
    return -_MATE - (us | them).bit_count()


def _child_edges(us: int, them: int, edges: int, s: int, d: int) -> int:
    # Exact local update of the cut-edge count after us moves s -> d.
    ce = (
        edges
        - (_NEI[s] & them).bit_count()
        - (_NEI[d] & us).bit_count()
        + 1
        + (_NEI[d] & them).bit_count()
    )
    return 0 if ce < 0 else ce


def _format_move(enc: int) -> str:
    if enc < 0:
        return "0,0,U"

    s = enc >> 5
    d = enc & 31

    if d == s - _COLS:
        ch = "U"
    elif d == s + 1:
        ch = "R"
    elif d == s + _COLS:
        ch = "D"
    else:
        ch = "L"

    return f"{s // _COLS},{s % _COLS},{ch}"


def _first_legal_move(us: int, them: int) -> int:
    u = us
    while u:
        sb = u & -u
        s = sb.bit_length() - 1
        u ^= sb
        t = _NEI[s] & them
        if t:
            d = (t & -t).bit_length() - 1
            return (s << 5) | d
    return -1


def _record_cutoff(enc: int, depth: int, ply: int) -> None:
    if 0 <= ply < len(_KILLERS):
        k = _KILLERS[ply]
        if k[0] != enc:
            k[1] = k[0]
            k[0] = enc

    idx = (enc >> 5) * _N + (enc & 31)
    if _HISTORY[idx] < 200_000:
        _HISTORY[idx] += depth * depth + 1


def _ordered_moves(us: int, them: int, edges: int, tt_move: int, ply: int):
    moves = []

    killer0 = killer1 = -1
    if 0 <= ply < len(_KILLERS):
        killer0, killer1 = _KILLERS[ply]

    u = us
    while u:
        sb = u & -u
        s = sb.bit_length() - 1
        u ^= sb

        targets = _NEI[s] & them
        if not targets:
            continue

        deg_s = targets.bit_count()
        t = targets
        while t:
            db = t & -t
            d = db.bit_length() - 1
            t ^= db

            ce = (
                edges
                - deg_s
                - ((_NEI[d] & us).bit_count())
                + 1
                + ((_NEI[d] & them).bit_count())
            )
            if ce < 0:
                ce = 0

            enc = (s << 5) | d
            score = (
                _HISTORY[s * _N + d]
                - 1000 * ce
                + 4 * _CELL_SCORE[d]
                - _CELL_SCORE[s]
            )

            if ce == 0:
                score += 300_000_000
            if enc == tt_move:
                score += 200_000_000
            if enc == killer0:
                score += 50_000_000
            elif enc == killer1:
                score += 25_000_000

            moves.append((score, enc, ce))

    moves.sort(key=lambda x: x[0], reverse=True)
    return moves


def _min_child_edges(us: int, them: int, edges: int) -> int:
    best = 99

    u = us
    while u:
        sb = u & -u
        s = sb.bit_length() - 1
        u ^= sb

        targets = _NEI[s] & them
        if not targets:
            continue

        deg_s = targets.bit_count()
        t = targets
        while t:
            db = t & -t
            d = db.bit_length() - 1
            t ^= db

            ce = (
                edges
                - deg_s
                - ((_NEI[d] & us).bit_count())
                + 1
                + ((_NEI[d] & them).bit_count())
            )
            if ce <= 0:
                return 0
            if ce < best:
                best = ce

    return 0 if best == 99 else best


def _mixed_component_parity(us: int, them: int) -> int:
    """Parity estimate of reducing each active mixed component to one survivor."""
    rem = us | them
    parity = 0

    while rem:
        seed = rem & -rem
        comp = 0
        frontier = seed

        while frontier:
            comp |= frontier
            frontier = _neighbor_bits(frontier) & rem & ~comp

        rem &= ~comp

        if (comp & us) and (comp & them):
            parity ^= (comp.bit_count() - 1) & 1

    return parity


def _evaluate(us: int, them: int, edges: int) -> int:
    if edges == 0:
        return _terminal_score(us, them)

    uc = us.bit_count()
    tc = them.bit_count()
    occ_count = uc + tc

    # If a one-ply win exists, that is a real forced win, not just a heuristic.
    my_min = -1
    if edges <= 7:
        my_min = _min_child_edges(us, them, edges)
        if my_min == 0:
            return (_MATE // 2) + occ_count

    nb_us = _neighbor_bits(us)
    nb_them = _neighbor_bits(them)

    front_us = (us & nb_them).bit_count()
    front_them = (them & nb_us).bit_count()

    safe_us = uc - front_us
    safe_them = tc - front_them

    score = 0
    score += 20 * (uc - tc)
    score += 10 * (front_them - front_us)
    score += 4 * (safe_us - safe_them)
    score += 2 * min(edges, 12)

    if occ_count <= 24 or edges <= 22:
        parity = _mixed_component_parity(us, them)
    else:
        # Early dense positions are normally one active component.
        parity = (occ_count - 1) & 1

    score += 45 if parity else -45

    if edges <= 14:
        if my_min < 0:
            my_min = _min_child_edges(us, them, edges)

        opp_min = _min_child_edges(them, us, edges)

        # Prefer positions where our best move can reduce opponent activity
        # more than the opponent's hypothetical best move could reduce ours.
        score += 80 * (opp_min - my_min)

        if opp_min == 0:
            score -= 1200
        if my_min <= 2:
            score += (3 - my_min) * 80

    return score


def _negamax(us: int, them: int, depth: int, alpha: int, beta: int, ply: int, edges: int) -> int:
    global _NODES

    _NODES += 1
    if (_NODES & 255) == 0:
        _check_time()

    key = (us, them)
    entry = _TT.get(key)
    tt_move = -1

    if entry is not None:
        e_depth, e_flag, e_score, e_move = entry
        tt_move = e_move
        if e_depth >= depth:
            if e_flag == _EXACT:
                return e_score
            if e_flag == _LOWER and e_score >= beta:
                return e_score
            if e_flag == _UPPER and e_score <= alpha:
                return e_score

    if edges == 0:
        sc = _terminal_score(us, them)
        _TT[key] = (99, _EXACT, sc, -1)
        return sc

    if depth <= 0:
        return _evaluate(us, them, edges)

    alpha0 = alpha
    beta0 = beta

    ordered = _ordered_moves(us, them, edges, tt_move, ply)
    if not ordered:
        sc = _terminal_score(us, them)
        _TT[key] = (99, _EXACT, sc, -1)
        return sc

    best = -_INF
    best_move = ordered[0][1]

    occ_count = (us | them).bit_count()
    can_reduce = depth >= 5 and depth < occ_count and occ_count > 14

    for move_index, (_, enc, ce) in enumerate(ordered):
        s = enc >> 5
        d = enc & 31
        sb = 1 << s
        db = 1 << d

        child_us = them & ~db
        child_them = (us & ~sb) | db

        if move_index == 0:
            val = -_negamax(child_us, child_them, depth - 1, -beta, -alpha, ply + 1, ce)
        else:
            val = None

            # Conservative late-move reduction in large non-endgame nodes.
            if can_reduce and move_index >= 8 and ce > 2:
                val = -_negamax(child_us, child_them, depth - 2, -alpha - 1, -alpha, ply + 1, ce)
                if val > alpha:
                    val = None

            if val is None:
                val = -_negamax(child_us, child_them, depth - 1, -alpha - 1, -alpha, ply + 1, ce)
                if alpha < val < beta:
                    val = -_negamax(child_us, child_them, depth - 1, -beta, -alpha, ply + 1, ce)

        if val > best:
            best = val
            best_move = enc

        if val > alpha:
            alpha = val

        if alpha >= beta:
            _record_cutoff(enc, depth, ply)
            break

    if best <= alpha0:
        flag = _UPPER
    elif best >= beta0:
        flag = _LOWER
    else:
        flag = _EXACT

    _TT[key] = (depth, flag, best, best_move)
    return best


def _root_search(us: int, them: int, edges: int, depth: int, preferred: int):
    tt_move = preferred
    entry = _TT.get((us, them))
    if entry is not None and entry[3] >= 0:
        tt_move = entry[3]

    ordered = _ordered_moves(us, them, edges, tt_move, 0)
    if not ordered:
        return _terminal_score(us, them), -1

    alpha = -_INF
    beta = _INF
    best = -_INF
    best_move = ordered[0][1]

    for move_index, (_, enc, ce) in enumerate(ordered):
        _check_time()

        s = enc >> 5
        d = enc & 31
        sb = 1 << s
        db = 1 << d

        child_us = them & ~db
        child_them = (us & ~sb) | db

        if move_index == 0:
            val = -_negamax(child_us, child_them, depth - 1, -beta, -alpha, 1, ce)
        else:
            val = -_negamax(child_us, child_them, depth - 1, -alpha - 1, -alpha, 1, ce)
            if alpha < val < beta:
                val = -_negamax(child_us, child_them, depth - 1, -beta, -alpha, 1, ce)

        if val > best:
            best = val
            best_move = enc

        if val > alpha:
            alpha = val

    _TT[(us, them)] = (depth, _EXACT, best, best_move)
    return best, best_move


def policy(you: list[int], opponent: list[int]) -> str:
    global _DEADLINE, _NODES, _KILLERS

    _DEADLINE = time.perf_counter() + _TIME_LIMIT
    _NODES = 0
    _KILLERS = [[-1, -1] for _ in range(64)]

    if len(_TT) > _TT_LIMIT:
        _TT.clear()

    us = _mask_from_array(you)
    them = _mask_from_array(opponent) & ~us

    edges = _cut_edges(us, them)
    if edges <= 0:
        return _format_move(_first_legal_move(us, them))

    preferred = -1
    entry = _TT.get((us, them))
    if entry is not None and entry[3] >= 0:
        preferred = entry[3]

    root_moves = _ordered_moves(us, them, edges, preferred, 0)
    if not root_moves:
        return _format_move(_first_legal_move(us, them))

    # Always take an immediate winning move.
    for _, enc, ce in root_moves:
        if ce == 0:
            return _format_move(enc)

    best_move = root_moves[0][1]

    if len(root_moves) == 1:
        return _format_move(best_move)

    occ = (us | them).bit_count()
    max_depth = occ

    try:
        depth = 1
        while depth <= max_depth:
            if time.perf_counter() >= _DEADLINE - 0.012:
                break

            _, move = _root_search(us, them, edges, depth, best_move)
            if move >= 0:
                best_move = move

            depth += 1

    except _SearchTimeout:
        pass

    return _format_move(best_move)
