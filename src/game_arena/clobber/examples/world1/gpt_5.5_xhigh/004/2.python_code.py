
from __future__ import annotations

import time

ROWS = 5
COLS = 6
N = ROWS * COLS
FULL = (1 << N) - 1
BITS = tuple(1 << i for i in range(N))

COL_LEFT = 0
COL_RIGHT = 0
for _r in range(ROWS):
    COL_LEFT |= 1 << (_r * COLS)
    COL_RIGHT |= 1 << (_r * COLS + COLS - 1)

NOT_LEFT = FULL ^ COL_LEFT
NOT_RIGHT = FULL ^ COL_RIGHT

MATE = 1_000_000
MATE_THRESHOLD = MATE // 2
INF = 1_000_000_000
EVAL_LIMIT = 50_000

TT_EXACT = 0
TT_LOWER = 1
TT_UPPER = 2

_TT = {}
_TT_LIMIT = 300_000

_DEADLINE = 0.0
_NODES = 0
_KILLERS = [[-1, -1] for _ in range(64)]

_CENTER = []
_DEG = []
for _r in range(ROWS):
    for _c in range(COLS):
        _CENTER.append(
            30
            - (
                abs(2 * _r - (ROWS - 1)) * 3
                + abs(2 * _c - (COLS - 1)) * 2
            )
        )
        _d = 4
        if _r == 0:
            _d -= 1
        if _r == ROWS - 1:
            _d -= 1
        if _c == 0:
            _d -= 1
        if _c == COLS - 1:
            _d -= 1
        _DEG.append(_d)


def _to_bits(board) -> int:
    bits = 0

    try:
        if len(board) == N:
            first = board[0]
            if not hasattr(first, "__len__"):
                for i in range(N):
                    if board[i]:
                        bits |= BITS[i]
                return bits
    except Exception:
        pass

    bits = 0
    try:
        for r in range(ROWS):
            row = board[r]
            base = r * COLS
            for c in range(COLS):
                if row[c]:
                    bits |= BITS[base + c]
        return bits
    except Exception:
        bits = 0
        for r in range(ROWS):
            base = r * COLS
            for c in range(COLS):
                if board[r, c]:
                    bits |= BITS[base + c]
        return bits


def _adjacent_to(x: int) -> int:
    return (
        ((x << COLS) & FULL)
        | (x >> COLS)
        | ((x << 1) & NOT_LEFT)
        | ((x >> 1) & NOT_RIGHT)
    )


def _move_count(a: int, b: int) -> int:
    return (
        (a & ((b << COLS) & FULL)).bit_count()
        + (a & (b >> COLS)).bit_count()
        + (a & ((b << 1) & NOT_LEFT)).bit_count()
        + (a & ((b >> 1) & NOT_RIGHT)).bit_count()
    )


def _gen_moves(a: int, b: int) -> list[int]:
    moves = []

    s = a & ((b << COLS) & FULL)       # Up
    while s:
        lb = s & -s
        i = lb.bit_length() - 1
        moves.append((i << 5) | (i - COLS))
        s ^= lb

    s = a & ((b >> 1) & NOT_RIGHT)     # Right
    while s:
        lb = s & -s
        i = lb.bit_length() - 1
        moves.append((i << 5) | (i + 1))
        s ^= lb

    s = a & (b >> COLS)                # Down
    while s:
        lb = s & -s
        i = lb.bit_length() - 1
        moves.append((i << 5) | (i + COLS))
        s ^= lb

    s = a & ((b << 1) & NOT_LEFT)      # Left
    while s:
        lb = s & -s
        i = lb.bit_length() - 1
        moves.append((i << 5) | (i - 1))
        s ^= lb

    return moves


def _parent_value(child_score: int) -> int:
    v = -child_score
    if v > MATE_THRESHOLD:
        return v - 1
    if v < -MATE_THRESHOLD:
        return v + 1
    return v


def _has_finisher(a: int, b: int) -> bool:
    for mv in _gen_moves(a, b):
        src = mv >> 5
        dst = mv & 31
        db = BITS[dst]
        sb = BITS[src]
        ca = b & ~db
        cb = (a & ~sb) | db
        if _move_count(ca, cb) == 0:
            return True
    return False


def _tactical_eval(a: int, b: int, edges: int):
    if edges == 0:
        return -MATE
    if edges > 7:
        return None

    moves = _gen_moves(a, b)
    if not moves:
        return -MATE

    all_lose_next = True
    for mv in moves:
        src = mv >> 5
        dst = mv & 31
        db = BITS[dst]
        sb = BITS[src]
        ca = b & ~db
        cb = (a & ~sb) | db
        e2 = _move_count(ca, cb)

        if e2 == 0:
            return MATE - 1

        if not (e2 <= 7 and _has_finisher(ca, cb)):
            all_lose_next = False

    if all_lose_next:
        return -MATE + 2
    return None


def _static_eval(a: int, b: int) -> int:
    edges = _move_count(a, b)
    if edges == 0:
        return -MATE

    tact = _tactical_eval(a, b, edges)
    if tact is not None:
        return tact

    adj_b = _adjacent_to(b)
    adj_a = _adjacent_to(a)

    active_a_mask = a & adj_b
    active_b_mask = b & adj_a
    active_a = active_a_mask.bit_count()
    active_b = active_b_mask.bit_count()

    frontier = active_a_mask | active_b_mask
    occ = a | b
    near = frontier | (_adjacent_to(frontier) & occ)

    live_mat = (a & near).bit_count() - (b & near).bit_count()
    total_mat = a.bit_count() - b.bit_count()

    score = 230 * live_mat + 55 * total_mat + 85 * (active_a - active_b)

    score += 65 if (edges & 1) else -65
    score += 20  # tempo

    if live_mat > 0 or (live_mat == 0 and total_mat >= 0):
        score -= edges
    else:
        score += edges

    if score > EVAL_LIMIT:
        return EVAL_LIMIT
    if score < -EVAL_LIMIT:
        return -EVAL_LIMIT
    return score


def _move_order_score(a: int, b: int, mv: int, tt_move: int, k1: int, k2: int) -> int:
    if mv == tt_move:
        return 100_000_000
    if mv == k1:
        return 95_000_000
    if mv == k2:
        return 94_000_000

    src = mv >> 5
    dst = mv & 31
    db = BITS[dst]
    sb = BITS[src]

    ca = b & ~db
    cb = (a & ~sb) | db
    edges = _move_count(ca, cb)

    if edges == 0:
        return 90_000_000 + _CENTER[dst]

    if edges <= 7:
        tact = _tactical_eval(ca, cb, edges)
        if tact is not None:
            pv = _parent_value(tact)
            if pv > MATE_THRESHOLD:
                return 80_000_000 + pv
            if pv < -MATE_THRESHOLD:
                return -80_000_000 + pv

    adj_opp = _adjacent_to(ca)
    adj_my = _adjacent_to(cb)
    my_active = (cb & adj_opp).bit_count()
    opp_active = (ca & adj_my).bit_count()

    mat = cb.bit_count() - ca.bit_count()
    parity = 180 if (edges & 1) == 0 else -180
    edge_weight = -220 if mat >= 0 else -120

    return (
        edge_weight * edges
        + parity
        + 90 * (my_active - opp_active)
        + 5 * _CENTER[dst]
        - 2 * _CENTER[src]
        + 8 * _DEG[dst]
        - 3 * _DEG[src]
    )


def _order_moves(a: int, b: int, moves: list[int], tt_move: int = -1, k1: int = -1, k2: int = -1) -> list[int]:
    if len(moves) > 1:
        moves.sort(
            key=lambda mv: _move_order_score(a, b, mv, tt_move, k1, k2),
            reverse=True,
        )
    return moves


def _check_time() -> None:
    global _NODES
    _NODES += 1
    if (_NODES & 511) == 0 and time.perf_counter() >= _DEADLINE:
        raise TimeoutError


def _search(a: int, b: int, depth: int, alpha: int, beta: int, ply: int) -> int:
    _check_time()

    if depth <= 0:
        return _static_eval(a, b)

    alpha0 = alpha
    beta0 = beta
    key = (a, b)

    entry = _TT.get(key)
    tt_move = -1
    if entry is not None:
        edepth, flag, score, best_move = entry
        tt_move = best_move

        if flag == TT_EXACT and (edepth >= depth or abs(score) > MATE_THRESHOLD):
            return score

        if edepth >= depth:
            if flag == TT_LOWER:
                if score > alpha:
                    alpha = score
            elif flag == TT_UPPER:
                if score < beta:
                    beta = score
            elif flag == TT_EXACT:
                return score

            if alpha >= beta:
                return score

    moves = _gen_moves(a, b)
    if not moves:
        return -MATE

    k1 = k2 = -1
    if ply < len(_KILLERS):
        k1, k2 = _KILLERS[ply]

    _order_moves(a, b, moves, tt_move, k1, k2)

    best = -INF
    best_move = moves[0]

    for mv in moves:
        src = mv >> 5
        dst = mv & 31
        db = BITS[dst]
        sb = BITS[src]

        ca = b & ~db
        cb = (a & ~sb) | db

        child_score = _search(ca, cb, depth - 1, -beta, -alpha, ply + 1)
        val = _parent_value(child_score)

        if val > best:
            best = val
            best_move = mv

        if val > alpha:
            alpha = val

        if alpha >= beta:
            if ply < len(_KILLERS):
                killers = _KILLERS[ply]
                if killers[0] != mv:
                    killers[1] = killers[0]
                    killers[0] = mv
            break

    if best <= alpha0:
        flag = TT_UPPER
    elif best >= beta0:
        flag = TT_LOWER
    else:
        flag = TT_EXACT

    _TT[key] = (depth, flag, best, best_move)
    return best


def _search_root(a: int, b: int, depth: int, preferred: int) -> tuple[int, int]:
    _check_time()

    moves = _gen_moves(a, b)
    if not moves:
        return -MATE, -1

    tt_move = preferred
    entry = _TT.get((a, b))
    if (tt_move is None or tt_move < 0) and entry is not None:
        tt_move = entry[3]

    _order_moves(a, b, moves, tt_move, -1, -1)

    alpha = -INF
    beta = INF
    best = -INF
    best_move = moves[0]

    for mv in moves:
        src = mv >> 5
        dst = mv & 31
        db = BITS[dst]
        sb = BITS[src]

        ca = b & ~db
        cb = (a & ~sb) | db

        child_score = _search(ca, cb, depth - 1, -beta, -alpha, 1)
        val = _parent_value(child_score)

        if val > best:
            best = val
            best_move = mv

        if val > alpha:
            alpha = val

    _TT[(a, b)] = (depth, TT_EXACT, best, best_move)
    return best, best_move


def _is_legal(a: int, b: int, mv: int) -> bool:
    if mv is None or mv < 0:
        return False

    src = mv >> 5
    dst = mv & 31
    if src < 0 or src >= N or dst < 0 or dst >= N:
        return False

    if not (a & BITS[src]):
        return False
    if not (b & BITS[dst]):
        return False

    delta = dst - src
    if delta == -COLS or delta == COLS:
        return True
    if delta == 1 and (src % COLS) != COLS - 1:
        return True
    if delta == -1 and (src % COLS) != 0:
        return True
    return False


def _move_to_str(mv: int) -> str:
    src = mv >> 5
    dst = mv & 31
    delta = dst - src

    if delta == -COLS:
        d = "U"
    elif delta == 1:
        d = "R"
    elif delta == COLS:
        d = "D"
    else:
        d = "L"

    return f"{src // COLS},{src % COLS},{d}"


def policy(you: list[int], opponent: list[int]) -> str:
    global _DEADLINE, _NODES, _KILLERS

    start = time.perf_counter()

    a = _to_bits(you) & FULL
    b = _to_bits(opponent) & FULL
    b &= ~a

    moves = _gen_moves(a, b)
    if not moves:
        return "0,0,U"

    if len(moves) == 1:
        return _move_to_str(moves[0])

    total = (a | b).bit_count()
    limit = 0.92 if total <= 14 else 0.88
    _DEADLINE = start + limit
    _NODES = 0
    _KILLERS = [[-1, -1] for _ in range(64)]

    if len(_TT) > _TT_LIMIT:
        _TT.clear()

    tt_pref = -1
    entry = _TT.get((a, b))
    if entry is not None and _is_legal(a, b, entry[3]):
        tt_pref = entry[3]

    _order_moves(a, b, moves, tt_pref, -1, -1)
    best = moves[0]
    preferred = best

    try:
        for depth in range(1, total + 1):
            if time.perf_counter() >= _DEADLINE:
                break

            try:
                score, mv = _search_root(a, b, depth, preferred)
            except TimeoutError:
                break

            if _is_legal(a, b, mv):
                best = mv
                preferred = mv

            if abs(score) > MATE_THRESHOLD:
                break
    except Exception:
        pass

    if not _is_legal(a, b, best):
        moves = _gen_moves(a, b)
        if moves:
            best = moves[0]
        else:
            return "0,0,U"

    return _move_to_str(best)
