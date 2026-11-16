
from time import perf_counter

INF = 10**18
EXACT, LOWER, UPPER = 0, 1, 2

TT = {}
DEADLINE = 0.0
NODES = 0


class SearchTimeout(Exception):
    pass


def house_sum(a):
    return a[0] + a[1] + a[2] + a[3] + a[4] + a[5]


def final_score(you, opponent):
    return ((you[6] + house_sum(you)) - (opponent[6] + house_sum(opponent))) * 10000


def apply_move(you, opponent, move):
    y = you[:]
    o = opponent[:]

    seeds = y[move]
    y[move] = 0

    q, r = divmod(seeds, 13)

    if q:
        for i in range(6):
            y[i] += q
            o[i] += q
        y[6] += q

    for t in range(1, r + 1):
        idx = (move + t) % 13
        if idx < 7:
            y[idx] += 1
        else:
            o[idx - 7] += 1

    last = (move + seeds) % 13

    if last < 6 and y[last] == 1 and o[5 - last] > 0:
        y[6] += 1 + o[5 - last]
        y[last] = 0
        o[5 - last] = 0

    y_h = house_sum(y)
    o_h = house_sum(o)
    game_over = (y_h == 0 or o_h == 0)

    if game_over:
        if y_h:
            y[6] += y_h
            y[0] = y[1] = y[2] = y[3] = y[4] = y[5] = 0
        if o_h:
            o[6] += o_h
            o[0] = o[1] = o[2] = o[3] = o[4] = o[5] = 0

    same_turn = (last == 6)
    return y, o, same_turn, game_over


def immediate_tactics(you, opponent):
    extra_turns = 0
    best_capture = 0

    for i in range(6):
        s = you[i]
        if s <= 0:
            continue

        last = (i + s) % 13
        if last == 6:
            extra_turns += 1

        cap = 0
        if s < 13:
            if last < 6 and you[last] == 0 and opponent[5 - last] > 0:
                cap = opponent[5 - last] + 1
        elif s == 13:
            if opponent[5 - i] > 0:
                cap = opponent[5 - i] + 1

        if cap > best_capture:
            best_capture = cap

    return extra_turns, best_capture


def evaluate(you, opponent, y_h=None, o_h=None):
    if y_h is None:
        y_h = house_sum(you)
        o_h = house_sum(opponent)

    if y_h == 0 or o_h == 0:
        return final_score(you, opponent)

    store_diff = you[6] - opponent[6]
    house_diff = y_h - o_h

    pos_diff = (
        (you[0] - opponent[0])
        + 2 * (you[1] - opponent[1])
        + 3 * (you[2] - opponent[2])
        + 4 * (you[3] - opponent[3])
        + 5 * (you[4] - opponent[4])
        + 6 * (you[5] - opponent[5])
    )

    my_extra, my_cap = immediate_tactics(you, opponent)
    op_extra, op_cap = immediate_tactics(opponent, you)

    remaining = y_h + o_h
    store_w = 30 + (48 - remaining) // 3
    house_w = 2 if remaining > 12 else 3

    return (
        store_w * store_diff
        + house_w * house_diff
        + pos_diff
        + 8 * (my_extra - op_extra)
        + 4 * (my_cap - op_cap)
        + 2
    )


def static_move_score(you, opponent, move):
    s = you[move]
    last = (move + s) % 13

    score = 0

    store_gain = s // 13
    if s % 13 >= (6 - move):
        store_gain += 1
    score += 30 * store_gain

    if last == 6:
        score += 1000

    cap = 0
    if s < 13:
        if last < 6 and you[last] == 0 and opponent[5 - last] > 0:
            cap = opponent[5 - last] + 1
    elif s == 13:
        if opponent[5 - move] > 0:
            cap = opponent[5 - move] + 1

    if cap:
        score += 200 + 10 * cap

    score += move
    return score


def ordered_moves(you, opponent, tt_move=None):
    moves = [i for i in range(6) if you[i] > 0]
    moves.sort(key=lambda m: static_move_score(you, opponent, m), reverse=True)

    if tt_move in moves:
        moves.remove(tt_move)
        moves.insert(0, tt_move)

    return moves


def search(you, opponent, depth, alpha, beta):
    global NODES, DEADLINE, TT

    NODES += 1
    if (NODES & 63) == 0 and perf_counter() >= DEADLINE:
        raise SearchTimeout

    y_h = house_sum(you)
    o_h = house_sum(opponent)

    if y_h == 0 or o_h == 0:
        return final_score(you, opponent)

    if depth <= 0:
        return evaluate(you, opponent, y_h, o_h)

    key = (tuple(you), tuple(opponent))
    alpha0 = alpha
    beta0 = beta

    entry = TT.get(key)
    tt_move = None
    if entry is not None:
        e_depth, e_score, e_flag, e_move = entry
        tt_move = e_move
        if e_depth >= depth:
            if e_flag == EXACT:
                return e_score
            if e_flag == LOWER and e_score > alpha:
                alpha = e_score
            elif e_flag == UPPER and e_score < beta:
                beta = e_score
            if alpha >= beta:
                return e_score

    moves = ordered_moves(you, opponent, tt_move)
    best_score = -INF
    best_move = moves[0]

    for move in moves:
        y2, o2, same_turn, game_over = apply_move(you, opponent, move)

        if game_over:
            score = final_score(y2, o2)
        elif same_turn:
            score = search(y2, o2, depth - 1, alpha, beta)
        else:
            score = -search(o2, y2, depth - 1, -beta, -alpha)

        if score > best_score:
            best_score = score
            best_move = move

        if score > alpha:
            alpha = score
        if alpha >= beta:
            break

    if best_score <= alpha0:
        flag = UPPER
    elif best_score >= beta0:
        flag = LOWER
    else:
        flag = EXACT

    TT[key] = (depth, best_score, flag, best_move)
    return best_score


def search_root(you, opponent, depth, hint_move=None):
    global DEADLINE

    moves = ordered_moves(you, opponent, hint_move)
    best_move = moves[0]
    best_score = -INF
    alpha = -INF
    beta = INF

    for move in moves:
        if perf_counter() >= DEADLINE:
            raise SearchTimeout

        y2, o2, same_turn, game_over = apply_move(you, opponent, move)

        if game_over:
            score = final_score(y2, o2)
        elif same_turn:
            score = search(y2, o2, depth - 1, alpha, beta)
        else:
            score = -search(o2, y2, depth - 1, -beta, -alpha)

        if score > best_score:
            best_score = score
            best_move = move

        if score > alpha:
            alpha = score

    return best_move, best_score


def policy(you: list[int], opponent: list[int]) -> int:
    legal = [i for i in range(6) if you[i] > 0]
    if len(legal) == 1:
        return legal[0]

    fallback = max(legal, key=lambda m: static_move_score(you, opponent, m))

    try:
        global DEADLINE, NODES, TT

        if len(TT) > 200000:
            TT.clear()

        start = perf_counter()
        DEADLINE = start + 0.94
        NODES = 0

        best_move = fallback
        best_score = None

        root_entry = TT.get((tuple(you), tuple(opponent)))
        hint = root_entry[3] if root_entry is not None else None

        depth = 1
        while True:
            if perf_counter() >= DEADLINE:
                break
            move, score = search_root(you, opponent, depth, hint if hint is not None else best_move)
            best_move = move
            best_score = score
            hint = move
            depth += 1

            if best_score is not None and abs(best_score) >= 400000:
                break

        return best_move

    except SearchTimeout:
        return best_move if 'best_move' in locals() and best_move in legal else fallback
    except Exception:
        return fallback
