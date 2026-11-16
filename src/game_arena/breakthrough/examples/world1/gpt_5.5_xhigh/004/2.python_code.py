
import time

# ---------- Board constants ----------

BOARD = (1 << 64) - 1
ROW_MASKS = tuple(((1 << 8) - 1) << (8 * r) for r in range(8))
ROW0 = ROW_MASKS[0]
ROW7 = ROW_MASKS[7]

FILE_A = sum(1 << (8 * r) for r in range(8))
FILE_H = sum(1 << (8 * r + 7) for r in range(8))
NOT_FILE_A = BOARD ^ FILE_A
NOT_FILE_H = BOARD ^ FILE_H

PROG_W = tuple(i >> 3 for i in range(64))          # white progress: row number
PROG_B = tuple(7 - (i >> 3) for i in range(64))    # black progress: inverted row

CENTER_VALUE = (3, 6, 9, 11, 11, 9, 6, 3)

# Evaluation weights.
PROGRESS_VALUE = (0, 14, 36, 82, 175, 380, 850, 5000)
ORDER_PROGRESS = (0, 25, 70, 170, 400, 950, 2500, 1000000)

# Indexed by distance to promotion: dist 1 is very dangerous.
PASSED_BONUS = (0, 3000, 1350, 600, 260, 110, 40, 0)
PASSED_ORDER = (0, 5000, 2200, 900, 350, 130, 45, 0)

WIN_SCORE = 1_000_000
WIN_IN_ONE = WIN_SCORE - 64
WIN_NEXT_BONUS = 180_000
INF = 10_000_000
TIME_LIMIT = 0.88


def _build_passed_masks(white: bool):
    masks = []
    for idx in range(64):
        r, c = divmod(idx, 8)
        m = 0
        rows = range(r + 1, 8) if white else range(r - 1, -1, -1)
        for rr in rows:
            for cc in (c - 1, c, c + 1):
                if 0 <= cc < 8:
                    m |= 1 << (rr * 8 + cc)
        masks.append(m)
    return tuple(masks)


PASS_W = _build_passed_masks(True)
PASS_B = _build_passed_masks(False)


# ---------- Search globals, reset each policy call ----------

_deadline = 0.0
_nodes = 0
_tt = {}
_killers = []
_history = {}


class _Timeout(Exception):
    pass


# ---------- Basic helpers ----------

def _to_bb(pieces):
    bb = 0
    for r, c in pieces:
        r = int(r)
        c = int(c)
        if 0 <= r < 8 and 0 <= c < 8:
            bb |= 1 << (r * 8 + c)
    return bb


def _move_to_tuple(mv):
    fr, to = mv
    return ((fr >> 3, fr & 7), (to >> 3, to & 7))


def _goal_mask(dir_):
    return ROW7 if dir_ > 0 else ROW0


def _attacks(bb, dir_):
    if dir_ > 0:
        return ((((bb & NOT_FILE_A) << 7) | ((bb & NOT_FILE_H) << 9)) & BOARD)
    return (((bb & NOT_FILE_A) >> 9) | ((bb & NOT_FILE_H) >> 7))


def _make_move(us, them, mv):
    fr, to = mv
    fb = 1 << fr
    tb = 1 << to
    return ((us ^ fb) | tb), (them & ~tb)


# ---------- Legal move generation ----------

def _generate_moves(us, them, dir_):
    occ = us | them
    moves = []

    if dir_ > 0:
        targets = ((us << 8) & BOARD) & ~occ
        while targets:
            lsb = targets & -targets
            to = lsb.bit_length() - 1
            moves.append((to - 8, to))
            targets ^= lsb

        targets = ((us & NOT_FILE_A) << 7) & BOARD & ~us
        while targets:
            lsb = targets & -targets
            to = lsb.bit_length() - 1
            moves.append((to - 7, to))
            targets ^= lsb

        targets = ((us & NOT_FILE_H) << 9) & BOARD & ~us
        while targets:
            lsb = targets & -targets
            to = lsb.bit_length() - 1
            moves.append((to - 9, to))
            targets ^= lsb

    else:
        targets = (us >> 8) & ~occ
        while targets:
            lsb = targets & -targets
            to = lsb.bit_length() - 1
            moves.append((to + 8, to))
            targets ^= lsb

        targets = ((us & NOT_FILE_A) >> 9) & ~us
        while targets:
            lsb = targets & -targets
            to = lsb.bit_length() - 1
            moves.append((to + 9, to))
            targets ^= lsb

        targets = ((us & NOT_FILE_H) >> 7) & ~us
        while targets:
            lsb = targets & -targets
            to = lsb.bit_length() - 1
            moves.append((to + 7, to))
            targets ^= lsb

    return moves


def _mobility_count(us, them, dir_):
    occ = us | them
    if dir_ > 0:
        f = (((us << 8) & BOARD) & ~occ).bit_count()
        l = (((us & NOT_FILE_A) << 7) & BOARD & ~us).bit_count()
        r = (((us & NOT_FILE_H) << 9) & BOARD & ~us).bit_count()
        return f + l + r
    f = ((us >> 8) & ~occ).bit_count()
    l = (((us & NOT_FILE_A) >> 9) & ~us).bit_count()
    r = (((us & NOT_FILE_H) >> 7) & ~us).bit_count()
    return f + l + r


def _square_attacked_by(bb, sq, dir_):
    r = sq >> 3
    c = sq & 7

    if dir_ > 0:
        if r <= 0:
            return False
        if c > 0 and (bb & (1 << (sq - 9))):
            return True
        if c < 7 and (bb & (1 << (sq - 7))):
            return True
        return False

    if r >= 7:
        return False
    if c > 0 and (bb & (1 << (sq + 7))):
        return True
    if c < 7 and (bb & (1 << (sq + 9))):
        return True
    return False


def _can_win_next(us, them, dir_):
    if us == 0:
        return False

    goal = ROW7 if dir_ > 0 else ROW0
    occ = us | them

    if dir_ > 0:
        straight = ((us << 8) & BOARD & goal & ~occ)
        diag = ((((us & NOT_FILE_A) << 7) | ((us & NOT_FILE_H) << 9)) & BOARD & goal & ~us)
    else:
        straight = ((us >> 8) & goal & ~occ)
        diag = ((((us & NOT_FILE_A) >> 9) | ((us & NOT_FILE_H) >> 7)) & goal & ~us)

    if straight or diag:
        return True

    # Capturing the last opponent piece is also an immediate win.
    if them and (them & (them - 1)) == 0:
        return bool(_attacks(us, dir_) & them)

    return False


def _terminal_value(us, them, dir_, depth):
    # In a normal search node, "them" is the player who just moved.
    if us == 0:
        return -WIN_SCORE - depth
    if them == 0:
        return WIN_SCORE + depth
    if them & _goal_mask(-dir_):
        return -WIN_SCORE - depth
    if us & _goal_mask(dir_):
        return WIN_SCORE + depth
    return None


# ---------- Evaluation ----------

def _evaluate(us, them, dir_):
    tv = _terminal_value(us, them, dir_, 0)
    if tv is not None:
        return tv

    score = 135 * (us.bit_count() - them.bit_count())

    # Negamax has already handled our own win-in-one. Penalize opponent's threat.
    if _can_win_next(them, us, -dir_):
        score -= WIN_NEXT_BONUS

    prog_us = PROG_W if dir_ > 0 else PROG_B
    prog_them = PROG_B if dir_ > 0 else PROG_W
    pass_us = PASS_W if dir_ > 0 else PASS_B
    pass_them = PASS_B if dir_ > 0 else PASS_W

    att_us = _attacks(us, dir_)
    att_them = _attacks(them, -dir_)

    protected_us = att_us & us
    protected_them = att_them & them
    attacked_us = att_them & us
    attacked_them = att_us & them

    score += 22 * (attacked_them.bit_count() - attacked_us.bit_count())
    score += 12 * (protected_us.bit_count() - protected_them.bit_count())

    hanging_us = attacked_us & ~protected_us
    hanging_them = attacked_them & ~protected_them
    score += 28 * (hanging_them.bit_count() - hanging_us.bit_count())

    max_us = 0
    b = us
    while b:
        lsb = b & -b
        idx = lsb.bit_length() - 1
        p = prog_us[idx]
        if p > max_us:
            max_us = p

        score += PROGRESS_VALUE[p]
        score += CENTER_VALUE[idx & 7] * (p + 1)

        if protected_us & lsb:
            score += 10 + 3 * p

        if attacked_us & lsb:
            if protected_us & lsb:
                score -= 8 + 2 * p
            else:
                score -= 28 + PROGRESS_VALUE[p] // 4

        if (them & pass_us[idx]) == 0:
            dist = 7 - p
            bonus = PASSED_BONUS[dist]
            if protected_us & lsb:
                bonus += bonus // 4
            if attacked_us & lsb:
                bonus -= bonus // 3
            score += bonus

        b ^= lsb

    max_them = 0
    b = them
    while b:
        lsb = b & -b
        idx = lsb.bit_length() - 1
        p = prog_them[idx]
        if p > max_them:
            max_them = p

        score -= PROGRESS_VALUE[p]
        score -= CENTER_VALUE[idx & 7] * (p + 1)

        if protected_them & lsb:
            score -= 10 + 3 * p

        if attacked_them & lsb:
            if protected_them & lsb:
                score += 8 + 2 * p
            else:
                score += 28 + PROGRESS_VALUE[p] // 4

        if (us & pass_them[idx]) == 0:
            dist = 7 - p
            bonus = PASSED_BONUS[dist]
            if protected_them & lsb:
                bonus += bonus // 4
            if attacked_them & lsb:
                bonus -= bonus // 3
            score -= bonus

        b ^= lsb

    score += 55 * (max_us - max_them)

    if max_us >= 5:
        score += (max_us - 4) * 90
    if max_them >= 5:
        score -= (max_them - 4) * 90

    score += 3 * (_mobility_count(us, them, dir_) - _mobility_count(them, us, -dir_))

    return score


# ---------- Move ordering ----------

def _move_order_score(mv, us, them, dir_):
    fr, to = mv
    fb = 1 << fr
    tb = 1 << to

    prog = PROG_W if dir_ > 0 else PROG_B
    opp_prog = PROG_B if dir_ > 0 else PROG_W
    pass_masks = PASS_W if dir_ > 0 else PASS_B

    p = prog[to]
    score = ORDER_PROGRESS[p] + CENTER_VALUE[to & 7] * 4

    if tb & them:
        score += 50000 + PROGRESS_VALUE[opp_prog[to]] * 6
    else:
        if (fr & 7) != (to & 7):
            score += 80

    if p == 6:
        score += 25000
    elif p == 7:
        score += 1000000

    if (them & pass_masks[to]) == 0:
        score += PASSED_ORDER[7 - p]

    them2 = them & ~tb
    new_us = (us ^ fb) | tb

    protected = _square_attacked_by(new_us, to, dir_)
    attacked = _square_attacked_by(them2, to, -dir_)

    if protected:
        score += 180 + 20 * p
    if attacked:
        score -= 260 + 35 * p
        if protected:
            score += 170

    return score


def _order_moves(us, them, dir_, moves, tt_move=None, ply=0):
    k1 = k2 = None
    if ply < len(_killers):
        k1, k2 = _killers[ply]

    scored = []
    for mv in moves:
        s = _move_order_score(mv, us, them, dir_)

        if mv == tt_move:
            s += 10_000_000
        elif mv == k1:
            s += 900_000
        elif mv == k2:
            s += 800_000

        s += _history.get((dir_, mv[0], mv[1]), 0)
        scored.append((s, mv))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [mv for _, mv in scored]


def _record_cutoff(dir_, mv, depth, ply):
    if ply < len(_killers):
        k1, _ = _killers[ply]
        if mv != k1:
            _killers[ply] = (mv, k1)

    key = (dir_, mv[0], mv[1])
    _history[key] = min(_history.get(key, 0) + depth * depth, 100000)


# ---------- Alpha-beta / negamax search ----------

def _negamax(us, them, dir_, depth, alpha, beta, ply):
    global _nodes, _tt

    _nodes += 1
    if (_nodes & 511) == 0 and time.perf_counter() >= _deadline:
        raise _Timeout()

    tv = _terminal_value(us, them, dir_, depth)
    if tv is not None:
        return tv

    # Exact tactical shortcut: if the side to move can end the game now, do it.
    if _can_win_next(us, them, dir_):
        return WIN_IN_ONE + depth

    if depth <= 0:
        return _evaluate(us, them, dir_)

    key = (us, them, dir_)
    entry = _tt.get(key)

    tt_move = None
    alpha_orig = alpha
    beta_orig = beta

    if entry is not None:
        e_depth, e_val, e_flag, e_move = entry
        tt_move = e_move
        if e_depth >= depth:
            if e_flag == 0:       # exact
                return e_val
            if e_flag == 1:       # lower bound
                if e_val > alpha:
                    alpha = e_val
            else:                 # upper bound
                if e_val < beta:
                    beta = e_val
            if alpha >= beta:
                return e_val

    moves = _generate_moves(us, them, dir_)
    if not moves:
        return -WIN_SCORE - depth

    ordered = _order_moves(us, them, dir_, moves, tt_move, ply)

    best = -INF
    best_move = ordered[0]
    searched = 0

    for mv in ordered:
        to_bit = 1 << mv[1]
        capture = bool(to_bit & them)
        nu, nt = _make_move(us, them, mv)

        # Principal variation search.
        if searched == 0:
            val = -_negamax(nt, nu, -dir_, depth - 1, -beta, -alpha, ply + 1)
        else:
            val = -_negamax(nt, nu, -dir_, depth - 1, -alpha - 1, -alpha, ply + 1)
            if alpha < val < beta:
                val = -_negamax(nt, nu, -dir_, depth - 1, -beta, -alpha, ply + 1)

        searched += 1

        if val > best:
            best = val
            best_move = mv

        if val > alpha:
            alpha = val

        if alpha >= beta:
            if not capture:
                _record_cutoff(dir_, mv, depth, ply)
            break

    flag = 0
    if best <= alpha_orig:
        flag = -1       # upper bound
    elif best >= beta_orig:
        flag = 1        # lower bound

    if len(_tt) < 250000:
        _tt[key] = (depth, best, flag, best_move)

    return best


# ---------- Safety / policy ----------

def _is_legal_move(mv, us, them, dir_):
    if mv is None:
        return False
    fr, to = mv
    if not (0 <= fr < 64 and 0 <= to < 64):
        return False

    fb = 1 << fr
    tb = 1 << to

    if not (us & fb):
        return False
    if us & tb:
        return False

    rf, cf = divmod(fr, 8)
    rt, ct = divmod(to, 8)
    step = 1 if dir_ > 0 else -1

    if rt != rf + step:
        return False

    dc = ct - cf
    if dc == 0:
        return (tb & (us | them)) == 0
    if dc == 1 or dc == -1:
        return True

    return False


def _fallback_tuple(us, them, dir_):
    moves = _generate_moves(us, them, dir_)
    if moves:
        return _move_to_tuple(moves[0])

    # A valid non-terminal Breakthrough state should always have a legal move.
    # This branch is only for malformed terminal inputs.
    if us:
        idx = (us & -us).bit_length() - 1
        return ((idx >> 3, idx & 7), (idx >> 3, idx & 7))
    return ((0, 0), (0, 0))


def _choose_max_depth(us, them):
    pieces = us.bit_count() + them.bit_count()
    if pieces <= 6:
        return 12
    if pieces <= 10:
        return 10
    if pieces <= 16:
        return 8
    if pieces <= 24:
        return 7
    return 6


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    global _deadline, _nodes, _tt, _killers, _history

    us = _to_bb(me)
    them = _to_bb(opp)
    dir_ = -8 if color == 'b' else 8

    legal = _generate_moves(us, them, dir_)
    if not legal:
        return _fallback_tuple(us, them, dir_)

    max_depth = _choose_max_depth(us, them)

    _deadline = time.perf_counter() + TIME_LIMIT
    _nodes = 0
    _tt = {}
    _killers = [(None, None) for _ in range(max_depth + 8)]
    _history = {}

    ordered0 = _order_moves(us, them, dir_, legal, None, 0)

    # Never search past an immediate win.
    goal = _goal_mask(dir_)
    for mv in ordered0:
        nu, nt = _make_move(us, them, mv)
        if nt == 0 or (nu & goal):
            return _move_to_tuple(mv)

    if len(legal) == 1:
        return _move_to_tuple(legal[0])

    best = ordered0[0]
    best_score = -INF

    for depth in range(1, max_depth + 1):
        try:
            if time.perf_counter() >= _deadline:
                break

            local_best = best
            local_score = -INF
            alpha = -INF
            beta = INF

            root_moves = _order_moves(us, them, dir_, legal, best, 0)

            for mv in root_moves:
                if time.perf_counter() >= _deadline:
                    raise _Timeout()

                nu, nt = _make_move(us, them, mv)
                score = -_negamax(nt, nu, -dir_, depth - 1, -beta, -alpha, 1)

                if score > local_score:
                    local_score = score
                    local_best = mv

                if score > alpha:
                    alpha = score

            best = local_best
            best_score = local_score

            if best_score > WIN_SCORE // 2:
                break
            if time.perf_counter() > _deadline - 0.025:
                break

        except _Timeout:
            break

    if not _is_legal_move(best, us, them, dir_):
        for mv in legal:
            if _is_legal_move(mv, us, them, dir_):
                best = mv
                break

    return _move_to_tuple(best)
