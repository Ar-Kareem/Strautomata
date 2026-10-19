
import time
from functools import lru_cache

_ALL = (1 << 64) - 1
_NOT_A = 0xFEFEFEFEFEFEFEFE
_NOT_H = 0x7F7F7F7F7F7F7F7F
_BITS = tuple(1 << i for i in range(64))
_ROWS = tuple(i >> 3 for i in range(64))
_COLS = tuple(i & 7 for i in range(64))
_SQUARE_SUM = tuple(
    _ROWS[i] * _ROWS[i] + _COLS[i] * _COLS[i]
    for i in range(64)
)
_CENTER = tuple(
    -((2 * _ROWS[i] - 7) ** 2 + (2 * _COLS[i] - 7) ** 2)
    for i in range(64)
)

_MATE = 1000000
_MATE_BOUND = 900000
_INF = 2000000
_EXACT, _LOWER, _UPPER = 0, 1, 2


def _expand(bits):
    horizontal = (
        bits
        | ((bits & _NOT_A) >> 1)
        | ((bits & _NOT_H) << 1)
    )
    return (horizontal | (horizontal << 8) | (horizontal >> 8)) & _ALL


_NEIGHBORS = tuple(_expand(_BITS[i]) ^ _BITS[i] for i in range(64))


def _build_move_tables():
    tables = []
    axes = ((0, 1), (1, 0), (1, 1), (1, -1))

    for square in range(64):
        row, col = divmod(square, 8)
        square_tables = []

        for dr, dc in axes:
            line = _BITS[square]
            distances = [[] for _ in range(9)]

            for sign in (-1, 1):
                path = 0
                for distance in range(1, 8):
                    nr = row + sign * dr * distance
                    nc = col + sign * dc * distance
                    if not (0 <= nr < 8 and 0 <= nc < 8):
                        break

                    target = nr * 8 + nc
                    target_bit = _BITS[target]
                    line |= target_bit
                    distances[distance].append((target, target_bit, path))
                    path |= target_bit

            square_tables.append(
                (line, tuple(tuple(x) for x in distances))
            )

        tables.append(tuple(square_tables))

    return tuple(tables)


_MOVE_TABLES = _build_move_tables()


def _legal_moves(own, enemy):
    occupied = own | enemy
    remaining = own
    result = []
    append = result.append

    while remaining:
        source_bit = remaining & -remaining
        remaining ^= source_bit
        source = source_bit.bit_length() - 1

        for line, distances in _MOVE_TABLES[source]:
            distance = (occupied & line).bit_count()
            for target, target_bit, path in distances[distance]:
                if not (own & target_bit) and not (enemy & path):
                    append((source, target))

    return result


@lru_cache(maxsize=65536)
def _shape(bits):
    """Return (positional score, component count, piece count, sum_r, sum_c)."""
    count = bits.bit_count()
    if count == 0:
        return (-20000, 0, 0, 0, 0)
    if count == 1:
        return (0, 1, 1, 0, 0)

    remaining = bits
    components = 0
    largest_size = 0
    largest_group = 0

    while remaining:
        group = remaining & -remaining

        while True:
            horizontal = (
                group
                | ((group & _NOT_A) >> 1)
                | ((group & _NOT_H) << 1)
            )
            grown = (
                horizontal | (horizontal << 8) | (horizontal >> 8)
            ) & remaining
            if grown == group:
                break
            group = grown

        components += 1
        size = group.bit_count()
        if size > largest_size:
            largest_size = size
            largest_group = group

        remaining ^= group

    if components == 1:
        return (0, 1, count, 0, 0)

    sum_r = 0
    sum_c = 0
    square_sum = 0
    remaining = bits

    while remaining:
        piece = remaining & -remaining
        remaining ^= piece
        square = piece.bit_length() - 1
        sum_r += _ROWS[square]
        sum_c += _COLS[square]
        square_sum += _SQUARE_SUM[square]

    denominator = count * count
    variance = (
        count * square_sum - sum_r * sum_r - sum_c * sum_c
    ) / denominator

    center_offset = (
        (2 * sum_r - 7 * count) ** 2
        + (2 * sum_c - 7 * count) ** 2
    ) / (4 * denominator)

    links = (
        (((bits & _NOT_H) << 1) & bits).bit_count()
        + ((bits << 8) & bits).bit_count()
        + (((bits & _NOT_H) << 9) & bits).bit_count()
        + (((bits & _NOT_A) << 7) & bits).bit_count()
    )

    # Chebyshev distances from pieces outside the largest group.
    outside = bits ^ largest_group
    reach = largest_group
    distance = 0
    distance_sum = 0

    while outside:
        distance += 1
        reach = _expand(reach)
        reached = outside & reach
        distance_sum += distance * reached.bit_count()
        outside ^= reached

    component_weight = 25.0 + 45.0 / (variance + 2.0)

    score = (
        -29.0 * variance
        - component_weight * (components - 1)
        + 100.0 * largest_size / count
        + 10.0 * links / count
        - 3.0 * center_offset
        - 12.0 * distance_sum / count
        - 5.0 * distance
    )

    return (int(round(score)), components, count, sum_r, sum_c)


class _SearchTimeout(Exception):
    pass


def _encode_move(move):
    source, target = move
    return (
        f"{source >> 3},{source & 7}:"
        f"{target >> 3},{target & 7}"
    )


def _store_mate(value, ply):
    if value > _MATE_BOUND:
        return value + ply
    if value < -_MATE_BOUND:
        return value - ply
    return value


def _load_mate(value, ply):
    if value > _MATE_BOUND:
        return value - ply
    if value < -_MATE_BOUND:
        return value + ply
    return value


def policy(board) -> str:
    deadline = time.perf_counter() + 0.89

    own = 0
    enemy = 0
    for row in range(8):
        for col in range(8):
            value = int(board[row][col])
            if value == 1:
                own |= _BITS[row * 8 + col]
            elif value == -1:
                enemy |= _BITS[row * 8 + col]

    root_moves = _legal_moves(own, enemy)

    # A legal move can only be returned when the position has one.
    # Normal arena calls are nonterminal positions with legal actions.
    if not root_moves:
        raise ValueError("This position has no legal move.")

    best_move = root_moves[0]
    if len(root_moves) == 1:
        return _encode_move(best_move)

    enemy_shape = _shape(enemy)
    best_score = -_INF

    # Establish a complete one-ply result and a legal fallback.
    for move in root_moves:
        source, target = move
        target_bit = _BITS[target]
        next_own = (own ^ _BITS[source]) | target_bit
        next_enemy = enemy & ~target_bit
        own_shape = _shape(next_own)

        if own_shape[1] == 1:
            return _encode_move(move)

        other_shape = (
            enemy_shape if next_enemy == enemy else _shape(next_enemy)
        )

        if other_shape[1] == 1:
            value = -_MATE + 1
        elif next_enemy == 0:
            value = _MATE - 1
        else:
            value = own_shape[0] - other_shape[0] - 8

        if value > best_score:
            best_score = value
            best_move = move

    transpositions = {
        (own, enemy): (1, _EXACT, best_score, best_move)
    }
    history = [0] * 4096
    killers = [[None, None] for _ in range(128)]
    nodes = 0

    def search(a, b, depth, alpha, beta, ply):
        nonlocal nodes
        nodes += 1
        if (nodes & 63) == 0 and time.perf_counter() >= deadline:
            raise _SearchTimeout

        sa = _shape(a)
        sb = _shape(b)

        # In simultaneous connection, the player who just moved wins.
        if sb[1] == 1:
            return -_MATE + ply
        if sa[1] == 1:
            return _MATE - ply
        if not a:
            return -_MATE + ply
        if not b:
            return _MATE - ply

        if depth <= 0:
            return sa[0] - sb[0] + 8

        key = (a, b)
        entry = transpositions.get(key)
        hash_move = None

        if entry is not None:
            stored_depth, flag, stored_value, hash_move = entry
            if stored_depth >= depth:
                value = _load_mate(stored_value, ply)
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

        original_alpha = alpha
        pv_node = beta - alpha > 1
        moves = root_moves if ply == 0 else _legal_moves(a, b)

        if not moves:
            # LOA's usual no-move convention is to pass.
            return -search(b, a, depth - 1, -beta, -alpha, ply + 1)

        if ply < len(killers):
            killer_one, killer_two = killers[ply]
        else:
            killer_one = killer_two = None

        ordered = []

        if depth >= 2:
            for move in moves:
                source, target = move
                target_bit = _BITS[target]
                na = (a ^ _BITS[source]) | target_bit
                nb = b & ~target_bit
                nsa = _shape(na)

                # An immediate win is optimal, irrespective of the window.
                if nsa[1] == 1:
                    value = _MATE - ply - 1
                    transpositions[key] = (
                        depth, _EXACT, _store_mate(value, ply), move
                    )
                    return value

                nsb = sb if nb == b else _shape(nb)
                if nsb[1] == 1:
                    priority = -_MATE
                else:
                    priority = nsa[0] - nsb[0]
                    priority += min(
                        150, history[(source << 6) | target] // 16
                    )

                if move == hash_move:
                    priority += 4000000
                elif move == killer_one:
                    priority += 20000
                elif move == killer_two:
                    priority += 15000

                ordered.append((priority, move, na, nb))

            if time.perf_counter() >= deadline:
                raise _SearchTimeout

        else:
            count, sum_r, sum_c = sa[2], sa[3], sa[4]

            for move in moves:
                source, target = move
                target_bit = _BITS[target]
                na = (a ^ _BITS[source]) | target_bit
                nb = b & ~target_bit

                dr = _ROWS[target] - _ROWS[source]
                dc = _COLS[target] - _COLS[source]
                compactness = (
                    2 * sum_r * dr
                    + 2 * sum_c * dc
                    + dr * dr
                    + dc * dc
                    - count * (_SQUARE_SUM[target] - _SQUARE_SUM[source])
                ) // count

                link_change = (
                    (na & _NEIGHBORS[target]).bit_count()
                    - (a & _NEIGHBORS[source]).bit_count()
                )

                priority = (
                    2 * compactness
                    + 12 * link_change
                    + (_CENTER[target] - _CENTER[source]) // 4
                    + history[(source << 6) | target] // 8
                )

                if nb != b:
                    priority += 6
                    if sb[2] == 2:
                        priority -= _MATE

                if move == hash_move:
                    priority += 4000000
                elif move == killer_one:
                    priority += 2000000
                elif move == killer_two:
                    priority += 1500000

                ordered.append((priority, move, na, nb))

        ordered.sort(key=lambda item: item[0], reverse=True)

        value_best = -_INF
        move_best = ordered[0][1]

        for index, (_, move, na, nb) in enumerate(ordered):
            child_depth = depth - 1

            if index == 0:
                value = -search(
                    nb, na, child_depth, -beta, -alpha, ply + 1
                )
            else:
                reduction = 0

                # Reduce only late, quiet, non-PV moves that do not
                # improve the moving player's component count.
                if (
                    depth >= 3
                    and index >= 5
                    and not pv_node
                    and nb == b
                    and move != hash_move
                    and move != killer_one
                    and move != killer_two
                ):
                    new_components = _shape(na)[1]
                    if new_components > 2 and new_components >= sa[1]:
                        reduction = 1

                value = -search(
                    nb,
                    na,
                    child_depth - reduction,
                    -alpha - 1,
                    -alpha,
                    ply + 1,
                )

                if reduction and value > alpha:
                    value = -search(
                        nb, na, child_depth, -alpha - 1, -alpha, ply + 1
                    )

                if alpha < value < beta:
                    value = -search(
                        nb, na, child_depth, -beta, -alpha, ply + 1
                    )

            if value > value_best:
                value_best = value
                move_best = move

            if value > alpha:
                alpha = value

            if alpha >= beta:
                if nb == b:
                    source, target = move
                    history_index = (source << 6) | target
                    history[history_index] = min(
                        32768,
                        history[history_index] + 16 * depth * depth,
                    )

                    if ply < len(killers) and move != killers[ply][0]:
                        killers[ply][1] = killers[ply][0]
                        killers[ply][0] = move
                break

        if value_best <= original_alpha:
            flag = _UPPER
        elif value_best >= beta:
            flag = _LOWER
        else:
            flag = _EXACT

        transpositions[key] = (
            depth, flag, _store_mate(value_best, ply), move_best
        )
        return value_best

    root_key = (own, enemy)

    for depth in range(2, 65):
        if time.perf_counter() >= deadline - 0.003:
            break

        if depth >= 3 and abs(best_score) < _MATE_BOUND:
            alpha = best_score - 80
            beta = best_score + 80
        else:
            alpha, beta = -_INF, _INF

        try:
            score = search(own, enemy, depth, alpha, beta, 0)

            if score <= alpha or score >= beta:
                score = search(own, enemy, depth, -_INF, _INF, 0)

            entry = transpositions.get(root_key)
            if entry is not None and entry[3] in root_moves:
                best_move = entry[3]
                best_score = score

            if best_score > _MATE_BOUND:
                break

        except _SearchTimeout:
            break

    return _encode_move(best_move)
