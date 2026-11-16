
"""Time-bounded Kalah policy using iterative-deepening alpha-beta search."""

import sys
import time

sys.setrecursionlimit(10000)

_INF = 10**30
_WIN = 10**15

_EXACT = 0
_LOWER = 1
_UPPER = 2

# key -> (searched_depth, bound_type, value, best_move)
_TT = {}
_HISTORY = [0, 0, 0, 0, 0, 0]

_DEADLINE = 0.0
_NODES = 0


class _SearchTimeout(Exception):
    pass


def _check_time() -> None:
    global _NODES
    _NODES += 1
    if (_NODES & 127) == 0 and time.perf_counter() >= _DEADLINE:
        raise _SearchTimeout


def _terminal_score(diff: int) -> int:
    """Return a terminal utility from the current actor's perspective."""
    if diff > 0:
        return _WIN + min(diff, _WIN // 2)
    if diff < 0:
        return -_WIN - min(-diff, _WIN // 2)
    return 0


def _play(a_state: tuple, b_state: tuple, move: int):
    """
    Play a move for side a.

    Returns:
        new_a, new_b, extra_move, terminal, store_gain, captured
    """
    a = list(a_state)
    b = list(b_state)

    old_store = a[6]
    stones = a[move]
    a[move] = 0

    # The sowing ring has 13 locations:
    # a[0..5], a store, b[0..5].
    full_laps, remainder = divmod(stones, 13)

    if full_laps:
        for j in range(7):
            a[j] += full_laps
        for j in range(6):
            b[j] += full_laps

    for step in range(1, remainder + 1):
        pos = (move + step) % 13
        if pos <= 6:
            a[pos] += 1
        else:
            b[pos - 7] += 1

    last = (move + stones) % 13
    extra = last == 6
    captured = 0

    # A final count of one means the house was empty immediately before
    # the final seed was placed there.
    if last < 6 and a[last] == 1:
        opposite = 5 - last
        if b[opposite] > 0:
            captured = b[opposite] + 1
            a[6] += captured
            a[last] = 0
            b[opposite] = 0

    terminal = not any(a[:6]) or not any(b[:6])
    if terminal:
        remaining_a = sum(a[:6])
        remaining_b = sum(b[:6])
        if remaining_a:
            a[6] += remaining_a
            for j in range(6):
                a[j] = 0
        if remaining_b:
            b[6] += remaining_b
            for j in range(6):
                b[j] = 0
        extra = False

    return (
        tuple(a),
        tuple(b),
        extra,
        terminal,
        a[6] - old_store,
        captured,
    )


def _side_features(x: tuple, y: tuple):
    """Calculate tactical features available to side x."""
    bonus_moves = 0
    best_capture = 0
    best_bank = 0
    mobility = 0

    for i in range(6):
        stones = x[i]
        if stones <= 0:
            continue

        mobility += 1
        laps, rem = divmod(stones, 13)
        last = (i + stones) % 13

        banked = laps
        if rem >= 6 - i:
            banked += 1
        if banked > best_bank:
            best_bank = banked

        if last == 6:
            bonus_moves += 1

        if last < 6:
            # Count in the landing house after sowing.
            base = 0 if last == i else x[last]
            final_count = base + laps + (1 if rem else 0)

            if final_count == 1:
                opposite = 5 - last
                opposite_after = y[opposite] + laps

                # Was the opposite pit visited during the partial lap?
                target_position = 7 + opposite
                if target_position - i <= rem:
                    opposite_after += 1

                if opposite_after > 0:
                    capture = opposite_after + 1
                    if capture > best_capture:
                        best_capture = capture

    return bonus_moves, best_capture, best_bank, mobility


def _evaluate(a: tuple, b: tuple) -> int:
    """Heuristic value from the player-to-move's perspective."""
    store_diff = a[6] - b[6]
    pit_diff = sum(a[:6]) - sum(b[:6])

    # Seeds nearer a player's store are generally easier to secure.
    position_a = (
        a[0] + 2 * a[1] + 3 * a[2]
        + 4 * a[3] + 5 * a[4] + 6 * a[5]
    )
    position_b = (
        b[0] + 2 * b[1] + 3 * b[2]
        + 4 * b[3] + 5 * b[4] + 6 * b[5]
    )

    bonus_a, capture_a, bank_a, mobility_a = _side_features(a, b)
    bonus_b, capture_b, bank_b, mobility_b = _side_features(b, a)

    score = 120 * store_diff
    score += 3 * pit_diff
    score += position_a - position_b
    score += 20 * (bonus_a - bonus_b) + 6 * bonus_a
    score += 45 * (capture_a - capture_b) + 15 * capture_a
    score += 4 * (bank_a - bank_b)
    score += 2 * (mobility_a - mobility_b)

    # Keep all heuristic scores strictly below terminal utilities.
    limit = _WIN // 4
    if score > limit:
        return limit
    if score < -limit:
        return -limit
    return int(score)


def _move_priority(move: int, result, tt_move: int) -> int:
    """Ordering score; this does not affect minimax values."""
    new_a, new_b, extra, terminal, store_gain, captured = result

    priority = _HISTORY[move]

    if move == tt_move:
        priority += 5_000_000

    if terminal:
        diff = new_a[6] - new_b[6]
        if diff > 0:
            priority += 3_000_000
        elif diff == 0:
            priority += 1_000_000
        else:
            priority -= 3_000_000

    if extra:
        priority += 400_000

    priority += min(captured, 10000) * 12_000
    priority += min(store_gain, 10000) * 200
    priority += move

    return priority


def _ordered_moves(a: tuple, b: tuple, tt_move: int):
    items = []
    for move in range(6):
        if a[move] > 0:
            result = _play(a, b, move)
            priority = _move_priority(move, result, tt_move)
            items.append((priority, move, result))

    items.sort(key=lambda item: item[0], reverse=True)
    return items


def _search(a: tuple, b: tuple, depth: int, alpha: int, beta: int) -> int:
    """Negamax alpha-beta search, retaining depth across extra moves."""
    _check_time()

    key = (a, b)
    entry = _TT.get(key)
    tt_move = -1

    if entry is not None:
        entry_depth, flag, value, tt_move = entry
        if entry_depth >= depth:
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

    effective_alpha = alpha
    effective_beta = beta

    moves = _ordered_moves(a, b, tt_move)
    best_value = -_INF
    best_move = moves[0][1]
    first_child = True

    for _, move, result in moves:
        new_a, new_b, extra, terminal, _, _ = result

        if terminal:
            value = _terminal_score(new_a[6] - new_b[6])
        elif extra:
            if first_child:
                value = _search(new_a, new_b, depth, alpha, beta)
            else:
                # Principal variation search with a null window.
                value = _search(new_a, new_b, depth, alpha, alpha + 1)
                if alpha < value < beta:
                    value = _search(new_a, new_b, depth, alpha, beta)
        else:
            child_depth = depth - 1
            if first_child:
                value = -_search(
                    new_b, new_a, child_depth, -beta, -alpha
                )
            else:
                value = -_search(
                    new_b, new_a, child_depth, -alpha - 1, -alpha
                )
                if alpha < value < beta:
                    value = -_search(
                        new_b, new_a, child_depth, -beta, -alpha
                    )

        first_child = False

        if value > best_value:
            best_value = value
            best_move = move

        if value > alpha:
            alpha = value

        if alpha >= beta:
            bonus = depth * depth + 1
            _HISTORY[move] = min(200_000, _HISTORY[move] + bonus)
            break

    if best_value <= effective_alpha:
        new_flag = _UPPER
    elif best_value >= effective_beta:
        new_flag = _LOWER
    else:
        new_flag = _EXACT

    old = _TT.get(key)
    if old is None or depth >= old[0] or new_flag == _EXACT:
        _TT[key] = (depth, new_flag, best_value, best_move)

    return best_value


def policy(you: list[int], opponent: list[int]) -> int:
    """
    Return a legal Kalah house index in the range 0..5.
    """
    global _DEADLINE, _NODES

    legal = [i for i in range(6) if you[i] > 0]
    # The API guarantees at least one legal move.
    if len(legal) == 1:
        return legal[0]

    a = tuple(you)
    b = tuple(opponent)

    start = time.perf_counter()
    _DEADLINE = start + 0.94
    _NODES = 0

    # Bound persistent memory while retaining useful information between turns.
    if len(_TT) > 250_000:
        _TT.clear()

    if max(_HISTORY) > 180_000:
        for i in range(6):
            _HISTORY[i] //= 2

    # Establish a tactically sensible legal fallback before timed search.
    fallback = legal[0]
    fallback_priority = -_INF
    old_entry = _TT.get((a, b))
    old_tt_move = old_entry[3] if old_entry is not None else -1

    try:
        for move in legal:
            result = _play(a, b, move)
            priority = _move_priority(move, result, old_tt_move)
            if priority > fallback_priority:
                fallback_priority = priority
                fallback = move
    except Exception:
        return fallback

    best_move = fallback

    try:
        depth = 1
        while depth <= 64 and time.perf_counter() < _DEADLINE:
            value = _search(a, b, depth, -_INF, _INF)

            entry = _TT.get((a, b))
            if entry is not None:
                candidate = entry[3]
                if 0 <= candidate <= 5 and you[candidate] > 0:
                    best_move = candidate

            # A terminal-valued result proves a forced result at this depth.
            if abs(value) >= _WIN:
                break

            depth += 1

    except _SearchTimeout:
        pass
    except Exception:
        # The fallback and last completed iterative-deepening result remain legal.
        pass

    if 0 <= best_move <= 5 and you[best_move] > 0:
        return best_move
    return legal[0]
