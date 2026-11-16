
import time
import sys

sys.setrecursionlimit(10000)

INF = 10**9
EXACT = 0
LOWER = 1
UPPER = 2

TIME_BUDGET = 0.88
TT_LIMIT = 250000

TT = {}
DEADLINE = 0.0
NODE_COUNT = 0


class _SearchTimeout(Exception):
    pass


def _house_sum(side):
    return side[0] + side[1] + side[2] + side[3] + side[4] + side[5]


def _terminal_value(a, b, a_sum=None, b_sum=None):
    if a_sum is None:
        a_sum = _house_sum(a)
    if b_sum is None:
        b_sum = _house_sum(b)
    if a_sum == 0:
        return 1000 * (a[6] - (b[6] + b_sum))
    return 1000 * ((a[6] + a_sum) - b[6])


def _apply_move(a, b, move):
    na = a.copy()
    nb = b.copy()

    seeds = na[move]
    na[move] = 0
    loc = move

    while seeds:
        loc = (loc + 1) % 13
        if loc < 6:
            na[loc] += 1
        elif loc == 6:
            na[6] += 1
        else:
            nb[loc - 7] += 1
        seeds -= 1

    if loc < 6 and na[loc] == 1:
        opp = 5 - loc
        if nb[opp] > 0:
            na[6] += 1 + nb[opp]
            na[loc] = 0
            nb[opp] = 0

    a_sum = _house_sum(na)
    if a_sum == 0:
        b_sum = _house_sum(nb)
        if b_sum:
            nb[6] += b_sum
            nb[0] = nb[1] = nb[2] = nb[3] = nb[4] = nb[5] = 0
        return na, nb, False, True

    b_sum = _house_sum(nb)
    if b_sum == 0:
        na[6] += a_sum
        na[0] = na[1] = na[2] = na[3] = na[4] = na[5] = 0
        return na, nb, False, True

    return na, nb, (loc == 6), False


def _move_order_score(a, b, move, tt_move=-1):
    if move == tt_move:
        return 10**7

    s = a[move]
    loc = (move + s) % 13
    score = move * 2 + min(s, 13)

    if loc == 6:
        score += 100000
    elif s <= 13 and loc < 6 and b[5 - loc] > 0 and (loc == move or a[loc] == 0):
        score += 10000 + 100 * b[5 - loc]

    return score


def _ordered_moves(a, b, tt_move=-1):
    moves = [i for i in range(6) if a[i] > 0]
    if len(moves) > 1:
        moves.sort(key=lambda m: _move_order_score(a, b, m, tt_move), reverse=True)
    return moves


def _evaluate(a, b):
    a0, a1, a2, a3, a4, a5, astore = a
    b0, b1, b2, b3, b4, b5, bstore = b

    a_sum = a0 + a1 + a2 + a3 + a4 + a5
    b_sum = b0 + b1 + b2 + b3 + b4 + b5

    if a_sum == 0 or b_sum == 0:
        return _terminal_value(a, b, a_sum, b_sum)

    store_diff = astore - bstore
    house_diff = a_sum - b_sum

    pos_a = a1 + 2 * a2 + 3 * a3 + 4 * a4 + 5 * a5
    pos_b = b1 + 2 * b2 + 3 * b3 + 4 * b4 + 5 * b5
    pos_diff = pos_a - pos_b

    free_a = 0
    free_b = 0
    cap_a = 0
    cap_b = 0
    legal_a = 0
    legal_b = 0

    for i in range(6):
        s = a[i]
        if s:
            legal_a += 1
            if (i + s) % 13 == 6:
                free_a += 1
            if s <= 13:
                loc = (i + s) % 13
                if loc < 6 and b[5 - loc] > 0 and (loc == i or a[loc] == 0):
                    cap = 1 + b[5 - loc]
                    if cap > cap_a:
                        cap_a = cap

    for i in range(6):
        s = b[i]
        if s:
            legal_b += 1
            if (i + s) % 13 == 6:
                free_b += 1
            if s <= 13:
                loc = (i + s) % 13
                if loc < 6 and a[5 - loc] > 0 and (loc == i or b[loc] == 0):
                    cap = 1 + a[5 - loc]
                    if cap > cap_b:
                        cap_b = cap

    return (
        1000 * store_diff
        + 42 * house_diff
        + 2 * pos_diff
        + 150 * (free_a - free_b)
        + 45 * (cap_a - cap_b)
        + 10 * (legal_a - legal_b)
    )


def _state_key(a, b):
    return (*a, *b)


def _tt_best_move(a, b):
    entry = TT.get(_state_key(a, b))
    if entry is None:
        return -1
    return entry[3]


def _search(a, b, depth, alpha, beta):
    global NODE_COUNT

    NODE_COUNT += 1
    if (NODE_COUNT & 255) == 0 and time.perf_counter() >= DEADLINE:
        raise _SearchTimeout

    a_sum = _house_sum(a)
    b_sum = _house_sum(b)
    if a_sum == 0 or b_sum == 0:
        return _terminal_value(a, b, a_sum, b_sum)

    if depth <= 0:
        return _evaluate(a, b)

    alpha0 = alpha
    beta0 = beta

    key = _state_key(a, b)
    entry = TT.get(key)
    tt_move = -1
    if entry is not None:
        edepth, eflag, evalv, emove = entry
        tt_move = emove
        if edepth >= depth:
            if eflag == EXACT:
                return evalv
            if eflag == LOWER:
                if evalv > alpha:
                    alpha = evalv
            else:
                if evalv < beta:
                    beta = evalv
            if alpha >= beta:
                return evalv

    moves = _ordered_moves(a, b, tt_move)
    if not moves:
        return _evaluate(a, b)

    best = -INF
    best_move = moves[0]

    for move in moves:
        na, nb, same_turn, terminal = _apply_move(a, b, move)

        if terminal:
            val = 1000 * (na[6] - nb[6])
        elif same_turn:
            val = _search(na, nb, depth, alpha, beta)
        else:
            val = -_search(nb, na, depth - 1, -beta, -alpha)

        if val > best:
            best = val
            best_move = move

        if val > alpha:
            alpha = val
            if alpha >= beta:
                break

    if best <= alpha0:
        flag = UPPER
    elif best >= beta0:
        flag = LOWER
    else:
        flag = EXACT

    old = TT.get(key)
    if old is None or old[0] <= depth:
        if len(TT) < TT_LIMIT or key in TT:
            TT[key] = (depth, flag, best, best_move)

    return best


def _root_search(a, b, depth, pv_move=-1):
    alpha = -INF
    beta = INF

    tt_move = pv_move if (0 <= pv_move <= 5 and a[pv_move] > 0) else _tt_best_move(a, b)
    moves = _ordered_moves(a, b, tt_move)

    best_move = moves[0]
    best_val = -INF

    for move in moves:
        na, nb, same_turn, terminal = _apply_move(a, b, move)

        if terminal:
            val = 1000 * (na[6] - nb[6])
        elif same_turn:
            val = _search(na, nb, depth, alpha, beta)
        else:
            val = -_search(nb, na, depth - 1, -beta, -alpha)

        if val > best_val:
            best_val = val
            best_move = move

        if val > alpha:
            alpha = val

    return best_move, best_val


def _greedy_move(a, b, legal_moves=None):
    if legal_moves is None:
        legal_moves = [i for i in range(6) if a[i] > 0]

    best_move = legal_moves[0]
    best_score = -INF

    for move in legal_moves:
        na, nb, same_turn, terminal = _apply_move(a, b, move)

        if terminal:
            score = 1000 * (na[6] - nb[6])
        elif same_turn:
            score = _evaluate(na, nb)
        else:
            score = -_evaluate(nb, na)

        score += 20 * (na[6] - a[6])

        if score > best_score:
            best_score = score
            best_move = move

    return best_move


def policy(you: list[int], opponent: list[int]) -> int:
    global DEADLINE, NODE_COUNT

    you = list(you)
    opponent = list(opponent)

    legal = [i for i in range(6) if you[i] > 0]
    if not legal:
        return 0
    if len(legal) == 1:
        return legal[0]

    fallback = _greedy_move(you, opponent, legal)

    try:
        if len(TT) > TT_LIMIT:
            TT.clear()

        NODE_COUNT = 0
        DEADLINE = time.perf_counter() + TIME_BUDGET

        total_seeds = _house_sum(you) + _house_sum(opponent)
        if total_seeds <= 12:
            max_depth = 64
        elif total_seeds <= 20:
            max_depth = 24
        else:
            max_depth = 14

        best_move = fallback
        depth = 1

        while depth <= max_depth and time.perf_counter() < DEADLINE:
            try:
                move, _ = _root_search(you, opponent, depth, best_move)
                if you[move] > 0:
                    best_move = move
                depth += 1
            except _SearchTimeout:
                break

        if 0 <= best_move <= 5 and you[best_move] > 0:
            return best_move
        return fallback

    except Exception:
        return fallback
