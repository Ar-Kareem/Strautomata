
import time

_FULL = (1 << 64) - 1
_NOT_A = _FULL ^ 0x0101010101010101
_NOT_H = _FULL ^ 0x8080808080808080
_BITS = tuple(1 << i for i in range(64))
_ROWS = tuple(i // 8 for i in range(64))
_COLS = tuple(i % 8 for i in range(64))
_SQUARES = tuple(_ROWS[i] ** 2 + _COLS[i] ** 2 for i in range(64))

_MATE = 1_000_000
_INF = 2_000_000
_CONNECTED = 10_000_000

_NEIGHBORS = []
_GEOMETRY = []

for _s in range(64):
    _r, _c = divmod(_s, 8)
    _neighbors = 0
    for _dr in (-1, 0, 1):
        for _dc in (-1, 0, 1):
            if (_dr or _dc) and 0 <= _r + _dr < 8 and 0 <= _c + _dc < 8:
                _neighbors |= 1 << ((_r + _dr) * 8 + _c + _dc)
    _NEIGHBORS.append(_neighbors)

    _axes = []
    for _dr, _dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
        _line = 0
        for _k in range(-7, 8):
            _rr, _cc = _r + _k * _dr, _c + _k * _dc
            if 0 <= _rr < 8 and 0 <= _cc < 8:
                _line |= 1 << (_rr * 8 + _cc)

        _choices = []
        for _distance in range(9):
            _options = []
            if _distance:
                for _sign in (-1, 1):
                    _rr = _r + _sign * _distance * _dr
                    _cc = _c + _sign * _distance * _dc
                    if 0 <= _rr < 8 and 0 <= _cc < 8:
                        _destination = _rr * 8 + _cc
                        _between = 0
                        for _step in range(1, _distance):
                            _pr = _r + _sign * _step * _dr
                            _pc = _c + _sign * _step * _dc
                            _between |= 1 << (_pr * 8 + _pc)
                        _options.append((
                            1 << _destination,
                            _between,
                            (_s << 6) | _destination,
                        ))
            _choices.append(tuple(_options))
        _axes.append((_line, tuple(_choices)))
    _GEOMETRY.append(tuple(_axes))

_NEIGHBORS = tuple(_NEIGHBORS)
_GEOMETRY = tuple(_GEOMETRY)


def _spread(bits):
    horizontal = bits | ((bits << 1) & _NOT_A) | ((bits >> 1) & _NOT_H)
    return (horizontal | (horizontal << 8) | (horizontal >> 8)) & _FULL


def _is_connected(bits):
    if not bits:
        return False
    component = bits & -bits
    while True:
        enlarged = _spread(component) & bits
        if enlarged == component:
            return component == bits
        component = enlarged


def _legal_moves(ours, theirs):
    occupied = ours | theirs
    pieces = ours
    result = []
    append = result.append
    while pieces:
        source_bit = pieces & -pieces
        pieces ^= source_bit
        source = source_bit.bit_length() - 1
        for line, choices in _GEOMETRY[source]:
            distance = (occupied & line).bit_count()
            for destination_bit, between, move in choices[distance]:
                if not (destination_bit & ours) and not (between & theirs):
                    append(move)
    return result


def _move_string(move):
    source, destination = move >> 6, move & 63
    return (
        f"{source // 8},{source % 8}:"
        f"{destination // 8},{destination % 8}"
    )


class _TimeUp(Exception):
    pass


def policy(board) -> str:
    deadline = time.perf_counter() + 0.88

    ours = 0
    theirs = 0
    for r in range(8):
        for c in range(8):
            value = int(board[r][c])
            if value == 1:
                ours |= _BITS[r * 8 + c]
            elif value == -1:
                theirs |= _BITS[r * 8 + c]

    root_moves = _legal_moves(ours, theirs)

    # A playable position must have a legal move under the supplied API.
    best_move = root_moves[0]
    if len(root_moves) == 1:
        return _move_string(best_move)

    position_cache = {}
    transpositions = {}
    history = [[0] * 4096 for _ in range(2)]
    killers = [[-1, -1] for _ in range(128)]
    nodes = 0

    def position_info(bits):
        cached = position_cache.get(bits)
        if cached is not None:
            return cached

        n = bits.bit_count()
        if not n:
            result = (-10000, 0, 0, 0, (), (), 0, {})
            position_cache[bits] = result
            return result

        remaining = bits
        groups = []
        while remaining:
            component = remaining & -remaining
            while True:
                enlarged = _spread(component) & remaining
                if enlarged == component:
                    break
                component = enlarged
            groups.append(component)
            remaining ^= component

        groups = tuple(groups)
        expanded = tuple(_spread(group) for group in groups)

        if len(groups) == 1:
            result = (_CONNECTED, n, 0, 0, groups, expanded, 0, {})
            position_cache[bits] = result
            return result

        sr = sc = ss = 0
        rmin = cmin = 8
        rmax = cmax = -1
        pieces = bits
        while pieces:
            bit = pieces & -pieces
            pieces ^= bit
            square = bit.bit_length() - 1
            r, c = _ROWS[square], _COLS[square]
            sr += r
            sc += c
            ss += _SQUARES[square]
            if r < rmin:
                rmin = r
            if r > rmax:
                rmax = r
            if c < cmin:
                cmin = c
            if c > cmax:
                cmax = c

        links = 2 * (
            (bits & ((bits << 1) & _NOT_A)).bit_count()
            + (bits & (bits << 8)).bit_count()
            + (bits & ((bits << 9) & _NOT_A)).bit_count()
            + (bits & ((bits << 7) & _NOT_H)).bit_count()
        )

        largest = max(group.bit_count() for group in groups)
        gap_sum = 0
        max_gap = 0
        for i, group in enumerate(groups):
            other_groups = bits ^ group
            reach = expanded[i]
            gap = 0
            while not (reach & other_groups):
                reach = _spread(reach)
                gap += 1
            gap_sum += gap
            if gap > max_gap:
                max_gap = gap

        concentration = (ss * n - sr * sr - sc * sc) / (n * n)
        center_distance = (
            (2 * sr - 7 * n) ** 2 + (2 * sc - 7 * n) ** 2
        ) / (4 * n * n)
        area = (rmax - rmin + 1) * (cmax - cmin + 1)

        score = (
            -42 * (len(groups) - 1)
            - int(24 * concentration)
            - 9 * gap_sum
            - 13 * max_gap
            + 105 * largest // n
            + 12 * links // n
            - 2 * area
            - int(2 * center_distance)
        )

        # A winning destination must touch every surviving component.
        prefix = [_FULL ^ bits]
        for region in expanded:
            prefix.append(prefix[-1] & region)
        common_targets = prefix[-1]

        singleton_targets = {}
        suffix = _FULL
        for i in range(len(groups) - 1, -1, -1):
            group = groups[i]
            if not (group & (group - 1)):
                targets = prefix[i] & suffix
                if targets:
                    singleton_targets[group] = targets
            suffix &= expanded[i]

        result = (
            score, n, sr, sc, groups, expanded,
            common_targets, singleton_targets,
        )
        position_cache[bits] = result
        return result

    def winning_move(a, b, info):
        common = info[6]
        exceptions = info[7]
        if not common and not exceptions:
            return None

        if common:
            sources = a
        else:
            sources = 0
            for bit in exceptions:
                sources |= bit

        occupied = a | b
        while sources:
            source_bit = sources & -sources
            sources ^= source_bit
            targets = exceptions.get(source_bit, common)
            if not targets:
                continue
            source = source_bit.bit_length() - 1
            for line, choices in _GEOMETRY[source]:
                distance = (occupied & line).bit_count()
                for destination_bit, between, move in choices[distance]:
                    if targets & destination_bit and not (between & b):
                        moved = (a ^ source_bit) | destination_bit
                        if _is_connected(moved):
                            return move
        return None

    def ordered_moves(a, b, moves, ai, bi, tt_move, ply):
        ranked = []
        hist = history[ply & 1]
        killer1, killer2 = killers[ply]
        n, sr, sc, groups = ai[1], ai[2], ai[3], ai[4]

        for move in moves:
            if move == tt_move:
                ranked.append((1_000_000_000, move))
                continue

            source, destination = move >> 6, move & 63
            source_bit, destination_bit = _BITS[source], _BITS[destination]
            moved = (a ^ source_bit) | destination_bit
            child_info = position_cache.get(moved)

            if child_info is not None and child_info[0] == _CONNECTED:
                ranked.append((500_000_000, move))
                continue

            if child_info is not None:
                score = 3 * (child_info[0] - ai[0])
            else:
                old_neighbors = (_NEIGHBORS[source] & a).bit_count()
                new_neighbors = _NEIGHBORS[destination] & (a ^ source_bit)
                touched = 0
                for group in groups:
                    if group & new_neighbors:
                        touched += 1

                joining = touched + (old_neighbors == 0) - 1
                center_gain = (
                    n * (_SQUARES[source] - _SQUARES[destination])
                    - 2 * (
                        sr * (_ROWS[source] - _ROWS[destination])
                        + sc * (_COLS[source] - _COLS[destination])
                    )
                ) // max(n, 1)
                score = (
                    120 * joining
                    + 9 * center_gain
                    + 14 * (new_neighbors.bit_count() - old_neighbors)
                )

            if destination_bit & b:
                opponent_child = position_cache.get(b ^ destination_bit)
                if opponent_child is not None:
                    if opponent_child[0] == _CONNECTED:
                        ranked.append((-100_000_000, move))
                        continue
                    score += 3 * (bi[0] - opponent_child[0])
                else:
                    neighbors = (_NEIGHBORS[destination] & b).bit_count()
                    score += 14 * (neighbors - 2)

            score += hist[move]
            if move == killer1:
                score += 6000
            elif move == killer2:
                score += 4500
            ranked.append((score, move))

        ranked.sort(reverse=True)
        return [move for _, move in ranked]

    def save_tt(key, depth, score, flag, move, ply):
        if score > 900000:
            score += ply
        elif score < -900000:
            score -= ply
        old = transpositions.get(key)
        if old is None or depth >= old[0]:
            transpositions[key] = (depth, score, flag, move)

    def search(a, b, depth, alpha, beta, ply):
        nonlocal nodes
        nodes += 1
        if (nodes & 63) == 0 and time.perf_counter() >= deadline:
            raise _TimeUp

        key = (a, b)
        entry = transpositions.get(key)
        tt_move = -1
        if entry is not None:
            stored_depth, value, flag, tt_move = entry
            if value > 900000:
                value -= ply
            elif value < -900000:
                value += ply
            if stored_depth >= depth:
                if flag == 0:
                    return value
                if flag == 1 and value >= beta:
                    return value
                if flag == 2 and value <= alpha:
                    return value

        ai = position_info(a)
        bi = position_info(b)

        # If both sides connect, the player who just moved wins.
        if bi[0] == _CONNECTED:
            return -_MATE + ply
        if ai[0] == _CONNECTED:
            return _MATE - ply
        if not a:
            return -_MATE + ply
        if not b:
            return _MATE - ply

        if depth <= 0:
            immediate = winning_move(a, b, ai)
            if immediate is not None:
                value = _MATE - ply - 1
                save_tt(key, 99, value, 0, immediate, ply)
                return value
            value = ai[0] - bi[0] + 8
            save_tt(key, 0, value, 0, -1, ply)
            return value

        moves = _legal_moves(a, b)
        if not moves:
            # Standard LOA passes when a player has no legal move.
            if not _legal_moves(b, a):
                return 0
            return -search(b, a, depth - 1, -beta, -alpha, ply + 1)

        moves = ordered_moves(a, b, moves, ai, bi, tt_move, ply)
        original_alpha = alpha
        best_value = -_INF
        best = moves[0]
        killer1, killer2 = killers[ply]

        for index, move in enumerate(moves):
            source_bit = _BITS[move >> 6]
            destination_bit = _BITS[move & 63]
            next_a = (a ^ source_bit) | destination_bit
            capture = bool(b & destination_bit)
            next_b = b & ~destination_bit

            if index == 0:
                value = -search(
                    next_b, next_a, depth - 1, -beta, -alpha, ply + 1
                )
            else:
                reduction = int(
                    depth >= 3
                    and index >= 10
                    and not capture
                    and move != killer1
                    and move != killer2
                    and len(ai[4]) >= 3
                    and len(bi[4]) >= 3
                )
                value = -search(
                    next_b, next_a, depth - 1 - reduction,
                    -alpha - 1, -alpha, ply + 1,
                )
                if reduction and value > alpha:
                    value = -search(
                        next_b, next_a, depth - 1,
                        -alpha - 1, -alpha, ply + 1,
                    )
                if alpha < value < beta:
                    value = -search(
                        next_b, next_a, depth - 1,
                        -beta, -alpha, ply + 1,
                    )

            if value > best_value:
                best_value, best = value, move
            if value > alpha:
                alpha = value
            if alpha >= beta:
                if not capture:
                    if killers[ply][0] != move:
                        killers[ply][1] = killers[ply][0]
                        killers[ply][0] = move
                    hist = history[ply & 1]
                    hist[move] = min(12000, hist[move] + 20 * depth * depth)
                break

        if best_value <= original_alpha:
            flag = 2
        elif best_value >= beta:
            flag = 1
        else:
            flag = 0
        save_tt(key, depth, best_value, flag, best, ply)
        return best_value

    try:
        initial_scores = {}
        initial_best = -_INF

        # Establish a tactically checked fallback and find immediate wins.
        for move in root_moves:
            if time.perf_counter() >= deadline:
                raise _TimeUp
            destination_bit = _BITS[move & 63]
            next_ours = (ours ^ _BITS[move >> 6]) | destination_bit
            next_theirs = theirs & ~destination_bit

            if position_info(next_ours)[0] == _CONNECTED:
                return _move_string(move)

            score = -search(next_theirs, next_ours, 0, -_INF, _INF, 1)
            initial_scores[move] = score
            if score > initial_best:
                initial_best = score
                best_move = move

        root_moves.sort(key=lambda m: initial_scores[m], reverse=True)

        for depth in range(2, 65):
            alpha = -_INF
            iteration_scores = {}
            iteration_best = -_INF

            for index, move in enumerate(root_moves):
                if time.perf_counter() >= deadline:
                    raise _TimeUp

                destination_bit = _BITS[move & 63]
                next_ours = (ours ^ _BITS[move >> 6]) | destination_bit
                next_theirs = theirs & ~destination_bit

                if index == 0:
                    score = -search(
                        next_theirs, next_ours, depth - 1,
                        -_INF, _INF, 1,
                    )
                else:
                    score = -search(
                        next_theirs, next_ours, depth - 1,
                        -alpha - 1, -alpha, 1,
                    )
                    if score > alpha:
                        score = -search(
                            next_theirs, next_ours, depth - 1,
                            -_INF, -alpha, 1,
                        )

                iteration_scores[move] = score
                if score > iteration_best:
                    iteration_best = score
                    best_move = move
                if score > alpha:
                    alpha = score

            root_moves.sort(
                key=lambda m: iteration_scores[m],
                reverse=True,
            )
            if iteration_best > 900000:
                break

    except _TimeUp:
        pass

    return _move_string(best_move)
