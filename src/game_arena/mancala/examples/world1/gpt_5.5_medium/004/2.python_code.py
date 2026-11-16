
import time

# Time limit kept below 1 second to leave safety margin.
_TIME_LIMIT = 0.88

_INF = 10 ** 18
_WIN = 10 ** 9

# State layout:
# indices 0..6   = root player's houses 0..5 and store
# indices 7..13  = opponent's houses 0..5 and store
# index 14       = side to move, 0 for root player, 1 for opponent

_PATH0 = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12)
_PATH1 = (7, 8, 9, 10, 11, 12, 13, 0, 1, 2, 3, 4, 5)

_deadline = 0.0
_nodes = 0
_tt = {}


class _Timeout(Exception):
    pass


def policy(you: list[int], opponent: list[int]) -> int:
    """
    Return a legal move index 0..5 with you[index] > 0.
    """
    global _deadline, _nodes, _tt

    legal = [i for i in range(6) if you[i] > 0]
    if not legal:
        return 0  # Should never be called in this state.

    if len(legal) == 1:
        return legal[0]

    # Strong standard opening: house 2 gives an immediate extra turn.
    if (
        you[:6] == [4, 4, 4, 4, 4, 4]
        and opponent[:6] == [4, 4, 4, 4, 4, 4]
        and you[6] == 0
        and opponent[6] == 0
    ):
        return 2

    _deadline = time.perf_counter() + _TIME_LIMIT
    _nodes = 0
    _tt = {}

    state = tuple(you + opponent + [0])

    # Guaranteed legal fallback.
    best_move = _greedy_move(state, legal)

    depth = 1
    try:
        while True:
            value, move = _root_search(state, depth, best_move)
            best_move = move

            # If a forced terminal result is already found at meaningful depth,
            # further search is less important.
            if abs(value) >= _WIN and depth >= 4:
                break

            depth += 1
            if depth > 64:
                break
    except _Timeout:
        pass
    except Exception:
        # Absolute safety: never fail to return a legal move.
        pass

    if 0 <= best_move <= 5 and you[best_move] > 0:
        return best_move

    return legal[0]


def _check_time():
    if time.perf_counter() >= _deadline:
        raise _Timeout()


def _legal_moves(state):
    side = state[14]
    if side == 0:
        return [i for i in range(6) if state[i] > 0]
    return [i for i in range(6) if state[7 + i] > 0]


def _add_to_loc(a, b, loc, amount):
    if amount == 0:
        return
    if loc <= 6:
        a[loc] += amount
    elif loc == 13:
        b[6] += amount
    else:
        b[loc - 7] += amount


def _apply_move(state, move):
    a = list(state[:7])
    b = list(state[7:14])
    side = state[14]

    if side == 0:
        stones = a[move]
        a[move] = 0
        path = _PATH0
        start = move

        q, r = divmod(stones, 13)

        if q:
            for loc in path:
                _add_to_loc(a, b, loc, q)

        last_loc = path[start]
        for k in range(1, r + 1):
            loc = path[(start + k) % 13]
            _add_to_loc(a, b, loc, 1)
            last_loc = loc

        extra = last_loc == 6

        # Capture.
        if 0 <= last_loc <= 5 and a[last_loc] == 1:
            opp = 5 - last_loc
            if b[opp] > 0:
                a[6] += b[opp] + 1
                b[opp] = 0
                a[last_loc] = 0

        next_side = 0 if extra else 1

    else:
        stones = b[move]
        b[move] = 0
        path = _PATH1
        start = move

        q, r = divmod(stones, 13)

        if q:
            for loc in path:
                _add_to_loc(a, b, loc, q)

        last_loc = path[start]
        for k in range(1, r + 1):
            loc = path[(start + k) % 13]
            _add_to_loc(a, b, loc, 1)
            last_loc = loc

        extra = last_loc == 13

        # Capture.
        if 7 <= last_loc <= 12:
            j = last_loc - 7
            if b[j] == 1:
                opp = 5 - j
                if a[opp] > 0:
                    b[6] += a[opp] + 1
                    a[opp] = 0
                    b[j] = 0

        next_side = 1 if extra else 0

    # End-game sweep.
    sa = a[0] + a[1] + a[2] + a[3] + a[4] + a[5]
    sb = b[0] + b[1] + b[2] + b[3] + b[4] + b[5]

    if sa == 0 or sb == 0:
        a[6] += sa
        b[6] += sb
        for i in range(6):
            a[i] = 0
            b[i] = 0
        next_side = 0

    return tuple(a + b + [next_side])


def _is_terminal(state):
    return (
        state[0] + state[1] + state[2] + state[3] + state[4] + state[5] == 0
        or state[7] + state[8] + state[9] + state[10] + state[11] + state[12] == 0
    )


def _terminal_value(state):
    # Be robust even if the terminal state has not been swept yet.
    root_final = state[6] + state[0] + state[1] + state[2] + state[3] + state[4] + state[5]
    opp_final = state[13] + state[7] + state[8] + state[9] + state[10] + state[11] + state[12]
    diff = root_final - opp_final

    if diff > 0:
        return _WIN + diff * 1000
    if diff < 0:
        return -_WIN + diff * 1000
    return 0


def _free_moves_for_side(houses):
    count = 0
    for i, n in enumerate(houses):
        if n > 0 and n % 13 == 6 - i:
            count += 1
    return count


def _evaluate_light(state):
    if _is_terminal(state):
        return _terminal_value(state)

    a_store = state[6]
    b_store = state[13]
    a_houses = state[:6]
    b_houses = state[7:13]

    a_sum = sum(a_houses)
    b_sum = sum(b_houses)

    score = 100 * (a_store - b_store)
    score += 3 * (a_sum - b_sum)

    # Seeds closer to own store are generally more useful.
    positional = 0
    for i in range(6):
        positional += (i + 1) * state[i]
        positional -= (i + 1) * state[7 + i]
    score += positional

    score += 18 * (_free_moves_for_side(a_houses) - _free_moves_for_side(b_houses))

    # Small initiative bonus.
    score += 2 if state[14] == 0 else -2

    return score


def _evaluate_full(state):
    if _is_terminal(state):
        return _terminal_value(state)

    score = _evaluate_light(state)

    # Tactical one-move store gain/capture potential for both players.
    a_base = state[6]
    b_base = state[13]

    best_a_gain = 0
    if any(state[i] > 0 for i in range(6)):
        s0 = tuple(list(state[:14]) + [0])
        for m in range(6):
            if state[m] > 0:
                child = _apply_move(s0, m)
                gain = child[6] - a_base
                if gain > best_a_gain:
                    best_a_gain = gain

    best_b_gain = 0
    if any(state[7 + i] > 0 for i in range(6)):
        s1 = tuple(list(state[:14]) + [1])
        for m in range(6):
            if state[7 + m] > 0:
                child = _apply_move(s1, m)
                gain = child[13] - b_base
                if gain > best_b_gain:
                    best_b_gain = gain

    score += 12 * (best_a_gain - best_b_gain)

    return score


def _ordered_children(state):
    moves = _legal_moves(state)
    side = state[14]

    preferred = None
    entry = _tt.get(state)
    if entry is not None:
        preferred = entry[3]

    children = []
    for m in moves:
        child = _apply_move(state, m)
        children.append((_evaluate_light(child), m, child))

    children.sort(key=lambda x: x[0], reverse=(side == 0))

    if preferred is not None:
        for idx, item in enumerate(children):
            if item[1] == preferred:
                children.insert(0, children.pop(idx))
                break

    return children


def _search(state, depth, alpha, beta):
    global _nodes, _tt

    _nodes += 1
    if (_nodes & 511) == 0:
        _check_time()

    if depth <= 0 or _is_terminal(state):
        return _evaluate_full(state)

    alpha_orig = alpha
    beta_orig = beta

    entry = _tt.get(state)
    if entry is not None and entry[0] >= depth:
        _, val, flag, _ = entry
        if flag == 0:      # Exact
            return val
        if flag == 1:      # Lower bound
            if val > alpha:
                alpha = val
        elif flag == 2:    # Upper bound
            if val < beta:
                beta = val
        if alpha >= beta:
            return val

    side = state[14]
    children = _ordered_children(state)

    if not children:
        return _evaluate_full(state)

    best_move = children[0][1]

    if side == 0:
        value = -_INF
        for _, m, child in children:
            v = _search(child, depth - 1, alpha, beta)
            if v > value:
                value = v
                best_move = m
            if value > alpha:
                alpha = value
            if alpha >= beta:
                break
    else:
        value = _INF
        for _, m, child in children:
            v = _search(child, depth - 1, alpha, beta)
            if v < value:
                value = v
                best_move = m
            if value < beta:
                beta = value
            if alpha >= beta:
                break

    if value <= alpha_orig:
        flag = 2  # Upper bound
    elif value >= beta_orig:
        flag = 1  # Lower bound
    else:
        flag = 0  # Exact

    _tt[state] = (depth, value, flag, best_move)
    return value


def _root_search(state, depth, previous_best):
    _check_time()

    moves = _legal_moves(state)
    children = []

    for m in moves:
        child = _apply_move(state, m)
        score = _evaluate_light(child)
        if m == previous_best:
            score += 10 ** 7
        children.append((score, m, child))

    children.sort(key=lambda x: x[0], reverse=True)

    best_value = -_INF
    best_move = children[0][1]
    alpha = -_INF
    beta = _INF

    for _, m, child in children:
        v = _search(child, depth - 1, alpha, beta)
        if v > best_value:
            best_value = v
            best_move = m
        if best_value > alpha:
            alpha = best_value

    return best_value, best_move


def _greedy_move(state, legal):
    best_move = legal[0]
    best_value = -_INF

    for m in legal:
        child = _apply_move(state, m)
        value = _evaluate_full(child)
        if value > best_value:
            best_value = value
            best_move = m

    return best_move
