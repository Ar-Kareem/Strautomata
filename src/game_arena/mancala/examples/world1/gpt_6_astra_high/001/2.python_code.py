
import time

_WIN = 1_000_000
_INF = 2_000_000
_EXACT, _LOWER, _UPPER = 0, 1, 2

# Retaining this table also helps when the arena reuses the Python process.
_TT = {}


class _SearchTimeout(Exception):
    pass


def _play(state, move):
    """Return (child in its active player's orientation, extra_turn)."""
    board = list(state)
    seeds = board[move]
    board[move] = 0

    # The sowing ring has 13 positions: skip the opponent's store.
    rounds, remainder = divmod(seeds, 13)
    if rounds:
        for j in range(13):
            board[j] += rounds

    last = move
    for _ in range(remainder):
        last += 1
        if last == 13:
            last = 0
        board[last] += 1

    extra = last == 6

    if last < 6 and board[last] == 1:
        opposite = 12 - last
        if board[opposite]:
            board[6] += board[opposite] + 1
            board[last] = 0
            board[opposite] = 0

    own_empty = not (
        board[0] or board[1] or board[2]
        or board[3] or board[4] or board[5]
    )
    other_empty = not (
        board[7] or board[8] or board[9]
        or board[10] or board[11] or board[12]
    )

    if own_empty or other_empty:
        board[6] += sum(board[:6])
        board[13] += sum(board[7:13])
        board[:6] = [0] * 6
        board[7:13] = [0] * 6

    if extra:
        return tuple(board), True
    return tuple(board[7:] + board[:7]), False


def _ordered_moves(state, preferred=-1):
    ranked = []

    for i in range(6):
        seeds = state[i]
        if not seeds:
            continue

        landing = (i + seeds) % 13
        extra = landing == 6
        capture = 0

        # A capture is impossible after more than one complete circuit.
        if seeds <= 13 and landing < 6:
            if landing == i or state[landing] == 0:
                opposite = state[12 - landing] + int(i + seeds >= 13)
                if opposite:
                    capture = opposite + 1

        banked = (seeds + i + 7) // 13
        spill = min(6, max(0, i + (seeds % 13) - 6))
        rank = (
            700 * extra
            + 180 * capture
            + 45 * banked
            - 8 * spill
            + i
        )
        if i == preferred:
            rank += 10_000_000

        ranked.append((rank, i))

    ranked.sort(reverse=True)
    return [i for _, i in ranked]


def _features(state, offset, opposite_offset):
    material = 0
    mobility = 0
    extras = 0
    largest_capture = 0

    for i in range(6):
        seeds = state[offset + i]
        if not seeds:
            continue

        material += seeds
        mobility += 1
        landing = (i + seeds) % 13

        if landing == 6:
            extras += 1
        elif seeds <= 13 and landing < 6:
            if landing == i or state[offset + landing] == 0:
                capturable = (
                    state[opposite_offset + 5 - landing]
                    + int(i + seeds >= 13)
                )
                if capturable > largest_capture:
                    largest_capture = capturable

    return material, mobility, extras, largest_capture


def _evaluate(state):
    a = _features(state, 0, 7)
    b = _features(state, 7, 0)

    remaining = a[0] + b[0]
    material_weight = 60 if remaining <= 12 else 48

    value = (
        128 * (state[6] - state[13])
        + material_weight * (a[0] - b[0])
        + 8 * (a[1] - b[1])
        + 60 * a[2] - 32 * b[2]
        + 88 * a[3] - 44 * b[3]
        + (24 if a[3] else 0)
        - (12 if b[3] else 0)
        + 12
    )

    # Keep heuristic values strictly below proven outcomes, even on
    # unusually large, but otherwise valid, input positions.
    return max(-_WIN // 2, min(_WIN // 2, value))


def policy(you: list[int], opponent: list[int]) -> int:
    started = time.perf_counter()
    deadline = started + 0.90

    root = tuple(you) + tuple(opponent)
    legal = [i for i in range(6) if you[i] > 0]
    best_move = _ordered_moves(root)[0]

    table = _TT
    if len(table) > 150_000:
        table.clear()

    total = sum(root)
    half = total // 2
    nodes = 0

    def search(state, depth, alpha, beta, ply):
        nonlocal nodes
        nodes += 1
        if (nodes & 127) == 0:
            if time.perf_counter() >= deadline:
                raise _SearchTimeout

        # Stores never lose seeds, so a strict majority proves the result.
        if state[6] > half:
            return _WIN
        if state[13] > half:
            return -_WIN
        if state[6] + state[13] == total:
            return 0

        entry = table.get(state)
        preferred = -1
        if entry is not None:
            saved_depth, saved_value, flag, preferred = entry
            if saved_depth >= depth:
                if flag == _EXACT:
                    return saved_value
                if flag == _LOWER and saved_value >= beta:
                    return saved_value
                if flag == _UPPER and saved_value <= alpha:
                    return saved_value

        if ply >= 120:
            return _evaluate(state)

        if depth <= 0:
            value = _evaluate(state)
            if entry is None or entry[0] <= 0:
                table[state] = (0, value, _EXACT, -1)
            return value

        original_alpha = alpha
        best_value = -_INF
        chosen = -1
        first = True

        for move in _ordered_moves(state, preferred):
            child, extra = _play(state, move)

            if extra:
                # A complete extra-turn sequence belongs to this turn.
                if first:
                    value = search(child, depth, alpha, beta, ply + 1)
                else:
                    value = search(
                        child, depth, alpha, alpha + 1, ply + 1
                    )
                    if alpha < value < beta:
                        value = search(
                            child, depth, alpha, beta, ply + 1
                        )
            else:
                if first:
                    value = -search(
                        child, depth - 1, -beta, -alpha, ply + 1
                    )
                else:
                    value = -search(
                        child, depth - 1, -alpha - 1, -alpha, ply + 1
                    )
                    if alpha < value < beta:
                        value = -search(
                            child, depth - 1, -beta, -alpha, ply + 1
                        )

            first = False

            if value > best_value:
                best_value = value
                chosen = move

            if value > alpha:
                alpha = value

            if alpha >= beta:
                break

        if best_value <= original_alpha:
            flag = _UPPER
        elif best_value >= beta:
            flag = _LOWER
        else:
            flag = _EXACT

        table[state] = (depth, best_value, flag, chosen)
        return best_value

    previous_score = None

    try:
        for depth in range(1, 65):
            if time.perf_counter() >= deadline:
                break

            if previous_score is None or depth <= 3:
                alpha, beta = -_INF, _INF
            else:
                alpha = previous_score - 192
                beta = previous_score + 192

            score = search(root, depth, alpha, beta, 0)
            entry = table.get(root)
            candidate = entry[3] if entry is not None else best_move

            if abs(score) == _WIN:
                if candidate in legal:
                    best_move = candidate
                break

            if score <= alpha or score >= beta:
                # A fail-high move is a useful fallback if the full-window
                # retry runs out of time.
                if score >= beta and candidate in legal:
                    best_move = candidate

                score = search(root, depth, -_INF, _INF, 0)
                entry = table.get(root)
                candidate = entry[3] if entry is not None else best_move

            if candidate in legal:
                best_move = candidate
            previous_score = score

            if abs(score) == _WIN:
                break

    except (_SearchTimeout, RecursionError):
        pass

    # The API guarantees at least one legal move.
    return int(best_move if best_move in legal else legal[0])
