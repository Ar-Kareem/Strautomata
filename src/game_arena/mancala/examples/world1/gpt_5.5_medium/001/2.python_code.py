
from time import perf_counter

INF = 10**18
WIN_SCALE = 1_000_000

EXACT = 0
LOWER = 1
UPPER = 2

_deadline = 0.0
_nodes = 0
_tt = {}


class _TimeOut(Exception):
    pass


def _sum_houses(side):
    return side[0] + side[1] + side[2] + side[3] + side[4] + side[5]


def _terminal_value(cur, opp):
    """
    Return final store difference from cur player's perspective if terminal,
    otherwise None.
    """
    cur_sum = _sum_houses(cur)
    opp_sum = _sum_houses(opp)
    if cur_sum == 0 or opp_sum == 0:
        return (cur[6] + cur_sum) - (opp[6] + opp_sum)
    return None


def _check_time():
    global _nodes
    _nodes += 1
    if (_nodes & 1023) == 0 and perf_counter() > _deadline:
        raise _TimeOut()


def _make_move(cur, opp, move):
    """
    cur is the player to move.
    Returns: child_cur, child_opp, extra_turn
    If no extra turn, orientation is swapped so child_cur is next player.
    """
    c = list(cur)
    o = list(opp)

    seeds = c[move]
    c[move] = 0
    pos = move

    while seeds:
        pos = (pos + 1) % 13

        if pos < 6:
            c[pos] += 1
        elif pos == 6:
            c[6] += 1
        else:
            o[pos - 7] += 1

        seeds -= 1

    extra = (pos == 6)

    # Capture: last seed in own empty house, opposite has seeds.
    if pos < 6 and c[pos] == 1:
        opposite = 5 - pos
        if o[opposite] > 0:
            c[6] += o[opposite] + 1
            c[pos] = 0
            o[opposite] = 0

    c = tuple(c)
    o = tuple(o)

    if extra:
        return c, o, True
    else:
        return o, c, False


def _feature_score(me, other):
    """
    Lightweight tactical features for one side.
    """
    score = 0
    advancement = 0

    for i in range(6):
        seeds = me[i]
        advancement += seeds * i

        if seeds <= 0:
            continue

        dist_to_store = 6 - i

        # Seeds that pass through the store.
        if seeds >= dist_to_store:
            score += 8 * (1 + (seeds - dist_to_store) // 13)

        landing = (i + seeds) % 13

        # Immediate extra-turn possibility.
        if landing == 6:
            score += 70

        # Approximate immediate capture potential.
        # Capture is only possible if the final pit did not receive an earlier
        # seed in this same sowing.
        if landing < 6 and seeds <= 13 and other[5 - landing] > 0:
            if landing == i or me[landing] == 0:
                score += 40 + 12 * other[5 - landing]

    score += 2 * advancement
    return score


def _evaluate(cur, opp):
    """
    Evaluation from cur player's perspective.
    Terminal positions are handled before this function is called.
    """
    cur_h = _sum_houses(cur)
    opp_h = _sum_houses(opp)

    score = 0

    # Store lead is the most important stable advantage.
    score += 1000 * (cur[6] - opp[6])

    # Seeds on our side are slightly preferable, especially when ahead.
    score += 10 * (cur_h - opp_h)

    # Tactical and positional potential.
    score += _feature_score(cur, opp)
    score -= _feature_score(opp, cur)

    # Mobility.
    cur_moves = sum(1 for i in range(6) if cur[i] > 0)
    opp_moves = sum(1 for i in range(6) if opp[i] > 0)
    score += 5 * (cur_moves - opp_moves)

    return score


def _generate_moves(cur, opp, hint=-1):
    """
    Generate legal moves with children, ordered for alpha-beta efficiency.
    """
    moves = []

    for m in range(6):
        if cur[m] <= 0:
            continue

        child_cur, child_opp, extra = _make_move(cur, opp, m)

        # Store gain from the mover's perspective.
        mover_store_after = child_cur[6] if extra else child_opp[6]
        gain = mover_store_after - cur[6]

        order = 100 * gain
        if extra:
            order += 10000

        tv = _terminal_value(child_cur, child_opp)
        if tv is not None:
            parent_tv = tv if extra else -tv
            order += parent_tv * WIN_SCALE

        if m == hint:
            order += 10**12

        # Small deterministic tie-breaker.
        order += m

        moves.append((order, m, child_cur, child_opp, extra))

    moves.sort(key=lambda x: x[0], reverse=True)
    return moves


def _negamax(cur, opp, depth, alpha, beta):
    _check_time()

    tv = _terminal_value(cur, opp)
    if tv is not None:
        return tv * WIN_SCALE

    if depth <= 0:
        return _evaluate(cur, opp)

    key = (cur, opp)
    entry = _tt.get(key)
    hint = -1

    alpha_orig = alpha
    beta_orig = beta

    if entry is not None:
        e_depth, e_value, e_flag, e_best = entry
        hint = e_best

        if e_depth >= depth:
            if e_flag == EXACT:
                return e_value
            elif e_flag == LOWER:
                alpha = max(alpha, e_value)
            elif e_flag == UPPER:
                beta = min(beta, e_value)

            if alpha >= beta:
                return e_value

    best_value = -INF
    best_move = -1

    for _, move, child_cur, child_opp, extra in _generate_moves(cur, opp, hint):
        if extra:
            value = _negamax(child_cur, child_opp, depth - 1, alpha, beta)
        else:
            value = -_negamax(child_cur, child_opp, depth - 1, -beta, -alpha)

        if value > best_value:
            best_value = value
            best_move = move

        if value > alpha:
            alpha = value

        if alpha >= beta:
            break

    if best_value <= alpha_orig:
        flag = UPPER
    elif best_value >= beta_orig:
        flag = LOWER
    else:
        flag = EXACT

    _tt[key] = (depth, best_value, flag, best_move)
    return best_value


def _search_root(cur, opp, depth, preferred):
    best_value = -INF
    best_move = preferred
    alpha = -INF
    beta = INF

    moves = _generate_moves(cur, opp, preferred)
    if not moves:
        return best_value, best_move

    best_move = moves[0][1]

    for _, move, child_cur, child_opp, extra in moves:
        if perf_counter() > _deadline:
            raise _TimeOut()

        if extra:
            value = _negamax(child_cur, child_opp, depth - 1, alpha, beta)
        else:
            value = -_negamax(child_cur, child_opp, depth - 1, -beta, -alpha)

        if value > best_value:
            best_value = value
            best_move = move

        if value > alpha:
            alpha = value

    return best_value, best_move


def _greedy_move(cur, opp):
    """
    Fast safe fallback. Always returns a legal move when one exists.
    """
    legal = [i for i in range(6) if cur[i] > 0]
    if not legal:
        return 0

    best_move = legal[0]
    best_score = -INF

    for m in legal:
        child_cur, child_opp, extra = _make_move(cur, opp, m)

        tv = _terminal_value(child_cur, child_opp)
        if tv is not None:
            score = tv * WIN_SCALE if extra else -tv * WIN_SCALE
        else:
            if extra:
                score = _evaluate(child_cur, child_opp)
            else:
                score = -_evaluate(child_cur, child_opp)

        mover_store_after = child_cur[6] if extra else child_opp[6]
        score += 200 * (mover_store_after - cur[6])
        if extra:
            score += 5000

        if score > best_score:
            best_score = score
            best_move = m

    return best_move


def policy(you: list[int], opponent: list[int]) -> int:
    """
    Return a legal move index 0..5.
    """
    global _deadline, _nodes, _tt

    cur = tuple(int(x) for x in you)
    opp = tuple(int(x) for x in opponent)

    legal = [i for i in range(6) if cur[i] > 0]
    if not legal:
        return 0

    if len(legal) == 1:
        return legal[0]

    # Strong standard opening: pit 2 gives an immediate extra turn
    # on the normal 4-seed initial board.
    if (
        cur[:6] == (4, 4, 4, 4, 4, 4)
        and opp[:6] == (4, 4, 4, 4, 4, 4)
        and cur[6] == 0
        and opp[6] == 0
    ):
        return 2

    _deadline = perf_counter() + 0.88
    _nodes = 0
    _tt = {}

    best = _greedy_move(cur, opp)

    total_houses = _sum_houses(cur) + _sum_houses(opp)
    max_depth = 60 if total_houses <= 16 else 30

    depth = 1
    try:
        while depth <= max_depth:
            if perf_counter() > _deadline:
                break

            _, move = _search_root(cur, opp, depth, best)

            if move in legal:
                best = move

            depth += 1

    except _TimeOut:
        pass
    except Exception:
        # Safety first: never fail to return a legal move.
        best = _greedy_move(cur, opp)

    if best not in legal or cur[best] <= 0:
        best = legal[0]

    return int(best)
