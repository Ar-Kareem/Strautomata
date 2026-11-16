
import time


# A move is represented internally as:
# (source_square, destination_square, captured_square_or_minus_one, promotes)
_DIRECTIONS = ((-1, -1), (-1, 1), (1, -1), (1, 1))
_MATE = 100000
_INF = 1000000


class _SearchTimeout(Exception):
    pass


def _mask_from_squares(squares):
    mask = 0
    for row, col in squares:
        mask |= 1 << (row * 8 + col)
    return mask


def _iter_bits(mask):
    while mask:
        bit = mask & -mask
        yield bit.bit_length() - 1
        mask ^= bit


# Precomputed positional information.
_MAN_TABLE = [[0] * 64 for _ in range(2)]
_KING_TABLE = [0] * 64
_ADJACENT = [0] * 64
_CENTER_VALUE = [0] * 64

for _row in range(8):
    for _col in range(8):
        _sq = _row * 8 + _col

        # Integer approximation of closeness to the four central squares.
        _central_distance = (
            abs(2 * _row - 7) + abs(2 * _col - 7)
        )
        _center = max(0, 14 - _central_distance)
        _CENTER_VALUE[_sq] = _center
        _KING_TABLE[_sq] = _center

        for _color in (0, 1):
            # 0 is black (toward row 0), 1 is white (toward row 7).
            _progress = 7 - _row if _color == 0 else _row
            _value = 4 * _progress

            if 2 <= _row <= 5 and 2 <= _col <= 5:
                _value += 5
            elif 1 <= _col <= 6:
                _value += 2

            # Edge men cannot be captured from the outside.
            if _col == 0 or _col == 7:
                _value += 3

            # Preserve some back-rank defense.
            if (_color == 0 and _row == 7) or (
                _color == 1 and _row == 0
            ):
                _value += 8

            # Men close to promotion are especially valuable.
            if _progress == 6:
                _value += 8

            _MAN_TABLE[_color][_sq] = _value

        _adj = 0
        for _dr, _dc in _DIRECTIONS:
            _nr = _row + _dr
            _nc = _col + _dc
            if 0 <= _nr < 8 and 0 <= _nc < 8:
                _adj |= 1 << (_nr * 8 + _nc)
        _ADJACENT[_sq] = _adj


def _capture_moves(mm, mk, om, ok, color):
    occupied = mm | mk | om | ok
    opponents = om | ok
    moves = []

    # Regular men capture in their forward direction.
    forward = -1 if color == 0 else 1
    for source in _iter_bits(mm):
        row, col = divmod(source, 8)
        for dc in (-1, 1):
            middle_row = row + forward
            middle_col = col + dc
            dest_row = row + 2 * forward
            dest_col = col + 2 * dc

            if not (
                0 <= middle_row < 8
                and 0 <= middle_col < 8
                and 0 <= dest_row < 8
                and 0 <= dest_col < 8
            ):
                continue

            middle = middle_row * 8 + middle_col
            destination = dest_row * 8 + dest_col

            if (
                opponents & (1 << middle)
                and not (occupied & (1 << destination))
            ):
                promotes = (
                    (color == 0 and dest_row == 0)
                    or (color == 1 and dest_row == 7)
                )
                moves.append((source, destination, middle, promotes))

    # Kings capture one square in all four diagonal directions.
    for source in _iter_bits(mk):
        row, col = divmod(source, 8)
        for dr, dc in _DIRECTIONS:
            middle_row = row + dr
            middle_col = col + dc
            dest_row = row + 2 * dr
            dest_col = col + 2 * dc

            if not (
                0 <= middle_row < 8
                and 0 <= middle_col < 8
                and 0 <= dest_row < 8
                and 0 <= dest_col < 8
            ):
                continue

            middle = middle_row * 8 + middle_col
            destination = dest_row * 8 + dest_col

            if (
                opponents & (1 << middle)
                and not (occupied & (1 << destination))
            ):
                moves.append((source, destination, middle, False))

    return moves


def _quiet_moves(mm, mk, om, ok, color):
    occupied = mm | mk | om | ok
    moves = []

    forward = -1 if color == 0 else 1
    for source in _iter_bits(mm):
        row, col = divmod(source, 8)
        dest_row = row + forward
        if not (0 <= dest_row < 8):
            continue

        for dc in (-1, 1):
            dest_col = col + dc
            if not (0 <= dest_col < 8):
                continue

            destination = dest_row * 8 + dest_col
            if not (occupied & (1 << destination)):
                promotes = (
                    (color == 0 and dest_row == 0)
                    or (color == 1 and dest_row == 7)
                )
                moves.append((source, destination, -1, promotes))

    for source in _iter_bits(mk):
        row, col = divmod(source, 8)
        for dr, dc in _DIRECTIONS:
            dest_row = row + dr
            dest_col = col + dc
            if not (
                0 <= dest_row < 8 and 0 <= dest_col < 8
            ):
                continue

            destination = dest_row * 8 + dest_col
            if not (occupied & (1 << destination)):
                moves.append((source, destination, -1, False))

    return moves


def _legal_moves(state):
    mm, mk, om, ok, color = state
    captures = _capture_moves(mm, mk, om, ok, color)
    if captures:
        return captures
    return _quiet_moves(mm, mk, om, ok, color)


def _apply_move(state, move):
    mm, mk, om, ok, color = state
    source, destination, captured, promotes = move

    source_bit = 1 << source
    destination_bit = 1 << destination
    moving_king = bool(mk & source_bit)

    if moving_king:
        mk = (mk ^ source_bit) | destination_bit
    else:
        mm ^= source_bit
        if promotes:
            mk |= destination_bit
        else:
            mm |= destination_bit

    if captured >= 0:
        captured_bit = 1 << captured
        om &= ~captured_bit
        ok &= ~captured_bit

    # Negamax always stores the next player first.
    return om, ok, mm, mk, 1 - color


def _mobility(mm, mk, occupied, color):
    total = 0
    forward = -1 if color == 0 else 1

    for source in _iter_bits(mm):
        row, col = divmod(source, 8)
        nr = row + forward
        if 0 <= nr < 8:
            if col > 0 and not (
                occupied & (1 << (nr * 8 + col - 1))
            ):
                total += 1
            if col < 7 and not (
                occupied & (1 << (nr * 8 + col + 1))
            ):
                total += 1

    for source in _iter_bits(mk):
        row, col = divmod(source, 8)
        for dr, dc in _DIRECTIONS:
            nr = row + dr
            nc = col + dc
            if (
                0 <= nr < 8
                and 0 <= nc < 8
                and not (occupied & (1 << (nr * 8 + nc)))
            ):
                total += 1

    return total


def _positional_sum(mask, table):
    result = 0
    while mask:
        bit = mask & -mask
        square = bit.bit_length() - 1
        result += table[square]
        mask ^= bit
    return result


def _connection_score(pieces):
    links = 0
    remaining = pieces
    while remaining:
        bit = remaining & -remaining
        square = bit.bit_length() - 1
        links += (_ADJACENT[square] & pieces).bit_count()
        remaining ^= bit
    return links // 2


def _king_endgame_activity(my_kings, opp_pieces):
    if not my_kings or not opp_pieces:
        return 0

    score = 0
    for king_sq in _iter_bits(my_kings):
        kr, kc = divmod(king_sq, 8)
        best = 8
        for enemy_sq in _iter_bits(opp_pieces):
            er, ec = divmod(enemy_sq, 8)
            distance = max(abs(kr - er), abs(kc - ec))
            if distance < best:
                best = distance
        score += 7 - best
    return score


def _evaluate(state):
    mm, mk, om, ok, color = state
    opponent_color = 1 - color

    my_men_count = mm.bit_count()
    my_king_count = mk.bit_count()
    opp_men_count = om.bit_count()
    opp_king_count = ok.bit_count()

    my_material = 100 * my_men_count + 178 * my_king_count
    opp_material = 100 * opp_men_count + 178 * opp_king_count
    material_difference = my_material - opp_material

    score = material_difference
    score += _positional_sum(mm, _MAN_TABLE[color])
    score -= _positional_sum(om, _MAN_TABLE[opponent_color])
    score += _positional_sum(mk, _KING_TABLE)
    score -= _positional_sum(ok, _KING_TABLE)

    my_pieces = mm | mk
    opp_pieces = om | ok
    occupied = my_pieces | opp_pieces

    score += 3 * (
        _connection_score(my_pieces) - _connection_score(opp_pieces)
    )

    my_mobility = _mobility(mm, mk, occupied, color)
    opp_mobility = _mobility(om, ok, occupied, opponent_color)
    score += 2 * (my_mobility - opp_mobility)

    total_pieces = (
        my_men_count
        + my_king_count
        + opp_men_count
        + opp_king_count
    )

    # When ahead, exchanging pieces generally improves winning chances.
    if material_difference > 0:
        score += 2 * (24 - total_pieces)
    elif material_difference < 0:
        score -= 2 * (24 - total_pieces)

    # In sparse endings, active kings should approach enemy pieces.
    if total_pieces <= 8:
        score += 2 * _king_endgame_activity(mk, opp_pieces)
        score -= 2 * _king_endgame_activity(ok, my_pieces)

    return score


def policy(
    my_men,
    my_kings,
    opp_men,
    opp_kings,
    color
) -> tuple[tuple[int, int], tuple[int, int]]:
    color_id = 0 if color == "b" else 1

    state = (
        _mask_from_squares(my_men),
        _mask_from_squares(my_kings),
        _mask_from_squares(opp_men),
        _mask_from_squares(opp_kings),
        color_id,
    )

    root_moves = _legal_moves(state)

    # A terminal position should not be sent to a move policy. This branch is
    # retained only as a defensive fallback for malformed arena calls.
    if not root_moves:
        return ((0, 0), (0, 0))

    # A legal answer is selected before any timed work begins.
    fallback = root_moves[0]
    if len(root_moves) == 1:
        source, destination = fallback[0], fallback[1]
        return divmod(source, 8), divmod(destination, 8)

    deadline = time.perf_counter() + 0.90
    nodes = 0
    transposition = {}
    history = {}
    killers = [[None, None] for _ in range(96)]
    path = set()

    def check_time():
        nonlocal nodes
        nodes += 1
        if (nodes & 255) == 0 and time.perf_counter() >= deadline:
            raise _SearchTimeout

    def order_moves(current_state, moves, tt_move, ply):
        if len(moves) <= 1:
            return moves

        mm, mk, om, ok, side = current_state
        killer_one = killers[ply][0] if ply < len(killers) else None
        killer_two = killers[ply][1] if ply < len(killers) else None

        def move_score(move):
            source, destination, captured, promotes = move

            if move == tt_move:
                return 10000000

            score = _CENTER_VALUE[destination]

            if captured >= 0:
                score += 100000
                captured_bit = 1 << captured
                if ok & captured_bit:
                    score += 3000
                else:
                    score += 1000

                # Prefer using a man rather than exposing a king, all else equal.
                if mk & (1 << source):
                    score -= 100
            else:
                if move == killer_one:
                    score += 80000
                elif move == killer_two:
                    score += 70000
                score += history.get((side, source, destination), 0)

            if promotes:
                score += 6000

            return score

        return sorted(moves, key=move_score, reverse=True)

    def quiescence(current_state, alpha, beta, ply):
        check_time()
        key = current_state

        if key in path:
            return 0

        mm, mk, om, ok, side = current_state
        captures = _capture_moves(mm, mk, om, ok, side)

        if not captures:
            quiet = _quiet_moves(mm, mk, om, ok, side)
            if not quiet:
                return -_MATE + ply
            return _evaluate(current_state)

        path.add(key)
        try:
            captures = order_moves(current_state, captures, None, ply)
            best = -_INF

            for index, move in enumerate(captures):
                child = _apply_move(current_state, move)

                if index == 0:
                    value = -quiescence(child, -beta, -alpha, ply + 1)
                else:
                    value = -quiescence(
                        child, -alpha - 1, -alpha, ply + 1
                    )
                    if alpha < value < beta:
                        value = -quiescence(
                            child, -beta, -alpha, ply + 1
                        )

                if value > best:
                    best = value
                if value > alpha:
                    alpha = value
                if alpha >= beta:
                    break

            return best
        finally:
            path.remove(key)

    def search(current_state, depth, alpha, beta, ply):
        check_time()

        if depth <= 0:
            return quiescence(current_state, alpha, beta, ply)

        key = current_state
        if key in path:
            return 0

        original_alpha = alpha
        original_beta = beta
        tt_move = None

        entry = transposition.get(key)
        if entry is not None:
            stored_depth, stored_value, flag, tt_move = entry
            if stored_depth >= depth:
                if flag == 0:
                    return stored_value
                if flag == 1:
                    alpha = max(alpha, stored_value)
                else:
                    beta = min(beta, stored_value)
                if alpha >= beta:
                    return stored_value

        path.add(key)
        try:
            moves = _legal_moves(current_state)
            if not moves:
                return -_MATE + ply

            moves = order_moves(current_state, moves, tt_move, ply)
            best_value = -_INF
            best_move = moves[0]

            for index, move in enumerate(moves):
                child = _apply_move(current_state, move)
                next_depth = depth - 1

                # Promotion is tactically important and occurs only once per man.
                if move[3]:
                    next_depth += 1

                is_capture = move[2] >= 0

                if index == 0:
                    value = -search(
                        child, next_depth, -beta, -alpha, ply + 1
                    )
                else:
                    # Late quiet moves receive a reduced probe first.
                    if (
                        not is_capture
                        and not move[3]
                        and depth >= 4
                        and index >= 3
                    ):
                        reduced_depth = max(0, next_depth - 1)
                        value = -search(
                            child,
                            reduced_depth,
                            -alpha - 1,
                            -alpha,
                            ply + 1,
                        )
                    else:
                        value = alpha + 1

                    if value > alpha:
                        value = -search(
                            child,
                            next_depth,
                            -alpha - 1,
                            -alpha,
                            ply + 1,
                        )
                        if alpha < value < beta:
                            value = -search(
                                child,
                                next_depth,
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
                    if not is_capture:
                        hist_key = (
                            current_state[4],
                            move[0],
                            move[1],
                        )
                        history[hist_key] = min(
                            200000,
                            history.get(hist_key, 0) + depth * depth,
                        )

                        if ply < len(killers) and move != killers[ply][0]:
                            killers[ply][1] = killers[ply][0]
                            killers[ply][0] = move
                    break

            if best_value <= original_alpha:
                flag = 2  # Upper bound.
            elif best_value >= original_beta:
                flag = 1  # Lower bound.
            else:
                flag = 0  # Exact.

            if len(transposition) < 200000:
                old = transposition.get(key)
                if old is None or depth >= old[0]:
                    transposition[key] = (
                        depth,
                        best_value,
                        flag,
                        best_move,
                    )

            return best_value
        finally:
            path.remove(key)

    def root_search(depth, preferred_move):
        alpha = -_INF
        beta = _INF
        best_value = -_INF
        best_move = preferred_move

        ordered = order_moves(state, root_moves, preferred_move, 0)
        path.add(state)
        try:
            for index, move in enumerate(ordered):
                if time.perf_counter() >= deadline:
                    raise _SearchTimeout

                child = _apply_move(state, move)
                next_depth = depth - 1 + (1 if move[3] else 0)

                if index == 0:
                    value = -search(
                        child, next_depth, -beta, -alpha, 1
                    )
                else:
                    value = -search(
                        child, next_depth, -alpha - 1, -alpha, 1
                    )
                    if alpha < value < beta:
                        value = -search(
                            child, next_depth, -beta, -alpha, 1
                        )

                if value > best_value:
                    best_value = value
                    best_move = move

                if value > alpha:
                    alpha = value
        finally:
            path.remove(state)

        if len(transposition) < 200000:
            transposition[state] = (depth, best_value, 0, best_move)

        return best_value, best_move

    best_move = fallback
    depth = 1

    while depth <= 30:
        try:
            value, candidate = root_search(depth, best_move)
            best_move = candidate

            # There is no need to search deeper after a forced mate is found.
            if value >= _MATE - 100:
                break

            depth += 1
        except _SearchTimeout:
            break

    source, destination = best_move[0], best_move[1]
    return divmod(source, 8), divmod(destination, 8)
