
import time

INF = 10**18
TIME_LIMIT = 0.95


class _Timeout(Exception):
    pass


def _legal_moves(you):
    return [i for i in range(6) if you[i] > 0]


def _apply_move(you, opp, move):
    y = you[:]
    o = opp[:]

    seeds = y[move]
    y[move] = 0
    pos = move

    while seeds:
        pos = (pos + 1) % 13
        if pos < 7:
            y[pos] += 1
        else:
            o[pos - 7] += 1
        seeds -= 1

    extra = (pos == 6)

    if 0 <= pos <= 5 and y[pos] == 1:
        opp_idx = 5 - pos
        if o[opp_idx] > 0:
            y[6] += y[pos] + o[opp_idx]
            y[pos] = 0
            o[opp_idx] = 0

    ysum = y[0] + y[1] + y[2] + y[3] + y[4] + y[5]
    osum = o[0] + o[1] + o[2] + o[3] + o[4] + o[5]

    terminal = False
    if ysum == 0 or osum == 0:
        terminal = True
        y[6] += ysum
        o[6] += osum
        for i in range(6):
            y[i] = 0
            o[i] = 0

    return y, o, extra, terminal


def _count_extra_turn_moves(you):
    c = 0
    for i in range(6):
        s = you[i]
        if s <= 0:
            continue
        if (i + s) % 13 == 6:
            c += 1
    return c


def _capture_potential(you, opp):
    score = 0
    for i in range(6):
        s = you[i]
        if s <= 0:
            continue
        landing = (i + s) % 13
        if 0 <= landing <= 5 and you[landing] == 0 and opp[5 - landing] > 0:
            score += 1 + opp[5 - landing]
    return score


def _evaluate(you, opp):
    store_diff = you[6] - opp[6]
    seeds_you = you[0] + you[1] + you[2] + you[3] + you[4] + you[5]
    seeds_opp = opp[0] + opp[1] + opp[2] + opp[3] + opp[4] + opp[5]
    board_diff = seeds_you - seeds_opp

    extra_you = _count_extra_turn_moves(you)
    extra_opp = _count_extra_turn_moves(opp)

    cap_you = _capture_potential(you, opp)
    cap_opp = _capture_potential(opp, you)

    mobility = sum(1 for i in range(6) if you[i] > 0) - sum(1 for i in range(6) if opp[i] > 0)

    return (
        32 * store_diff
        + 2 * board_diff
        + 8 * (extra_you - extra_opp)
        + 3 * (cap_you - cap_opp)
        + mobility
    )


def _move_order(you, opp, moves):
    scored = []
    for m in moves:
        ny, no, extra, terminal = _apply_move(you, opp, m)
        gain = ny[6] - you[6]
        score = 0
        if terminal:
            score += 100000 + (ny[6] - no[6]) * 100
        if extra:
            score += 5000
        score += gain * 200

        if not terminal:
            if not extra:
                score += -_evaluate(no, ny) // 4
            else:
                score += _evaluate(ny, no) // 4

        scored.append((score, m))
    scored.sort(reverse=True)
    return [m for _, m in scored]


def _negamax(you, opp, depth, alpha, beta, deadline, tt):
    if time.perf_counter() >= deadline:
        raise _Timeout

    key = (tuple(you), tuple(opp), depth)
    cached = tt.get(key)
    if cached is not None:
        return cached

    legal = _legal_moves(you)
    if not legal:
        val = you[6] - opp[6]
        tt[key] = val
        return val

    if depth == 0:
        val = _evaluate(you, opp)
        tt[key] = val
        return val

    remaining = sum(you[:6]) + sum(opp[:6])
    if remaining <= 10:
        depth = max(depth, remaining + 2)

    best = -INF
    ordered = _move_order(you, opp, legal)

    for m in ordered:
        ny, no, extra, terminal = _apply_move(you, opp, m)

        if terminal:
            val = ny[6] - no[6]
        elif extra:
            val = _negamax(ny, no, depth - 1, alpha, beta, deadline, tt)
        else:
            val = -_negamax(no, ny, depth - 1, -beta, -alpha, deadline, tt)

        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    tt[key] = best
    return best


def policy(you, opponent):
    legal = _legal_moves(you)
    if not legal:
        return 0

    best_move = legal[0]

    ordered_root = _move_order(you, opponent, legal)
    if ordered_root:
        best_move = ordered_root[0]

    deadline = time.perf_counter() + TIME_LIMIT
    depth = 1

    try:
        while True:
            if time.perf_counter() >= deadline:
                break

            tt = {}
            current_best = best_move
            current_best_val = -INF

            root_moves = _move_order(you, opponent, legal)
            alpha = -INF
            beta = INF

            for m in root_moves:
                if time.perf_counter() >= deadline:
                    raise _Timeout

                ny, no, extra, terminal = _apply_move(you, opponent, m)

                if terminal:
                    val = ny[6] - no[6]
                elif extra:
                    val = _negamax(ny, no, depth - 1, alpha, beta, deadline, tt)
                else:
                    val = -_negamax(no, ny, depth - 1, -beta, -alpha, deadline, tt)

                if val > current_best_val:
                    current_best_val = val
                    current_best = m
                if val > alpha:
                    alpha = val

            best_move = current_best
            depth += 1

    except _Timeout:
        pass

    if you[best_move] > 0:
        return best_move

    for m in legal:
        if you[m] > 0:
            return m

    return 0
