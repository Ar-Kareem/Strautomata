
from time import perf_counter

# Transposition-table flags
_EXACT = 0
_LOWER = 1
_UPPER = 2

_INF = float("inf")
_TT = {}
_DEADLINE = 0.0
_NODES = 0


class _SearchTimeout(Exception):
    pass


def _swap(state):
    """Change from the current player's perspective to the other player's."""
    return state[7:14] + state[0:7]


def _win_value(difference, total_seeds):
    """Terminal utility that makes every win preferable to any heuristic leaf."""
    if difference > 0:
        return (total_seeds + 1) * 1000 + difference
    if difference < 0:
        return -(total_seeds + 1) * 1000 + difference
    return 0


def _terminal_value(state):
    return _win_value(state[6] - state[13], sum(state))


def _play(state, move):
    """
    Apply a move while retaining the moving player's perspective.

    Returns:
        child_state, extra_turn, terminal
    """
    own = list(state[:7])
    other = list(state[7:14])

    seeds = own[move]
    own[move] = 0

    # The sowing ring contains 13 locations:
    # own houses, own store, and opponent houses.
    rounds, remainder = divmod(seeds, 13)

    if rounds:
        own[0] += rounds
        own[1] += rounds
        own[2] += rounds
        own[3] += rounds
        own[4] += rounds
        own[5] += rounds
        own[6] += rounds

        other[0] += rounds
        other[1] += rounds
        other[2] += rounds
        other[3] += rounds
        other[4] += rounds
        other[5] += rounds

    for step in range(1, remainder + 1):
        position = (move + step) % 13
        if position <= 6:
            own[position] += 1
        else:
            other[position - 7] += 1

    last = (move + seeds) % 13

    # Capture after all sowing has finished.
    if 0 <= last < 6 and own[last] == 1:
        opposite = 5 - last
        if other[opposite] > 0:
            own[6] += 1 + other[opposite]
            own[last] = 0
            other[opposite] = 0

    own_house_sum = (
        own[0] + own[1] + own[2] +
        own[3] + own[4] + own[5]
    )
    other_house_sum = (
        other[0] + other[1] + other[2] +
        other[3] + other[4] + other[5]
    )

    terminal = own_house_sum == 0 or other_house_sum == 0

    if terminal:
        own[6] += own_house_sum
        other[6] += other_house_sum
        own[0] = own[1] = own[2] = 0
        own[3] = own[4] = own[5] = 0
        other[0] = other[1] = other[2] = 0
        other[3] = other[4] = other[5] = 0
        extra_turn = False
    else:
        extra_turn = last == 6

    return tuple(own + other), extra_turn, terminal


def _tactical_features(houses, opposing_houses):
    """
    Estimate the largest immediate store gain and number of bonus-turn moves
    without allocating successor positions.
    """
    best_gain = 0
    bonus_moves = 0

    for move in range(6):
        seeds = houses[move]
        if seeds <= 0:
            continue

        rounds, remainder = divmod(seeds, 13)
        gain = rounds

        # Does the partial lap pass through the store?
        if remainder >= 6 - move:
            gain += 1

        last = (move + seeds) % 13

        if last == 6:
            bonus_moves += 1

        # Determine whether this move makes a capture.
        if 0 <= last < 6:
            landing_count = (0 if last == move else houses[last]) + rounds
            if remainder:
                landing_count += 1

            if landing_count == 1:
                opposite = 5 - last
                opposite_count = opposing_houses[opposite] + rounds
                distance = (7 + opposite - move) % 13
                if distance <= remainder:
                    opposite_count += 1

                if opposite_count > 0:
                    gain += 1 + opposite_count

        if gain > best_gain:
            best_gain = gain

    return best_gain, bonus_moves


def _evaluate(state):
    """Heuristic value from the player-to-move's perspective."""
    own = state[:6]
    other = state[7:13]

    own_sum = sum(own)
    other_sum = sum(other)

    own_mobility = sum(1 for x in own if x > 0)
    other_mobility = sum(1 for x in other if x > 0)

    own_position = (
        own[1] + 2 * own[2] + 3 * own[3] +
        4 * own[4] + 5 * own[5]
    )
    other_position = (
        other[1] + 2 * other[2] + 3 * other[3] +
        4 * other[4] + 5 * other[5]
    )

    own_gain, own_bonus = _tactical_features(own, other)
    other_gain, other_bonus = _tactical_features(other, own)

    return (
        120 * (state[6] - state[13])
        + 3 * (own_sum - other_sum)
        + (own_position - other_position)
        + 8 * (own_mobility - other_mobility)
        + 24 * own_gain
        - 9 * other_gain
        + 14 * own_bonus
        - 6 * other_bonus
    )


def _ordered_children(state, tt_move):
    children = []

    for move in range(6):
        if state[move] <= 0:
            continue

        child, extra, terminal = _play(state, move)
        store_gain = child[6] - state[6]

        priority = 100 * store_gain + move

        if extra:
            priority += 100000

        terminal_score = None
        if terminal:
            terminal_score = _terminal_value(child)
            if terminal_score > 0:
                priority += 1000000
            elif terminal_score == 0:
                priority += 200000
            else:
                priority -= 1000000

        if move == tt_move:
            priority += 10000000

        children.append(
            (priority, move, child, extra, terminal, terminal_score)
        )

    children.sort(key=lambda item: item[0], reverse=True)
    return children


def _search(state, depth, alpha, beta, ply=0):
    global _NODES

    _NODES += 1
    if (_NODES & 63) == 0 and perf_counter() >= _DEADLINE:
        raise _SearchTimeout

    # Protect against pathological, unusually long bonus-move chains.
    if depth <= 0 or ply >= 160:
        return _evaluate(state), None

    alpha_start = alpha
    beta_start = beta

    entry = _TT.get(state)
    tt_move = None

    if entry is not None:
        stored_depth, stored_value, flag, tt_move = entry

        if stored_depth >= depth:
            if flag == _EXACT:
                return stored_value, tt_move
            if flag == _LOWER and stored_value >= beta:
                return stored_value, tt_move
            if flag == _UPPER and stored_value <= alpha:
                return stored_value, tt_move

    best_value = -_INF
    best_move = None
    first_child = True

    for _, move, child, extra, terminal, terminal_score in _ordered_children(
        state, tt_move
    ):
        if terminal:
            score = terminal_score
        else:
            next_depth = depth if extra else depth - 1

            if first_child:
                if extra:
                    score, _ = _search(
                        child, next_depth, alpha, beta, ply + 1
                    )
                else:
                    value, _ = _search(
                        _swap(child), next_depth, -beta, -alpha, ply + 1
                    )
                    score = -value
            else:
                # Principal-variation search: use a narrow window first.
                if extra:
                    score, _ = _search(
                        child, next_depth, alpha, alpha + 1, ply + 1
                    )
                    if alpha < score < beta:
                        score, _ = _search(
                            child, next_depth, alpha, beta, ply + 1
                        )
                else:
                    value, _ = _search(
                        _swap(child),
                        next_depth,
                        -alpha - 1,
                        -alpha,
                        ply + 1,
                    )
                    score = -value
                    if alpha < score < beta:
                        value, _ = _search(
                            _swap(child),
                            next_depth,
                            -beta,
                            -alpha,
                            ply + 1,
                        )
                        score = -value

        first_child = False

        if score > best_value:
            best_value = score
            best_move = move

        if score > alpha:
            alpha = score

        if alpha >= beta:
            break

    if best_value <= alpha_start:
        flag = _UPPER
    elif best_value >= beta_start:
        flag = _LOWER
    else:
        flag = _EXACT

    if len(_TT) < 300000:
        _TT[state] = (depth, best_value, flag, best_move)

    return best_value, best_move


def policy(you: list[int], opponent: list[int]) -> int:
    global _DEADLINE, _NODES

    start = perf_counter()
    state = tuple(int(x) for x in you + opponent)
    legal_moves = [i for i in range(6) if state[i] > 0]

    # The API guarantees this is nonempty.
    fallback = legal_moves[0]
    fallback_priority = -_INF

    # Establish a tactically sensible legal answer before timed search starts.
    for move in legal_moves:
        child, extra, terminal = _play(state, move)
        priority = 100 * (child[6] - state[6]) + move

        if extra:
            priority += 100000

        if terminal:
            result = _terminal_value(child)
            if result > 0:
                priority += 1000000
            elif result == 0:
                priority += 200000
            else:
                priority -= 1000000

        if priority > fallback_priority:
            fallback_priority = priority
            fallback = move

    if len(_TT) > 240000:
        _TT.clear()

    _DEADLINE = start + 0.94
    _NODES = 0

    best_move = fallback
    total_seeds = sum(state)
    terminal_scale = (total_seeds + 1) * 1000
    house_seeds = sum(state[:6]) + sum(state[7:13])

    depth = 1

    try:
        while depth <= 64 and perf_counter() < _DEADLINE:
            value, move = _search(state, depth, -_INF, _INF)

            if move is not None and 0 <= move <= 5 and state[move] > 0:
                best_move = move

            # A terminal-scale result proves a win or loss within the horizon.
            if abs(value) >= terminal_scale:
                break

            # Attempt an exact or near-exact solve in small endgames after
            # first obtaining several safe, completed iterations.
            if house_seeds <= 10 and depth == 4:
                depth = 40
            else:
                depth += 1

    except _SearchTimeout:
        pass
    except Exception:
        # The previously selected fallback and completed iterations remain
        # legal even if an unexpected search error occurs.
        pass

    if 0 <= best_move <= 5 and state[best_move] > 0:
        return best_move
    return fallback
