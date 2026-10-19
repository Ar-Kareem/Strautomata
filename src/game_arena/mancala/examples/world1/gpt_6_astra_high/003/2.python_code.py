
from time import perf_counter

# Reused across calls when the arena keeps the Python process alive.
_TT = {}
_EXACT = 0
_LOWER = 1
_UPPER = 2


class _SearchTimeout(Exception):
    pass


def _play(board, move):
    """Return (next board, same player moves again, ordering score)."""
    b = list(board)
    seeds = b[move]
    b[move] = 0

    # Indices 0..12 form the sowing circuit; index 13 is skipped.
    laps, remainder = divmod(seeds, 13)
    if laps:
        for j in range(13):
            b[j] += laps

    last = move
    for _ in range(remainder):
        last += 1
        if last == 13:
            last = 0
        b[last] += 1

    again = last == 6

    if last < 6 and b[last] == 1:
        opposite = 12 - last
        if b[opposite]:
            b[6] += b[opposite] + 1
            b[last] = 0
            b[opposite] = 0

    own_seeds = sum(b[:6])
    enemy_seeds = sum(b[7:13])

    if own_seeds == 0 or enemy_seeds == 0:
        own_store = b[6] + own_seeds
        enemy_store = b[13] + enemy_seeds
        b = [0, 0, 0, 0, 0, 0, own_store,
             0, 0, 0, 0, 0, 0, enemy_store]
        own_seeds = enemy_seeds = 0

    order = (
        100 * (b[6] - b[13])
        + 30 * (own_seeds - enemy_seeds)
        + 90 * again
    )

    if again:
        return tuple(b), True, order

    # Orient every search position toward its player to move.
    return tuple(b[7:] + b[:7]), False, order


def _ordered_moves(board, hint):
    # Search the transposition-table move before constructing other children.
    if 0 <= hint < 6 and board[hint] > 0:
        child, again, _ = _play(board, hint)
        yield hint, child, again
    else:
        hint = -1

    moves = []
    for move in range(6):
        if board[move] and move != hint:
            child, again, order = _play(board, move)
            moves.append((order, move, child, again))

    moves.sort(reverse=True)
    for _, move, child, again in moves:
        yield move, child, again


def _evaluate(board):
    value = 100 * (board[6] - board[13])

    for base, enemy in ((0, 7), (7, 0)):
        material = 0
        mobility = 0
        bonuses = 0
        best_capture = 0
        spill = 0

        for i in range(6):
            seeds = board[base + i]
            if not seeds:
                continue

            material += seeds
            mobility += 1
            distance = 6 - i
            last = (i + seeds) % 13

            if last == 6:
                bonuses += 1

            # A capture can only finish with one seed in the landing
            # house when the move contains at most one complete circuit.
            elif (
                seeds <= 13
                and last < 6
                and (last == i or board[base + last] == 0)
            ):
                opposite_seeds = board[enemy + 5 - last]
                if i + seeds >= 13:
                    opposite_seeds += 1
                if opposite_seeds:
                    captured = opposite_seeds + 1
                    if captured > best_capture:
                        best_capture = captured

            # Large piles must eventually distribute some seeds to
            # the other side, so their current ownership is discounted.
            if seeds > distance:
                laps, remainder = divmod(seeds, 13)
                spill += 6 * laps
                excess = remainder - distance
                if excess > 0:
                    spill += min(excess, 6)

        positional = 42 * material + 4 * mobility - 16 * spill

        if base == 0:
            value += positional + 24 * bonuses + 40 * best_capture
        else:
            value -= positional + 16 * bonuses + 26 * best_capture

    return value


def policy(you: list[int], opponent: list[int]) -> int:
    started = perf_counter()
    legal = [i for i in range(6) if you[i] > 0]

    # The API guarantees at least one legal move.
    if len(legal) == 1:
        return legal[0]

    board = tuple(you) + tuple(opponent)

    # Establish a legal, tactically sensible answer before doing any search.
    best_move = legal[0]
    best_order = None
    for move in legal:
        _, _, order = _play(board, move)
        if best_order is None or order > best_order:
            best_order = order
            best_move = move

    if not any(opponent[:6]):
        return best_move

    # Bound persistent memory use. Clearing is included in the time budget.
    if len(_TT) > 120_000:
        _TT.clear()

    table = _TT
    deadline = started + 0.90
    total = sum(board)
    win = 100_000 + 1000 * total
    infinity = 4 * win

    nodes = 0
    root_choice = best_move

    def search(position, depth, alpha, beta, at_root=False):
        nonlocal nodes, root_choice

        nodes += 1
        if (nodes & 127) == 0 and perf_counter() >= deadline:
            raise _SearchTimeout

        own_store = position[6]
        enemy_store = position[13]

        # Once more than half the seeds are banked, the outcome cannot
        # change. The added margin is the minimum guaranteed final lead.
        if 2 * own_store > total:
            return win + 100 * (2 * own_store - total)
        if 2 * enemy_store > total:
            return -win - 100 * (2 * enemy_store - total)
        if own_store + enemy_store == total:
            return 0

        original_alpha = alpha
        entry = table.get(position)
        hint = -1

        if entry is not None:
            saved_depth, saved_value, flag, hint = entry
            if saved_depth >= depth:
                usable = (
                    flag == _EXACT
                    or (flag == _LOWER and saved_value >= beta)
                    or (flag == _UPPER and saved_value <= alpha)
                )
                if usable:
                    if at_root and 0 <= hint < 6 and position[hint]:
                        root_choice = hint
                    return saved_value

        if depth <= 0:
            value = _evaluate(position)
            if entry is None or entry[0] <= 0:
                table[position] = (0, value, _EXACT, -1)
            return value

        best_value = -infinity
        chosen = -1
        first = True

        for move, child, again in _ordered_moves(position, hint):
            next_depth = depth if again else depth - 1

            if first or depth <= 2:
                if again:
                    value = search(child, next_depth, alpha, beta)
                else:
                    value = -search(child, next_depth, -beta, -alpha)
            else:
                # Principal-variation search: most later moves only
                # need a narrow-window test.
                if again:
                    value = search(child, next_depth, alpha, alpha + 1)
                else:
                    value = -search(
                        child, next_depth, -alpha - 1, -alpha
                    )

                if alpha < value < beta:
                    if again:
                        value = search(child, next_depth, alpha, beta)
                    else:
                        value = -search(
                            child, next_depth, -beta, -alpha
                        )

            first = False

            if value > best_value:
                best_value = value
                chosen = move

            if value > alpha:
                alpha = value

            if alpha >= beta:
                break

        # Defensive handling; normally terminal positions were swept
        # by _play and handled above.
        if chosen < 0:
            difference = (
                own_store - enemy_store - sum(position[7:13])
            )
            if difference > 0:
                return win + 100 * difference
            if difference < 0:
                return -win + 100 * difference
            return 0

        if best_value <= original_alpha:
            flag = _UPPER
        elif best_value >= beta:
            flag = _LOWER
        else:
            flag = _EXACT

        if entry is None or depth >= entry[0] or flag == _EXACT:
            table[position] = (depth, best_value, flag, chosen)

        if at_root:
            root_choice = chosen

        return best_value

    previous_value = None

    for depth in range(1, 65):
        if perf_counter() >= deadline:
            break

        root_choice = best_move

        if depth >= 4 and previous_value is not None:
            alpha = previous_value - 180
            beta = previous_value + 180
        else:
            alpha = -infinity
            beta = infinity

        try:
            value = search(board, depth, alpha, beta, True)

            # Repeat failed aspiration searches with unrestricted bounds.
            if value <= alpha or value >= beta:
                value = search(
                    board, depth, -infinity, infinity, True
                )

        except (_SearchTimeout, RecursionError):
            break

        # Only completed iterations replace the trusted answer.
        if root_choice in legal:
            best_move = root_choice
        previous_value = value

        if abs(value) >= win:
            break

    return best_move if 0 <= best_move < 6 and you[best_move] else legal[0]
