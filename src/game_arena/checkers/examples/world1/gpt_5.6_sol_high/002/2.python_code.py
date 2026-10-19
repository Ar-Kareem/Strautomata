
import time

# Persistent transposition table. Entries are:
# key -> (searched_depth, score, flag, best_move)
# flag: 0 = exact, 1 = lower bound, 2 = upper bound
_TT = {}

_DEADLINE = 0.0
_NODES = 0

_INF = 1_000_000
_WIN = 100_000


class _SearchTimeout(Exception):
    pass


def _iter_bits(board):
    while board:
        bit = board & -board
        square = bit.bit_length() - 1
        yield square
        board ^= bit


def _legal_moves(men, kings, opp_men, opp_kings, down):
    """
    Return encoded legal moves. A move is encoded as source | (destination << 6).
    Captures are mandatory.
    """
    occupied = men | kings | opp_men | opp_kings
    opponents = opp_men | opp_kings
    captures = []

    pieces = men | kings
    while pieces:
        source_bit = pieces & -pieces
        source = source_bit.bit_length() - 1
        pieces ^= source_bit

        row = source >> 3
        col = source & 7

        if kings & source_bit:
            directions = ((-1, -1), (-1, 1), (1, -1), (1, 1))
        else:
            dr = -1 if down else 1
            directions = ((dr, -1), (dr, 1))

        for dr, dc in directions:
            target_row = row + 2 * dr
            target_col = col + 2 * dc
            if not (0 <= target_row < 8 and 0 <= target_col < 8):
                continue

            middle = (row + dr) * 8 + (col + dc)
            target = target_row * 8 + target_col
            if ((opponents >> middle) & 1) and not ((occupied >> target) & 1):
                captures.append(source | (target << 6))

    if captures:
        return captures

    moves = []
    pieces = men | kings
    while pieces:
        source_bit = pieces & -pieces
        source = source_bit.bit_length() - 1
        pieces ^= source_bit

        row = source >> 3
        col = source & 7

        if kings & source_bit:
            directions = ((-1, -1), (-1, 1), (1, -1), (1, 1))
        else:
            dr = -1 if down else 1
            directions = ((dr, -1), (dr, 1))

        for dr, dc in directions:
            target_row = row + dr
            target_col = col + dc
            if not (0 <= target_row < 8 and 0 <= target_col < 8):
                continue

            target = target_row * 8 + target_col
            if not ((occupied >> target) & 1):
                moves.append(source | (target << 6))

    return moves


def _apply_move(men, kings, opp_men, opp_kings, down, move):
    source = move & 63
    target = (move >> 6) & 63

    source_bit = 1 << source
    target_bit = 1 << target
    was_king = bool(kings & source_bit)

    if was_king:
        kings &= ~source_bit
    else:
        men &= ~source_bit

    source_row = source >> 3
    target_row = target >> 3

    if abs(target_row - source_row) == 2:
        middle = (source + target) // 2
        middle_bit = 1 << middle
        opp_men &= ~middle_bit
        opp_kings &= ~middle_bit

    promotion_row = 0 if down else 7
    if was_king or target_row == promotion_row:
        kings |= target_bit
    else:
        men |= target_bit

    return men, kings, opp_men, opp_kings


def _support_count(pieces, down):
    """Count pieces supported by a friendly piece diagonally toward home."""
    count = 0
    dr = 1 if down else -1

    for square in _iter_bits(pieces):
        row = square >> 3
        col = square & 7
        support_row = row + dr

        if not (0 <= support_row < 8):
            continue

        supported = False
        if col > 0:
            supported = bool(pieces & (1 << (support_row * 8 + col - 1)))
        if not supported and col < 7:
            supported = bool(pieces & (1 << (support_row * 8 + col + 1)))

        if supported:
            count += 1

    return count


def _positional_score(men, kings, down):
    score = 0
    home_row = 7 if down else 0

    for square in _iter_bits(men):
        row = square >> 3
        col = square & 7
        advancement = 7 - row if down else row

        score += advancement * 4

        if 2 <= row <= 5 and 2 <= col <= 5:
            score += 5
        elif 1 <= row <= 6 and 1 <= col <= 6:
            score += 2

        if col == 0 or col == 7:
            score += 2

        if row == home_row:
            score += 7

    for square in _iter_bits(kings):
        row = square >> 3
        col = square & 7

        # Central kings have more mobility and greater tactical reach.
        centrality = 14 - abs(7 - 2 * row) - abs(7 - 2 * col)
        score += max(0, centrality // 2)

        # A slight edge safety bonus, without making passive kings too valuable.
        if col == 0 or col == 7:
            score += 1

    score += 3 * _support_count(men | kings, down)
    return score


def _is_capture(move):
    source = move & 63
    target = (move >> 6) & 63
    return abs((source >> 3) - (target >> 3)) == 2


def _evaluate(men, kings, opp_men, opp_kings, down, own_moves=None):
    own_count = men.bit_count() + kings.bit_count()
    opp_count = opp_men.bit_count() + opp_kings.bit_count()
    total_count = own_count + opp_count

    # Kings become increasingly valuable as the board opens.
    king_value = 178 + max(0, 12 - total_count) * 2

    score = 100 * (men.bit_count() - opp_men.bit_count())
    score += king_value * (kings.bit_count() - opp_kings.bit_count())

    score += _positional_score(men, kings, down)
    score -= _positional_score(opp_men, opp_kings, not down)

    if own_moves is None:
        own_moves = _legal_moves(men, kings, opp_men, opp_kings, down)
    opp_moves = _legal_moves(opp_men, opp_kings, men, kings, not down)

    own_mobility = min(len(own_moves), 12)
    opp_mobility = min(len(opp_moves), 12)
    score += 2 * (own_mobility - opp_mobility)

    if not opp_moves and (opp_men or opp_kings):
        score += 70

    own_captures = len(own_moves) if own_moves and _is_capture(own_moves[0]) else 0
    opp_captures = len(opp_moves) if opp_moves and _is_capture(opp_moves[0]) else 0
    score += 10 * (own_captures - opp_captures)

    # When ahead, exchanging pieces is generally favorable.
    material_lead = own_count - opp_count
    if material_lead > 0:
        score += max(0, 16 - total_count) * material_lead
    elif material_lead < 0:
        score += min(0, 16 - total_count) * (-material_lead)

    return score


def _move_order_score(move, men, kings, opp_men, opp_kings, down, tt_move):
    if move == tt_move:
        return 1_000_000

    source = move & 63
    target = (move >> 6) & 63
    source_row = source >> 3
    target_row = target >> 3
    target_col = target & 7

    score = 0
    if abs(target_row - source_row) == 2:
        score += 20_000
        middle = (source + target) // 2
        if opp_kings & (1 << middle):
            score += 1_000
        else:
            score += 300

    source_is_man = bool(men & (1 << source))
    promotion_row = 0 if down else 7
    if source_is_man and target_row == promotion_row:
        score += 2_000

    if 2 <= target_row <= 5 and 2 <= target_col <= 5:
        score += 80
    elif 1 <= target_row <= 6 and 1 <= target_col <= 6:
        score += 30

    if target_col == 0 or target_col == 7:
        score += 15

    if source_is_man:
        advancement = source_row - target_row if down else target_row - source_row
        score += 10 * advancement

    return score


def _ordered_moves(moves, men, kings, opp_men, opp_kings, down, tt_move):
    return sorted(
        moves,
        key=lambda mv: _move_order_score(
            mv, men, kings, opp_men, opp_kings, down, tt_move
        ),
        reverse=True,
    )


def _search(men, kings, opp_men, opp_kings, down,
            depth, alpha, beta, quiescence_left):
    global _NODES

    _NODES += 1
    if (_NODES & 255) == 0 and time.perf_counter() >= _DEADLINE:
        raise _SearchTimeout

    key = (men, kings, opp_men, opp_kings, down)
    tt_move = -1

    if depth > 0:
        entry = _TT.get(key)
        if entry is not None:
            stored_depth, stored_score, flag, tt_move = entry
            if stored_depth >= depth:
                if flag == 0:
                    return stored_score
                if flag == 1:
                    alpha = max(alpha, stored_score)
                else:
                    beta = min(beta, stored_score)
                if alpha >= beta:
                    return stored_score

    moves = _legal_moves(men, kings, opp_men, opp_kings, down)
    if not moves:
        return -_WIN

    capture_position = _is_capture(moves[0])

    if depth <= 0:
        if not capture_position or quiescence_left <= 0:
            return _evaluate(
                men, kings, opp_men, opp_kings, down, moves
            )

    alpha_start = alpha
    beta_start = beta
    best_score = -_INF
    best_move = moves[0]

    ordered = _ordered_moves(
        moves, men, kings, opp_men, opp_kings, down, tt_move
    )

    if depth > 0:
        next_depth = depth - 1
        next_quiescence = quiescence_left
    else:
        next_depth = 0
        next_quiescence = quiescence_left - 1

    for move in ordered:
        new_men, new_kings, new_opp_men, new_opp_kings = _apply_move(
            men, kings, opp_men, opp_kings, down, move
        )

        score = -_search(
            new_opp_men,
            new_opp_kings,
            new_men,
            new_kings,
            not down,
            next_depth,
            -beta,
            -alpha,
            next_quiescence,
        )

        if score > best_score:
            best_score = score
            best_move = move

        if score > alpha:
            alpha = score

        if alpha >= beta:
            break

    if depth > 0:
        if best_score <= alpha_start:
            flag = 2
        elif best_score >= beta_start:
            flag = 1
        else:
            flag = 0

        old_entry = _TT.get(key)
        if old_entry is None or depth >= old_entry[0]:
            _TT[key] = (depth, best_score, flag, best_move)

    return best_score


def _to_bitboard(squares):
    board = 0
    for row, col in squares:
        board |= 1 << (int(row) * 8 + int(col))
    return board


def _decode_move(move):
    source = move & 63
    target = (move >> 6) & 63
    return (
        (source >> 3, source & 7),
        (target >> 3, target & 7),
    )


def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[
    tuple[int, int], tuple[int, int]
]:
    global _DEADLINE, _NODES

    men = _to_bitboard(my_men)
    kings = _to_bitboard(my_kings)
    enemy_men = _to_bitboard(opp_men)
    enemy_kings = _to_bitboard(opp_kings)
    down = color == "b"

    legal = _legal_moves(men, kings, enemy_men, enemy_kings, down)

    # A policy is normally not called in a terminal position.
    if not legal:
        return ((0, 0), (0, 0))

    # If there is no choice, immediately return the only legal move.
    if len(legal) == 1:
        return _decode_move(legal[0])

    if len(_TT) > 220_000:
        _TT.clear()

    _NODES = 0
    _DEADLINE = time.perf_counter() + 0.92

    root_key = (men, kings, enemy_men, enemy_kings, down)
    previous_move = _TT.get(root_key, (0, 0, 0, -1))[3]

    ordered_fallback = _ordered_moves(
        legal, men, kings, enemy_men, enemy_kings, down, previous_move
    )
    best_move = ordered_fallback[0]

    piece_count = (
        men.bit_count()
        + kings.bit_count()
        + enemy_men.bit_count()
        + enemy_kings.bit_count()
    )

    if piece_count <= 6:
        maximum_depth = 30
    elif piece_count <= 10:
        maximum_depth = 22
    else:
        maximum_depth = 16

    for depth in range(1, maximum_depth + 1):
        try:
            _search(
                men,
                kings,
                enemy_men,
                enemy_kings,
                down,
                depth,
                -_INF,
                _INF,
                10,
            )

            entry = _TT.get(root_key)
            if entry is not None and entry[0] >= depth and entry[3] in legal:
                best_move = entry[3]

            if abs(entry[1]) >= _WIN if entry is not None else False:
                break

            if time.perf_counter() >= _DEADLINE:
                break

        except _SearchTimeout:
            break

    return _decode_move(best_move)
