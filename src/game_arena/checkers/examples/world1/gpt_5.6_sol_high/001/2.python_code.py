
import time


BOARD_SIZE = 8
MATE_SCORE = 100000
INF = 1000000


class SearchTimeout(Exception):
    pass


def _bits_from_squares(squares):
    result = 0
    for row, col in squares:
        if 0 <= row < 8 and 0 <= col < 8:
            result |= 1 << (row * 8 + col)
    return result


def _iter_bits(bits):
    while bits:
        bit = bits & -bits
        yield bit.bit_length() - 1
        bits ^= bit


def _generate_moves(state):
    """
    State is relative to the player to move:
        (my_men, my_kings, opp_men, opp_kings, direction)

    Each generated move is:
        (from_index, to_index, child_state, is_capture,
         is_promotion, captured_king, ordering_score)
    """
    my_men, my_kings, opp_men, opp_kings, direction = state
    occupied = my_men | my_kings | opp_men | opp_kings
    captures = []

    for is_king, pieces in ((False, my_men), (True, my_kings)):
        for source in _iter_bits(pieces):
            row, col = divmod(source, 8)
            row_directions = (-1, 1) if is_king else (direction,)

            for dr in row_directions:
                for dc in (-1, 1):
                    middle_row = row + dr
                    middle_col = col + dc
                    target_row = row + 2 * dr
                    target_col = col + 2 * dc

                    if not (0 <= target_row < 8 and
                            0 <= target_col < 8 and
                            0 <= middle_row < 8 and
                            0 <= middle_col < 8):
                        continue

                    middle = middle_row * 8 + middle_col
                    target = target_row * 8 + target_col
                    middle_bit = 1 << middle
                    target_bit = 1 << target

                    if not ((opp_men | opp_kings) & middle_bit):
                        continue
                    if occupied & target_bit:
                        continue

                    source_bit = 1 << source
                    new_my_men = my_men
                    new_my_kings = my_kings
                    promotion = False

                    if is_king:
                        new_my_kings = (new_my_kings ^ source_bit) | target_bit
                    else:
                        new_my_men ^= source_bit
                        promotion_row = 7 if direction == 1 else 0
                        if target_row == promotion_row:
                            new_my_kings |= target_bit
                            promotion = True
                        else:
                            new_my_men |= target_bit

                    captured_king = bool(opp_kings & middle_bit)
                    new_opp_men = opp_men & ~middle_bit
                    new_opp_kings = opp_kings & ~middle_bit

                    child = (
                        new_opp_men,
                        new_opp_kings,
                        new_my_men,
                        new_my_kings,
                        -direction,
                    )

                    center = 7 - (
                        abs(2 * target_row - 7) +
                        abs(2 * target_col - 7)
                    ) // 2
                    order_score = (
                        10000
                        + (700 if captured_king else 300)
                        + (500 if promotion else 0)
                        + center
                    )

                    captures.append((
                        source,
                        target,
                        child,
                        True,
                        promotion,
                        captured_king,
                        order_score,
                    ))

    if captures:
        return captures

    quiet_moves = []

    for is_king, pieces in ((False, my_men), (True, my_kings)):
        for source in _iter_bits(pieces):
            row, col = divmod(source, 8)
            row_directions = (-1, 1) if is_king else (direction,)

            for dr in row_directions:
                target_row = row + dr
                if not 0 <= target_row < 8:
                    continue

                for dc in (-1, 1):
                    target_col = col + dc
                    if not 0 <= target_col < 8:
                        continue

                    target = target_row * 8 + target_col
                    target_bit = 1 << target
                    if occupied & target_bit:
                        continue

                    source_bit = 1 << source
                    new_my_men = my_men
                    new_my_kings = my_kings
                    promotion = False

                    if is_king:
                        new_my_kings = (new_my_kings ^ source_bit) | target_bit
                    else:
                        new_my_men ^= source_bit
                        promotion_row = 7 if direction == 1 else 0
                        if target_row == promotion_row:
                            new_my_kings |= target_bit
                            promotion = True
                        else:
                            new_my_men |= target_bit

                    child = (
                        opp_men,
                        opp_kings,
                        new_my_men,
                        new_my_kings,
                        -direction,
                    )

                    center = 7 - (
                        abs(2 * target_row - 7) +
                        abs(2 * target_col - 7)
                    ) // 2

                    edge_bonus = 3 if target_col in (0, 7) else 0
                    order_score = (
                        (1200 if promotion else 0)
                        + 3 * center
                        + edge_bonus
                    )

                    quiet_moves.append((
                        source,
                        target,
                        child,
                        False,
                        promotion,
                        False,
                        order_score,
                    ))

    return quiet_moves


def _position_value(men, kings, direction):
    value = 0
    friendly = men | kings
    home_row = 0 if direction == 1 else 7

    for square in _iter_bits(men):
        row, col = divmod(square, 8)
        progress = row if direction == 1 else 7 - row

        piece_value = 100 + 5 * progress

        if row == home_row:
            piece_value += 10
        if col in (0, 7):
            piece_value += 3
        if 2 <= row <= 5 and 2 <= col <= 5:
            piece_value += 4

        support_row = row - direction
        if 0 <= support_row < 8:
            supported = False
            for support_col in (col - 1, col + 1):
                if 0 <= support_col < 8:
                    support_bit = 1 << (support_row * 8 + support_col)
                    if friendly & support_bit:
                        supported = True
                        break
            if supported:
                piece_value += 5

        value += piece_value

    for square in _iter_bits(kings):
        row, col = divmod(square, 8)
        centrality = 7 - (
            abs(2 * row - 7) + abs(2 * col - 7)
        ) // 2
        value += 180 + 2 * centrality

        if col in (0, 7):
            value += 2

    return value


def _mobility_count(men, kings, opp_men, opp_kings, direction):
    occupied = men | kings | opp_men | opp_kings
    count = 0

    for is_king, pieces in ((False, men), (True, kings)):
        for square in _iter_bits(pieces):
            row, col = divmod(square, 8)
            row_directions = (-1, 1) if is_king else (direction,)

            for dr in row_directions:
                next_row = row + dr
                if not 0 <= next_row < 8:
                    continue
                for dc in (-1, 1):
                    next_col = col + dc
                    if not 0 <= next_col < 8:
                        continue
                    bit = 1 << (next_row * 8 + next_col)
                    if not occupied & bit:
                        count += 1

    return count


def _capture_pressure(men, kings, opp_men, opp_kings, direction):
    occupied = men | kings | opp_men | opp_kings
    pressure = 0

    for is_king, pieces in ((False, men), (True, kings)):
        for square in _iter_bits(pieces):
            row, col = divmod(square, 8)
            row_directions = (-1, 1) if is_king else (direction,)

            for dr in row_directions:
                for dc in (-1, 1):
                    middle_row = row + dr
                    middle_col = col + dc
                    target_row = row + 2 * dr
                    target_col = col + 2 * dc

                    if not (0 <= target_row < 8 and
                            0 <= target_col < 8 and
                            0 <= middle_row < 8 and
                            0 <= middle_col < 8):
                        continue

                    middle_bit = 1 << (
                        middle_row * 8 + middle_col
                    )
                    target_bit = 1 << (
                        target_row * 8 + target_col
                    )

                    if (opp_men | opp_kings) & middle_bit:
                        if not occupied & target_bit:
                            pressure += (
                                18 if opp_kings & middle_bit else 10
                            )

    return pressure


def _endgame_chase_bonus(my_men, my_kings, opp_men, opp_kings):
    my_material = 100 * my_men.bit_count() + 180 * my_kings.bit_count()
    opp_material = 100 * opp_men.bit_count() + 180 * opp_kings.bit_count()
    total_pieces = (
        my_men.bit_count() + my_kings.bit_count() +
        opp_men.bit_count() + opp_kings.bit_count()
    )

    if total_pieces > 8 or my_material == opp_material:
        return 0

    my_pieces = my_men | my_kings
    opp_pieces = opp_men | opp_kings

    if my_material > opp_material and my_kings and opp_pieces:
        best_distance = 14
        for king_square in _iter_bits(my_kings):
            kr, kc = divmod(king_square, 8)
            for enemy_square in _iter_bits(opp_pieces):
                er, ec = divmod(enemy_square, 8)
                distance = abs(kr - er) + abs(kc - ec)
                best_distance = min(best_distance, distance)
        return 2 * (14 - best_distance)

    if opp_material > my_material and opp_kings and my_pieces:
        best_distance = 14
        for king_square in _iter_bits(opp_kings):
            kr, kc = divmod(king_square, 8)
            for piece_square in _iter_bits(my_pieces):
                pr, pc = divmod(piece_square, 8)
                distance = abs(kr - pr) + abs(kc - pc)
                best_distance = min(best_distance, distance)
        return -2 * (14 - best_distance)

    return 0


def _evaluate(state):
    my_men, my_kings, opp_men, opp_kings, direction = state

    score = (
        _position_value(my_men, my_kings, direction)
        - _position_value(opp_men, opp_kings, -direction)
    )

    my_mobility = _mobility_count(
        my_men, my_kings, opp_men, opp_kings, direction
    )
    opp_mobility = _mobility_count(
        opp_men, opp_kings, my_men, my_kings, -direction
    )
    score += 2 * (my_mobility - opp_mobility)

    my_pressure = _capture_pressure(
        my_men, my_kings, opp_men, opp_kings, direction
    )
    opp_pressure = _capture_pressure(
        opp_men, opp_kings, my_men, my_kings, -direction
    )
    score += my_pressure - opp_pressure

    score += _endgame_chase_bonus(
        my_men, my_kings, opp_men, opp_kings
    )

    return score + 2


def policy(
    my_men,
    my_kings,
    opp_men,
    opp_kings,
    color
) -> tuple[tuple[int, int], tuple[int, int]]:
    direction = -1 if color == 'b' else 1

    root_state = (
        _bits_from_squares(my_men),
        _bits_from_squares(my_kings),
        _bits_from_squares(opp_men),
        _bits_from_squares(opp_kings),
        direction,
    )

    root_moves = _generate_moves(root_state)

    if not root_moves:
        # A terminal position has no legal move. The arena should not request
        # a policy action in such a state.
        if my_men:
            square = tuple(my_men[0])
            return square, square
        if my_kings:
            square = tuple(my_kings[0])
            return square, square
        return (0, 0), (0, 0)

    # Establish a guaranteed legal move before any timed search.
    root_moves.sort(key=lambda move: move[6], reverse=True)
    best_move = (root_moves[0][0], root_moves[0][1])

    deadline = time.perf_counter() + 0.88
    transposition = {}
    nodes = [0]

    def check_time():
        nodes[0] += 1
        if (nodes[0] & 127) == 0:
            if time.perf_counter() >= deadline:
                raise SearchTimeout

    def order_moves(moves, preferred):
        if preferred is None:
            moves.sort(key=lambda move: move[6], reverse=True)
        else:
            moves.sort(
                key=lambda move: (
                    1 if (move[0], move[1]) == preferred else 0,
                    move[6],
                ),
                reverse=True,
            )

    def quiescence(state, alpha, beta, ply, remaining):
        check_time()
        moves = _generate_moves(state)

        if not moves:
            return -MATE_SCORE + ply

        if remaining <= 0 or not moves[0][3]:
            return _evaluate(state)

        order_moves(moves, None)
        best_score = -INF

        for move in moves:
            score = -quiescence(
                move[2], -beta, -alpha, ply + 1, remaining - 1
            )

            if score > best_score:
                best_score = score
            if score > alpha:
                alpha = score
            if alpha >= beta:
                break

        return best_score

    def negamax(state, depth, alpha, beta, ply):
        check_time()

        if depth <= 0:
            return quiescence(state, alpha, beta, ply, 16), None

        original_alpha = alpha
        original_beta = beta
        entry = transposition.get(state)
        preferred = None

        if entry is not None:
            entry_depth, flag, score, stored_move = entry
            preferred = stored_move

            if entry_depth >= depth:
                if flag == 0:
                    return score, stored_move
                if flag == 1:
                    alpha = max(alpha, score)
                else:
                    beta = min(beta, score)
                if alpha >= beta:
                    return score, stored_move

        moves = _generate_moves(state)

        if not moves:
            return -MATE_SCORE + ply, None

        order_moves(moves, preferred)

        best_score = -INF
        local_best_move = (moves[0][0], moves[0][1])

        for move in moves:
            child_score, _ = negamax(
                move[2], depth - 1, -beta, -alpha, ply + 1
            )
            score = -child_score

            if score > best_score:
                best_score = score
                local_best_move = (move[0], move[1])

            if score > alpha:
                alpha = score

            if alpha >= beta:
                break

        if best_score <= original_alpha:
            flag = 2  # Upper bound
        elif best_score >= original_beta:
            flag = 1  # Lower bound
        else:
            flag = 0  # Exact

        transposition[state] = (
            depth,
            flag,
            best_score,
            local_best_move,
        )
        return best_score, local_best_move

    try:
        for depth in range(1, 31):
            score, candidate = negamax(
                root_state, depth, -INF, INF, 0
            )
            if candidate is not None:
                best_move = candidate

            if abs(score) >= MATE_SCORE - 100:
                break

            if time.perf_counter() >= deadline:
                break

    except SearchTimeout:
        pass

    from_square = divmod(best_move[0], 8)
    to_square = divmod(best_move[1], 8)
    return from_square, to_square
