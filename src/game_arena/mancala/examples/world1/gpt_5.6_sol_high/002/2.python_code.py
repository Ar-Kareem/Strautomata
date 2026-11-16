
import time

# Transposition-table flags
_EXACT = 0
_LOWER = 1
_UPPER = 2

_TT = {}
_DEADLINE = 0.0
_NODES = 0


class _SearchTimeout(Exception):
    pass


def _apply_move(a, b, move):
    """Apply a move. The returned sides retain the same orientation."""
    aa = list(a)
    bb = list(b)

    seeds = aa[move]
    aa[move] = 0

    full_laps, remainder = divmod(seeds, 13)

    if full_laps:
        for i in range(7):
            aa[i] += full_laps
        for i in range(6):
            bb[i] += full_laps

    last = move
    for step in range(1, remainder + 1):
        pos = (move + step) % 13
        last = pos
        if pos <= 6:
            aa[pos] += 1
        else:
            bb[pos - 7] += 1

    # With an exact number of laps, the final seed returned to the source.
    if remainder == 0:
        last = move

    extra_turn = last == 6

    # Capture if the final own house contained only the newly placed seed.
    if 0 <= last < 6 and aa[last] == 1:
        opposite = 5 - last
        if bb[opposite] > 0:
            aa[6] += bb[opposite] + 1
            bb[opposite] = 0
            aa[last] = 0

    return tuple(aa), tuple(bb), extra_turn


def _terminal_value(a, b):
    """Return exact utility from a's perspective, or None if nonterminal."""
    houses_a = sum(a[:6])
    houses_b = sum(b[:6])

    if houses_a != 0 and houses_b != 0:
        return None

    final_a = a[6] + houses_a
    final_b = b[6] + houses_b
    difference = final_a - final_b

    if difference == 0:
        return 0

    total = final_a + final_b
    result_base = total * 1000 + 1

    if difference > 0:
        return result_base + difference
    return -result_base + difference


def _immediate_potential(a, b):
    """
    Estimate the best immediate store gain and count available extra turns
    without constructing every child position.
    """
    best_gain = 0
    extra_moves = 0

    for i in range(6):
        seeds = a[i]
        if seeds <= 0:
            continue

        full_laps, remainder = divmod(seeds, 13)
        gain = full_laps

        distance_to_store = 6 - i
        if remainder >= distance_to_store:
            gain += 1

        final_pos = (i + remainder) % 13 if remainder else i

        if final_pos == 6:
            extra_moves += 1

        if final_pos < 6:
            initial_target = 0 if final_pos == i else a[final_pos]
            final_target_count = initial_target + full_laps
            if remainder:
                final_target_count += 1

            if final_target_count == 1:
                opposite = 5 - final_pos
                opposite_position = 7 + opposite
                opposite_distance = (opposite_position - i) % 13

                opposite_count = b[opposite] + full_laps
                if remainder and opposite_distance <= remainder:
                    opposite_count += 1

                if opposite_count > 0:
                    gain += opposite_count + 1

        if gain > best_gain:
            best_gain = gain

    return best_gain, extra_moves


def _evaluate(a, b):
    """Heuristic utility from the perspective of side a, which is to move."""
    terminal = _terminal_value(a, b)
    if terminal is not None:
        return terminal

    houses_a = sum(a[:6])
    houses_b = sum(b[:6])
    store_difference = a[6] - b[6]
    house_difference = houses_a - houses_b

    # Seeds nearer the store are usually easier to secure.
    position_a = sum((i + 1) * a[i] for i in range(6))
    position_b = sum((i + 1) * b[i] for i in range(6))

    mobility_a = sum(1 for i in range(6) if a[i] > 0)
    mobility_b = sum(1 for i in range(6) if b[i] > 0)

    gain_a, extras_a = _immediate_potential(a, b)
    gain_b, extras_b = _immediate_potential(b, a)

    return (
        120 * store_difference
        + 5 * house_difference
        + (position_a - position_b)
        + 2 * (mobility_a - mobility_b)
        + 8 * gain_a
        - 5 * gain_b
        + 9 * extras_a
        - 4 * extras_b
    )


def _ordered_moves(a, b, tt_move):
    """Generate children in a strong alpha-beta ordering."""
    children = []

    for move in range(6):
        if a[move] <= 0:
            continue

        child_a, child_b, extra = _apply_move(a, b, move)
        gain = child_a[6] - a[6]
        terminal = _terminal_value(child_a, child_b)

        if terminal is None:
            terminal_rank = 1
        elif terminal > 0:
            terminal_rank = 3
        elif terminal == 0:
            terminal_rank = 2
        else:
            terminal_rank = 0

        order_key = (
            1 if move == tt_move else 0,
            terminal_rank,
            1 if extra else 0,
            gain,
            move,
        )
        children.append(
            (order_key, move, child_a, child_b, extra)
        )

    children.sort(key=lambda item: item[0], reverse=True)
    return children


def _store_tt(key, depth, flag, value, best_move):
    old = _TT.get(key)

    replace = (
        old is None
        or depth > old[0]
        or (depth == old[0] and flag == _EXACT and old[1] != _EXACT)
        or (flag == _EXACT and old[1] != _EXACT)
    )

    if replace:
        _TT[key] = (depth, flag, value, best_move)


def _search(a, b, depth, alpha, beta):
    """Negamax search where a is always the player to move."""
    global _NODES

    _NODES += 1
    if (_NODES & 127) == 0 and time.perf_counter() >= _DEADLINE:
        raise _SearchTimeout

    terminal = _terminal_value(a, b)
    if terminal is not None:
        return terminal

    key = (a, b)
    entry = _TT.get(key)
    tt_move = entry[3] if entry is not None else None

    original_alpha = alpha
    original_beta = beta

    if entry is not None and entry[0] >= depth:
        entry_depth, flag, value, _ = entry

        if flag == _EXACT:
            return value
        if flag == _LOWER:
            if value > alpha:
                alpha = value
        else:
            if value < beta:
                beta = value

        if alpha >= beta:
            return value

    if depth <= 0:
        return _evaluate(a, b)

    best_value = -float("inf")
    best_move = None
    first_child = True

    for _, move, child_a, child_b, extra in _ordered_moves(a, b, tt_move):
        if extra:
            child_depth = depth

            if first_child:
                value = _search(
                    child_a, child_b, child_depth, alpha, beta
                )
            else:
                value = _search(
                    child_a, child_b, child_depth, alpha, alpha + 1
                )
                if alpha < value < beta:
                    value = _search(
                        child_a, child_b, child_depth, alpha, beta
                    )
        else:
            child_depth = depth - 1

            if first_child:
                value = -_search(
                    child_b, child_a, child_depth, -beta, -alpha
                )
            else:
                value = -_search(
                    child_b,
                    child_a,
                    child_depth,
                    -alpha - 1,
                    -alpha,
                )
                if alpha < value < beta:
                    value = -_search(
                        child_b,
                        child_a,
                        child_depth,
                        -beta,
                        -alpha,
                    )

        first_child = False

        if value > best_value:
            best_value = value
            best_move = move

        if value > alpha:
            alpha = value

        if alpha >= beta:
            break

    if best_value <= original_alpha:
        flag = _UPPER
    elif best_value >= original_beta:
        flag = _LOWER
    else:
        flag = _EXACT

    _store_tt(key, depth, flag, best_value, best_move)
    return best_value


def _fallback_move(a, b, legal):
    """Fast one-ply choice used if deeper search cannot finish."""
    best_move = legal[0]
    best_value = -float("inf")

    for move in legal:
        child_a, child_b, extra = _apply_move(a, b, move)
        terminal = _terminal_value(child_a, child_b)

        if terminal is not None:
            value = terminal
        elif extra:
            value = _evaluate(child_a, child_b) + 40
        else:
            value = -_evaluate(child_b, child_a)

        if value > best_value:
            best_value = value
            best_move = move

    return best_move


def policy(you: list[int], opponent: list[int]) -> int:
    global _DEADLINE, _NODES

    legal = [i for i in range(6) if you[i] > 0]
    # The API guarantees at least one legal move.
    if not legal:
        return 0

    a = tuple(you)
    b = tuple(opponent)
    best_move = legal[0]

    _DEADLINE = time.perf_counter() + 0.94
    _NODES = 0

    try:
        best_move = _fallback_move(a, b, legal)

        # Prevent unbounded memory growth across a long series of games.
        if len(_TT) > 220000:
            _TT.clear()

        last_score = None
        total = sum(a) + sum(b)
        terminal_base = total * 1000 + 1

        for depth in range(1, 65):
            if time.perf_counter() >= _DEADLINE:
                break

            try:
                if last_score is None:
                    score = _search(
                        a, b, depth, -float("inf"), float("inf")
                    )
                else:
                    window = 180
                    low = last_score - window
                    high = last_score + window
                    score = _search(a, b, depth, low, high)

                    if score <= low or score >= high:
                        score = _search(
                            a,
                            b,
                            depth,
                            -float("inf"),
                            float("inf"),
                        )

                root_entry = _TT.get((a, b))
                if root_entry is not None:
                    candidate = root_entry[3]
                    if candidate in legal:
                        best_move = candidate

                last_score = score

                # A terminal-valued minimax result proves the game outcome.
                if abs(score) >= terminal_base:
                    break

            except _SearchTimeout:
                break

    except Exception:
        # best_move was initialized to a legal action before searching.
        pass

    if best_move not in legal:
        best_move = legal[0]

    return best_move
