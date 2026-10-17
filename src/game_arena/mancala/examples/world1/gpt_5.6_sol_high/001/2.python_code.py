
import sys
import time

sys.setrecursionlimit(10000)

# Transposition table flags.
_EXACT = 0
_LOWER = 1
_UPPER = 2

_WIN = 1_000_000_000
_INF = 10**18

# key -> (depth, flag, value, best_move)
_TT = {}

_DEADLINE = 0.0
_NODES = 0


class _TimeUp(Exception):
    pass


def _terminal_score(diff):
    """Terminal score from the current actor's perspective."""
    if diff > 0:
        return _WIN + diff
    if diff < 0:
        return -_WIN + diff
    return 0


def _apply_move(cur, opp, move):
    """
    Apply a move for cur.

    Returns:
        new_cur, new_opp, extra_turn, terminal
    """
    seeds = cur[move]

    # The sowing ring consists of:
    # cur[0..5], cur store, opp[0..5]
    ring = list(cur[:7]) + list(opp[:6])
    ring[move] = 0

    full_laps, remainder = divmod(seeds, 13)

    if full_laps:
        for j in range(13):
            ring[j] += full_laps

    pos = move
    for _ in range(remainder):
        pos = (pos + 1) % 13
        ring[pos] += 1

    # If remainder is zero, the final seed completed a full lap.
    last = (move + seeds) % 13

    # Capture. A final count of one means the house was empty
    # immediately before the final seed was placed there.
    if 0 <= last <= 5 and ring[last] == 1:
        opposite_pos = 12 - last
        if ring[opposite_pos] > 0:
            ring[6] += ring[last] + ring[opposite_pos]
            ring[last] = 0
            ring[opposite_pos] = 0

    own_house_sum = sum(ring[:6])
    opp_house_sum = sum(ring[7:13])

    terminal = own_house_sum == 0 or opp_house_sum == 0

    if terminal:
        if own_house_sum:
            ring[6] += own_house_sum
            for j in range(6):
                ring[j] = 0

        opp_store = opp[6] + opp_house_sum
        for j in range(7, 13):
            ring[j] = 0
    else:
        opp_store = opp[6]

    new_cur = tuple(ring[:7])
    new_opp = tuple(ring[7:13]) + (opp_store,)

    extra_turn = (last == 6) and not terminal
    return new_cur, new_opp, extra_turn, terminal


def _side_features(side, other):
    """
    Cheap tactical features for a side, treating it as if it could move.
    """
    best_gain = 0
    best_capture = 0
    extra_moves = 0
    mobility = 0

    for i in range(6):
        seeds = side[i]
        if seeds <= 0:
            continue

        mobility += 1
        full_laps, remainder = divmod(seeds, 13)
        last = (i + seeds) % 13

        # Seeds placed in the store by ordinary sowing.
        gain = full_laps
        store_distance = 6 - i
        if remainder >= store_distance:
            gain += 1

        if last == 6:
            extra_moves += 1

        capture_gain = 0
        if 0 <= last <= 5:
            initial = 0 if last == i else side[last]
            deposits = full_laps + (1 if remainder else 0)

            if initial + deposits == 1:
                opposite = 5 - last
                opposite_ring_pos = 7 + opposite
                distance = (opposite_ring_pos - i) % 13
                if distance == 0:
                    distance = 13

                opposite_count = other[opposite] + full_laps
                if remainder and distance <= remainder:
                    opposite_count += 1

                if opposite_count > 0:
                    capture_gain = opposite_count + 1
                    gain += capture_gain

        if gain > best_gain:
            best_gain = gain
        if capture_gain > best_capture:
            best_capture = capture_gain

    return best_gain, best_capture, extra_moves, mobility


def _evaluate(cur, opp):
    """
    Static evaluation from the side-to-move's perspective.
    Kept strictly below terminal win/loss values.
    """
    cur_houses = sum(cur[:6])
    opp_houses = sum(opp[:6])

    store_diff = cur[6] - opp[6]
    house_diff = cur_houses - opp_houses

    # Seeds in higher-indexed houses are generally closer to the store.
    cur_progress = sum((i + 1) * cur[i] for i in range(6))
    opp_progress = sum((i + 1) * opp[i] for i in range(6))

    cur_gain, cur_capture, cur_extra, cur_mobility = _side_features(cur, opp)
    opp_gain, opp_capture, opp_extra, opp_mobility = _side_features(opp, cur)

    value = (
        120 * store_diff
        + 3 * house_diff
        + (cur_progress - opp_progress)
        + 12 * (cur_gain - opp_gain)
        + 4 * (cur_capture - opp_capture)
        + 10 * (cur_extra - opp_extra)
        + 2 * (cur_mobility - opp_mobility)
    )

    limit = _WIN // 4
    if value > limit:
        return limit
    if value < -limit:
        return -limit
    return value


def _ordered_moves(cur, opp, tt_move=None):
    """Generate and order legal moves together with their resulting states."""
    results = []
    old_store = cur[6]

    for move in range(6):
        if cur[move] <= 0:
            continue

        new_cur, new_opp, extra, terminal = _apply_move(cur, opp, move)
        gain = new_cur[6] - old_store

        if terminal:
            priority = _terminal_score(new_cur[6] - new_opp[6])
        else:
            priority = 0
            if extra:
                priority += 10_000_000
            priority += gain * 10_000
            priority += (new_cur[6] - new_opp[6]) * 100
            priority -= sum(1 for x in new_opp[:6] if x > 0) * 3

        if move == tt_move:
            priority += 1_000_000_000_000

        results.append(
            (priority, move, new_cur, new_opp, extra, terminal)
        )

    results.sort(key=lambda item: item[0], reverse=True)
    return results


def _child_value(new_cur, new_opp, extra, terminal,
                 depth, alpha, beta):
    """Search one already-generated child."""
    if terminal:
        return _terminal_score(new_cur[6] - new_opp[6])

    if extra:
        # Same player moves again, so perspective and depth are unchanged.
        return _search(new_cur, new_opp, depth, alpha, beta)

    # Turn changes: swap board perspectives and negate the result.
    return -_search(new_opp, new_cur, depth - 1, -beta, -alpha)


def _search(cur, opp, depth, alpha, beta):
    """Negamax alpha-beta search using turn changes as depth units."""
    global _NODES

    _NODES += 1
    if (_NODES & 127) == 0 and time.perf_counter() >= _DEADLINE:
        raise _TimeUp

    if depth <= 0:
        return _evaluate(cur, opp)

    key = (cur, opp)
    original_alpha = alpha
    original_beta = beta

    entry = _TT.get(key)
    tt_move = None

    if entry is not None:
        stored_depth, flag, stored_value, tt_move = entry

        if stored_depth >= depth:
            if flag == _EXACT:
                return stored_value
            if flag == _LOWER:
                if stored_value > alpha:
                    alpha = stored_value
            else:
                if stored_value < beta:
                    beta = stored_value

            if alpha >= beta:
                return stored_value

    moves = _ordered_moves(cur, opp, tt_move)

    # Defensive handling for an already-terminal or malformed search node.
    if not moves:
        final_cur = cur[6] + sum(cur[:6])
        final_opp = opp[6] + sum(opp[:6])
        return _terminal_score(final_cur - final_opp)

    best_value = -_INF
    best_move = moves[0][1]
    first = True

    for _, move, new_cur, new_opp, extra, terminal in moves:
        if first:
            value = _child_value(
                new_cur, new_opp, extra, terminal,
                depth, alpha, beta
            )
            first = False
        else:
            # Principal variation search: first try a narrow window.
            value = _child_value(
                new_cur, new_opp, extra, terminal,
                depth, alpha, alpha + 1
            )

            if alpha < value < beta:
                value = _child_value(
                    new_cur, new_opp, extra, terminal,
                    depth, alpha, beta
                )

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

    _TT[key] = (depth, flag, best_value, best_move)
    return best_value


def policy(you: list[int], opponent: list[int]) -> int:
    """
    Return a legal Kalah move in the range 0..5.
    """
    global _DEADLINE, _NODES

    legal = [i for i in range(6) if you[i] > 0]

    # The API promises at least one legal move, but retain a defensive result.
    if not legal:
        return 0

    if len(legal) == 1:
        return legal[0]

    cur = tuple(you)
    opp = tuple(opponent)

    # If presented with a technically finished position, still honor the
    # requirement to return a legal house.
    if sum(opponent[:6]) == 0:
        return legal[0]

    # Keep persistent tables useful across calls without unbounded growth.
    if len(_TT) > 400_000:
        _TT.clear()

    start = time.perf_counter()
    _DEADLINE = start + 0.90
    _NODES = 0

    root_key = (cur, opp)
    old_entry = _TT.get(root_key)
    old_best = old_entry[3] if old_entry is not None else None

    # Strong heuristic fallback, guaranteed legal even if time expires.
    fallback_moves = _ordered_moves(cur, opp, old_best)
    best_move = fallback_moves[0][1]

    previous_value = None
    depth = 1

    while depth <= 64:
        if time.perf_counter() >= _DEADLINE:
            break

        try:
            if previous_value is None:
                value = _search(cur, opp, depth, -_INF, _INF)
            else:
                # Aspiration window around the previous completed iteration.
                window = 250
                low = previous_value - window
                high = previous_value + window
                value = _search(cur, opp, depth, low, high)

                if value <= low or value >= high:
                    value = _search(cur, opp, depth, -_INF, _INF)

            entry = _TT.get(root_key)
            if entry is not None:
                candidate = entry[3]
                if candidate is not None and 0 <= candidate <= 5:
                    if cur[candidate] > 0:
                        best_move = candidate

            previous_value = value

            # A terminal-magnitude result proves a forced win or loss.
            if abs(value) >= _WIN:
                break

            depth += 1

        except _TimeUp:
            break

    # Final legality guard.
    if 0 <= best_move <= 5 and you[best_move] > 0:
        return best_move
    return legal[0]
