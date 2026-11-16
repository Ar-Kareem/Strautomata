
from time import perf_counter
from typing import Optional

# Transposition-table flags
_EXACT = 0
_LOWER = 1
_UPPER = 2

_INF = 10**30
_TT_LIMIT = 200_000

# Entries are: depth, value, flag, best_move
_tt: dict[tuple[tuple[int, ...], tuple[int, ...]],
          tuple[int, int, int, int]] = {}

_deadline = 0.0
_nodes = 0
_history = [0] * 6


class _SearchTimeout(Exception):
    pass


def _side_empty(side: tuple[int, ...]) -> bool:
    return not (side[0] or side[1] or side[2] or
                side[3] or side[4] or side[5])


def _terminal_value(a: tuple[int, ...], b: tuple[int, ...]) -> int:
    """Terminal value from a's perspective."""
    a_total = a[6] + a[0] + a[1] + a[2] + a[3] + a[4] + a[5]
    b_total = b[6] + b[0] + b[1] + b[2] + b[3] + b[4] + b[5]
    diff = a_total - b_total

    if diff == 0:
        return 0

    total_seeds = a_total + b_total
    win_base = (total_seeds + 1) * 10_000
    if diff > 0:
        return win_base + diff * 100
    return -win_base + diff * 100


def _play(
    a: tuple[int, ...],
    b: tuple[int, ...],
    move: int
) -> tuple[tuple[int, ...], tuple[int, ...], bool, bool]:
    """
    Apply a move while retaining the moving player's orientation.

    Returns:
        new_a, new_b, extra_turn, terminal
    """
    stones = a[move]
    aa = list(a)
    bb = list(b)
    aa[move] = 0

    # The sowing ring contains:
    # a[0..5], a_store, b[0..5] -- 13 locations.
    full_laps, remainder = divmod(stones, 13)

    if full_laps:
        for i in range(7):
            aa[i] += full_laps
        for i in range(6):
            bb[i] += full_laps

    for step in range(1, remainder + 1):
        pos = (move + step) % 13
        if pos <= 6:
            aa[pos] += 1
        else:
            bb[pos - 7] += 1

    last = (move + stones) % 13

    # Capture. A final count of exactly one means the house was empty
    # immediately before the last seed was placed there.
    if last < 6 and aa[last] == 1:
        opposite = 5 - last
        if bb[opposite] > 0:
            aa[6] += bb[opposite] + 1
            aa[last] = 0
            bb[opposite] = 0

    a_houses = aa[0] + aa[1] + aa[2] + aa[3] + aa[4] + aa[5]
    b_houses = bb[0] + bb[1] + bb[2] + bb[3] + bb[4] + bb[5]

    terminal = (a_houses == 0 or b_houses == 0)
    if terminal:
        aa[6] += a_houses
        bb[6] += b_houses
        for i in range(6):
            aa[i] = 0
            bb[i] = 0
        return tuple(aa), tuple(bb), False, True

    return tuple(aa), tuple(bb), last == 6, False


def _tactical_potential(
    side: tuple[int, ...],
    other: tuple[int, ...]
) -> int:
    """Estimate the best immediately available capture/extra-turn tactic."""
    best = 0
    extra_options = 0

    for i in range(6):
        stones = side[i]
        if stones <= 0:
            continue

        full_laps, remainder = divmod(stones, 13)
        last = (i + stones) % 13

        # Number of seeds deposited in this player's store.
        distance_to_store = 6 - i
        store_deposits = full_laps
        if remainder >= distance_to_store:
            store_deposits += 1

        gain = store_deposits
        extra = (last == 6)
        if extra:
            extra_options += 1

        if last < 6:
            base_count = 0 if last == i else side[last]
            resulting_count = base_count + full_laps
            if remainder:
                resulting_count += 1

            if resulting_count == 1:
                opposite_seeds = other[5 - last]
                if opposite_seeds:
                    gain += opposite_seeds + 1

        candidate = 5 * gain + (8 if extra else 0)
        if candidate > best:
            best = candidate

    return best + min(extra_options, 2)


def _evaluate(a: tuple[int, ...], b: tuple[int, ...]) -> int:
    """Antisymmetric non-terminal evaluation from a's perspective."""
    a_houses = a[0] + a[1] + a[2] + a[3] + a[4] + a[5]
    b_houses = b[0] + b[1] + b[2] + b[3] + b[4] + b[5]

    store_score = 100 * (a[6] - b[6])
    house_score = 3 * (a_houses - b_houses)

    # Seeds nearer the store are usually easier to convert into points
    # or extra moves.
    a_position = (
        a[0] + 2 * a[1] + 3 * a[2] +
        4 * a[3] + 5 * a[4] + 6 * a[5]
    )
    b_position = (
        b[0] + 2 * b[1] + 3 * b[2] +
        4 * b[3] + 5 * b[4] + 6 * b[5]
    )

    a_moves = sum(1 for i in range(6) if a[i] > 0)
    b_moves = sum(1 for i in range(6) if b[i] > 0)

    tactical = (
        _tactical_potential(a, b) -
        _tactical_potential(b, a)
    )

    return (
        store_score
        + house_score
        + (a_position - b_position)
        + 2 * (a_moves - b_moves)
        + 7 * tactical
    )


def _check_time() -> None:
    global _nodes
    _nodes += 1
    if (_nodes & 511) == 0 and perf_counter() >= _deadline:
        raise _SearchTimeout


def _put_tt(
    key: tuple[tuple[int, ...], tuple[int, ...]],
    entry: tuple[int, int, int, int]
) -> None:
    old = _tt.get(key)
    if old is not None:
        if entry[0] >= old[0]:
            _tt[key] = entry
    elif len(_tt) < _TT_LIMIT:
        _tt[key] = entry


def _ordered_children(
    a: tuple[int, ...],
    b: tuple[int, ...],
    tt_move: int
) -> list[tuple[int, int, tuple[int, ...], tuple[int, ...], bool, bool]]:
    children = []

    for move in range(6):
        if a[move] <= 0:
            continue

        na, nb, extra, terminal = _play(a, b, move)
        store_gain = na[6] - a[6]

        order = store_gain * 2_000 + _history[move]
        if extra:
            order += 100_000

        if terminal:
            order += 10 * _terminal_value(na, nb)

        if move == tt_move:
            order += 10**18

        children.append((order, move, na, nb, extra, terminal))

    children.sort(key=lambda item: item[0], reverse=True)
    return children


def _search(
    a: tuple[int, ...],
    b: tuple[int, ...],
    depth: int,
    alpha: int,
    beta: int
) -> int:
    _check_time()

    if _side_empty(a) or _side_empty(b):
        return _terminal_value(a, b)

    if depth <= 0:
        return _evaluate(a, b)

    key = (a, b)
    original_alpha = alpha
    original_beta = beta
    entry = _tt.get(key)
    tt_move = -1

    if entry is not None:
        stored_depth, stored_value, flag, tt_move = entry
        if stored_depth >= depth:
            if flag == _EXACT:
                return stored_value
            if flag == _LOWER:
                if stored_value > alpha:
                    alpha = stored_value
            elif flag == _UPPER:
                if stored_value < beta:
                    beta = stored_value
            if alpha >= beta:
                return stored_value

    children = _ordered_children(a, b, tt_move)
    best_value = -_INF
    best_move = children[0][1]
    first = True

    for _, move, na, nb, extra, _ in children:
        if first:
            if extra:
                value = _search(na, nb, depth, alpha, beta)
            else:
                value = -_search(nb, na, depth - 1, -beta, -alpha)
            first = False
        else:
            # Principal-variation search: first try a narrow window.
            if extra:
                value = _search(na, nb, depth, alpha, alpha + 1)
                if alpha < value < beta:
                    value = _search(na, nb, depth, alpha, beta)
            else:
                value = -_search(
                    nb, na, depth - 1, -(alpha + 1), -alpha
                )
                if alpha < value < beta:
                    value = -_search(
                        nb, na, depth - 1, -beta, -alpha
                    )

        if value > best_value:
            best_value = value
            best_move = move

        if value > alpha:
            alpha = value

        if alpha >= beta:
            _history[move] += depth * depth + 1
            break

    if best_value <= original_alpha:
        flag = _UPPER
    elif best_value >= original_beta:
        flag = _LOWER
    else:
        flag = _EXACT

    _put_tt(key, (depth, best_value, flag, best_move))
    return best_value


def _root_search(
    a: tuple[int, ...],
    b: tuple[int, ...],
    depth: int
) -> tuple[int, int]:
    key = (a, b)
    entry = _tt.get(key)
    tt_move = entry[3] if entry is not None else -1

    children = _ordered_children(a, b, tt_move)
    alpha = -_INF
    beta = _INF
    best_value = -_INF
    best_move = children[0][1]
    first = True

    for _, move, na, nb, extra, _ in children:
        if perf_counter() >= _deadline:
            raise _SearchTimeout

        if first:
            if extra:
                value = _search(na, nb, depth, alpha, beta)
            else:
                value = -_search(nb, na, depth - 1, -beta, -alpha)
            first = False
        else:
            if extra:
                value = _search(na, nb, depth, alpha, alpha + 1)
                if alpha < value < beta:
                    value = _search(na, nb, depth, alpha, beta)
            else:
                value = -_search(
                    nb, na, depth - 1, -(alpha + 1), -alpha
                )
                if alpha < value < beta:
                    value = -_search(
                        nb, na, depth - 1, -beta, -alpha
                    )

        if value > best_value:
            best_value = value
            best_move = move

        if value > alpha:
            alpha = value

    _put_tt(key, (depth, best_value, _EXACT, best_move))
    return best_value, best_move


def policy(you: list[int], opponent: list[int]) -> int:
    global _deadline, _nodes, _history

    a = tuple(you)
    b = tuple(opponent)
    legal = [i for i in range(6) if a[i] > 0]

    # The API guarantees at least one legal move.
    if len(legal) == 1:
        return legal[0]

    # Keep memory bounded across calls while retaining useful positions
    # from recent searches when possible.
    if len(_tt) > 160_000:
        _tt.clear()

    _history = [0] * 6
    _nodes = 0
    _deadline = perf_counter() + 0.92

    # Establish a tactically informed legal fallback before timed search.
    best_move = legal[0]
    best_fallback = -_INF

    for move in legal:
        na, nb, extra, terminal = _play(a, b, move)
        if terminal:
            value = _terminal_value(na, nb)
        else:
            value = _evaluate(na, nb)
            if extra:
                value += 300

        if value > best_fallback:
            best_fallback = value
            best_move = move

    total_seeds = sum(a) + sum(b)
    win_base = (total_seeds + 1) * 10_000

    # A depth unit is principally a change of player. Extra-turn chains
    # retain the same depth and are therefore explored as one coherent turn.
    try:
        for depth in range(1, 65):
            if perf_counter() >= _deadline:
                break

            value, move = _root_search(a, b, depth)
            best_move = move

            # The heuristic cannot reach this range, so this is a proven
            # terminal win or loss within the completed search horizon.
            if value >= win_base or value <= -win_base:
                break

    except _SearchTimeout:
        pass

    # Defensive legality check guarantees a valid action even if search
    # state was interrupted unexpectedly.
    if 0 <= best_move <= 5 and a[best_move] > 0:
        return best_move
    return legal[0]
