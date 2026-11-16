
import time

BOARD_CELLS = 27
FULL_MASK = (1 << BOARD_CELLS) - 1
WIN_VALUE = 1_000_000
INF = 10_000_000_000
TIME_LIMIT = 0.88


class _Timeout(Exception):
    pass


def _idx(i, j, k):
    return i * 9 + j * 3 + k


def _coords_from_bit(bit):
    n = bit.bit_length() - 1
    return (n // 9, (n // 3) % 3, n % 3)


def _build_lines():
    line_set = set()
    dirs = [
        (dx, dy, dz)
        for dx in (-1, 0, 1)
        for dy in (-1, 0, 1)
        for dz in (-1, 0, 1)
        if (dx, dy, dz) != (0, 0, 0)
    ]
    for dx, dy, dz in dirs:
        for i in range(3):
            for j in range(3):
                for k in range(3):
                    pts = []
                    ok = True
                    for t in range(3):
                        x = i + dx * t
                        y = j + dy * t
                        z = k + dz * t
                        if 0 <= x < 3 and 0 <= y < 3 and 0 <= z < 3:
                            pts.append(_idx(x, y, z))
                        else:
                            ok = False
                            break
                    if ok:
                        line_set.add(tuple(sorted(pts)))
    lines = sorted(line_set)
    masks = [(1 << a) | (1 << b) | (1 << c) for a, b, c in lines]
    cell_lines = [[] for _ in range(BOARD_CELLS)]
    for lm in masks:
        m = lm
        while m:
            b = m & -m
            cell_lines[b.bit_length() - 1].append(lm)
            m ^= b
    weights = [len(cell_lines[i]) for i in range(BOARD_CELLS)]
    return masks, cell_lines, weights


LINE_MASKS, CELL_LINES, CELL_WEIGHT = _build_lines()
CENTER_BIT = 1 << _idx(1, 1, 1)


def _won(mask):
    for lm in LINE_MASKS:
        if mask & lm == lm:
            return True
    return False


def _winning_bits(cur, opp):
    # Empty cells that complete three in a row for cur.
    res = 0
    for lm in LINE_MASKS:
        if lm & opp:
            continue
        cm = lm & cur
        if cm.bit_count() == 2:
            res |= lm ^ cm
    return res


def _best_bit_by_weight(mask):
    best = 0
    best_score = -1
    m = mask
    while m:
        b = m & -m
        m ^= b
        s = CELL_WEIGHT[b.bit_length() - 1]
        if s > best_score:
            best_score = s
            best = b
    return best


def _evaluate(cur, opp):
    # Evaluation from the perspective of the side to move (cur).
    my_wins = _winning_bits(cur, opp)
    if my_wins:
        return WIN_VALUE - 500 + my_wins.bit_count() * 25

    opp_wins = _winning_bits(opp, cur)
    opp_count = opp_wins.bit_count()
    if opp_count >= 2:
        return -WIN_VALUE + 500 - opp_count * 25

    score = 0
    if opp_count == 1:
        score -= 35_000

    for lm in LINE_MASKS:
        a = lm & cur
        b = lm & opp
        if a and b:
            continue
        if b == 0:
            ca = a.bit_count()
            if ca == 1:
                score += 5
            elif ca == 2:
                score += 80
        elif a == 0:
            cb = b.bit_count()
            if cb == 1:
                score -= 6
            elif cb == 2:
                score -= 100

    m = cur
    while m:
        b = m & -m
        m ^= b
        score += CELL_WEIGHT[b.bit_length() - 1] * 4
    m = opp
    while m:
        b = m & -m
        m ^= b
        score -= CELL_WEIGHT[b.bit_length() - 1] * 4
    return score


def _ordered_moves(cur, opp, tt_move=0):
    occ = cur | opp
    empt = FULL_MASK & ~occ
    my_wins = _winning_bits(cur, opp)
    opp_wins = _winning_bits(opp, cur)
    my_win_count = my_wins.bit_count()

    scored = []
    m = empt
    while m:
        b = m & -m
        m ^= b
        ci = b.bit_length() - 1

        if b & my_wins:
            score = 300_000_000 + CELL_WEIGHT[ci] * 1000
        else:
            score = 0
            if b == tt_move:
                score += 80_000_000

            remaining_opp_wins = opp_wins & ~b
            if remaining_opp_wins:
                score -= 120_000_000 + remaining_opp_wins.bit_count() * 20_000_000
            if b & opp_wins:
                score += 60_000_000

            new_threats = 0
            potential = 0
            for lm in CELL_LINES[ci]:
                if lm & opp:
                    continue
                cm = lm & cur
                ca = cm.bit_count()
                if ca == 1:
                    r = lm ^ cm ^ b
                    if r and not (r & (cur | opp | b)):
                        new_threats |= r
                        potential += 1500
                elif ca == 0:
                    potential += 60

            threat_count = my_win_count + new_threats.bit_count()
            if threat_count:
                score += threat_count * 900_000
                if threat_count >= 2:
                    score += 25_000_000
            score += potential + CELL_WEIGHT[ci] * 100

        scored.append((score, b))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [b for _, b in scored]


def _find_fork(cur, opp):
    # A fork is a quiet move creating at least two distinct immediate winning threats.
    if _winning_bits(cur, opp) or _winning_bits(opp, cur):
        return 0
    occ = cur | opp
    empt = FULL_MASK & ~occ
    best = 0
    best_key = (-1, -1, -1)
    m = empt
    while m:
        b = m & -m
        m ^= b
        ci = b.bit_length() - 1
        new_threats = 0
        for lm in CELL_LINES[ci]:
            if lm & opp:
                continue
            cm = lm & cur
            if cm.bit_count() == 1:
                r = lm ^ cm ^ b
                if r and not (r & (cur | opp | b)):
                    new_threats |= r
        tc = new_threats.bit_count()
        if tc >= 2:
            threat_weight = 0
            x = new_threats
            while x:
                rb = x & -x
                x ^= rb
                threat_weight += CELL_WEIGHT[rb.bit_length() - 1]
            key = (tc, threat_weight, CELL_WEIGHT[ci])
            if key > best_key:
                best_key = key
                best = b
    return best


def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    try:
        me = 0
        opp = 0
        for i in range(3):
            for j in range(3):
                for k in range(3):
                    v = board[i][j][k]
                    if v == 1:
                        me |= 1 << _idx(i, j, k)
                    elif v == -1:
                        opp |= 1 << _idx(i, j, k)

        occ = me | opp
        empt = FULL_MASK & ~occ
        if empt == 0:
            return (0, 0, 0)  # No legal move exists; should not happen in normal play.

        wins = _winning_bits(me, opp)
        if wins:
            return _coords_from_bit(_best_bit_by_weight(wins))

        opp_wins = _winning_bits(opp, me)
        if opp_wins:
            return _coords_from_bit(_best_bit_by_weight(opp_wins))

        if occ == 0:
            return (1, 1, 1)
        if (empt & CENTER_BIT) and occ.bit_count() <= 1:
            return (1, 1, 1)

        fork = _find_fork(me, opp)
        if fork:
            return _coords_from_bit(fork)

        start = time.monotonic()
        deadline = start + TIME_LIMIT
        tt = {}
        node_count = 0

        def check_time():
            nonlocal node_count
            node_count += 1
            if (node_count & 1023) == 0 and time.monotonic() >= deadline:
                raise _Timeout()

        def negamax(cur, opp, depth, alpha, beta):
            check_time()
            if _won(opp):
                return -WIN_VALUE + (cur | opp).bit_count()
            occ = cur | opp
            if occ == FULL_MASK:
                return 0
            rem = BOARD_CELLS - occ.bit_count()
            if depth <= 0:
                return _evaluate(cur, opp)
            if depth > rem:
                depth = rem

            key = (cur, opp)
            ent = tt.get(key)
            tt_move = 0
            alpha0 = alpha
            if ent is not None and ent[0] >= depth:
                _, val, flag, bm = ent
                tt_move = bm
                if flag == 0:
                    return val
                if flag == 1:
                    if val > alpha:
                        alpha = val
                elif val < beta:
                    beta = val
                if alpha >= beta:
                    return val

            best_val = -INF
            best_move = 0
            for b in _ordered_moves(cur, opp, tt_move):
                after = cur | b
                if b & _winning_bits(cur, opp):
                    val = WIN_VALUE - (occ.bit_count() + 1)
                else:
                    val = -negamax(opp, after, depth - 1, -beta, -alpha)
                if val > best_val:
                    best_val = val
                    best_move = b
                if val > alpha:
                    alpha = val
                if alpha >= beta:
                    break

            if best_move == 0:
                return _evaluate(cur, opp)

            flag = 0
            if best_val <= alpha0:
                flag = 2
            elif best_val >= beta:
                flag = 1
            old = tt.get(key)
            if old is None or old[0] <= depth:
                tt[key] = (depth, best_val, flag, best_move)
            return best_val

        best_move = _ordered_moves(me, opp, 0)[0]
        max_depth = empt.bit_count()

        for depth in range(1, max_depth + 1):
            if time.monotonic() >= deadline:
                break
            try:
                alpha = -INF
                beta = INF
                best_val = -INF
                best_this = best_move
                for b in _ordered_moves(me, opp, best_move):
                    if time.monotonic() >= deadline:
                        raise _Timeout()
                    after = me | b
                    if _won(after):
                        val = WIN_VALUE - (occ.bit_count() + 1)
                    else:
                        val = -negamax(opp, after, depth - 1, -beta, -alpha)
                    if val > best_val:
                        best_val = val
                        best_this = b
                    if val > alpha:
                        alpha = val
                best_move = best_this
                if best_val >= WIN_VALUE - 1000:
                    break
            except _Timeout:
                break

        if best_move and (best_move & empt):
            return _coords_from_bit(best_move)
        return _coords_from_bit(empt & -empt)

    except Exception:
        try:
            for i in range(3):
                for j in range(3):
                    for k in range(3):
                        if board[i][j][k] == 0:
                            return (i, j, k)
        except Exception:
            pass
        return (0, 0, 0)
