
import time

# Each path contains one complete sowing circuit.
# Houses: ours 0..5, opponent's 6..11; temporary store: 12.
_PATHS = tuple(
    tuple(range(i + 1, 6))
    + (12,)
    + tuple(range(6, 12))
    + tuple(range(i + 1))
    for i in range(6)
)

_TABLE = {}
_INF = 10**15
_EXACT, _LOWER, _UPPER = 0, 1, 2


class _SearchTimeout(Exception):
    pass


def _play(board, move):
    """Return (next board, immediate score differential, extra turn)."""
    stones = board[move]
    b = list(board)
    b.append(0)
    b[move] = 0

    rounds, remainder = divmod(stones, 13)

    if rounds:
        for j in range(13):
            b[j] += rounds

    path = _PATHS[move]
    for j in path[:remainder]:
        b[j] += 1

    last = path[remainder - 1] if remainder else move

    if last < 6 and b[last] == 1:
        opposite = 11 - last
        if b[opposite]:
            b[12] += b[opposite] + 1
            b[opposite] = 0
            b[last] = 0

    own = b[:6]
    other = b[6:12]
    reward = 100 * b[12]

    if not any(own) or not any(other):
        reward += 100 * (sum(own) - sum(other))
        return None, reward, False

    extra = last == 12
    if extra:
        child = tuple(own + other)
    else:
        child = tuple(other + own)

    return child, reward, extra


def _ordered_moves(board, preferred=-1):
    """Order moves without constructing their successor boards."""
    moves = []

    for i in range(6):
        n = board[i]
        if not n:
            continue

        rounds, remainder = divmod(n, 13)
        distance = 6 - i
        last = (i + remainder) % 13

        deposits = rounds + (remainder >= distance)
        passed = 6 * rounds + min(6, max(0, remainder - distance))

        captured = 0
        if (
            n <= 13
            and last < 6
            and (last == i or board[last] == 0)
        ):
            captured = board[11 - last] + (i + n >= 13)

        gain = deposits
        if captured:
            gain += captured + 1

        order = (
            60 * gain
            - 80 * passed
            + 80 * captured
            + 90 * (last == 6)
        )
        if i == preferred:
            order += 10**12

        moves.append((order, i))

    moves.sort(reverse=True)
    return moves


def _evaluate(board):
    own_seeds = sum(board[:6])
    other_seeds = sum(board[6:])

    own_capture = other_capture = 0
    own_extras = other_extras = 0
    mobility = 0
    exposure = 0

    for i in range(6):
        n = board[i]
        if n:
            mobility += 1
            exposure += min(6, max(0, n + i - 6))
            last = (i + n) % 13

            if last == 6:
                own_extras += 1
            elif (
                n <= 13
                and last < 6
                and (last == i or board[last] == 0)
            ):
                taken = board[11 - last] + (i + n >= 13)
                if taken:
                    own_capture = max(own_capture, 2 * taken + 1)

        n = board[6 + i]
        if n:
            mobility -= 1
            exposure -= min(6, max(0, n + i - 6))
            last = (i + n) % 13

            if last == 6:
                other_extras += 1
            elif (
                n <= 13
                and last < 6
                and (last == i or board[6 + last] == 0)
            ):
                taken = board[5 - last] + (i + n >= 13)
                if taken:
                    other_capture = max(other_capture, 2 * taken + 1)

    return (
        40 * (own_seeds - other_seeds)
        + 4 * mobility
        - 8 * exposure
        + 40 * own_capture
        - 25 * other_capture
        + 60 * own_extras
        - 40 * other_extras
    )


def policy(you: list[int], opponent: list[int]) -> int:
    legal = [i for i in range(6) if you[i] > 0]
    if len(legal) == 1:
        return legal[0]

    clock = time.perf_counter
    deadline = clock() + 0.90

    board = tuple(you[:6]) + tuple(opponent[:6])
    best_move = _ordered_moves(board)[0][1]

    # Stored values concern only future collections. Existing stores
    # contribute a constant, so they need not be part of the cache key.
    table = _TABLE
    if len(table) > 180000:
        table.clear()

    evaluate = _evaluate
    ordered_moves = _ordered_moves
    play = _play
    nodes = 0

    def search(position, depth, alpha, beta):
        nonlocal nodes
        nodes += 1
        if (nodes & 255) == 0 and clock() >= deadline:
            raise _SearchTimeout

        original_alpha = alpha
        entry = table.get(position)
        preferred = -1

        if entry is not None:
            old_depth, old_score, old_flag, preferred = entry
            if old_depth >= depth:
                if old_flag == _EXACT:
                    return old_score
                if old_flag == _LOWER and old_score >= beta:
                    return old_score
                if old_flag == _UPPER and old_score <= alpha:
                    return old_score

        if depth <= 0:
            value = evaluate(position)
            if entry is None or entry[0] <= 0:
                table[position] = (0, value, _EXACT, -1)
            return value

        moves = ordered_moves(position, preferred)
        best_score = -_INF
        selected = moves[0][1]

        can_reduce = (
            depth >= 4
            and beta - alpha == 1
            and sum(position) > 18
        )

        for number, (_, move) in enumerate(moves):
            child, reward, extra = play(position, move)

            if child is None:
                value = reward

            elif number == 0 or depth <= 1:
                if extra:
                    value = reward + search(
                        child, depth, alpha - reward, beta - reward
                    )
                else:
                    value = reward - search(
                        child, depth - 1, reward - beta, reward - alpha
                    )

            else:
                # Principal-variation search: test later moves with
                # a narrow window before performing a full re-search.
                if extra:
                    value = reward + search(
                        child, depth,
                        alpha - reward, alpha + 1 - reward
                    )
                else:
                    next_depth = depth - 1
                    reduction = int(
                        can_reduce
                        and number >= 3
                        and reward <= 100
                        and move != preferred
                    )
                    value = reward - search(
                        child, next_depth - reduction,
                        reward - alpha - 1, reward - alpha
                    )

                    if reduction and value > alpha:
                        value = reward - search(
                            child, next_depth,
                            reward - alpha - 1, reward - alpha
                        )

                if alpha < value < beta:
                    if extra:
                        value = reward + search(
                            child, depth,
                            alpha - reward, beta - reward
                        )
                    else:
                        value = reward - search(
                            child, depth - 1,
                            reward - beta, reward - alpha
                        )

            if value > best_score:
                best_score = value
                selected = move

            if value > alpha:
                alpha = value
            if alpha >= beta:
                break

        if best_score <= original_alpha:
            flag = _UPPER
        elif best_score >= beta:
            flag = _LOWER
        else:
            flag = _EXACT

        table[position] = (depth, best_score, flag, selected)
        return best_score

    previous_score = 0

    try:
        for depth in range(1, 65):
            if clock() >= deadline:
                break

            if depth <= 2:
                alpha, beta = -_INF, _INF
                margin = _INF
            else:
                margin = 175
                alpha = previous_score - margin
                beta = previous_score + margin

            while True:
                if clock() >= deadline:
                    raise _SearchTimeout

                value = search(board, depth, alpha, beta)

                if value <= alpha:
                    margin *= 2
                    alpha = max(-_INF, value - margin)
                elif value >= beta:
                    margin *= 2
                    beta = min(_INF, value + margin)
                else:
                    entry = table.get(board)
                    if entry is not None and entry[3] in legal:
                        best_move = entry[3]
                    previous_score = value
                    break

    except _SearchTimeout:
        pass

    return int(best_move if best_move in legal else legal[0])
