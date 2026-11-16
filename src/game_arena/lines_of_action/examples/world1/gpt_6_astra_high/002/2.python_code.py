
import time

_FULL = (1 << 64) - 1
_NOT_A = _FULL ^ 0x0101010101010101
_NOT_H = _FULL ^ 0x8080808080808080
_BITS = tuple(1 << i for i in range(64))
_X = tuple(i & 7 for i in range(64))
_Y = tuple(i >> 3 for i in range(64))
_SQ = tuple(_X[i] ** 2 + _Y[i] ** 2 for i in range(64))
_EDGE = tuple(
    int(_X[i] in (0, 7) or _Y[i] in (0, 7))
    for i in range(64)
)

_MATE = 1000000
_INF = 100000000


def _halo(bits):
    horizontal = (
        bits
        | ((bits & _NOT_H) << 1)
        | ((bits & _NOT_A) >> 1)
    )
    return (
        horizontal | (horizontal << 8) | (horizontal >> 8)
    ) & _FULL


_ADJ = tuple(_halo(_BITS[i]) ^ _BITS[i] for i in range(64))
_FROM = tuple(_BITS[m >> 6] for m in range(4096))
_TO = tuple(_BITS[m & 63] for m in range(4096))
_CHANGE = tuple(_FROM[m] | _TO[m] for m in range(4096))
_DX = tuple(_X[m & 63] - _X[m >> 6] for m in range(4096))
_DY = tuple(_Y[m & 63] - _Y[m >> 6] for m in range(4096))
_DSQ = tuple(_SQ[m & 63] - _SQ[m >> 6] for m in range(4096))


def _build_move_tables():
    tables = []
    for source in range(64):
        r, c = divmod(source, 8)
        axes = []
        for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
            line = 0
            for step in range(-7, 8):
                rr = r + step * dr
                cc = c + step * dc
                if 0 <= rr < 8 and 0 <= cc < 8:
                    line |= _BITS[rr * 8 + cc]

            distances = [()]
            for distance in range(1, 9):
                choices = []
                for sign in (1, -1):
                    rr = r + sign * distance * dr
                    cc = c + sign * distance * dc
                    if not (0 <= rr < 8 and 0 <= cc < 8):
                        continue
                    target = rr * 8 + cc
                    path = 0
                    for step in range(1, distance):
                        pr = r + sign * step * dr
                        pc = c + sign * step * dc
                        path |= _BITS[pr * 8 + pc]
                    choices.append((
                        (source << 6) | target,
                        _BITS[target],
                        path,
                    ))
                distances.append(tuple(choices))
            axes.append((line, tuple(distances)))
        tables.append(tuple(axes))
    return tuple(tables)


_TABLES = _build_move_tables()


def _legal_moves(own, enemy):
    occupied = own | enemy
    pieces = own
    result = []
    while pieces:
        bit = pieces & -pieces
        pieces ^= bit
        source = bit.bit_length() - 1
        for line, distances in _TABLES[source]:
            count = (occupied & line).bit_count()
            for move, target, path in distances[count]:
                if not (target & own) and not (path & enemy):
                    result.append(move)
    return result


def _connected(pieces):
    if not pieces:
        return False
    reached = pieces & -pieces
    while True:
        horizontal = (
            reached
            | ((reached & _NOT_H) << 1)
            | ((reached & _NOT_A) >> 1)
        )
        expanded = (
            horizontal | (horizontal << 8) | (horizontal >> 8)
        ) & pieces
        if expanded == reached:
            return reached == pieces
        reached = expanded


def _format_move(move):
    source, target = move >> 6, move & 63
    return (
        f"{source >> 3},{source & 7}:"
        f"{target >> 3},{target & 7}"
    )


class _SearchTimeout(Exception):
    pass


def policy(board) -> str:
    start = time.perf_counter()
    deadline = start + 0.90

    own = 0
    enemy = 0
    for r in range(8):
        for c in range(8):
            value = int(board[r][c])
            if value == 1:
                own |= _BITS[r * 8 + c]
            elif value == -1:
                enemy |= _BITS[r * 8 + c]

    legal = _legal_moves(own, enemy)

    # Arena calls are expected to be nonterminal positions with a legal move.
    # Establish the fallback before beginning any timed search.
    chosen = legal[0]

    features = {}
    pattern_cache = {}
    winning_cache = {}
    transpositions = {}
    killers = [[-1, -1] for _ in range(128)]
    history = [[0] * 4096 for _ in range(2)]
    nodes = 0

    def info(pieces):
        cached = features.get(pieces)
        if cached is not None:
            return cached

        remaining = pieces
        components = []
        largest = 0
        isolated = 0

        while remaining:
            component = remaining & -remaining
            while True:
                horizontal = (
                    component
                    | ((component & _NOT_H) << 1)
                    | ((component & _NOT_A) >> 1)
                )
                expanded = (
                    horizontal | (horizontal << 8) | (horizontal >> 8)
                ) & pieces
                if expanded == component:
                    break
                component = expanded

            remaining &= ~component
            components.append(component)
            size = component.bit_count()
            if size > largest:
                largest = size
            if size == 1:
                isolated += 1

        groups = tuple(components)
        n = pieces.bit_count()

        if n == 0:
            result = (-_MATE, groups, 0, 0, 0)
            features[pieces] = result
            return result

        # Connected formations are terminal; their static score is unused.
        if len(groups) == 1:
            result = (0, groups, 0, 0, n)
            features[pieces] = result
            return result

        sx = sy = sum_squared = adjacency = edges = 0
        remaining = pieces
        while remaining:
            bit = remaining & -remaining
            remaining ^= bit
            square = bit.bit_length() - 1
            sx += _X[square]
            sy += _Y[square]
            sum_squared += _SQ[square]
            adjacency += (_ADJ[square] & pieces).bit_count()
            edges += _EDGE[square]

        variance = (
            sum_squared / n - (sx * sx + sy * sy) / (n * n)
        )
        center_distance = (
            (sx / n - 3.5) ** 2 + (sy / n - 3.5) ** 2
        )
        connection_weight = 18.0 + 2.0 * max(0.0, 5.0 - variance)

        value = int(
            -26.0 * variance
            - connection_weight * (len(groups) - 1)
            + 52.0 * largest / n
            + 4.0 * adjacency / n
            - 3.0 * isolated
            - 2.0 * center_distance
            - 2.0 * edges
        )

        result = (value, groups, sx, sy, n)
        features[pieces] = result
        return result

    def win_patterns(pieces, piece_info):
        cached = pattern_cache.get(pieces)
        if cached is not None:
            return cached

        groups = piece_info[1]
        halos = [_halo(group) for group in groups]
        available = _FULL ^ pieces

        prefix = [available]
        for halo in halos:
            prefix.append(prefix[-1] & halo)

        suffix = [_FULL] * (len(groups) + 1)
        for i in range(len(groups) - 1, -1, -1):
            suffix[i] = suffix[i + 1] & halos[i]

        patterns = []
        nonsingletons = 0

        for i, group in enumerate(groups):
            if group & (group - 1):
                nonsingletons |= group
            else:
                # Moving a singleton removes its original component.
                targets = prefix[i] & suffix[i + 1]
                if targets:
                    patterns.append((group, targets))

        if nonsingletons and prefix[-1]:
            patterns.append((nonsingletons, prefix[-1]))

        result = tuple(patterns)
        pattern_cache[pieces] = result
        return result

    def winning_move(pieces, opposition, piece_info):
        key = (pieces, opposition)
        cached = winning_cache.get(key)
        if cached is not None:
            return cached

        occupied = pieces | opposition
        for sources, targets in win_patterns(pieces, piece_info):
            while sources:
                source_bit = sources & -sources
                sources ^= source_bit
                source = source_bit.bit_length() - 1

                for line, distances in _TABLES[source]:
                    count = (occupied & line).bit_count()
                    for move, destination, path in distances[count]:
                        if not (destination & targets):
                            continue
                        if path & opposition:
                            continue

                        after = pieces ^ _CHANGE[move]
                        known = features.get(after)
                        connected = (
                            len(known[1]) == 1
                            if known is not None
                            else _connected(after)
                        )
                        if connected:
                            winning_cache[key] = move
                            return move

        winning_cache[key] = -1
        return -1

    def ordered_moves(pieces, opposition, moves, depth, ply,
                      preferred, pi, oi):
        ranked = []
        hist = history[ply & 1]
        killer1, killer2 = killers[ply]
        n = pi[4]
        sx, sy = pi[2], pi[3]

        for move in moves:
            if move == preferred:
                ranked.append((1000000000, move))
                continue

            destination = _TO[move]
            after = pieces ^ _CHANGE[move]
            capture = bool(destination & opposition)

            child_info = features.get(after)
            if depth >= 2 or capture:
                if child_info is None:
                    child_info = info(after)

            enemy_info = (
                info(opposition ^ destination) if capture else oi
            )

            if child_info is not None and len(child_info[1]) == 1:
                rank = 10000000
            elif len(enemy_info[1]) == 1:
                rank = -10000000
            else:
                if child_info is not None:
                    improvement = child_info[0] - pi[0]
                else:
                    dx, dy = _DX[move], _DY[move]
                    moment_gain = (
                        2 * sx * dx + dx * dx
                        + 2 * sy * dy + dy * dy
                        - n * _DSQ[move]
                    )
                    source = move >> 6
                    target = move & 63
                    old_neighbors = (
                        _ADJ[source] & pieces
                    ).bit_count()
                    new_neighbors = (
                        _ADJ[target] & (pieces ^ _FROM[move])
                    ).bit_count()
                    improvement = (
                        26 * moment_gain // (n * n)
                        + 5 * (new_neighbors - old_neighbors)
                        + 2 * (_EDGE[source] - _EDGE[target])
                    )

                improvement += oi[0] - enemy_info[0]
                rank = 32 * improvement + hist[move]
                if move == killer1:
                    rank += 40000
                elif move == killer2:
                    rank += 30000

            ranked.append((rank, move))

        ranked.sort(reverse=True)
        return [move for _, move in ranked]

    def search(pieces, opposition, depth, alpha, beta, ply):
        nonlocal nodes
        nodes += 1
        if (nodes & 31) == 0 and time.perf_counter() >= deadline:
            raise _SearchTimeout

        if not pieces:
            return -_MATE + ply
        if not opposition:
            return _MATE - ply

        oi = info(opposition)
        # The previous mover wins when both formations become connected.
        if len(oi[1]) == 1:
            return -_MATE + ply

        pi = info(pieces)
        if len(pi[1]) == 1:
            return _MATE - ply

        if depth <= 1:
            immediate = winning_move(pieces, opposition, pi)
            if immediate >= 0:
                return _MATE - ply - 1
            if depth <= 0:
                return pi[0] - oi[0]

        key = (pieces, opposition)
        original_alpha = alpha
        preferred = -1
        entry = transpositions.get(key)

        if entry is not None:
            stored_depth, value, flag, preferred = entry
            if value > _MATE - 1000:
                value -= ply
            elif value < -_MATE + 1000:
                value += ply

            if stored_depth >= depth:
                if flag == 0:
                    return value
                if flag == 1:
                    alpha = max(alpha, value)
                else:
                    beta = min(beta, value)
                if alpha >= beta:
                    return value

        moves = _legal_moves(pieces, opposition)
        if not moves:
            return -_MATE + ply

        moves = ordered_moves(
            pieces, opposition, moves, depth, ply, preferred, pi, oi
        )

        best_value = -_INF
        best_move = moves[0]

        for index, move in enumerate(moves):
            destination = _TO[move]
            child_pieces = pieces ^ _CHANGE[move]
            child_opposition = opposition & ~destination

            if index == 0:
                value = -search(
                    child_opposition, child_pieces,
                    depth - 1, -beta, -alpha, ply + 1
                )
            else:
                reduction = 0
                if (
                    depth >= 4
                    and index >= 6
                    and not (opposition & destination)
                    and len(pi[1]) > 2
                    and len(oi[1]) > 2
                    and move not in killers[ply]
                ):
                    reduction = 1

                value = -search(
                    child_opposition, child_pieces,
                    depth - 1 - reduction,
                    -alpha - 1, -alpha, ply + 1
                )

                if reduction and value > alpha:
                    value = -search(
                        child_opposition, child_pieces,
                        depth - 1, -alpha - 1, -alpha, ply + 1
                    )

                if alpha < value < beta:
                    value = -search(
                        child_opposition, child_pieces,
                        depth - 1, -beta, -alpha, ply + 1
                    )

            if value > best_value:
                best_value = value
                best_move = move

            if value > alpha:
                alpha = value

            if alpha >= beta:
                if killers[ply][0] != move:
                    killers[ply][1] = killers[ply][0]
                    killers[ply][0] = move
                hist = history[ply & 1]
                hist[move] = min(
                    12000, hist[move] + 12 * depth * depth
                )
                break

        if best_value <= original_alpha:
            flag = 2  # Upper bound.
        elif best_value >= beta:
            flag = 1  # Lower bound.
        else:
            flag = 0  # Exact.

        stored_value = best_value
        if stored_value > _MATE - 1000:
            stored_value += ply
        elif stored_value < -_MATE + 1000:
            stored_value -= ply

        transpositions[key] = (
            depth, stored_value, flag, best_move
        )
        return best_value

    # Find all immediate wins and establish a useful legal fallback.
    best_static = -_INF
    for move in legal:
        after = own ^ _CHANGE[move]
        after_info = info(after)
        if len(after_info[1]) == 1:
            return _format_move(move)

        enemy_after = enemy & ~_TO[move]
        enemy_info = info(enemy_after)
        if not enemy_after:
            value = _MATE
        elif len(enemy_info[1]) == 1:
            value = -_MATE
        else:
            value = after_info[0] - enemy_info[0]

        if value > best_static:
            best_static = value
            chosen = move

    winning_cache[(own, enemy)] = -1

    if len(legal) == 1:
        return _format_move(chosen)

    # Seed move ordering without claiming a completed search result.
    transpositions[(own, enemy)] = (-1, 0, 0, chosen)
    previous_score = best_static

    for depth in range(1, 33):
        if time.perf_counter() >= deadline:
            break

        try:
            if depth >= 3 and abs(previous_score) < _MATE - 1000:
                low = previous_score - 70
                high = previous_score + 70
                value = search(own, enemy, depth, low, high, 0)

                if value <= low or value >= high:
                    value = search(
                        own, enemy, depth, -_INF, _INF, 0
                    )
            else:
                value = search(
                    own, enemy, depth, -_INF, _INF, 0
                )

            entry = transpositions.get((own, enemy))
            if entry is not None and entry[3] in legal:
                chosen = entry[3]

            previous_score = value
            if abs(value) > _MATE - 1000:
                break

        except _SearchTimeout:
            break

    return _format_move(chosen)
