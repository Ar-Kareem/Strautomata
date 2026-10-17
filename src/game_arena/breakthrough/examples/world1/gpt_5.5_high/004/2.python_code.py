
import time

# Breakthrough policy for an 8x8 board.
# Internal board indexing: idx = row * 8 + col.

INF = 10**18
WIN = 100_000_000

DIR = {"b": -1, "w": 1}
OPPONENT = {"b": "w", "w": "b"}
GOAL_ROW = {"b": 0, "w": 7}

BIT = [1 << i for i in range(64)]
ROW = [i >> 3 for i in range(64)]
COL = [i & 7 for i in range(64)]

GOAL_MASK = {
    "b": sum(BIT[c] for c in range(8)),
    "w": sum(BIT[56 + c] for c in range(8)),
}

PROGRESS = {
    "b": [7 - ROW[i] for i in range(64)],
    "w": [ROW[i] for i in range(64)],
}

CENTER_BONUS = [0, 8, 16, 24, 24, 16, 8, 0]

FWD = {"b": [-1] * 64, "w": [-1] * 64}
DIAG = {"b": [()] * 64, "w": [()] * 64}
DEFENDERS = {"b": [0] * 64, "w": [0] * 64}
FRONT_CONE = {"b": [0] * 64, "w": [0] * 64}

for _color in ("b", "w"):
    _d = DIR[_color]
    for _idx in range(64):
        _r, _c = ROW[_idx], COL[_idx]

        _nr = _r + _d
        if 0 <= _nr < 8:
            FWD[_color][_idx] = _nr * 8 + _c
            ds = []
            for _nc in (_c - 1, _c + 1):
                if 0 <= _nc < 8:
                    ds.append(_nr * 8 + _nc)
            DIAG[_color][_idx] = tuple(ds)

        # Friendly pieces that diagonally defend/recapture this square.
        _sr = _r - _d
        mask = 0
        if 0 <= _sr < 8:
            for _sc in (_c - 1, _c + 1):
                if 0 <= _sc < 8:
                    mask |= BIT[_sr * 8 + _sc]
        DEFENDERS[_color][_idx] = mask

        # Squares ahead in the widening cone. If no enemy is in this cone,
        # the pawn is usually a dangerous passed pawn.
        mask = 0
        step = 1
        _rr = _r + _d
        while 0 <= _rr < 8:
            lo = max(0, _c - step)
            hi = min(7, _c + step)
            for _cc in range(lo, hi + 1):
                mask |= BIT[_rr * 8 + _cc]
            step += 1
            _rr += _d
        FRONT_CONE[_color][_idx] = mask

_ADVANCE_VALUE = [0, 8, 24, 55, 120, 260, 620, 5000]
_PASSED_VALUE_BY_DIST = [0, 9000, 3600, 1500, 650, 280, 110, 40]

_ROOT_COLOR = "w"
_ENEMY_COLOR = "b"
_DEADLINE = 0.0
_NODES = 0
_TT = {}
_EVAL_CACHE = {}


class _Timeout(Exception):
    pass


def _list_to_bb(pieces):
    bb = 0
    for r, c in pieces:
        if 0 <= r < 8 and 0 <= c < 8:
            bb |= BIT[r * 8 + c]
    return bb


def _idx_move_to_coord(move):
    fr, to = move
    return ((ROW[fr], COL[fr]), (ROW[to], COL[to]))


def _check_time():
    if time.perf_counter() >= _DEADLINE:
        raise _Timeout()


def _generate_moves(us, them, color):
    occ = us | them
    moves = []
    bb = us
    while bb:
        lsb = bb & -bb
        fr = lsb.bit_length() - 1
        bb ^= lsb

        to = FWD[color][fr]
        if to >= 0 and not (occ & BIT[to]):
            moves.append((fr, to))

        for to in DIAG[color][fr]:
            if not (us & BIT[to]):
                moves.append((fr, to))

    return moves


def _mobility_count(us, them, color):
    occ = us | them
    count = 0
    bb = us
    while bb:
        lsb = bb & -bb
        fr = lsb.bit_length() - 1
        bb ^= lsb

        to = FWD[color][fr]
        if to >= 0 and not (occ & BIT[to]):
            count += 1

        for to in DIAG[color][fr]:
            if not (us & BIT[to]):
                count += 1

    return count


def _immediate_win_count(us, them, color):
    """Number of legal moves by this side that immediately reach its goal row."""
    occ = us | them
    goal = GOAL_ROW[color]
    count = 0
    bb = us
    while bb:
        lsb = bb & -bb
        fr = lsb.bit_length() - 1
        bb ^= lsb

        # Only pieces one step from goal can win immediately.
        if ROW[fr] + DIR[color] != goal:
            continue

        to = FWD[color][fr]
        if to >= 0 and ROW[to] == goal and not (occ & BIT[to]):
            count += 1

        for to in DIAG[color][fr]:
            if ROW[to] == goal and not (us & BIT[to]):
                count += 1

    return count


def _apply_move(my, opp, move, turn_root):
    fr, to = move
    fm = BIT[fr]
    tm = BIT[to]

    if turn_root:
        return ((my & ~fm) | tm, opp & ~tm)
    else:
        return (my & ~tm, (opp & ~fm) | tm)


def _terminal_score(my, opp, depth_remaining):
    if opp == 0 or (my & GOAL_MASK[_ROOT_COLOR]):
        return WIN + depth_remaining
    if my == 0 or (opp & GOAL_MASK[_ENEMY_COLOR]):
        return -WIN - depth_remaining
    return None


def _min_goal_distance(bb, color):
    best = 7
    while bb:
        lsb = bb & -bb
        idx = lsb.bit_length() - 1
        bb ^= lsb
        dist = 7 - PROGRESS[color][idx]
        if dist < best:
            best = dist
    return best


def _piece_positional_score(us, them, color):
    enemy = OPPONENT[color]
    occ = us | them
    total = 0
    bb = us

    while bb:
        lsb = bb & -bb
        idx = lsb.bit_length() - 1
        bb ^= lsb

        prog = PROGRESS[color][idx]
        dist = 7 - prog

        total += _ADVANCE_VALUE[prog]
        total += CENTER_BONUS[COL[idx]]

        defenders = us & DEFENDERS[color][idx]
        attackers = them & DEFENDERS[enemy][idx]

        if defenders:
            total += 14 + 5 * prog

        if attackers:
            if defenders:
                total -= 10 + 3 * prog
            else:
                total -= 35 + 10 * prog

        # Passed pawns are often decisive in Breakthrough.
        if (them & FRONT_CONE[color][idx]) == 0:
            total += _PASSED_VALUE_BY_DIST[dist]
            if defenders:
                total += 25 + 12 * prog

        # A blocked straight path is mildly bad, but diagonal movement still exists.
        f = FWD[color][idx]
        if f >= 0 and (occ & BIT[f]):
            total -= 4 + 2 * prog

    return total


def _evaluate(my, opp, turn_root):
    key = (my, opp, turn_root)
    cached = _EVAL_CACHE.get(key)
    if cached is not None:
        return cached

    score = 0

    # Material matters, but less than progress/race threats.
    score += 115 * (my.bit_count() - opp.bit_count())

    score += _piece_positional_score(my, opp, _ROOT_COLOR)
    score -= _piece_positional_score(opp, my, _ENEMY_COLOR)

    # Mobility gives flexibility and helps avoid blocked formations.
    score += 4 * (
        _mobility_count(my, opp, _ROOT_COLOR)
        - _mobility_count(opp, my, _ENEMY_COLOR)
    )

    # Race component: being closer to promotion is valuable.
    if my and opp:
        score += 40 * (
            _min_goal_distance(opp, _ENEMY_COLOR)
            - _min_goal_distance(my, _ROOT_COLOR)
        )

    # Horizon tactical awareness for immediate winning moves.
    my_iw = _immediate_win_count(my, opp, _ROOT_COLOR)
    opp_iw = _immediate_win_count(opp, my, _ENEMY_COLOR)

    if my_iw:
        score += (300_000 if turn_root else 14_000) + 4_000 * (my_iw - 1)
    if opp_iw:
        score -= (300_000 if not turn_root else 14_000) + 4_000 * (opp_iw - 1)

    if len(_EVAL_CACHE) < 60000:
        _EVAL_CACHE[key] = score

    return score


def _move_order_score(move, us, them, color, preferred):
    if preferred is not None and move == preferred:
        return 50_000_000

    fr, to = move
    tm = BIT[to]
    enemy = OPPONENT[color]
    score = 0

    if ROW[to] == GOAL_ROW[color]:
        score += 20_000_000

    captured = bool(them & tm)
    if captured:
        # Capturing advanced enemy pieces is especially valuable.
        score += 1_000_000 + 4_000 * PROGRESS[enemy][to]

    prog_to = PROGRESS[color][to]
    score += 1_000 * prog_to
    score += CENTER_BONUS[COL[to]]

    them_after = them & ~tm
    us_after = (us & ~BIT[fr]) | tm

    if (them_after & FRONT_CONE[color][to]) == 0:
        score += 3_000 + 500 * prog_to

    # Moves to one step from goal create strong threats.
    if prog_to == 6:
        score += 25_000

    if us_after & DEFENDERS[color][to]:
        score += 800 + 80 * prog_to

    if them_after & DEFENDERS[enemy][to]:
        score -= 1_500 if not captured else 500

    return score


def _ordered_moves(moves, us, them, color, preferred=None):
    if len(moves) > 1:
        moves.sort(
            key=lambda m: _move_order_score(m, us, them, color, preferred),
            reverse=True,
        )
    return moves


def _alphabeta(my, opp, turn_root, depth, alpha, beta):
    global _NODES

    _NODES += 1
    if (_NODES & 1023) == 0:
        _check_time()

    term = _terminal_score(my, opp, depth)
    if term is not None:
        return term

    if depth <= 0:
        return _evaluate(my, opp, turn_root)

    key = (my, opp, turn_root)
    alpha_orig = alpha
    beta_orig = beta

    entry = _TT.get(key)
    preferred = None
    if entry is not None:
        stored_depth, stored_score, flag, stored_best = entry
        preferred = stored_best
        if stored_depth >= depth:
            if flag == 0:  # exact
                return stored_score
            if flag == 1:  # lower bound
                if stored_score > alpha:
                    alpha = stored_score
            else:  # upper bound
                if stored_score < beta:
                    beta = stored_score
            if alpha >= beta:
                return stored_score

    if turn_root:
        moves = _generate_moves(my, opp, _ROOT_COLOR)
        if not moves:
            return -WIN - depth

        moves = _ordered_moves(moves, my, opp, _ROOT_COLOR, preferred)
        value = -INF
        best_move = moves[0]

        for mv in moves:
            nmy, nopp = _apply_move(my, opp, mv, True)
            sc = _alphabeta(nmy, nopp, False, depth - 1, alpha, beta)

            if sc > value:
                value = sc
                best_move = mv

            if value > alpha:
                alpha = value
            if alpha >= beta:
                break

    else:
        moves = _generate_moves(opp, my, _ENEMY_COLOR)
        if not moves:
            return WIN + depth

        moves = _ordered_moves(moves, opp, my, _ENEMY_COLOR, preferred)
        value = INF
        best_move = moves[0]

        for mv in moves:
            nmy, nopp = _apply_move(my, opp, mv, False)
            sc = _alphabeta(nmy, nopp, True, depth - 1, alpha, beta)

            if sc < value:
                value = sc
                best_move = mv

            if value < beta:
                beta = value
            if alpha >= beta:
                break

    if value <= alpha_orig:
        flag = 2  # upper bound
    elif value >= beta_orig:
        flag = 1  # lower bound
    else:
        flag = 0  # exact

    if len(_TT) < 200000:
        _TT[key] = (depth, value, flag, best_move)

    return value


def _search_root(my, opp, depth, preferred):
    moves = _generate_moves(my, opp, _ROOT_COLOR)
    if not moves:
        return -WIN, None

    moves = _ordered_moves(moves, my, opp, _ROOT_COLOR, preferred)

    best_move = moves[0]
    best_score = -INF
    alpha = -INF
    beta = INF

    for mv in moves:
        _check_time()

        nmy, nopp = _apply_move(my, opp, mv, True)
        sc = _alphabeta(nmy, nopp, False, depth - 1, alpha, beta)

        if sc > best_score:
            best_score = sc
            best_move = mv

        if best_score > alpha:
            alpha = best_score

    return best_score, best_move


def _first_legal_from_lists(me, opp, color):
    me_set = set(me)
    opp_set = set(opp)
    d = DIR[color]

    for r, c in me:
        nr = r + d
        if not (0 <= nr < 8):
            continue

        # Straight forward only if empty.
        if (nr, c) not in me_set and (nr, c) not in opp_set:
            return ((r, c), (nr, c))

        # Diagonal forward if not occupied by own piece; empty or opponent is legal.
        for nc in (c - 1, c + 1):
            if 0 <= nc < 8 and (nr, nc) not in me_set:
                return ((r, c), (nr, nc))

    return None


def _is_legal_result(move, me, opp, color):
    try:
        (fr, fc), (tr, tc) = move
    except Exception:
        return False

    if not (0 <= fr < 8 and 0 <= fc < 8 and 0 <= tr < 8 and 0 <= tc < 8):
        return False

    me_set = set(me)
    opp_set = set(opp)

    if (fr, fc) not in me_set:
        return False
    if (tr, tc) in me_set:
        return False

    if tr - fr != DIR[color]:
        return False

    dc = tc - fc
    if dc == 0:
        return (tr, tc) not in opp_set
    if abs(dc) == 1:
        return True

    return False


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    global _ROOT_COLOR, _ENEMY_COLOR, _DEADLINE, _NODES, _TT, _EVAL_CACHE

    if color not in ("b", "w"):
        color = "w"

    _ROOT_COLOR = color
    _ENEMY_COLOR = OPPONENT[color]

    my = _list_to_bb(me)
    op = _list_to_bb(opp)

    root_moves = _generate_moves(my, op, _ROOT_COLOR)
    if not root_moves:
        fallback_none = _first_legal_from_lists(me, opp, color)
        if fallback_none is not None:
            return fallback_none
        return ((0, 0), (0, 0))

    # Immediate wins are always best and avoid wasting time.
    immediate_ordered = _ordered_moves(root_moves[:], my, op, _ROOT_COLOR, None)
    for mv in immediate_ordered:
        nmy, nop = _apply_move(my, op, mv, True)
        if nop == 0 or (nmy & GOAL_MASK[_ROOT_COLOR]):
            return _idx_move_to_coord(mv)

    ordered = _ordered_moves(root_moves[:], my, op, _ROOT_COLOR, None)
    fallback = ordered[0]

    # If the opponent threatens to win immediately, prefer a move that removes
    # all such immediate wins, if such a move exists.
    if _immediate_win_count(op, my, _ENEMY_COLOR):
        for mv in ordered:
            nmy, nop = _apply_move(my, op, mv, True)
            if _immediate_win_count(nop, nmy, _ENEMY_COLOR) == 0:
                fallback = mv
                break

    _TT = {}
    _EVAL_CACHE = {}
    _NODES = 0
    _DEADLINE = time.perf_counter() + 0.92

    best = fallback

    piece_count = (my | op).bit_count()
    if piece_count <= 8:
        max_depth = 12
    elif piece_count <= 12:
        max_depth = 10
    elif piece_count <= 18:
        max_depth = 8
    else:
        max_depth = 6

    try:
        for depth in range(1, max_depth + 1):
            score, mv = _search_root(my, op, depth, best)
            if mv is not None:
                best = mv

            # Found a forced/near immediate win.
            if score >= WIN // 2:
                break

            if time.perf_counter() >= _DEADLINE - 0.025:
                break

    except _Timeout:
        pass
    except Exception:
        # Safety: never let an unexpected error prevent a legal move.
        best = fallback

    result = _idx_move_to_coord(best)
    if _is_legal_result(result, me, opp, color):
        return result

    fallback_result = _idx_move_to_coord(fallback)
    if _is_legal_result(fallback_result, me, opp, color):
        return fallback_result

    fresh = _first_legal_from_lists(me, opp, color)
    if fresh is not None:
        return fresh

    return ((0, 0), (0, 0))
