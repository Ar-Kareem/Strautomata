
import time

# Directions: NW, N, NE, W, E, SW, S, SE
_DIRS = (
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),             (0, 1),
    (1, -1),  (1, 0),    (1, 1),
)

# Axis used to count pieces in the movement line:
# 0 = row, 1 = column, 2 = \ diagonal, 3 = / diagonal
_DIR_AXIS = []
for _dr, _dc in _DIRS:
    if _dr == 0:
        _DIR_AXIS.append(0)
    elif _dc == 0:
        _DIR_AXIS.append(1)
    elif _dr == _dc:
        _DIR_AXIS.append(2)
    else:
        _DIR_AXIS.append(3)

_ALL = (1 << 64) - 1
_FILE_A = sum(1 << (r * 8) for r in range(8))
_FILE_H = sum(1 << (r * 8 + 7) for r in range(8))
_NOT_A = _ALL ^ _FILE_A
_NOT_H = _ALL ^ _FILE_H

# Masks for every movement line through every square.
_LINE_MASKS = [[0] * 4 for _ in range(64)]
for _sq in range(64):
    _r, _c = divmod(_sq, 8)

    row_mask = 0
    col_mask = 0
    back_diag = 0
    slash_diag = 0

    for _x in range(8):
        row_mask |= 1 << (_r * 8 + _x)
        col_mask |= 1 << (_x * 8 + _c)

    for _rr in range(8):
        for _cc in range(8):
            if _rr - _cc == _r - _c:
                back_diag |= 1 << (_rr * 8 + _cc)
            if _rr + _cc == _r + _c:
                slash_diag |= 1 << (_rr * 8 + _cc)

    _LINE_MASKS[_sq][0] = row_mask
    _LINE_MASKS[_sq][1] = col_mask
    _LINE_MASKS[_sq][2] = back_diag
    _LINE_MASKS[_sq][3] = slash_diag

# Destination and intervening-square masks for every source, direction,
# and possible movement distance.
_DEST = [[[-1] * 9 for _ in range(8)] for _ in range(64)]
_BETWEEN = [[[0] * 9 for _ in range(8)] for _ in range(64)]

for _sq in range(64):
    _r, _c = divmod(_sq, 8)
    for _d, (_dr, _dc) in enumerate(_DIRS):
        between = 0
        for _distance in range(1, 9):
            _tr = _r + _dr * _distance
            _tc = _c + _dc * _distance
            if 0 <= _tr < 8 and 0 <= _tc < 8:
                _DEST[_sq][_d][_distance] = _tr * 8 + _tc
                _BETWEEN[_sq][_d][_distance] = between
                between |= 1 << (_tr * 8 + _tc)
            else:
                break

# Neighbor masks and a centralization table.
_NEIGH = [0] * 64
_PST = [0] * 64

for _sq in range(64):
    _r, _c = divmod(_sq, 8)
    mask = 0
    for _dr in (-1, 0, 1):
        for _dc in (-1, 0, 1):
            if _dr == 0 and _dc == 0:
                continue
            _rr = _r + _dr
            _cc = _c + _dc
            if 0 <= _rr < 8 and 0 <= _cc < 8:
                mask |= 1 << (_rr * 8 + _cc)
    _NEIGH[_sq] = mask

    # Corners receive 0, central squares receive 12.
    _PST[_sq] = 14 - abs(2 * _r - 7) - abs(2 * _c - 7)


def _expand8(bits):
    """All squares adjacent in eight directions to at least one bit."""
    east = ((bits & _NOT_H) << 1) & _ALL
    west = (bits & _NOT_A) >> 1
    south = (bits << 8) & _ALL
    north = bits >> 8
    southeast = ((bits & _NOT_H) << 9) & _ALL
    southwest = ((bits & _NOT_A) << 7) & _ALL
    northeast = (bits & _NOT_H) >> 7
    northwest = (bits & _NOT_A) >> 9
    return east | west | south | north | southeast | southwest | northeast | northwest


def _is_connected(bits):
    """Whether all set bits form one nonempty 8-connected component."""
    if bits == 0:
        return False

    component = bits & -bits
    while True:
        enlarged = (component | _expand8(component)) & bits
        if enlarged == component:
            return component == bits
        component = enlarged


def _component_stats(bits):
    """Return (number of components, largest component size)."""
    remaining = bits
    count = 0
    largest = 0

    while remaining:
        count += 1
        component = remaining & -remaining

        while True:
            enlarged = (component | _expand8(component)) & bits
            if enlarged == component:
                break
            component = enlarged

        size = component.bit_count()
        if size > largest:
            largest = size
        remaining &= ~component

    return count, largest


def _generate_moves(us, them):
    """Generate all legal moves, encoded as from_square * 64 + to_square."""
    occupied = us | them
    moves = []
    pieces = us

    while pieces:
        from_bit = pieces & -pieces
        source = from_bit.bit_length() - 1
        pieces ^= from_bit

        masks = _LINE_MASKS[source]
        counts = (
            (occupied & masks[0]).bit_count(),
            (occupied & masks[1]).bit_count(),
            (occupied & masks[2]).bit_count(),
            (occupied & masks[3]).bit_count(),
        )

        for direction in range(8):
            distance = counts[_DIR_AXIS[direction]]
            target = _DEST[source][direction][distance]
            if target < 0:
                continue

            target_bit = 1 << target

            # A friendly piece may not be captured or landed upon.
            if us & target_bit:
                continue

            # Enemy pieces may not be jumped over. The destination is not
            # included in BETWEEN, so landing on an enemy remains legal.
            if them & _BETWEEN[source][direction][distance]:
                continue

            moves.append(source * 64 + target)

    return moves


def _side_score(bits):
    """Connectivity and concentration score for one side."""
    number = bits.bit_count()
    if number == 0:
        return -200000

    components, largest = _component_stats(bits)

    degree_squared = 0
    degree_sum = 0
    centrality = 0

    sum_r = 0
    sum_c = 0
    sum_r2 = 0
    sum_c2 = 0
    min_r = 8
    max_r = -1
    min_c = 8
    max_c = -1

    pieces = bits
    while pieces:
        bit = pieces & -pieces
        square = bit.bit_length() - 1
        pieces ^= bit

        row, col = divmod(square, 8)
        degree = (_NEIGH[square] & bits).bit_count()

        degree_sum += degree
        degree_squared += degree * degree
        centrality += _PST[square]

        sum_r += row
        sum_c += col
        sum_r2 += row * row
        sum_c2 += col * col

        if row < min_r:
            min_r = row
        if row > max_r:
            max_r = row
        if col < min_c:
            min_c = col
        if col > max_c:
            max_c = col

    # Translation-independent dispersion about the center of mass.
    variance_numerator = (
        number * sum_r2 - sum_r * sum_r
        + number * sum_c2 - sum_c * sum_c
    )
    variance = variance_numerator // number

    span_area = (max_r - min_r + 1) * (max_c - min_c + 1)
    friendly_links = degree_sum // 2

    score = 0
    score -= 560 * (components - 1)
    score += (220 * largest) // number
    score += 16 * degree_squared
    score += 8 * friendly_links
    score -= 5 * variance
    score -= 3 * span_area
    score += 2 * centrality

    return score


def _evaluate(us, them):
    """Evaluation from the perspective of the side represented by us."""
    return _side_score(us) - _side_score(them)


class _SearchTimeout(Exception):
    pass


def policy(board) -> str:
    start_time = time.perf_counter()
    deadline = start_time + 0.90

    us = 0
    them = 0

    for row in range(8):
        for col in range(8):
            value = int(board[row][col])
            bit = 1 << (row * 8 + col)
            if value > 0:
                us |= bit
            elif value < 0:
                them |= bit

    root_moves = _generate_moves(us, them)

    # A normal nonterminal LOA position supplied to a move policy has a move.
    # This branch is only a defensive fallback for malformed/terminal input.
    if not root_moves:
        return "0,0:0,0"

    WIN = 1000000
    INF = 2000000

    # Select a sound legal fallback before doing any timed search, and return
    # an immediate connecting move without delay.
    fallback = root_moves[0]
    fallback_score = -INF

    for move in root_moves:
        source = move // 64
        target = move & 63
        from_bit = 1 << source
        target_bit = 1 << target

        new_us = (us ^ from_bit) | target_bit
        new_them = them & ~target_bit

        if _is_connected(new_us):
            fr, fc = divmod(source, 8)
            tr, tc = divmod(target, 8)
            return f"{fr},{fc}:{tr},{tc}"

        # Capturing can connect the opponent by removing an isolated piece.
        if (target_bit & them) and _is_connected(new_them):
            value = -WIN
        else:
            value = _evaluate(new_us, new_them)

        if value > fallback_score:
            fallback_score = value
            fallback = move

    # TT entry: (depth, value, flag, best_move)
    # flag: 0 exact, 1 lower bound, 2 upper bound
    transposition = {}
    history = [0] * 4096
    killers = [[-1, -1] for _ in range(20)]
    nodes = [0]

    def check_time():
        nodes[0] += 1
        if (nodes[0] & 127) == 0 and time.perf_counter() >= deadline:
            raise _SearchTimeout

    def order_moves(side, enemy, moves, tt_move, ply):
        scored = []
        killer_a, killer_b = killers[ply] if ply < len(killers) else (-1, -1)

        for move in moves:
            source = move // 64
            target = move & 63
            from_bit = 1 << source
            target_bit = 1 << target
            resulting_side = (side ^ from_bit) | target_bit

            score = history[move]

            if move == tt_move:
                score += 1000000
            if enemy & target_bit:
                score += 30000
            if move == killer_a:
                score += 18000
            elif move == killer_b:
                score += 12000

            new_neighbors = (_NEIGH[target] & resulting_side).bit_count()
            old_neighbors = (_NEIGH[source] & side).bit_count()
            score += 280 * new_neighbors
            score -= 45 * old_neighbors
            score += 12 * (_PST[target] - _PST[source])

            scored.append((score, move))

        scored.sort(reverse=True)
        return [move for _, move in scored]

    def store_tt(key, depth, value, flag, best_move):
        old = transposition.get(key)
        if old is None or depth >= old[0]:
            transposition[key] = (depth, value, flag, best_move)

    def negamax(side, enemy, depth, alpha, beta, ply):
        check_time()

        key = (side, enemy)
        original_alpha = alpha
        original_beta = beta
        tt_move = -1

        entry = transposition.get(key)
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

        if depth == 0:
            value = _evaluate(side, enemy)
            store_tt(key, 0, value, 0, -1)
            return value

        moves = _generate_moves(side, enemy)
        if not moves:
            return -WIN + ply

        moves = order_moves(side, enemy, moves, tt_move, ply)

        best_value = -INF
        best_move = moves[0]

        for move in moves:
            source = move // 64
            target = move & 63
            from_bit = 1 << source
            target_bit = 1 << target

            new_side = (side ^ from_bit) | target_bit
            new_enemy = enemy & ~target_bit
            capture = bool(enemy & target_bit)

            # The moving player wins simultaneous connections.
            if _is_connected(new_side) or new_enemy == 0:
                value = WIN - (ply + 1)
            elif capture and _is_connected(new_enemy):
                value = -WIN + (ply + 1)
            else:
                value = -negamax(
                    new_enemy,
                    new_side,
                    depth - 1,
                    -beta,
                    -alpha,
                    ply + 1,
                )

            if value > best_value:
                best_value = value
                best_move = move

            if value > alpha:
                alpha = value

            if alpha >= beta:
                if not capture:
                    history[move] += depth * depth + 1
                    if ply < len(killers) and move != killers[ply][0]:
                        killers[ply][1] = killers[ply][0]
                        killers[ply][0] = move
                break

        if best_value <= original_alpha:
            flag = 2
        elif best_value >= original_beta:
            flag = 1
        else:
            flag = 0

        store_tt(key, depth, best_value, flag, best_move)
        return best_value

    def root_search(depth, preferred_move):
        if time.perf_counter() >= deadline:
            raise _SearchTimeout

        ordered = order_moves(us, them, root_moves, preferred_move, 0)
        alpha = -INF
        beta = INF
        best_value = -INF
        best_move = ordered[0]

        for move in ordered:
            if time.perf_counter() >= deadline:
                raise _SearchTimeout

            source = move // 64
            target = move & 63
            from_bit = 1 << source
            target_bit = 1 << target

            new_us = (us ^ from_bit) | target_bit
            new_them = them & ~target_bit
            capture = bool(them & target_bit)

            if _is_connected(new_us) or new_them == 0:
                value = WIN - 1
            elif capture and _is_connected(new_them):
                value = -WIN + 1
            else:
                value = -negamax(
                    new_them,
                    new_us,
                    depth - 1,
                    -beta,
                    -alpha,
                    1,
                )

            if value > best_value:
                best_value = value
                best_move = move

            if value > alpha:
                alpha = value

        store_tt((us, them), depth, best_value, 0, best_move)
        return best_value, best_move

    best_completed_move = fallback
    preferred = fallback

    # Iterative deepening ensures that interruption preserves the result of
    # the deepest fully completed search.
    try:
        for depth in range(1, 11):
            if time.perf_counter() >= deadline:
                break

            value, move = root_search(depth, preferred)
            best_completed_move = move
            preferred = move

            # A forced win has been found; deeper search cannot improve it
            # except for an already minimal mate distance.
            if value >= WIN - 2:
                break

    except _SearchTimeout:
        pass

    source = best_completed_move // 64
    target = best_completed_move & 63
    from_row, from_col = divmod(source, 8)
    to_row, to_col = divmod(target, 8)

    return f"{from_row},{from_col}:{to_row},{to_col}"
