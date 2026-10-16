
import time

# Entries: board -> (depth, bound_type, score, best_move)
# Bound types: 0 = exact, 1 = lower bound, 2 = upper bound.
_TABLE = {}


class _SearchTimeout(Exception):
    pass


def _play(board, move):
    """Return (next board, same player moves again, captured seed count)."""
    b = list(board)
    seeds = b[move]
    b[move] = 0

    # In this orientation the sowing circuit is exactly indices 0..12.
    # Index 13 is the opponent's store and is never visited.
    laps, remainder = divmod(seeds, 13)
    if laps:
        for k in range(13):
            b[k] += laps

    last = move
    for _ in range(remainder):
        last += 1
        if last == 13:
            last = 0
        b[last] += 1

    captured = 0
    if last < 6 and b[last] == 1:
        opposite = 12 - last
        if b[opposite]:
            captured = b[opposite] + 1
            b[6] += captured
            b[last] = 0
            b[opposite] = 0

    if last == 6:
        return tuple(b), True, captured

    # Keep every search position oriented toward its player to move.
    return tuple(b[7:] + b[:7]), False, captured


def _features(pits, opposing):
    positional = 40 * sum(pits)
    extra_turns = 0
    best_capture = 0

    for i, seeds in enumerate(pits):
        if not seeds:
            continue

        positional += 3  # Flexibility from having another playable house.

        # Large houses near the store will have to feed the opposing side.
        spill = seeds + i - 6
        if spill > 0:
            positional -= 6 * min(spill, 6)

        landing = (i + seeds) % 13

        if landing == 6:
            extra_turns += 32 if seeds < 13 else 8

        elif (
            seeds <= 13
            and landing < 6
            and (landing == i or pits[landing] == 0)
        ):
            wrapped = landing <= i
            opposite_seeds = opposing[5 - landing] + int(wrapped)

            if opposite_seeds:
                # Material improvement, including the cost of feeding seeds
                # around the opposing side when the move wraps.
                gain = 140 * opposite_seeds + 60
                if wrapped:
                    gain -= 420
                if gain > best_capture:
                    best_capture = gain

    return positional, extra_turns, best_capture


def _evaluate(board):
    ours = board[:6]
    theirs = board[7:13]
    a, ae, ac = _features(ours, theirs)
    b, be, bc = _features(theirs, ours)

    return (
        100 * (board[6] - board[13])
        + a - b
        + ae - (3 * be) // 4
        + (3 * ac) // 5 - (2 * bc) // 5
    )


def policy(you: list[int], opponent: list[int]) -> int:
    clock = time.perf_counter
    deadline = clock() + 0.91

    legal = [i for i in range(6) if you[i] > 0]
    if len(legal) == 1:
        return int(legal[0])

    board = tuple(you) + tuple(opponent)
    total = sum(board)

    # A proved win must dominate every heuristic evaluation.
    win_score = 100000 + 1000 * total
    infinity = win_score + 200 * total + 10000

    table = _TABLE
    if len(table) > 150000:
        table.clear()

    killers = [[-1, -1] for _ in range(162)]
    history = [0] * 6
    nodes = 0

    def terminal_value(difference):
        if difference > 0:
            return win_score + 100 * difference
        if difference < 0:
            return -win_score + 100 * difference
        return 0

    def ordered_moves(position, hint, ply):
        ranked = []
        first_killer, second_killer = killers[ply]

        for i in range(6):
            seeds = position[i]
            if not seeds:
                continue

            laps, remainder = divmod(seeds, 13)
            endpoint = i + remainder
            landing = endpoint if endpoint < 13 else endpoint - 13

            feed = endpoint - 6
            if feed < 0:
                feed = 0
            elif feed > 6:
                feed = 6

            store_gain = laps + int(endpoint >= 6)
            opposing_gain = 6 * laps + feed
            tactical = 60 * store_gain - 80 * opposing_gain

            if landing == 6:
                tactical += 150
            elif (
                seeds <= 13
                and landing < 6
                and (landing == i or position[landing] == 0)
            ):
                opposite_seeds = (
                    position[12 - landing] + int(landing <= i)
                )
                if opposite_seeds:
                    tactical += 140 * opposite_seeds + 60

            priority = 16 * tactical + history[i]
            if i == first_killer:
                priority += 6000
            elif i == second_killer:
                priority += 3000
            if i == hint:
                priority += 1000000000

            ranked.append((priority, i))

        ranked.sort(reverse=True)
        return [i for _, i in ranked]

    entry = table.get(board)
    hint = entry[3] if entry is not None else -1
    best_move = ordered_moves(board, hint, 0)[0]

    def search(position, depth, alpha, beta, ply):
        nonlocal nodes
        nodes += 1
        if (nodes & 63) == 0 and clock() >= deadline:
            raise _SearchTimeout

        entry = table.get(position)
        hint = -1
        if entry is not None:
            stored_depth, bound, value, hint = entry
            if stored_depth >= depth:
                if bound == 0:
                    return value
                if bound == 1 and value >= beta:
                    return value
                if bound == 2 and value <= alpha:
                    return value

        # Apply the end-of-game sweep exactly.
        if not any(position[:6]) or not any(position[7:13]):
            difference = (
                position[6] + sum(position[:6])
                - position[13] - sum(position[7:13])
            )
            value = terminal_value(difference)
            table[position] = (10000, 0, value, -1)
            return value

        # Secured majorities prove the result without further search.
        if 2 * position[6] > total:
            value = win_score + 100 * (2 * position[6] - total)
            table[position] = (10000, 0, value, -1)
            return value
        if 2 * position[13] > total:
            value = -win_score - 100 * (2 * position[13] - total)
            table[position] = (10000, 0, value, -1)
            return value

        if depth <= 0 or ply >= 160:
            value = _evaluate(position)
            if entry is None and ply < 160:
                table[position] = (0, 0, value, -1)
            return value

        moves = ordered_moves(position, hint, ply)
        forced = len(moves) == 1
        original_alpha = alpha
        best_value = -infinity
        selected = moves[0]

        for move_number, move in enumerate(moves):
            child, extra, captured = _play(position, move)

            # Extra turns and forced continuations are searched through.
            next_depth = depth if extra or forced else depth - 1

            reduce = (
                depth >= 4
                and move_number >= 3
                and ply > 0
                and not extra
                and not forced
                and not captured
                and position[move] < 13
                and move not in killers[ply]
            )

            if reduce:
                # Probe late quiet moves more cheaply, then restore full
                # depth whenever the move might improve the result.
                value = -search(
                    child, next_depth - 1,
                    -alpha - 1, -alpha, ply + 1
                )
                if value > alpha:
                    value = -search(
                        child, next_depth,
                        -alpha - 1, -alpha, ply + 1
                    )
                    if alpha < value < beta:
                        value = -search(
                            child, next_depth,
                            -beta, -alpha, ply + 1
                        )

            elif move_number == 0 or depth <= 2:
                if extra:
                    value = search(
                        child, next_depth, alpha, beta, ply + 1
                    )
                else:
                    value = -search(
                        child, next_depth, -beta, -alpha, ply + 1
                    )

            else:
                # Principal-variation search.
                if extra:
                    value = search(
                        child, next_depth, alpha, alpha + 1, ply + 1
                    )
                    if alpha < value < beta:
                        value = search(
                            child, next_depth, alpha, beta, ply + 1
                        )
                else:
                    value = -search(
                        child, next_depth, -alpha - 1, -alpha, ply + 1
                    )
                    if alpha < value < beta:
                        value = -search(
                            child, next_depth, -beta, -alpha, ply + 1
                        )

            if value > best_value:
                best_value = value
                selected = move
            if value > alpha:
                alpha = value

            if alpha >= beta:
                if not captured and not extra:
                    if killers[ply][0] != move:
                        killers[ply][1] = killers[ply][0]
                        killers[ply][0] = move
                    bonus = min(512, 8 * depth * depth)
                    history[move] += (
                        bonus - history[move] * bonus // 8192
                    )
                break

        if best_value <= original_alpha:
            bound = 2
        elif best_value >= beta:
            bound = 1
        else:
            bound = 0

        if ply == 0 or entry is None or depth >= entry[0]:
            table[position] = (depth, bound, best_value, selected)

        return best_value

    previous_score = 0

    try:
        for depth in range(1, 81):
            if clock() >= deadline:
                break

            width = 200
            if depth < 4:
                alpha, beta = -infinity, infinity
            else:
                alpha = previous_score - width
                beta = previous_score + width

            while True:
                score = search(board, depth, alpha, beta, 0)
                root_entry = table.get(board)
                candidate = best_move
                if root_entry is not None:
                    move = root_entry[3]
                    if 0 <= move < 6 and you[move] > 0:
                        candidate = move

                if abs(score) >= win_score:
                    return int(candidate)

                if score <= alpha:
                    width *= 2
                    alpha = max(-infinity, score - width)
                elif score >= beta:
                    width *= 2
                    beta = min(infinity, score + width)
                else:
                    best_move = candidate
                    previous_score = score
                    break

                if clock() >= deadline:
                    raise _SearchTimeout

    except _SearchTimeout:
        pass

    if 0 <= best_move < 6 and you[best_move] > 0:
        return int(best_move)
    return int(legal[0])
