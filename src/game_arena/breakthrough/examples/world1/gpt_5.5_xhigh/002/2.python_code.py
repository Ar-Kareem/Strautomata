
from __future__ import annotations

import time

WIN_SCORE = 10_000_000
INF = 1_000_000_000
TIME_LIMIT = 0.90

BLACK = 0
WHITE = 1
DIRS = [-1, 1]

BITS = [1 << i for i in range(64)]
ROWS = [i >> 3 for i in range(64)]
COLS = [i & 7 for i in range(64)]

ROW_MASKS = []
for _r in range(8):
    _m = 0
    for _c in range(8):
        _m |= BITS[(_r << 3) | _c]
    ROW_MASKS.append(_m)

GOAL_MASK = [ROW_MASKS[0], ROW_MASKS[7]]
PREGOAL_MASK = [ROW_MASKS[1], ROW_MASKS[6]]

FWD = [[-1 for _ in range(64)] for _ in range(2)]
DIAG = [[() for _ in range(64)] for _ in range(2)]
ATTACK_FROM = [[0 for _ in range(64)] for _ in range(2)]
ATTACKERS = [[0 for _ in range(64)] for _ in range(2)]
PROGRESS = [[0 for _ in range(64)] for _ in range(2)]
PASS_CONE = [[0 for _ in range(64)] for _ in range(2)]

for ci, d in enumerate(DIRS):
    for i in range(64):
        r = ROWS[i]
        c = COLS[i]
        PROGRESS[ci][i] = r if ci == WHITE else 7 - r

        nr = r + d
        if 0 <= nr < 8:
            FWD[ci][i] = (nr << 3) | c
            targets = []
            mask = 0
            for dc in (-1, 1):
                nc = c + dc
                if 0 <= nc < 8:
                    t = (nr << 3) | nc
                    targets.append(t)
                    tb = BITS[t]
                    mask |= tb
                    ATTACKERS[ci][t] |= BITS[i]
            DIAG[ci][i] = tuple(targets)
            ATTACK_FROM[ci][i] = mask

for ci, d in enumerate(DIRS):
    for i in range(64):
        r = ROWS[i]
        c = COLS[i]
        mask = 0
        step = 1
        nr = r + d
        while 0 <= nr < 8:
            lo = max(0, c - step)
            hi = min(7, c + step)
            base = nr << 3
            for nc in range(lo, hi + 1):
                mask |= BITS[base | nc]
            step += 1
            nr += d
        PASS_CONE[ci][i] = mask

ADVANCE_VALUE = [0, 12, 30, 70, 150, 330, 820, 0]
PASSED_BONUS = [0, 10, 25, 60, 150, 360, 950, 0]
CENTER_VALUE = [0, 3, 7, 11, 11, 7, 3, 0]

PST = [[0 for _ in range(64)] for _ in range(2)]
for ci in range(2):
    for i in range(64):
        p = PROGRESS[ci][i]
        PST[ci][i] = 95 + ADVANCE_VALUE[p] + CENTER_VALUE[COLS[i]] * (1 + p // 2)


class _SearchTimeout(Exception):
    pass


def _to_bits(pieces):
    b = 0
    for r, c in pieces:
        if 0 <= r < 8 and 0 <= c < 8:
            b |= BITS[(r << 3) | c]
    return b


def _decode_move(code):
    fr = code >> 6
    to = code & 63
    return ((ROWS[fr], COLS[fr]), (ROWS[to], COLS[to]))


def _immediate_win_count(us, them, ci):
    occ = us | them
    bb = us & PREGOAL_MASK[ci]
    count = 0
    bits = BITS
    fwd = FWD[ci]
    diag = DIAG[ci]

    while bb:
        lsb = bb & -bb
        fr = lsb.bit_length() - 1
        bb ^= lsb

        f = fwd[fr]
        if f >= 0 and not (occ & bits[f]):
            count += 1

        for t in diag[fr]:
            if not (us & bits[t]):
                count += 1

    return count


def _has_immediate_win(us, them, ci):
    if _immediate_win_count(us, them, ci):
        return True

    # Capturing the last opponent piece also wins immediately.
    if them and (them & (them - 1)) == 0:
        target = them.bit_length() - 1
        if us & ATTACKERS[ci][target]:
            return True

    return False


def _side_score(pieces, enemy, ci):
    oppci = ci ^ 1
    total = 0
    bb = pieces

    bits = BITS
    pst = PST[ci]
    prog = PROGRESS[ci]
    fwd = FWD[ci]
    pass_cone = PASS_CONE[ci]
    attackers_own = ATTACKERS[ci]
    attackers_enemy = ATTACKERS[oppci]
    attack_from = ATTACK_FROM[ci]

    while bb:
        lsb = bb & -bb
        i = lsb.bit_length() - 1
        bb ^= lsb

        p = prog[i]
        total += pst[i]

        support = (pieces & attackers_own[i]).bit_count()
        if support:
            total += 14 * support + 3 * p * support

        attacked = (enemy & attackers_enemy[i]).bit_count()
        if attacked:
            if support:
                total += 7 * support - 5 * attacked
            else:
                total -= 38 + 9 * p + 12 * attacked

        f = fwd[i]
        if f >= 0:
            fb = bits[f]
            if enemy & fb:
                total -= 16 + 5 * p
            elif pieces & fb:
                total -= 5

        if not (enemy & pass_cone[i]):
            total += PASSED_BONUS[p]
            if support:
                total += 12 + 2 * p

        captures = (attack_from[i] & enemy).bit_count()
        if captures:
            total += 20 * captures + 4 * p

    return total


def _evaluate(us, them, ci, check_immediate=True):
    oppci = ci ^ 1

    if them == 0 or (us & GOAL_MASK[ci]):
        return WIN_SCORE
    if us == 0 or (them & GOAL_MASK[oppci]):
        return -WIN_SCORE

    if check_immediate and _has_immediate_win(us, them, ci):
        return WIN_SCORE - 1

    score = _side_score(us, them, ci) - _side_score(them, us, oppci)

    opp_goal_threats = _immediate_win_count(them, us, oppci)
    if opp_goal_threats:
        score -= 120_000 + 8_000 * opp_goal_threats

    # If we have only one piece left, an opponent capture of it is also fatal.
    if us and (us & (us - 1)) == 0:
        target = us.bit_length() - 1
        if them & ATTACKERS[oppci][target]:
            score -= 130_000

    return score


def _ordered_moves(us, them, ci, tt_move=-1):
    occ = us | them
    oppci = ci ^ 1
    result = []

    bits = BITS
    fwd = FWD[ci]
    diag = DIAG[ci]
    prog = PROGRESS[ci]
    oppprog = PROGRESS[oppci]
    pass_cone = PASS_CONE[ci]
    attackers_enemy = ATTACKERS[oppci]
    attackers_own = ATTACKERS[ci]
    goal = GOAL_MASK[ci]
    center = CENTER_VALUE
    cols = COLS

    bb = us
    while bb:
        lsb = bb & -bb
        fr = lsb.bit_length() - 1
        bb ^= lsb

        f = fwd[fr]
        if f >= 0:
            tb = bits[f]
            if not (occ & tb):
                code = (fr << 6) | f
                pto = prog[f]
                s = pto * 32 + center[cols[f]] * 5

                if tb & goal:
                    s += 5_000_000
                if pto == 6:
                    s += 2_800
                if not (them & pass_cone[f]):
                    s += 500 + pto * 55

                attacked = them & attackers_enemy[f]
                if attacked:
                    moved = (us ^ lsb) | tb
                    if moved & attackers_own[f]:
                        s += 120
                    else:
                        s -= 950 + pto * 90

                if code == tt_move:
                    s += 10_000_000

                result.append((s, code))

        for t in diag[fr]:
            tb = bits[t]
            if not (us & tb):
                code = (fr << 6) | t
                pto = prog[t]
                s = pto * 32 + center[cols[t]] * 5 + 100

                if tb & goal:
                    s += 5_000_000

                if them & tb:
                    s += 3_800 + oppprog[t] * 320
                    if (them & ~tb) == 0:
                        s += 4_000_000

                if pto == 6:
                    s += 2_800
                if not (them & pass_cone[t]):
                    s += 500 + pto * 55

                attacked = them & attackers_enemy[t]
                if attacked:
                    moved = (us ^ lsb) | tb
                    if moved & attackers_own[t]:
                        s += 120
                    else:
                        s -= 950 + pto * 90

                if code == tt_move:
                    s += 10_000_000

                result.append((s, code))

    if len(result) > 1:
        result.sort(reverse=True)

    return [code for _, code in result]


def _emergency_move(me, opp, color):
    us_set = set(me)
    opp_set = set(opp)
    occ = us_set | opp_set
    d = 1 if color == "w" else -1
    goal = 7 if color == "w" else 0

    # Prefer any legal move that reaches the goal row.
    for r, c in me:
        nr = r + d
        if 0 <= nr < 8 and nr == goal:
            if (nr, c) not in occ:
                return ((r, c), (nr, c))
            for nc in (c - 1, c + 1):
                if 0 <= nc < 8 and (nr, nc) not in us_set:
                    return ((r, c), (nr, nc))

    # Otherwise return the first legal move found.
    for r, c in me:
        nr = r + d
        if 0 <= nr < 8:
            if (nr, c) not in occ:
                return ((r, c), (nr, c))
            for nc in (c - 1, c + 1):
                if 0 <= nc < 8 and (nr, nc) not in us_set:
                    return ((r, c), (nr, nc))

    # A true no-legal-move state should not be supplied by the arena.
    if me:
        r, c = me[0]
        nr = max(0, min(7, r + d))
        return ((r, c), (nr, c))

    return ((0, 0), (0, 0))


def policy(
    me: list[tuple[int, int]],
    opp: list[tuple[int, int]],
    color: str,
) -> tuple[tuple[int, int], tuple[int, int]]:
    start = time.perf_counter()
    deadline = start + TIME_LIMIT

    ci = WHITE if color == "w" else BLACK
    oppci = ci ^ 1

    us = _to_bits(me)
    them = _to_bits(opp)

    root_moves = _ordered_moves(us, them, ci)
    if not root_moves:
        return _emergency_move(me, opp, color)

    # Return an immediate win without spending search time.
    for code in root_moves:
        to = code & 63
        tb = BITS[to]
        if tb & GOAL_MASK[ci]:
            return _decode_move(code)
        if (them & tb) and ((them & ~tb) == 0):
            return _decode_move(code)

    # Static one-ply fallback, guaranteed available if search times out.
    best_code = root_moves[0]
    best_score = -INF
    for code in root_moves:
        fr = code >> 6
        to = code & 63
        fb = BITS[fr]
        tb = BITS[to]
        moved = (us ^ fb) | tb
        remaining = them & ~tb
        val = -_evaluate(remaining, moved, oppci)
        if val > best_score:
            best_score = val
            best_code = code

    tt = {}
    nodes = 0

    def negamax(us_s, them_s, ci_s, depth, alpha, beta, ply):
        nonlocal nodes
        nodes += 1
        if (nodes & 2047) == 0 and time.perf_counter() >= deadline:
            raise _SearchTimeout()

        opp_s = ci_s ^ 1

        if them_s == 0 or (us_s & GOAL_MASK[ci_s]):
            return WIN_SCORE - ply
        if us_s == 0 or (them_s & GOAL_MASK[opp_s]):
            return -WIN_SCORE + ply

        if _has_immediate_win(us_s, them_s, ci_s):
            return WIN_SCORE - (ply + 1)

        if depth <= 0:
            return _evaluate(us_s, them_s, ci_s, check_immediate=False)

        key = (us_s, them_s, ci_s)
        alpha_orig = alpha
        beta_orig = beta
        tt_move = -1

        entry = tt.get(key)
        if entry is not None:
            edepth, escore, eflag, emove = entry
            tt_move = emove
            if edepth >= depth:
                if eflag == 0:
                    return escore
                if eflag == 1:
                    if escore > alpha:
                        alpha = escore
                else:
                    if escore < beta:
                        beta = escore
                if alpha >= beta:
                    return escore

        moves = _ordered_moves(us_s, them_s, ci_s, tt_move)
        if not moves:
            return -WIN_SCORE + ply

        best = -INF
        best_move = moves[0]
        first = True

        for code in moves:
            fr = code >> 6
            to = code & 63
            fb = BITS[fr]
            tb = BITS[to]
            moved = (us_s ^ fb) | tb
            remaining = them_s & ~tb

            if first:
                val = -negamax(
                    remaining,
                    moved,
                    opp_s,
                    depth - 1,
                    -beta,
                    -alpha,
                    ply + 1,
                )
                first = False
            else:
                val = -negamax(
                    remaining,
                    moved,
                    opp_s,
                    depth - 1,
                    -alpha - 1,
                    -alpha,
                    ply + 1,
                )
                if alpha < val < beta:
                    val = -negamax(
                        remaining,
                        moved,
                        opp_s,
                        depth - 1,
                        -beta,
                        -alpha,
                        ply + 1,
                    )

            if val > best:
                best = val
                best_move = code

            if val > alpha:
                alpha = val
                if alpha >= beta:
                    break

        flag = 0
        if best <= alpha_orig:
            flag = 2
        elif best >= beta_orig:
            flag = 1

        if len(tt) < 250_000:
            tt[key] = (depth, best, flag, best_move)

        return best

    total_pieces = us.bit_count() + them.bit_count()
    branching = len(root_moves)

    if total_pieces <= 10 or branching <= 8:
        max_depth = 10
    elif total_pieces <= 16 or branching <= 12:
        max_depth = 9
    elif total_pieces <= 24 or branching <= 18:
        max_depth = 8
    else:
        max_depth = 6

    try:
        for depth in range(1, max_depth + 1):
            if time.perf_counter() >= deadline:
                break

            current_best = best_code
            current_score = -INF
            alpha = -INF
            beta = INF
            root_values = {}

            ordered_root = [best_code]
            for m in root_moves:
                if m != best_code:
                    ordered_root.append(m)

            for code in ordered_root:
                if time.perf_counter() >= deadline:
                    raise _SearchTimeout()

                fr = code >> 6
                to = code & 63
                fb = BITS[fr]
                tb = BITS[to]
                moved = (us ^ fb) | tb
                remaining = them & ~tb

                val = -negamax(
                    remaining,
                    moved,
                    oppci,
                    depth - 1,
                    -beta,
                    -alpha,
                    1,
                )

                root_values[code] = val

                if val > current_score:
                    current_score = val
                    current_best = code

                if val > alpha:
                    alpha = val

            best_code = current_best
            best_score = current_score
            root_moves.sort(key=lambda m: root_values.get(m, -INF), reverse=True)

            if best_score >= WIN_SCORE - 100:
                break

    except _SearchTimeout:
        pass

    return _decode_move(best_code)
