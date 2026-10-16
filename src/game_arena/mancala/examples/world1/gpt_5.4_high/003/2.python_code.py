
import sys
from time import perf_counter

sys.setrecursionlimit(10000)

INF = 10**18
FINAL_SCALE = 100
ENDGAME_SEEDS = 12

EXACT = 0
LOWER = 1
UPPER = 2

TT = {}
EG_TT = {}

DEADLINE = 0.0
NODES = 0


class SearchTimeout(Exception):
    pass


def empty_side(x):
    return (x[0] | x[1] | x[2] | x[3] | x[4] | x[5]) == 0


def house_sum(x):
    return x[0] + x[1] + x[2] + x[3] + x[4] + x[5]


def terminal_score(a, b):
    # Returns scaled final score from the current player's perspective
    # if the game is over or one side is already empty; otherwise None.
    if empty_side(a):
        return (a[6] - (b[6] + house_sum(b))) * FINAL_SCALE
    if empty_side(b):
        return ((a[6] + house_sum(a)) - b[6]) * FINAL_SCALE
    return None


def time_check():
    global NODES
    NODES += 1
    if (NODES & 511) == 0 and perf_counter() >= DEADLINE:
        raise SearchTimeout


def apply_move(you, opp, move):
    # Returns (new_you, new_opp, same_turn, terminal)
    a = you[:]
    b = opp[:]

    seeds = a[move]
    a[move] = 0
    pos = move  # flat ring positions: 0..5 houses, 6 store, 7..12 opp houses

    while seeds:
        pos += 1
        if pos == 13:
            pos = 0
        if pos < 7:
            a[pos] += 1
        else:
            b[pos - 7] += 1
        seeds -= 1

    same_turn = (pos == 6)

    # Capture
    if pos < 6 and a[pos] == 1:
        opp_idx = 5 - pos
        if b[opp_idx] > 0:
            a[6] += 1 + b[opp_idx]
            a[pos] = 0
            b[opp_idx] = 0

    # End of game sweep
    if empty_side(a) or empty_side(b):
        sa = house_sum(a)
        sb = house_sum(b)
        if sa:
            a[6] += sa
            a[0] = a[1] = a[2] = a[3] = a[4] = a[5] = 0
        if sb:
            b[6] += sb
            b[0] = b[1] = b[2] = b[3] = b[4] = b[5] = 0
        same_turn = False
        return a, b, same_turn, True

    return a, b, same_turn, False


def side_tactics(side, opp):
    # Fast tactical summary used by evaluation.
    mobility = 0
    extra_count = 0
    best_move_value = 0

    for i in range(6):
        s = side[i]
        if s <= 0:
            continue

        mobility += 1
        q, r = divmod(s, 13)
        last = (i + s) % 13

        # Seeds gained immediately into store from sowing
        store_gain = q
        if r and r >= (6 - i):
            store_gain += 1

        extra = 1 if last == 6 else 0
        if extra:
            extra_count += 1

        capture = 0
        if last < 6:
            base = 0 if last == i else side[last]
            earlier = q if r else q - 1
            if base + earlier == 0:
                opp_seeds = opp[5 - last]
                if opp_seeds > 0:
                    capture = opp_seeds + 1

        move_value = 4 * store_gain + 12 * extra + 3 * capture
        if move_value > best_move_value:
            best_move_value = move_value

    return mobility, extra_count, best_move_value


def evaluate(a, b):
    # Heuristic score from current player's perspective, scaled similarly
    # to terminal scores but smaller.
    sa = house_sum(a)
    sb = house_sum(b)
    remaining = sa + sb

    store_diff = a[6] - b[6]
    pos_diff = (
        a[0] + 2 * a[1] + 3 * a[2] + 4 * a[3] + 5 * a[4] + 6 * a[5]
        - (b[0] + 2 * b[1] + 3 * b[2] + 4 * b[3] + 5 * b[4] + 6 * b[5])
    )

    ma, ea, ba = side_tactics(a, b)
    mb, eb, bb = side_tactics(b, a)

    if remaining > 24:
        store_w = 100
        house_w = 5
    elif remaining > 12:
        store_w = 110
        house_w = 4
    else:
        store_w = 120
        house_w = 3

    score = 0
    score += store_w * store_diff
    score += house_w * (sa - sb)
    score += pos_diff // 2
    score += 4 * (ma - mb)
    score += 15 * (ea - eb)
    score += 3 * (ba - bb)
    return score


def ordered_children(a, b, preferred_move=None):
    base_diff = a[6] - b[6]
    children = []

    for move in range(6):
        if a[move] <= 0:
            continue
        na, nb, same_turn, term = apply_move(a, b, move)

        h = 0
        if move == preferred_move:
            h += 10000

        delta_diff = (na[6] - nb[6]) - base_diff
        h += 60 * delta_diff

        if same_turn:
            h += 300

        if term:
            h += terminal_score(na, nb) // 10

        children.append((h, move, na, nb, same_turn, term))

    children.sort(key=lambda x: x[0], reverse=True)
    return children


def exact_search(a, b, alpha, beta):
    time_check()

    t = terminal_score(a, b)
    if t is not None:
        return t

    key = tuple(a) + tuple(b)
    cached = EG_TT.get(key)
    if cached is not None:
        return cached

    tt_entry = TT.get(key)
    preferred = tt_entry[3] if tt_entry is not None else None
    children = ordered_children(a, b, preferred)

    best = -INF
    for _, move, na, nb, same_turn, term in children:
        if term:
            val = terminal_score(na, nb)
        elif same_turn:
            val = exact_search(na, nb, alpha, beta)
        else:
            val = -exact_search(nb, na, -beta, -alpha)

        if val > best:
            best = val
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break

    EG_TT[key] = best
    return best


def negamax(a, b, depth, alpha, beta):
    time_check()

    t = terminal_score(a, b)
    if t is not None:
        return t

    remaining = house_sum(a) + house_sum(b)
    if remaining <= ENDGAME_SEEDS:
        return exact_search(a, b, alpha, beta)

    if depth <= 0:
        return evaluate(a, b)

    key = tuple(a) + tuple(b)
    tt_entry = TT.get(key)
    tt_move = None
    alpha_orig = alpha
    beta_orig = beta

    if tt_entry is not None:
        tt_depth, tt_value, tt_flag, tt_move = tt_entry
        if tt_depth >= depth:
            if tt_flag == EXACT:
                return tt_value
            if tt_flag == LOWER:
                if tt_value > alpha:
                    alpha = tt_value
            elif tt_flag == UPPER:
                if tt_value < beta:
                    beta = tt_value
            if alpha >= beta:
                return tt_value

    children = ordered_children(a, b, tt_move)
    best = -INF
    best_move = children[0][1]

    for _, move, na, nb, same_turn, term in children:
        if term:
            val = terminal_score(na, nb)
        elif same_turn:
            val = negamax(na, nb, depth, alpha, beta)
        else:
            val = -negamax(nb, na, depth - 1, -beta, -alpha)

        if val > best:
            best = val
            best_move = move

        if val > alpha:
            alpha = val
        if alpha >= beta:
            break

    if best <= alpha_orig:
        flag = UPPER
    elif best >= beta_orig:
        flag = LOWER
    else:
        flag = EXACT

    TT[key] = (depth, best, flag, best_move)
    return best


def search_root(a, b, depth, guess=None):
    time_check()

    key = tuple(a) + tuple(b)
    preferred = guess
    if preferred is None:
        tt_entry = TT.get(key)
        if tt_entry is not None:
            preferred = tt_entry[3]

    children = ordered_children(a, b, preferred)
    best_move = children[0][1]
    best_val = -INF
    alpha = -INF
    beta = INF

    for _, move, na, nb, same_turn, term in children:
        if term:
            val = terminal_score(na, nb)
        elif same_turn:
            val = negamax(na, nb, depth, alpha, beta)
        else:
            val = -negamax(nb, na, depth - 1, -beta, -alpha)

        if val > best_val:
            best_val = val
            best_move = move

        if val > alpha:
            alpha = val

    TT[key] = (depth, best_val, EXACT, best_move)
    return best_val, best_move


def fallback_move(a, b):
    children = ordered_children(a, b, None)
    return children[0][1]


def policy(you: list[int], opponent: list[int]) -> int:
    legal = [i for i in range(6) if you[i] > 0]
    if not legal:
        return 0
    if len(legal) == 1:
        return legal[0]

    # Tiny opening book for the standard start.
    if you == [4, 4, 4, 4, 4, 4, 0] and opponent == [4, 4, 4, 4, 4, 4, 0]:
        return 2

    try:
        global DEADLINE, NODES

        if len(TT) > 250000:
            TT.clear()
        if len(EG_TT) > 150000:
            EG_TT.clear()

        a = list(you)
        b = list(opponent)

        best_move = fallback_move(a, b)
        guess = best_move

        DEADLINE = perf_counter() + 0.92
        NODES = 0

        depth = 1
        while depth <= 20:
            score, move = search_root(a, b, depth, guess)
            best_move = move
            guess = move
            depth += 1
            if perf_counter() >= DEADLINE:
                break

        if 0 <= best_move <= 5 and you[best_move] > 0:
            return best_move
        return legal[0]

    except Exception:
        # Always return a legal move.
        return legal[0]
