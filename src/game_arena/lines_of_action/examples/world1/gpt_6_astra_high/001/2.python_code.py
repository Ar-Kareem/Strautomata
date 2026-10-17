
import time

_FULL = (1 << 64) - 1
_NOT_A = _FULL ^ 0x0101010101010101
_NOT_H = _FULL ^ 0x8080808080808080
_BITS = tuple(1 << s for s in range(64))
_ROWS = tuple(s // 8 for s in range(64))
_COLS = tuple(s % 8 for s in range(64))
_SQUARE_SUM = tuple(_ROWS[s] ** 2 + _COLS[s] ** 2 for s in range(64))

_NEIGH = []
_CENTER = []
_EDGE = 0

for s in range(64):
    r, c = divmod(s, 8)
    neighbors = 0
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if (dr or dc) and 0 <= r + dr < 8 and 0 <= c + dc < 8:
                neighbors |= 1 << ((r + dr) * 8 + c + dc)
    _NEIGH.append(neighbors)
    _CENTER.append(-((2 * r - 7) ** 2 + (2 * c - 7) ** 2))
    if r in (0, 7) or c in (0, 7):
        _EDGE |= 1 << s

_NEIGH = tuple(_NEIGH)

# For each source and line, precompute endpoints and intervening squares
# for every possible population of that line.
_RAYS = []
for s in range(64):
    r, c = divmod(s, 8)
    axes = []
    for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
        line = 0
        for k in range(-7, 8):
            rr, cc = r + k * dr, c + k * dc
            if 0 <= rr < 8 and 0 <= cc < 8:
                line |= 1 << (rr * 8 + cc)

        distances = [()]
        for distance in range(1, 9):
            choices = []
            for sign in (-1, 1):
                rr = r + sign * distance * dr
                cc = c + sign * distance * dc
                if not (0 <= rr < 8 and 0 <= cc < 8):
                    continue
                target = rr * 8 + cc
                middle = 0
                for k in range(1, distance):
                    ar = r + sign * k * dr
                    ac = c + sign * k * dc
                    middle |= 1 << (ar * 8 + ac)
                choices.append((_BITS[target], middle, s * 64 + target))
            distances.append(tuple(choices))
        axes.append((line, tuple(distances)))
    _RAYS.append(tuple(axes))
_RAYS = tuple(_RAYS)

_FROM = tuple(_BITS[m >> 6] for m in range(4096))
_TO = tuple(_BITS[m & 63] for m in range(4096))
_CHANGE = tuple(_FROM[m] ^ _TO[m] for m in range(4096))
_KEEP = tuple(_FULL ^ _TO[m] for m in range(4096))
_ARRIVE = tuple(_NEIGH[m & 63] & ~_FROM[m] for m in range(4096))
_CENTER_GAIN = tuple(
    _CENTER[m & 63] - _CENTER[m >> 6] for m in range(4096)
)

_CONNECTED = 10000000
_MATE = 1000000
_INF = 2000000
_TEMPO = 7


def _legal_moves(mine, enemy):
    occupied = mine | enemy
    pieces = mine
    result = []
    append = result.append
    while pieces:
        bit = pieces & -pieces
        pieces ^= bit
        source = bit.bit_length() - 1
        for line, distances in _RAYS[source]:
            count = (occupied & line).bit_count()
            for target, middle, move in distances[count]:
                if not (target & mine) and not (middle & enemy):
                    append(move)
    return result


def _format_move(move):
    source, target = divmod(move, 64)
    return (
        str(source // 8) + "," + str(source % 8) + ":"
        + str(target // 8) + "," + str(target % 8)
    )


class _SearchTimeout(Exception):
    pass


def policy(board) -> str:
    deadline = time.perf_counter() + 0.90

    mine = 0
    enemy = 0
    for r in range(8):
        for c in range(8):
            value = board[r][c]
            if value == 1:
                mine |= 1 << (8 * r + c)
            elif value == -1:
                enemy |= 1 << (8 * r + c)

    root_moves = _legal_moves(mine, enemy)

    # Playable arena positions have at least one legal action.
    # Establish the fallback before any potentially interrupted search.
    best_move = root_moves[0]

    feature_cache = {}
    transpositions = {}
    history = [[0] * 4096 for _ in range(2)]
    killers = [[-1, -1] for _ in range(128)]
    nodes = 0
    clock = time.perf_counter

    def features(bits):
        cached = feature_cache.get(bits)
        if cached is not None:
            return cached

        n = bits.bit_count()
        if n <= 1:
            feature_cache[bits] = _CONNECTED
            return _CONNECTED

        # Exact eight-neighbor connected components.
        remaining = bits
        groups = []
        largest = 0
        largest_index = 0
        group_mass = 0

        while remaining:
            component = remaining & -remaining
            while True:
                horizontal = (
                    component
                    | ((component << 1) & _NOT_A)
                    | ((component >> 1) & _NOT_H)
                )
                expanded = bits & (
                    horizontal | (horizontal << 8) | (horizontal >> 8)
                )
                if expanded == component:
                    break
                component = expanded

            remaining ^= component
            size = component.bit_count()
            if size > largest:
                largest = size
                largest_index = len(groups)
            group_mass += size * size
            groups.append(component)

        group_count = len(groups)
        if group_count == 1:
            feature_cache[bits] = _CONNECTED
            return _CONNECTED

        # Prim's minimum spanning tree over components. Edge weights
        # are Chebyshev separation minus one, measured with dilations.
        tree = groups.pop(largest_index)
        remaining = bits ^ tree
        total_gap = 0
        worst_gap = 0

        while groups:
            reach = tree
            gap = -1
            while not (reach & remaining):
                horizontal = (
                    reach
                    | ((reach << 1) & _NOT_A)
                    | ((reach >> 1) & _NOT_H)
                )
                reach = (
                    horizontal | (horizontal << 8) | (horizontal >> 8)
                ) & _FULL
                gap += 1

            hit = reach & remaining
            for i, component in enumerate(groups):
                if component & hit:
                    break
            component = groups.pop(i)
            tree |= component
            remaining ^= component
            total_gap += gap
            if gap > worst_gap:
                worst_gap = gap

        sr = sc = square_sum = 0
        pieces = bits
        while pieces:
            bit = pieces & -pieces
            pieces ^= bit
            s = bit.bit_length() - 1
            sr += _ROWS[s]
            sc += _COLS[s]
            square_sum += _SQUARE_SUM[s]

        variance = (n * square_sum - sr * sr - sc * sc) / (n * n)
        centrality = (sr / n - 3.5) ** 2 + (sc / n - 3.5) ** 2

        links = (
            (bits & (bits >> 1) & _NOT_H).bit_count()
            + (bits & (bits >> 8)).bit_count()
            + (bits & (bits >> 9) & _NOT_H).bit_count()
            + (bits & (bits >> 7) & _NOT_A).bit_count()
        )

        score = int(
            -58 * total_gap
            -20 * (group_count - 1)
            -10 * worst_gap
            -11 * variance
            -3 * centrality
            +28 * largest / n
            +12 * group_mass / (n * n)
            +7 * links / n
            -5 * (bits & _EDGE).bit_count() / n
        )
        feature_cache[bits] = score
        return score

    def ordered_moves(moves, us, them, our_score, their_score, tt_move, ply):
        hist = history[ply & 1]
        killer0, killer1 = killers[ply]

        def rank(move):
            child_score = feature_cache.get(us ^ _CHANGE[move])
            if child_score == _CONNECTED:
                return 2000000000
            if move == tt_move:
                return 1000000000

            if child_score is None:
                value = (
                    28 * (
                        (_ARRIVE[move] & us).bit_count()
                        - (_NEIGH[move >> 6] & us).bit_count()
                    )
                    + _CENTER_GAIN[move] // 2
                )
            else:
                value = 3 * (child_score - our_score)

            if them & _TO[move]:
                captured_score = feature_cache.get(them & _KEEP[move])
                if captured_score == _CONNECTED:
                    return -1000000000
                if captured_score is not None:
                    value -= 3 * (captured_score - their_score)
                else:
                    value += 12 * (
                        (_NEIGH[move & 63] & them).bit_count() - 2
                    )
            elif move == killer0:
                value += 1100
            elif move == killer1:
                value += 900

            return value + hist[move] // 16

        moves.sort(key=rank, reverse=True)
        return moves

    def search(us, them, depth, alpha, beta, ply):
        nonlocal nodes
        nodes += 1
        if (nodes & 63) == 0 and clock() >= deadline:
            raise _SearchTimeout

        # The previous mover wins if both sides became connected.
        their_score = features(them)
        if their_score == _CONNECTED:
            return -_MATE + ply
        our_score = features(us)
        if our_score == _CONNECTED:
            return _MATE - ply

        if depth <= 0:
            return our_score - their_score + _TEMPO

        key = (us, them)
        entry = transpositions.get(key)
        tt_move = -1
        if entry is not None:
            stored_depth, value, bound, tt_move = entry
            if value > _MATE - 1000:
                value -= ply
            elif value < -_MATE + 1000:
                value += ply
            if stored_depth >= depth:
                if bound == 0:
                    return value
                if bound == 1 and value >= beta:
                    return value
                if bound == 2 and value <= alpha:
                    return value

        moves = _legal_moves(us, them)
        if not moves:
            # Standard LOA passes a turn when no move is available.
            return -search(them, us, depth - 1, -beta, -alpha, ply + 1)

        ordered_moves(
            moves, us, them, our_score, their_score, tt_move, ply
        )

        original_alpha = alpha
        best_value = -_INF
        local_best = moves[0]
        killer0, killer1 = killers[ply]

        for index, move in enumerate(moves):
            next_us = us ^ _CHANGE[move]
            next_them = them & _KEEP[move]
            capture = next_them != them

            if depth == 1:
                # Inline the final ply, avoiding recursive-call overhead.
                nodes += 1
                if (nodes & 63) == 0 and clock() >= deadline:
                    raise _SearchTimeout

                moved_score = features(next_us)
                if moved_score == _CONNECTED:
                    value = _MATE - ply - 1
                else:
                    other_score = features(next_them) if capture else their_score
                    if other_score == _CONNECTED:
                        value = -_MATE + ply + 1
                    else:
                        value = moved_score - other_score - _TEMPO

            elif index == 0:
                value = -search(
                    next_them, next_us, depth - 1, -beta, -alpha, ply + 1
                )
            else:
                reduce = (
                    depth >= 3
                    and index >= 6
                    and not capture
                    and move != killer0
                    and move != killer1
                    and move != tt_move
                )
                reduced_depth = depth - 1 - int(reduce)
                value = -search(
                    next_them, next_us, reduced_depth,
                    -alpha - 1, -alpha, ply + 1
                )
                if reduce and value > alpha:
                    value = -search(
                        next_them, next_us, depth - 1,
                        -alpha - 1, -alpha, ply + 1
                    )
                if alpha < value < beta:
                    value = -search(
                        next_them, next_us, depth - 1,
                        -beta, -alpha, ply + 1
                    )

            if value > best_value:
                best_value = value
                local_best = move
            if value > alpha:
                alpha = value
            if alpha >= beta:
                if not capture:
                    if killers[ply][0] != move:
                        killers[ply][1] = killers[ply][0]
                        killers[ply][0] = move
                    hist = history[ply & 1]
                    hist[move] = min(
                        16384, hist[move] + 32 * depth * depth
                    )
                break

        if best_value <= original_alpha:
            bound = 2
        elif best_value >= beta:
            bound = 1
        else:
            bound = 0

        stored_value = best_value
        if stored_value > _MATE - 1000:
            stored_value += ply
        elif stored_value < -_MATE + 1000:
            stored_value -= ply

        if entry is None or depth >= entry[0] or bound == 0:
            transpositions[key] = (
                depth, stored_value, bound, local_best
            )
        return best_value

    # Complete a one-ply evaluation first, checking every immediate win.
    root_scores = {}
    for move in root_moves:
        next_mine = mine ^ _CHANGE[move]
        next_enemy = enemy & _KEEP[move]
        our_score = features(next_mine)
        if our_score == _CONNECTED:
            return _format_move(move)

        their_score = features(next_enemy)
        if their_score == _CONNECTED:
            root_scores[move] = -_MATE + 1
        else:
            root_scores[move] = our_score - their_score - _TEMPO

    root_moves.sort(key=root_scores.__getitem__, reverse=True)
    best_move = root_moves[0]

    try:
        for depth in range(2, 33):
            previous_best = best_move
            root_moves.sort(
                key=lambda m: (m == previous_best, root_scores[m]),
                reverse=True
            )
            alpha = -_INF
            iteration_best = -_INF

            for index, move in enumerate(root_moves):
                if clock() >= deadline:
                    raise _SearchTimeout

                next_mine = mine ^ _CHANGE[move]
                next_enemy = enemy & _KEEP[move]

                if index == 0:
                    value = -search(
                        next_enemy, next_mine, depth - 1,
                        -_INF, _INF, 1
                    )
                else:
                    reduce = (
                        depth >= 4
                        and index >= 8
                        and next_enemy == enemy
                    )
                    value = -search(
                        next_enemy, next_mine,
                        depth - 1 - int(reduce),
                        -alpha - 1, -alpha, 1
                    )
                    if reduce and value > alpha:
                        value = -search(
                            next_enemy, next_mine, depth - 1,
                            -alpha - 1, -alpha, 1
                        )
                    if value > alpha:
                        value = -search(
                            next_enemy, next_mine, depth - 1,
                            -_INF, -alpha, 1
                        )

                root_scores[move] = value
                if value > iteration_best:
                    iteration_best = value
                    # Only completed child searches may update the answer.
                    best_move = move
                if value > alpha:
                    alpha = value

                if value >= _MATE - 2:
                    return _format_move(best_move)

            if iteration_best > _MATE - 1000:
                break

    except _SearchTimeout:
        pass

    return _format_move(best_move)
