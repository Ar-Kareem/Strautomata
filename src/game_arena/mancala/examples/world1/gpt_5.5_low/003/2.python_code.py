
import time
from math import inf

# Kalah policy for a standard 6-house board.
# The function always returns a legal move index 0..5.


class _Timeout(Exception):
    pass


def policy(you: list[int], opponent: list[int]) -> int:
    start = time.perf_counter()
    deadline = start + 0.92  # stay safely under a 1 second limit

    legal = [i for i in range(6) if you[i] > 0]
    if not legal:
        return 0  # policy should never be called here, but keep a safe integer

    # Immediate tactical fallback: prefer moves that grant another turn,
    # then captures, then simply the rightmost legal move.
    best_move = _fallback_move(you, opponent, legal)

    # Transposition cache. Key includes depth because bounds are not stored.
    cache = {}

    def check_time():
        if time.perf_counter() > deadline:
            raise _Timeout()

    # Adaptive maximum depth. Endgames can be searched deeper.
    seeds_in_houses = sum(you[:6]) + sum(opponent[:6])
    if seeds_in_houses <= 10:
        max_depth = 18
    elif seeds_in_houses <= 18:
        max_depth = 14
    elif seeds_in_houses <= 28:
        max_depth = 11
    else:
        max_depth = 9

    try:
        for depth in range(1, max_depth + 1):
            check_time()
            current_best = best_move
            current_best_score = -inf

            moves = _ordered_moves(you, opponent, 0)
            for mv in moves:
                if you[mv] <= 0:
                    continue
                check_time()
                na, nb, next_side = _make_move(you, opponent, 0, mv)
                if _terminal(na, nb):
                    score = _evaluate(na, nb)
                elif next_side == 0:
                    score = _search(na, nb, next_side, depth - 1, -inf, inf,
                                    deadline, cache)
                else:
                    score = _search(na, nb, next_side, depth - 1, -inf, inf,
                                    deadline, cache)

                if score > current_best_score:
                    current_best_score = score
                    current_best = mv

            best_move = current_best

    except _Timeout:
        pass
    except Exception:
        # Never risk returning an illegal move because of an unexpected issue.
        return best_move if you[best_move] > 0 else legal[0]

    if 0 <= best_move <= 5 and you[best_move] > 0:
        return best_move
    return legal[0]


def _search(a, b, side, depth, alpha, beta, deadline, cache):
    if time.perf_counter() > deadline:
        raise _Timeout()

    if _terminal(a, b) or depth <= 0:
        return _evaluate(a, b)

    key = (tuple(a), tuple(b), side, depth)
    val = cache.get(key)
    if val is not None:
        return val

    if side == 0:
        value = -inf
        moves = _ordered_moves(a, b, side)
        any_move = False
        for mv in moves:
            if a[mv] <= 0:
                continue
            any_move = True
            na, nb, ns = _make_move(a, b, side, mv)
            score = _search(na, nb, ns, depth - 1, alpha, beta, deadline, cache)
            if score > value:
                value = score
            if value > alpha:
                alpha = value
            if alpha >= beta:
                break
        if not any_move:
            value = _evaluate(a, b)
    else:
        value = inf
        moves = _ordered_moves(a, b, side)
        any_move = False
        for mv in moves:
            if b[mv] <= 0:
                continue
            any_move = True
            na, nb, ns = _make_move(a, b, side, mv)
            score = _search(na, nb, ns, depth - 1, alpha, beta, deadline, cache)
            if score < value:
                value = score
            if value < beta:
                beta = value
            if alpha >= beta:
                break
        if not any_move:
            value = _evaluate(a, b)

    if len(cache) < 200000:
        cache[key] = value
    return value


def _make_move(a, b, side, move):
    """
    a is the root player's side: [h0..h5, store]
    b is the opponent's side:    [h0..h5, store]
    side == 0 means root player moves.
    side == 1 means opponent moves.
    Returns new_a, new_b, next_side.
    """
    a = a[:]
    b = b[:]

    if side == 0:
        seeds = a[move]
        a[move] = 0
        pos_side = 0
        pos = move

        while seeds:
            if pos_side == 0:
                pos += 1
                if pos <= 6:
                    a[pos] += 1
                    seeds -= 1
                    if seeds == 0:
                        last_side, last_pos = 0, pos
                        break
                else:
                    pos_side = 1
                    pos = -1
            else:
                pos += 1
                if pos <= 5:
                    b[pos] += 1
                    seeds -= 1
                    if seeds == 0:
                        last_side, last_pos = 1, pos
                        break
                else:
                    pos_side = 0
                    pos = -1

        # Capture
        if last_side == 0 and 0 <= last_pos <= 5 and a[last_pos] == 1:
            opp_pos = 5 - last_pos
            if b[opp_pos] > 0:
                a[6] += b[opp_pos] + 1
                b[opp_pos] = 0
                a[last_pos] = 0

        next_side = 0 if (last_side == 0 and last_pos == 6) else 1

    else:
        seeds = b[move]
        b[move] = 0
        pos_side = 1
        pos = move

        while seeds:
            if pos_side == 1:
                pos += 1
                if pos <= 6:
                    b[pos] += 1
                    seeds -= 1
                    if seeds == 0:
                        last_side, last_pos = 1, pos
                        break
                else:
                    pos_side = 0
                    pos = -1
            else:
                pos += 1
                if pos <= 5:
                    a[pos] += 1
                    seeds -= 1
                    if seeds == 0:
                        last_side, last_pos = 0, pos
                        break
                else:
                    pos_side = 1
                    pos = -1

        # Capture for opponent
        if last_side == 1 and 0 <= last_pos <= 5 and b[last_pos] == 1:
            opp_pos = 5 - last_pos
            if a[opp_pos] > 0:
                b[6] += a[opp_pos] + 1
                a[opp_pos] = 0
                b[last_pos] = 0

        next_side = 1 if (last_side == 1 and last_pos == 6) else 0

    # End game collection
    if sum(a[:6]) == 0 or sum(b[:6]) == 0:
        a[6] += sum(a[:6])
        b[6] += sum(b[:6])
        for i in range(6):
            a[i] = 0
            b[i] = 0

    return a, b, next_side


def _terminal(a, b):
    return sum(a[:6]) == 0 or sum(b[:6]) == 0


def _evaluate(a, b):
    store_diff = a[6] - b[6]

    if _terminal(a, b):
        return store_diff * 100000

    my_houses = sum(a[:6])
    opp_houses = sum(b[:6])

    score = store_diff * 1200
    score += (my_houses - opp_houses) * 18

    # Extra-turn opportunities.
    for i in range(6):
        if a[i] > 0 and a[i] == 6 - i:
            score += 95
        if b[i] > 0 and b[i] == 6 - i:
            score -= 95

    # Immediate capture opportunities and vulnerabilities.
    for i in range(6):
        if a[i] == 0 and b[5 - i] > 0:
            score += b[5 - i] * 2
        if b[i] == 0 and a[5 - i] > 0:
            score -= a[5 - i] * 2

    # Mobility: having more choices is usually useful.
    score += sum(1 for x in a[:6] if x > 0) * 8
    score -= sum(1 for x in b[:6] if x > 0) * 8

    # Seeds closer to our store are slightly more valuable.
    weights = [1, 2, 3, 4, 5, 6]
    score += sum(a[i] * weights[i] for i in range(6))
    score -= sum(b[i] * weights[i] for i in range(6))

    return score


def _ordered_moves(a, b, side):
    if side == 0:
        legal = [i for i in range(6) if a[i] > 0]
        scored = []
        for mv in legal:
            na, nb, ns = _make_move(a, b, side, mv)
            bonus = _evaluate(na, nb)
            if ns == 0:
                bonus += 500
            scored.append((bonus, mv))
        scored.sort(reverse=True)
        return [mv for _, mv in scored]
    else:
        legal = [i for i in range(6) if b[i] > 0]
        scored = []
        for mv in legal:
            na, nb, ns = _make_move(a, b, side, mv)
            bonus = _evaluate(na, nb)
            if ns == 1:
                bonus -= 500
            scored.append((bonus, mv))
        scored.sort()
        return [mv for _, mv in scored]


def _fallback_move(you, opponent, legal):
    best = legal[0]
    best_score = -10**18
    for mv in legal:
        na, nb, ns = _make_move(you, opponent, 0, mv)
        score = _evaluate(na, nb)
        if ns == 0:
            score += 10000
        if score > best_score:
            best_score = score
            best = mv
    return best
