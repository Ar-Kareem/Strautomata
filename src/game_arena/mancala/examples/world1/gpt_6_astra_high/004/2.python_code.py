
from time import perf_counter

_WIN = 10**9
_INF = 10**15

# Each state is:
# (our six houses, store_difference, their six houses).
_TABLE = {}

# Precomputed partial sowing paths, excluding the opponent's store.
_PATHS = tuple(
    tuple(
        tuple((i + step) % 13 for step in range(1, remainder + 1))
        for remainder in range(13)
    )
    for i in range(6)
)


class _SearchTimeout(Exception):
    pass


def _play(state, move):
    seeds = state[move]
    board = list(state)
    board[move] = 0

    if seeds < 13:
        remainder = seeds
    else:
        laps, remainder = divmod(seeds, 13)
        for j in range(13):
            board[j] += laps

    for j in _PATHS[move][remainder]:
        board[j] += 1

    last = (move + remainder) % 13

    if last < 6 and board[last] == 1:
        opposite = 12 - last
        if board[opposite]:
            board[6] += board[opposite] + 1
            board[last] = 0
            board[opposite] = 0

    extra = last == 6
    if extra:
        return tuple(board), True

    return (
        tuple(board[7:13]) + (-board[6],) + tuple(board[:6]),
        False,
    )


def _move_priority(state, move):
    seeds = state[move]
    laps, remainder = divmod(seeds, 13)
    last = (move + remainder) % 13

    gain = laps + int(remainder >= 6 - move)
    captured = 0

    if seeds <= 13 and last < 6:
        if seeds == 13 or state[last] == 0:
            opposite = state[12 - last]
            if seeds >= 12 - last - move:
                opposite += 1
            if opposite:
                captured = opposite
                gain += opposite + 1

    return (
        128 * gain
        + 256 * int(last == 6)
        + 16 * captured
        + (5 - move)
    )


def _heuristic(state, ours, theirs):
    captures = [0, 0]
    bonuses = [0, 0]
    mobility = [0, 0]

    for side in (0, 1):
        offset = 0 if side == 0 else 7
        other = 7 if side == 0 else 0

        for i in range(6):
            seeds = state[offset + i]
            if not seeds:
                continue

            mobility[side] += 1

            if seeds % 13 == 6 - i:
                bonuses[side] += 1

            if seeds <= 13:
                last = (i + seeds) % 13
                if last < 6:
                    if seeds == 13 or state[offset + last] == 0:
                        target = state[other + 5 - last]
                        if seeds >= 12 - last - i:
                            target += 1
                        if target > captures[side]:
                            captures[side] = target

    # House ownership becomes more reliable as the board empties.
    house_weight = 38 + max(0, 24 - ours - theirs) // 2

    return (
        100 * state[6]
        + house_weight * (ours - theirs)
        + 75 * captures[0]
        - 45 * captures[1]
        + 60 * min(bonuses[0], 2)
        - 35 * min(bonuses[1], 2)
        + 3 * (mobility[0] - mobility[1])
    )


def policy(you: list[int], opponent: list[int]) -> int:
    started = perf_counter()
    deadline = started + 0.90

    legal = [i for i in range(6) if you[i] > 0]
    if len(legal) == 1:
        return int(legal[0])

    state = (
        tuple(you[:6])
        + (you[6] - opponent[6],)
        + tuple(opponent[:6])
    )

    # This remains available even if the first search is interrupted.
    best_move = max(legal, key=lambda i: _move_priority(state, i))

    table = _TABLE
    if len(table) > 180000:
        table.clear()

    previous = table.get(state)
    if previous is not None and previous[3] in legal:
        best_move = previous[3]

    history = [0] * 192
    nodes = 0
    clock = perf_counter
    play = _play
    evaluate = _heuristic
    priority = _move_priority
    lookup = table.get

    def search(position, depth, alpha, beta):
        nonlocal nodes
        nodes += 1
        if (nodes & 127) == 0 and clock() >= deadline:
            raise _SearchTimeout

        original_alpha = alpha
        entry = lookup(position)
        tt_move = -1

        if entry is not None:
            stored_depth, stored_value, flag, tt_move = entry
            if stored_depth >= depth:
                if flag == 0:
                    return stored_value
                if flag == 1 and stored_value >= beta:
                    return stored_value
                if flag == 2 and stored_value <= alpha:
                    return stored_value

        ours = sum(position[:6])
        theirs = sum(position[7:13])
        difference = position[6]

        if ours == 0 or theirs == 0:
            margin = difference + ours - theirs
            if margin > 0:
                value = _WIN + 100 * margin
            elif margin < 0:
                value = -_WIN + 100 * margin
            else:
                value = 0
            table[position] = (10000, value, 0, -1)
            return value

        # Even losing every remaining seed cannot change this outcome.
        if difference > ours + theirs:
            value = _WIN + 100 * difference
            table[position] = (10000, value, 0, -1)
            return value
        if -difference > ours + theirs:
            value = -_WIN + 100 * difference
            table[position] = (10000, value, 0, -1)
            return value

        if depth <= 0:
            value = evaluate(position, ours, theirs)
            if entry is None or entry[0] <= 0:
                table[position] = (0, value, 0, -1)
            return value

        ordered = []
        for move in range(6):
            seeds = position[move]
            if seeds:
                if move == tt_move:
                    rank = 10**12
                else:
                    h = move * 32 + (seeds if seeds < 32 else 31)
                    rank = priority(position, move) + history[h] // 32
                ordered.append((rank, move))
        ordered.sort(reverse=True)

        best_value = -_INF
        local_best = ordered[0][1]
        first = True

        for _, move in ordered:
            child, extra = play(position, move)
            child_depth = depth if extra else depth - 1

            # Principal-variation search: later moves first get a
            # narrow test window, then a full search if necessary.
            if first or depth <= 1:
                if extra:
                    value = search(child, child_depth, alpha, beta)
                else:
                    value = -search(child, child_depth, -beta, -alpha)
            else:
                if extra:
                    value = search(child, child_depth, alpha, alpha + 1)
                else:
                    value = -search(
                        child, child_depth, -alpha - 1, -alpha
                    )

                if alpha < value < beta:
                    if extra:
                        value = search(child, child_depth, alpha, beta)
                    else:
                        value = -search(
                            child, child_depth, -beta, -alpha
                        )

            first = False

            if value > best_value:
                best_value = value
                local_best = move

            if value > alpha:
                alpha = value

            if alpha >= beta:
                seeds = position[move]
                h = move * 32 + (seeds if seeds < 32 else 31)
                history[h] = min(3072, history[h] + depth * depth)
                break

        if best_value <= original_alpha:
            flag = 2
        elif best_value >= beta:
            flag = 1
        else:
            flag = 0

        table[position] = (depth, best_value, flag, local_best)
        return best_value

    last_score = 0

    try:
        for depth in range(1, 65):
            if clock() >= deadline:
                break

            if depth >= 3 and abs(last_score) < _WIN:
                lower = last_score - 175
                upper = last_score + 175
            else:
                lower, upper = -_INF, _INF

            score = search(state, depth, lower, upper)

            # A fail-high winning score already proves a winning move.
            proved_win = score >= _WIN and score >= upper

            if not proved_win and (score <= lower or score >= upper):
                score = search(state, depth, -_INF, _INF)

            result = lookup(state)
            if result is not None and result[3] in legal:
                best_move = result[3]

            last_score = score
            if abs(score) >= _WIN:
                break

    except (_SearchTimeout, RecursionError):
        pass

    if best_move not in legal:
        best_move = legal[0]
    return int(best_move)
