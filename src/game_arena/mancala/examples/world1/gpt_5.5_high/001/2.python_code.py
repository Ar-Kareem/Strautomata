
import time

INF = 10 ** 30
TERMINAL_SCALE = 1_000_000

FLAG_EXACT = 0
FLAG_LOWER = 1
FLAG_UPPER = 2

_TT = {}
_MAX_TT_SIZE = 350_000

_START = 0.0
_DEADLINE = 0.0
_NODES = 0


class _Timeout(Exception):
    pass


def policy(you: list[int], opponent: list[int]) -> int:
    """
    Return a legal Kalah move index 0..5.
    """
    legal = [i for i in range(6) if you[i] > 0]
    if not legal:
        return 0
    if len(legal) == 1:
        return legal[0]

    me = tuple(int(x) for x in you)
    opp = tuple(int(x) for x in opponent)

    global _START, _DEADLINE, _NODES

    # Keep memory bounded across repeated calls.
    if len(_TT) > _MAX_TT_SIZE:
        _TT.clear()

    _START = time.perf_counter()
    _DEADLINE = _START + 0.88
    _NODES = 0

    best_move = legal[0]

    try:
        best_move = _fallback_move(me, opp)

        preferred = best_move
        depth = 1

        # Iterative deepening.  Depth counts opponent turn transitions;
        # extra moves are searched without consuming depth.
        while depth <= 64:
            if time.perf_counter() >= _DEADLINE:
                break

            move, _value = _root_search(me, opp, depth, preferred)
            best_move = move
            preferred = move
            depth += 1

    except _Timeout:
        pass
    except Exception:
        # Absolute safety: never fail to return a legal move.
        best_move = legal[0]

    if best_move not in legal or you[best_move] <= 0:
        return legal[0]
    return int(best_move)


def _check_time() -> None:
    global _NODES
    _NODES += 1
    if (_NODES & 511) == 0:
        if time.perf_counter() >= _DEADLINE:
            raise _Timeout()


def _root_search(me, opp, depth, preferred):
    alpha = -INF
    beta = INF

    moves = _ordered_moves(me, opp, preferred)
    best_move = moves[0]
    best_val = -INF

    for move in moves:
        _check_time()
        nme, nopp, extra, terminal = _apply_move(me, opp, move)

        if terminal:
            val = _terminal_value(nme, nopp)
        elif extra:
            val = _search(nme, nopp, depth, alpha, beta)
        else:
            val = -_search(nopp, nme, depth - 1, -beta, -alpha)

        if val > best_val:
            best_val = val
            best_move = move

        if val > alpha:
            alpha = val

    return best_move, best_val


def _search(me, opp, depth, alpha, beta):
    _check_time()

    my_sum = me[0] + me[1] + me[2] + me[3] + me[4] + me[5]
    op_sum = opp[0] + opp[1] + opp[2] + opp[3] + opp[4] + opp[5]

    if my_sum == 0 or op_sum == 0:
        return _terminal_from_state(me, opp, my_sum, op_sum)

    if depth <= 0:
        return _evaluate(me, opp)

    alpha_orig = alpha
    beta_orig = beta

    key = (me, opp)
    entry = _TT.get(key)
    preferred = -1

    if entry is not None:
        ent_depth, flag, ent_val, ent_move = entry
        preferred = ent_move

        if ent_depth >= depth:
            if flag == FLAG_EXACT:
                return ent_val
            if flag == FLAG_LOWER:
                if ent_val > alpha:
                    alpha = ent_val
            elif flag == FLAG_UPPER:
                if ent_val < beta:
                    beta = ent_val

            if alpha >= beta:
                return ent_val

    moves = _ordered_moves(me, opp, preferred)
    if not moves:
        return _terminal_from_state(me, opp, my_sum, op_sum)

    best_val = -INF
    best_move = moves[0]

    for move in moves:
        nme, nopp, extra, terminal = _apply_move(me, opp, move)

        if terminal:
            val = _terminal_value(nme, nopp)
        elif extra:
            # Same player moves again, so no negation and no depth loss.
            val = _search(nme, nopp, depth, alpha, beta)
        else:
            val = -_search(nopp, nme, depth - 1, -beta, -alpha)

        if val > best_val:
            best_val = val
            best_move = move

        if val > alpha:
            alpha = val

        if alpha >= beta:
            break

    if best_val <= alpha_orig:
        flag = FLAG_UPPER
    elif best_val >= beta_orig:
        flag = FLAG_LOWER
    else:
        flag = FLAG_EXACT

    _TT[key] = (depth, flag, best_val, best_move)
    return best_val


def _apply_move(me, opp, move):
    """
    Apply a move from the current player's perspective.

    Returns:
        new_me, new_opp, extra_turn, terminal
    """
    seeds = me[move]

    board = [
        me[0], me[1], me[2], me[3], me[4], me[5], me[6],
        opp[0], opp[1], opp[2], opp[3], opp[4], opp[5],
    ]

    board[move] = 0

    q, r = divmod(seeds, 13)

    if q:
        for i in range(13):
            board[i] += q

    for step in range(1, r + 1):
        board[(move + step) % 13] += 1

    last = (move + seeds) % 13

    # Capture.
    if 0 <= last <= 5 and board[last] == 1:
        opp_index = 12 - last
        captured = board[opp_index]
        if captured > 0:
            board[6] += captured + 1
            board[last] = 0
            board[opp_index] = 0

    my_sum = board[0] + board[1] + board[2] + board[3] + board[4] + board[5]
    op_sum = board[7] + board[8] + board[9] + board[10] + board[11] + board[12]

    opp_store = opp[6]
    terminal = (my_sum == 0 or op_sum == 0)

    if terminal:
        if my_sum:
            board[6] += my_sum
            board[0] = board[1] = board[2] = board[3] = board[4] = board[5] = 0

        if op_sum:
            opp_store += op_sum
            board[7] = board[8] = board[9] = board[10] = board[11] = board[12] = 0

    extra = (last == 6 and not terminal)

    new_me = (board[0], board[1], board[2], board[3], board[4], board[5], board[6])
    new_opp = (board[7], board[8], board[9], board[10], board[11], board[12], opp_store)

    return new_me, new_opp, extra, terminal


def _terminal_value(me, opp):
    return (me[6] - opp[6]) * TERMINAL_SCALE


def _terminal_from_state(me, opp, my_sum=None, op_sum=None):
    if my_sum is None:
        my_sum = me[0] + me[1] + me[2] + me[3] + me[4] + me[5]
    if op_sum is None:
        op_sum = opp[0] + opp[1] + opp[2] + opp[3] + opp[4] + opp[5]

    my_store = me[6]
    op_store = opp[6]

    if my_sum == 0:
        op_store += op_sum
    if op_sum == 0:
        my_store += my_sum

    return (my_store - op_store) * TERMINAL_SCALE


def _ordered_moves(me, opp, preferred=-1):
    scored = []
    for move in range(6):
        if me[move] > 0:
            score = _quick_move_score(me, opp, move)
            if move == preferred:
                score += 10 ** 12
            scored.append((score, move))

    scored.sort(reverse=True)
    return [move for _score, move in scored]


def _quick_move_score(me, opp, move):
    seeds = me[move]
    last = (move + seeds) % 13

    store_gain = _store_gain_for_move(me, move)
    capture_gain = _capture_amount_for_move(me, opp, move)

    score = 0
    score += store_gain * 350
    score += capture_gain * 850

    if last == 6:
        score += 12_000

    # Slight preference for moves nearer the store when all else is equal.
    score += move * 3

    return score


def _store_gain_for_move(side, move):
    seeds = side[move]
    q, r = divmod(seeds, 13)

    # Own store is board position 6; distance from house move to store.
    dist = 6 - move
    return q + (1 if r >= dist else 0)


def _capture_amount_for_move(side, other, move):
    seeds = side[move]
    q, r = divmod(seeds, 13)
    last = (move + seeds) % 13

    if last > 5:
        return 0

    # Final count in the landing house.
    base = 0 if last == move else side[last]
    final_count = base + q + (1 if r else 0)

    if final_count != 1:
        return 0

    opp_house = 5 - last
    opp_board_pos = 7 + opp_house

    added_to_opp = q
    if r:
        dist = opp_board_pos - move
        if dist <= 0:
            dist += 13
        if dist <= r:
            added_to_opp += 1

    opposite_count = other[opp_house] + added_to_opp
    if opposite_count <= 0:
        return 0

    return opposite_count + 1


def _evaluate(me, opp):
    my_sum = me[0] + me[1] + me[2] + me[3] + me[4] + me[5]
    op_sum = opp[0] + opp[1] + opp[2] + opp[3] + opp[4] + opp[5]

    if my_sum == 0 or op_sum == 0:
        return _terminal_from_state(me, opp, my_sum, op_sum)

    store_diff = me[6] - opp[6]
    house_diff = my_sum - op_sum

    # Banked seeds are most important, but house seeds, mobility, captures,
    # and extra turns all matter before the endgame.
    val = 1000 * store_diff
    val += 28 * house_diff

    # Positional value: seeds closer to own store are generally more flexible.
    my_pos = (
        0 * me[0] + 1 * me[1] + 2 * me[2] +
        3 * me[3] + 4 * me[4] + 5 * me[5]
    )
    op_pos = (
        0 * opp[0] + 1 * opp[1] + 2 * opp[2] +
        3 * opp[3] + 4 * opp[4] + 5 * opp[5]
    )
    val += 5 * (my_pos - op_pos)

    my_best_gain, my_cap_total, my_extras, my_mobility = _side_features(me, opp)
    op_best_gain, op_cap_total, op_extras, op_mobility = _side_features(opp, me)

    val += 60 * (my_best_gain - op_best_gain)
    val += 25 * (my_cap_total - op_cap_total)
    val += 90 * (my_extras - op_extras)
    val += 8 * (my_mobility - op_mobility)

    # Latent capture potential.
    my_capture_potential = 0
    op_capture_potential = 0
    for i in range(6):
        if me[i] == 0:
            my_capture_potential += opp[5 - i]
        if opp[i] == 0:
            op_capture_potential += me[5 - i]

    val += 7 * (my_capture_potential - op_capture_potential)

    return val


def _side_features(side, other):
    best_gain = 0
    capture_total = 0
    extra_count = 0
    mobility = 0

    for move in range(6):
        if side[move] <= 0:
            continue

        mobility += 1

        store_gain = _store_gain_for_move(side, move)
        cap_gain = _capture_amount_for_move(side, other, move)
        total_gain = store_gain + cap_gain

        if total_gain > best_gain:
            best_gain = total_gain

        capture_total += cap_gain

        if (move + side[move]) % 13 == 6:
            extra_count += 1

    return best_gain, capture_total, extra_count, mobility


def _fallback_move(me, opp):
    moves = _ordered_moves(me, opp)
    best_move = moves[0]
    best_val = -INF

    for move in moves:
        nme, nopp, extra, terminal = _apply_move(me, opp, move)

        if terminal:
            val = _terminal_value(nme, nopp)
        elif extra:
            val = _evaluate(nme, nopp) + 100
        else:
            val = -_evaluate(nopp, nme)

        if val > best_val:
            best_val = val
            best_move = move

    return best_move
