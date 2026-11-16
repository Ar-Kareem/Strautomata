
import time

INF = 10 ** 12

_DEADLINE = 0.0
_NODES = 0
_TT = {}


def policy(you: list[int], opponent: list[int]) -> int:
    """
    Return a legal Kalah move index 0..5 for the current player.
    """
    global _DEADLINE, _NODES, _TT

    legal = [i for i in range(6) if you[i] > 0]
    if not legal:
        return 0
    if len(legal) == 1:
        return legal[0]

    y = tuple(you)
    o = tuple(opponent)

    # Small opening preference: on the standard initial board this gives an
    # immediate extra turn and is generally strong.
    if y == (4, 4, 4, 4, 4, 4, 0) and o == (4, 4, 4, 4, 4, 4, 0):
        return 2

    _DEADLINE = time.perf_counter() + 0.86
    _NODES = 0
    _TT = {}

    ordered = _ordered_children(y, o)
    best_move = ordered[0][0]

    total_house_seeds = sum(y[:6]) + sum(o[:6])
    if total_house_seeds <= 8:
        max_depth = 50
    elif total_house_seeds <= 14:
        max_depth = 34
    elif total_house_seeds <= 22:
        max_depth = 22
    else:
        max_depth = 12

    # Iterative deepening. If time expires, keep the best move from the last
    # fully completed depth.
    for depth in range(1, max_depth + 1):
        try:
            alpha = -INF
            beta = INF
            depth_best_move = best_move
            depth_best_val = -INF

            for move, ny, no, extra in ordered:
                _check_time()

                if extra:
                    val = _negamax(ny, no, depth - 1, alpha, beta)
                else:
                    val = -_negamax(no, ny, depth - 1, -beta, -alpha)

                if val > depth_best_val:
                    depth_best_val = val
                    depth_best_move = move

                if val > alpha:
                    alpha = val

            best_move = depth_best_move

            # Decisive found result; no need to spend more time.
            if abs(depth_best_val) > 900000:
                break

        except TimeoutError:
            break

    if 0 <= best_move <= 5 and you[best_move] > 0:
        return best_move

    # Absolute safety fallback.
    return legal[0]


def _check_time():
    global _NODES
    _NODES += 1
    if (_NODES & 1023) == 0 and time.perf_counter() > _DEADLINE:
        raise TimeoutError


def _negamax(y, o, depth, alpha, beta):
    _check_time()

    if _is_terminal(y, o):
        return _terminal_value(y, o)

    if depth <= 0:
        return _evaluate(y, o)

    key = (y, o, depth)
    cached = _TT.get(key)
    if cached is not None:
        return cached

    best = -INF
    original_alpha = alpha

    children = _ordered_children(y, o)
    if not children:
        return _terminal_value(y, o)

    for move, ny, no, extra in children:
        if extra:
            val = _negamax(ny, no, depth - 1, alpha, beta)
        else:
            val = -_negamax(no, ny, depth - 1, -beta, -alpha)

        if val > best:
            best = val
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break

    # Store only exact values, not beta-cutoff bounds.
    if alpha < beta and best > original_alpha:
        _TT[key] = best
    elif best <= original_alpha:
        _TT[key] = best

    return best


def _make_move(y, o, move):
    y = list(y)
    o = list(o)

    seeds = y[move]
    y[move] = 0

    # Board path from current player's perspective:
    # indices 0..5 are own houses, 6 is own store, 7..12 are opponent houses.
    pos = move
    last = pos

    for _ in range(seeds):
        pos = (pos + 1) % 13
        last = pos

        if pos <= 5:
            y[pos] += 1
        elif pos == 6:
            y[6] += 1
        else:
            o[pos - 7] += 1

    extra = last == 6

    # Capture: last seed lands in an own empty house and opposite has seeds.
    if 0 <= last <= 5 and y[last] == 1:
        opp_idx = 5 - last
        if o[opp_idx] > 0:
            y[6] += o[opp_idx] + 1
            o[opp_idx] = 0
            y[last] = 0

    # Game end: if either side is empty, collect all remaining house seeds.
    if sum(y[:6]) == 0 or sum(o[:6]) == 0:
        y[6] += sum(y[:6])
        o[6] += sum(o[:6])
        for i in range(6):
            y[i] = 0
            o[i] = 0
        extra = False

    return tuple(y), tuple(o), extra


def _ordered_children(y, o):
    children = []

    for m in range(6):
        if y[m] <= 0:
            continue

        ny, no, extra = _make_move(y, o, m)

        store_gain = ny[6] - y[6]
        score = store_gain * 300

        if extra:
            score += 12000

        if _is_terminal(ny, no):
            score += _terminal_value(ny, no)

        score += _evaluate_light(ny, no)

        # Prefer moves from houses closer to the store as a mild tie-breaker.
        score += m

        children.append((score, m, ny, no, extra))

    children.sort(reverse=True, key=lambda x: x[0])
    return [(m, ny, no, extra) for score, m, ny, no, extra in children]


def _is_terminal(y, o):
    return sum(y[:6]) == 0 or sum(o[:6]) == 0


def _terminal_value(y, o):
    # If terminal state has not already been collected, this formula still
    # gives the correct final margin.
    return ((y[6] + sum(y[:6])) - (o[6] + sum(o[:6]))) * 100000


def _evaluate(y, o):
    if _is_terminal(y, o):
        return _terminal_value(y, o)

    sy = sum(y[:6])
    so = sum(o[:6])

    store_diff = y[6] - o[6]
    house_diff = sy - so

    weighted_y = sum((i + 1) * y[i] for i in range(6))
    weighted_o = sum((i + 1) * o[i] for i in range(6))

    extra_y = _extra_potential(y)
    extra_o = _extra_potential(o)

    cap_y = _capture_potential(y, o)
    cap_o = _capture_potential(o, y)

    # Store seeds are guaranteed points, so they dominate the heuristic.
    return (
        120 * store_diff
        + 5 * house_diff
        + 2 * (weighted_y - weighted_o)
        + 30 * (extra_y - extra_o)
        + 12 * (cap_y - cap_o)
    )


def _evaluate_light(y, o):
    if _is_terminal(y, o):
        return _terminal_value(y, o)

    return (
        120 * (y[6] - o[6])
        + 4 * (sum(y[:6]) - sum(o[:6]))
        + 20 * (_extra_potential(y) - _extra_potential(o))
    )


def _extra_potential(side):
    count = 0
    for i in range(6):
        seeds = side[i]
        if seeds > 0 and seeds % 13 == 6 - i:
            count += 1
    return count


def _capture_potential(side, other):
    best = 0

    for i in range(6):
        seeds = side[i]
        if seeds <= 0:
            continue

        # Approximate direct capture potential. Most useful captures occur
        # before a full lap; this keeps evaluation fast.
        if seeds <= 13:
            last = (i + seeds) % 13
            if 0 <= last <= 5:
                if last == i or side[last] == 0:
                    opp_idx = 5 - last
                    if other[opp_idx] > 0:
                        gain = other[opp_idx] + 1
                        if gain > best:
                            best = gain

    return best
