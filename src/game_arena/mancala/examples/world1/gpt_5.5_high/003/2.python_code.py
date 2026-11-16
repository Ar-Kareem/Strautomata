
import time

INF = 10 ** 12
WIN_BASE = 10 ** 9
WIN_MULT = 10000

EXACT = 0
LOWER = 1
UPPER = 2

CYCLE0 = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12)
CYCLE1 = (7, 8, 9, 10, 11, 12, 13, 0, 1, 2, 3, 4, 5)

TT = {}
DEADLINE = 0.0
NODES = 0


class SearchTimeout(Exception):
    pass


def terminal_value(s):
    my_h = s[0] + s[1] + s[2] + s[3] + s[4] + s[5]
    op_h = s[7] + s[8] + s[9] + s[10] + s[11] + s[12]

    if my_h == 0 or op_h == 0:
        diff = (s[6] + my_h) - (s[13] + op_h)
        if diff > 0:
            return WIN_BASE + diff * WIN_MULT
        if diff < 0:
            return -WIN_BASE + diff * WIN_MULT
        return 0
    return None


def make_move(s, side, move):
    b = list(s)

    if side == 0:
        pos = move
        seeds = b[pos]
        b[pos] = 0

        q, rem = divmod(seeds, 13)

        if q:
            for p in CYCLE0:
                b[p] += q

        if rem:
            for k in range(1, rem + 1):
                b[CYCLE0[(move + k) % 13]] += 1

        last = CYCLE0[(move + seeds) % 13]
        next_side = 0 if last == 6 else 1

        if 0 <= last <= 5 and b[last] == 1:
            opp = 7 + (5 - last)
            captured = b[opp]
            if captured:
                b[6] += captured + 1
                b[last] = 0
                b[opp] = 0

    else:
        pos = 7 + move
        seeds = b[pos]
        b[pos] = 0

        q, rem = divmod(seeds, 13)

        if q:
            for p in CYCLE1:
                b[p] += q

        if rem:
            for k in range(1, rem + 1):
                b[CYCLE1[(move + k) % 13]] += 1

        last = CYCLE1[(move + seeds) % 13]
        next_side = 1 if last == 13 else 0

        if 7 <= last <= 12 and b[last] == 1:
            pit = last - 7
            opp = 5 - pit
            captured = b[opp]
            if captured:
                b[13] += captured + 1
                b[last] = 0
                b[opp] = 0

    my_h = b[0] + b[1] + b[2] + b[3] + b[4] + b[5]
    op_h = b[7] + b[8] + b[9] + b[10] + b[11] + b[12]

    if my_h == 0 or op_h == 0:
        b[6] += my_h
        b[13] += op_h
        b[0] = b[1] = b[2] = b[3] = b[4] = b[5] = 0
        b[7] = b[8] = b[9] = b[10] = b[11] = b[12] = 0

    return tuple(b), next_side


def capture_gain(s, side, move):
    if side == 0:
        seeds = s[move]
    else:
        seeds = s[7 + move]

    q, rem = divmod(seeds, 13)
    last = (move + seeds) % 13

    if last > 5:
        return 0

    if side == 0:
        final_count = (0 if last == move else s[last]) + q + (1 if rem else 0)
        if final_count == 1:
            opp = s[7 + (5 - last)]
            if opp:
                return opp + 1
    else:
        final_count = (0 if last == move else s[7 + last]) + q + (1 if rem else 0)
        if final_count == 1:
            opp = s[5 - last]
            if opp:
                return opp + 1

    return 0


def move_tactical_score(s, side, move):
    seeds = s[move] if side == 0 else s[7 + move]
    q, rem = divmod(seeds, 13)

    dist_to_store = 6 - move
    store_gain = q + (1 if rem >= dist_to_store else 0)

    last = (move + seeds) % 13
    extra = 1 if last == 6 else 0
    cap = capture_gain(s, side, move)

    return extra * 100000 + cap * 2000 + store_gain * 200 + seeds + move


def immediate_features(s, side):
    extra_count = 0
    best_cap = 0
    best_store = 0
    mobility = 0

    if side == 0:
        for m in range(6):
            seeds = s[m]
            if seeds <= 0:
                continue

            mobility += 1
            q, rem = divmod(seeds, 13)

            dist_to_store = 6 - m
            store_gain = q + (1 if rem >= dist_to_store else 0)
            if store_gain > best_store:
                best_store = store_gain

            last = (m + seeds) % 13
            if last == 6:
                extra_count += 1
            elif last < 6:
                final_count = (0 if last == m else s[last]) + q + (1 if rem else 0)
                if final_count == 1:
                    opp = s[7 + (5 - last)]
                    if opp:
                        cap = opp + 1
                        if cap > best_cap:
                            best_cap = cap

    else:
        for m in range(6):
            seeds = s[7 + m]
            if seeds <= 0:
                continue

            mobility += 1
            q, rem = divmod(seeds, 13)

            dist_to_store = 6 - m
            store_gain = q + (1 if rem >= dist_to_store else 0)
            if store_gain > best_store:
                best_store = store_gain

            last = (m + seeds) % 13
            if last == 6:
                extra_count += 1
            elif last < 6:
                final_count = (0 if last == m else s[7 + last]) + q + (1 if rem else 0)
                if final_count == 1:
                    opp = s[5 - last]
                    if opp:
                        cap = opp + 1
                        if cap > best_cap:
                            best_cap = cap

    return extra_count, best_cap, best_store, mobility


def heuristic(s, side):
    tv = terminal_value(s)
    if tv is not None:
        return tv

    my_h = s[0] + s[1] + s[2] + s[3] + s[4] + s[5]
    op_h = s[7] + s[8] + s[9] + s[10] + s[11] + s[12]

    store_diff = s[6] - s[13]

    my_pos = (
        s[0] * 1 + s[1] * 2 + s[2] * 3 +
        s[3] * 4 + s[4] * 5 + s[5] * 6
    )
    op_pos = (
        s[7] * 1 + s[8] * 2 + s[9] * 3 +
        s[10] * 4 + s[11] * 5 + s[12] * 6
    )

    my_extra, my_cap, my_store, my_mob = immediate_features(s, 0)
    op_extra, op_cap, op_store, op_mob = immediate_features(s, 1)

    score = 0
    score += store_diff * 140
    score += (my_h - op_h) * 3
    score += (my_pos - op_pos) * 2

    score += (my_extra - op_extra) * 35
    score += (my_cap - op_cap) * 12
    score += (my_store - op_store) * 10
    score += (my_mob - op_mob) * 2

    score += 6 if side == 0 else -6

    return score


def ordered_moves(s, side, tt_move=-1):
    moves = []

    if side == 0:
        for m in range(6):
            if s[m] > 0:
                sc = move_tactical_score(s, side, m)
                if m == tt_move:
                    sc += 10000000
                moves.append((sc, m))
    else:
        for m in range(6):
            if s[7 + m] > 0:
                sc = move_tactical_score(s, side, m)
                if m == tt_move:
                    sc += 10000000
                moves.append((sc, m))

    moves.sort(reverse=True)
    return moves


def search(s, side, depth, alpha, beta):
    global NODES

    NODES += 1
    if (NODES & 2047) == 0 and time.perf_counter() >= DEADLINE:
        raise SearchTimeout()

    tv = terminal_value(s)
    if tv is not None:
        if tv > 0:
            return tv + depth
        if tv < 0:
            return tv - depth
        return 0

    if depth <= 0:
        return heuristic(s, side)

    key = (s, side)
    entry = TT.get(key)
    tt_move = -1

    alpha_orig = alpha
    beta_orig = beta

    if entry is not None:
        ent_depth, ent_value, ent_flag, ent_move = entry
        tt_move = ent_move

        if ent_depth >= depth:
            if ent_flag == EXACT:
                return ent_value
            elif ent_flag == LOWER:
                if ent_value > alpha:
                    alpha = ent_value
            elif ent_flag == UPPER:
                if ent_value < beta:
                    beta = ent_value

            if alpha >= beta:
                return ent_value

    best_move = -1

    if side == 0:
        best = -INF

        for _, m in ordered_moves(s, side, tt_move):
            child, ns = make_move(s, side, m)
            nd = depth if ns == side else depth - 1

            val = search(child, ns, nd, alpha, beta)

            if val > best:
                best = val
                best_move = m

            if best > alpha:
                alpha = best

            if alpha >= beta:
                break

    else:
        best = INF

        for _, m in ordered_moves(s, side, tt_move):
            child, ns = make_move(s, side, m)
            nd = depth if ns == side else depth - 1

            val = search(child, ns, nd, alpha, beta)

            if val < best:
                best = val
                best_move = m

            if best < beta:
                beta = best

            if alpha >= beta:
                break

    if best_move == -1:
        return heuristic(s, side)

    if best <= alpha_orig:
        flag = UPPER
    elif best >= beta_orig:
        flag = LOWER
    else:
        flag = EXACT

    TT[key] = (depth, best, flag, best_move)
    return best


def root_order(s, previous_scores):
    moves = []

    for m in range(6):
        if s[m] > 0:
            tact = move_tactical_score(s, 0, m)
            if previous_scores:
                moves.append((previous_scores.get(m, -INF), tact, m))
            else:
                moves.append((tact, m))

    moves.sort(reverse=True)
    return [x[-1] for x in moves]


def root_search(s, depth, previous_scores):
    moves = root_order(s, previous_scores)

    best_move = moves[0]
    best_val = -INF
    alpha = -INF
    beta = INF
    scores = {}

    for m in moves:
        if time.perf_counter() >= DEADLINE:
            raise SearchTimeout()

        child, ns = make_move(s, 0, m)
        nd = depth if ns == 0 else depth - 1

        val = search(child, ns, nd, alpha, beta)
        scores[m] = val

        if val > best_val:
            best_val = val
            best_move = m

        if best_val > alpha:
            alpha = best_val

    return best_val, best_move, scores


def choose_fallback(s, legal):
    best = legal[0]
    best_val = -INF

    for m in legal:
        child, ns = make_move(s, 0, m)
        val = heuristic(child, ns) + move_tactical_score(s, 0, m) // 100

        if val > best_val:
            best_val = val
            best = m

    return best


def policy(you: list[int], opponent: list[int]) -> int:
    global DEADLINE, NODES

    legal = [i for i in range(6) if you[i] > 0]
    if not legal:
        return 0
    if len(legal) == 1:
        return int(legal[0])

    try:
        s = (
            int(you[0]), int(you[1]), int(you[2]),
            int(you[3]), int(you[4]), int(you[5]), int(you[6]),
            int(opponent[0]), int(opponent[1]), int(opponent[2]),
            int(opponent[3]), int(opponent[4]), int(opponent[5]),
            int(opponent[6])
        )

        # Strong standard opening: pit 2 gives an immediate extra move.
        if s == (4, 4, 4, 4, 4, 4, 0, 4, 4, 4, 4, 4, 4, 0):
            return 2

        if len(TT) > 250000:
            TT.clear()

        fallback = choose_fallback(s, legal)
        best_move = fallback
        previous_scores = {}

        house_total = (
            s[0] + s[1] + s[2] + s[3] + s[4] + s[5] +
            s[7] + s[8] + s[9] + s[10] + s[11] + s[12]
        )

        if house_total <= 14:
            max_depth = 64
        elif house_total <= 24:
            max_depth = 28
        else:
            max_depth = 16

        DEADLINE = time.perf_counter() + 0.86

        for depth in range(1, max_depth + 1):
            NODES = 0
            try:
                _, move, scores = root_search(s, depth, previous_scores)
                if 0 <= move <= 5 and s[move] > 0:
                    best_move = move
                    previous_scores = scores
            except SearchTimeout:
                break

            if time.perf_counter() >= DEADLINE:
                break

        if 0 <= best_move <= 5 and you[best_move] > 0:
            return int(best_move)

    except Exception:
        pass

    for i in range(6):
        if you[i] > 0:
            return int(i)

    return 0
