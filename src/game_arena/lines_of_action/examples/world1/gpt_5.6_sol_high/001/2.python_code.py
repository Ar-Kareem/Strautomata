
from time import perf_counter

FULL = (1 << 64) - 1
FILE_A = sum(1 << (r * 8) for r in range(8))
FILE_H = sum(1 << (r * 8 + 7) for r in range(8))
NOT_A = FULL ^ FILE_A
NOT_H = FULL ^ FILE_H

MATE = 1_000_000
INF = 2_000_000

DIRS = (
    (-1, 0, 1),
    (1, 0, 1),
    (0, -1, 0),
    (0, 1, 0),
    (-1, -1, 2),
    (1, 1, 2),
    (-1, 1, 3),
    (1, -1, 3),
)

LINE_MASKS = [[0] * 64 for _ in range(4)]
NEIGHBOR_MASKS = [0] * 64
CENTER_VALUE = [0] * 64

for r in range(8):
    for c in range(8):
        sq = r * 8 + c

        row_mask = 0
        col_mask = 0
        main_diag = 0
        anti_diag = 0

        for x in range(8):
            row_mask |= 1 << (r * 8 + x)
            col_mask |= 1 << (x * 8 + c)

            y = x + c - r
            if 0 <= y < 8:
                main_diag |= 1 << (x * 8 + y)

            y = r + c - x
            if 0 <= y < 8:
                anti_diag |= 1 << (x * 8 + y)

        LINE_MASKS[0][sq] = row_mask
        LINE_MASKS[1][sq] = col_mask
        LINE_MASKS[2][sq] = main_diag
        LINE_MASKS[3][sq] = anti_diag

        neighbor_mask = 0
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                rr = r + dr
                cc = c + dc
                if 0 <= rr < 8 and 0 <= cc < 8:
                    neighbor_mask |= 1 << (rr * 8 + cc)
        NEIGHBOR_MASKS[sq] = neighbor_mask

        CENTER_VALUE[sq] = 14 - abs(2 * r - 7) - abs(2 * c - 7)


class _SearchTimeout(Exception):
    pass


_deadline = 0.0
_nodes = 0
_tt = {}
_history = {}
_killers = []


def _neighbors(bits):
    horizontal = ((bits & NOT_H) << 1) | ((bits & NOT_A) >> 1)
    vertical = (bits << 8) | (bits >> 8)
    diagonal = (
        ((bits & NOT_H) << 9)
        | ((bits & NOT_A) << 7)
        | ((bits & NOT_H) >> 7)
        | ((bits & NOT_A) >> 9)
    )
    return (horizontal | vertical | diagonal) & FULL


def _is_connected(bits):
    if bits == 0:
        return False

    seen = bits & -bits
    while True:
        grown = seen | (_neighbors(seen) & bits)
        if grown == seen:
            return seen == bits
        seen = grown


def _group_stats(bits):
    if bits == 0:
        return 0, 0

    remaining = bits
    groups = 0
    largest = 0

    while remaining:
        groups += 1
        component = remaining & -remaining

        while True:
            grown = component | (_neighbors(component) & bits)
            if grown == component:
                break
            component = grown

        size = component.bit_count()
        if size > largest:
            largest = size
        remaining &= ~component

    return groups, largest


def _generate_moves(me, opponent):
    occupied = me | opponent
    moves = []
    pieces = me

    while pieces:
        source_bit = pieces & -pieces
        source = source_bit.bit_length() - 1
        pieces ^= source_bit

        r = source >> 3
        c = source & 7

        for dr, dc, axis in DIRS:
            distance = (occupied & LINE_MASKS[axis][source]).bit_count()
            tr = r + dr * distance
            tc = c + dc * distance

            if not (0 <= tr < 8 and 0 <= tc < 8):
                continue

            destination = tr * 8 + tc
            destination_bit = 1 << destination

            if me & destination_bit:
                continue

            rr = r + dr
            cc = c + dc
            blocked = False

            for _ in range(1, distance):
                if opponent & (1 << (rr * 8 + cc)):
                    blocked = True
                    break
                rr += dr
                cc += dc

            if not blocked:
                moves.append((source << 6) | destination)

    return moves


def _apply_move(me, opponent, move):
    source = move >> 6
    destination = move & 63
    source_bit = 1 << source
    destination_bit = 1 << destination

    new_me = (me ^ source_bit) | destination_bit
    new_opponent = opponent & ~destination_bit
    return new_me, new_opponent


def _structural_score(bits):
    count = bits.bit_count()
    if count == 0:
        return -10000

    groups, largest = _group_stats(bits)

    squares = []
    work = bits
    row_sum = 0
    col_sum = 0
    adjacency_twice = 0
    center_sum = 0

    min_r = 7
    max_r = 0
    min_c = 7
    max_c = 0

    while work:
        bit = work & -work
        sq = bit.bit_length() - 1
        work ^= bit

        r = sq >> 3
        c = sq & 7
        squares.append((r, c))

        row_sum += r
        col_sum += c
        adjacency_twice += (NEIGHBOR_MASKS[sq] & bits).bit_count()
        center_sum += CENTER_VALUE[sq]

        if r < min_r:
            min_r = r
        if r > max_r:
            max_r = r
        if c < min_c:
            min_c = c
        if c > max_c:
            max_c = c

    adjacency = adjacency_twice // 2

    scaled_dispersion = 0
    for r, c in squares:
        scaled_dispersion += abs(r * count - row_sum)
        scaled_dispersion += abs(c * count - col_sum)

    dispersion_100 = (100 * scaled_dispersion) // (count * count)

    if count > 1:
        nearest_sum = 0
        for i, (r1, c1) in enumerate(squares):
            nearest = 8
            for j, (r2, c2) in enumerate(squares):
                if i == j:
                    continue
                distance = max(abs(r1 - r2), abs(c1 - c2))
                if distance < nearest:
                    nearest = distance
            nearest_sum += nearest
        nearest_100 = (100 * nearest_sum) // count
    else:
        nearest_100 = 0

    bounding_span = (max_r - min_r) + (max_c - min_c)
    center_average = center_sum // count

    score = 0
    score -= 650 * (groups - 1)
    score += (220 * largest) // count
    score += (110 * adjacency) // count
    score -= dispersion_100 // 2
    score -= nearest_100 // 2
    score -= 10 * bounding_span
    score += 3 * center_average
    score += 5 * count

    return score


def _evaluate(me, opponent):
    return _structural_score(me) - _structural_score(opponent)


def _check_time():
    global _nodes
    _nodes += 1
    if (_nodes & 255) == 0 and perf_counter() >= _deadline:
        raise _SearchTimeout


def _move_order_score(move, me, opponent, ply, tt_move):
    if move == tt_move:
        return 10_000_000

    source = move >> 6
    destination = move & 63
    source_bit = 1 << source
    destination_bit = 1 << destination
    friends_without_source = me ^ source_bit

    joined = (NEIGHBOR_MASKS[destination] & friends_without_source).bit_count()
    left = (NEIGHBOR_MASKS[source] & friends_without_source).bit_count()

    score = _history.get(move, 0)
    score += 42 * joined
    score -= 10 * left
    score += 4 * (CENTER_VALUE[destination] - CENTER_VALUE[source])

    if opponent & destination_bit:
        score += 90

    if ply < len(_killers):
        if move == _killers[ply][0]:
            score += 5000
        elif move == _killers[ply][1]:
            score += 3500

    return score


def _ordered_moves(moves, me, opponent, ply, tt_move=-1):
    moves.sort(
        key=lambda mv: _move_order_score(
            mv, me, opponent, ply, tt_move
        ),
        reverse=True,
    )
    return moves


def _negamax(me, opponent, depth, alpha, beta, ply):
    _check_time()

    if depth <= 0:
        return _evaluate(me, opponent)

    key = (me, opponent)
    alpha_original = alpha
    beta_original = beta
    tt_move = -1

    entry = _tt.get(key)
    if entry is not None:
        stored_depth, stored_value, flag, tt_move = entry
        if stored_depth >= depth:
            if flag == 0:
                return stored_value
            if flag == 1:
                if stored_value > alpha:
                    alpha = stored_value
            else:
                if stored_value < beta:
                    beta = stored_value
            if alpha >= beta:
                return stored_value

    moves = _generate_moves(me, opponent)
    if not moves:
        return -MATE + ply

    _ordered_moves(moves, me, opponent, ply, tt_move)

    best_value = -INF
    best_move = moves[0]
    first = True

    for move in moves:
        new_me, new_opponent = _apply_move(me, opponent, move)

        if _is_connected(new_me) or new_opponent == 0:
            value = MATE - ply
        elif _is_connected(new_opponent):
            value = -MATE + ply
        elif first:
            value = -_negamax(
                new_opponent,
                new_me,
                depth - 1,
                -beta,
                -alpha,
                ply + 1,
            )
        else:
            value = -_negamax(
                new_opponent,
                new_me,
                depth - 1,
                -alpha - 1,
                -alpha,
                ply + 1,
            )
            if alpha < value < beta:
                value = -_negamax(
                    new_opponent,
                    new_me,
                    depth - 1,
                    -beta,
                    -alpha,
                    ply + 1,
                )

        first = False

        if value > best_value:
            best_value = value
            best_move = move

        if value > alpha:
            alpha = value

        if alpha >= beta:
            _history[move] = _history.get(move, 0) + depth * depth

            if ply < len(_killers) and move != _killers[ply][0]:
                _killers[ply][1] = _killers[ply][0]
                _killers[ply][0] = move
            break

    if best_value <= alpha_original:
        flag = 2
    elif best_value >= beta_original:
        flag = 1
    else:
        flag = 0

    if len(_tt) < 150000:
        _tt[key] = (depth, best_value, flag, best_move)

    return best_value


def _root_search(me, opponent, moves, depth, previous_best):
    root_moves = list(moves)
    _ordered_moves(root_moves, me, opponent, 0, previous_best)

    alpha = -INF
    beta = INF
    best_value = -INF
    best_move = root_moves[0]
    first = True

    for move in root_moves:
        if perf_counter() >= _deadline:
            raise _SearchTimeout

        new_me, new_opponent = _apply_move(me, opponent, move)

        if _is_connected(new_me) or new_opponent == 0:
            value = MATE
        elif _is_connected(new_opponent):
            value = -MATE
        elif first:
            value = -_negamax(
                new_opponent,
                new_me,
                depth - 1,
                -beta,
                -alpha,
                1,
            )
        else:
            value = -_negamax(
                new_opponent,
                new_me,
                depth - 1,
                -alpha - 1,
                -alpha,
                1,
            )
            if alpha < value < beta:
                value = -_negamax(
                    new_opponent,
                    new_me,
                    depth - 1,
                    -beta,
                    -alpha,
                    1,
                )

        first = False

        if value > best_value:
            best_value = value
            best_move = move

        if value > alpha:
            alpha = value

    return best_value, best_move


def policy(board) -> str:
    global _deadline, _nodes, _tt, _history, _killers

    start = perf_counter()
    _deadline = start + 0.90
    _nodes = 0
    _tt = {}
    _history = {}
    _killers = [[-1, -1] for _ in range(16)]

    me = 0
    opponent = 0

    for r in range(8):
        for c in range(8):
            value = int(board[r][c])
            bit = 1 << (r * 8 + c)
            if value == 1:
                me |= bit
            elif value == -1:
                opponent |= bit

    legal_moves = _generate_moves(me, opponent)

    if not legal_moves:
        return "0,0:0,0"

    best_move = legal_moves[0]

    # Immediate wins are selected before beginning the timed search.
    for move in legal_moves:
        new_me, new_opponent = _apply_move(me, opponent, move)
        if _is_connected(new_me) or new_opponent == 0:
            source = move >> 6
            destination = move & 63
            return (
                f"{source // 8},{source % 8}:"
                f"{destination // 8},{destination % 8}"
            )

    previous_best = best_move

    try:
        for depth in range(1, 8):
            score, candidate = _root_search(
                me, opponent, legal_moves, depth, previous_best
            )
            best_move = candidate
            previous_best = candidate

            if score >= MATE - 50 or score <= -MATE + 50:
                break
    except _SearchTimeout:
        pass

    source = best_move >> 6
    destination = best_move & 63

    return (
        f"{source // 8},{source % 8}:"
        f"{destination // 8},{destination % 8}"
    )
