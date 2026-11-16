
import time


INF = 1_000_000
MATE = 100_000

_TT = {}
_HISTORY = {}
_KILLERS = {}
_DEADLINE = 0.0
_NODES = 0


class _SearchTimeout(Exception):
    pass


def _bits(squares):
    result = 0
    for row, col in squares:
        result |= 1 << (row * 8 + col)
    return result


def _check_time():
    if time.perf_counter() >= _DEADLINE:
        raise _SearchTimeout


def _generate_moves(state, side):
    """Return (moves, captures_exist).

    A move is (source_index, destination_index, captured_index, promotes).
    """
    bm, bk, wm, wk = state
    occupied = bm | bk | wm | wk
    captures = []

    if side == 0:
        men = bm
        kings = bk
        enemy = wm | wk
        man_dr = -1
        promotion_row = 0
    else:
        men = wm
        kings = wk
        enemy = bm | bk
        man_dr = 1
        promotion_row = 7

    pieces = men
    while pieces:
        lsb = pieces & -pieces
        src = lsb.bit_length() - 1
        pieces ^= lsb
        row, col = divmod(src, 8)

        jump_row = row + 2 * man_dr
        if 0 <= jump_row < 8:
            middle_row = row + man_dr
            for dc in (-1, 1):
                middle_col = col + dc
                dest_col = col + 2 * dc
                if 0 <= middle_col < 8 and 0 <= dest_col < 8:
                    middle = middle_row * 8 + middle_col
                    dest = jump_row * 8 + dest_col
                    if ((enemy >> middle) & 1) and not ((occupied >> dest) & 1):
                        captures.append(
                            (src, dest, middle, jump_row == promotion_row)
                        )

    pieces = kings
    while pieces:
        lsb = pieces & -pieces
        src = lsb.bit_length() - 1
        pieces ^= lsb
        row, col = divmod(src, 8)

        for dr in (-1, 1):
            jump_row = row + 2 * dr
            middle_row = row + dr
            if not 0 <= jump_row < 8:
                continue
            for dc in (-1, 1):
                middle_col = col + dc
                dest_col = col + 2 * dc
                if 0 <= middle_col < 8 and 0 <= dest_col < 8:
                    middle = middle_row * 8 + middle_col
                    dest = jump_row * 8 + dest_col
                    if ((enemy >> middle) & 1) and not ((occupied >> dest) & 1):
                        captures.append((src, dest, middle, False))

    if captures:
        return captures, True

    quiet = []

    pieces = men
    while pieces:
        lsb = pieces & -pieces
        src = lsb.bit_length() - 1
        pieces ^= lsb
        row, col = divmod(src, 8)
        dest_row = row + man_dr

        if 0 <= dest_row < 8:
            for dc in (-1, 1):
                dest_col = col + dc
                if 0 <= dest_col < 8:
                    dest = dest_row * 8 + dest_col
                    if not ((occupied >> dest) & 1):
                        quiet.append(
                            (src, dest, -1, dest_row == promotion_row)
                        )

    pieces = kings
    while pieces:
        lsb = pieces & -pieces
        src = lsb.bit_length() - 1
        pieces ^= lsb
        row, col = divmod(src, 8)

        for dr in (-1, 1):
            dest_row = row + dr
            if not 0 <= dest_row < 8:
                continue
            for dc in (-1, 1):
                dest_col = col + dc
                if 0 <= dest_col < 8:
                    dest = dest_row * 8 + dest_col
                    if not ((occupied >> dest) & 1):
                        quiet.append((src, dest, -1, False))

    return quiet, False


def _apply_move(state, side, move):
    bm, bk, wm, wk = state
    src, dest, captured, promotes = move
    src_bit = 1 << src
    dest_bit = 1 << dest

    if side == 0:
        if bm & src_bit:
            bm &= ~src_bit
            if promotes:
                bk |= dest_bit
            else:
                bm |= dest_bit
        else:
            bk = (bk & ~src_bit) | dest_bit

        if captured >= 0:
            captured_bit = 1 << captured
            if wm & captured_bit:
                wm &= ~captured_bit
            else:
                wk &= ~captured_bit
    else:
        if wm & src_bit:
            wm &= ~src_bit
            if promotes:
                wk |= dest_bit
            else:
                wm |= dest_bit
        else:
            wk = (wk & ~src_bit) | dest_bit

        if captured >= 0:
            captured_bit = 1 << captured
            if bm & captured_bit:
                bm &= ~captured_bit
            else:
                bk &= ~captured_bit

    return bm, bk, wm, wk


def _side_position(men, kings, black, occupied):
    score = 0
    own = men | kings
    center_bonus = (0, 1, 3, 5, 5, 3, 1, 0)

    pieces = men
    while pieces:
        lsb = pieces & -pieces
        square = lsb.bit_length() - 1
        pieces ^= lsb
        row, col = divmod(square, 8)

        advancement = 7 - row if black else row
        value = 100 + 4 * advancement + center_bonus[col]

        if (black and row == 7) or ((not black) and row == 0):
            value += 7
        if (black and row == 1) or ((not black) and row == 6):
            value += 8
        if col == 0 or col == 7:
            value += 1

        # Reward diagonal support from a piece closer to the home rank.
        support_row = row + 1 if black else row - 1
        if 0 <= support_row < 8:
            for dc in (-1, 1):
                support_col = col + dc
                if 0 <= support_col < 8:
                    support_square = support_row * 8 + support_col
                    if (own >> support_square) & 1:
                        value += 2

        score += value

    pieces = kings
    while pieces:
        lsb = pieces & -pieces
        square = lsb.bit_length() - 1
        pieces ^= lsb
        row, col = divmod(square, 8)

        centrality = 14 - abs(2 * row - 7) - abs(2 * col - 7)
        score += 180 + centrality

    return score


def _mobility(state, side):
    bm, bk, wm, wk = state
    occupied = bm | bk | wm | wk

    if side == 0:
        men, kings, dr = bm, bk, -1
    else:
        men, kings, dr = wm, wk, 1

    count = 0
    pieces = men
    while pieces:
        lsb = pieces & -pieces
        square = lsb.bit_length() - 1
        pieces ^= lsb
        row, col = divmod(square, 8)
        dest_row = row + dr

        if 0 <= dest_row < 8:
            for dc in (-1, 1):
                dest_col = col + dc
                if 0 <= dest_col < 8:
                    dest = dest_row * 8 + dest_col
                    if not ((occupied >> dest) & 1):
                        count += 1

    pieces = kings
    while pieces:
        lsb = pieces & -pieces
        square = lsb.bit_length() - 1
        pieces ^= lsb
        row, col = divmod(square, 8)

        for step_row in (-1, 1):
            dest_row = row + step_row
            if not 0 <= dest_row < 8:
                continue
            for dc in (-1, 1):
                dest_col = col + dc
                if 0 <= dest_col < 8:
                    dest = dest_row * 8 + dest_col
                    if not ((occupied >> dest) & 1):
                        count += 1

    return count


def _evaluate(state, side):
    bm, bk, wm, wk = state
    occupied = bm | bk | wm | wk

    black_score = _side_position(bm, bk, True, occupied)
    white_score = _side_position(wm, wk, False, occupied)
    score = black_score - white_score

    total_pieces = occupied.bit_count()
    if total_pieces <= 14:
        score += 2 * (_mobility(state, 0) - _mobility(state, 1))

        # In sparse endings, kings become especially valuable.
        score += 3 * (bk.bit_count() - wk.bit_count())

    return score if side == 0 else -score


def _move_score(state, side, move, tt_move, ply):
    src, dest, captured, promotes = move
    score = 0

    if move == tt_move:
        score += 1_000_000

    if captured >= 0:
        score += 20_000
        captured_bit = 1 << captured
        if side == 0:
            if state[3] & captured_bit:
                score += 900
        else:
            if state[1] & captured_bit:
                score += 900
        if promotes:
            score += 700
    else:
        if promotes:
            score += 5_000

        killers = _KILLERS.get(ply)
        if killers:
            if move == killers[0]:
                score += 3_000
            elif len(killers) > 1 and move == killers[1]:
                score += 2_000

        score += _HISTORY.get((side, src, dest), 0)

    row, col = divmod(dest, 8)
    score += 12 - abs(2 * row - 7) - abs(2 * col - 7)
    return score


def _order_moves(moves, state, side, ply, tt_move):
    moves.sort(
        key=lambda move: _move_score(state, side, move, tt_move, ply),
        reverse=True,
    )


def _record_killer(move, ply, depth, side):
    if move[2] >= 0:
        return

    killers = _KILLERS.setdefault(ply, [])
    if not killers or killers[0] != move:
        if move in killers:
            killers.remove(move)
        killers.insert(0, move)
        if len(killers) > 2:
            killers.pop()

    key = (side, move[0], move[1])
    _HISTORY[key] = _HISTORY.get(key, 0) + depth * depth


def _search(state, side, depth, alpha, beta, ply):
    global _NODES

    _NODES += 1
    if (_NODES & 255) == 0:
        _check_time()

    key = (state[0], state[1], state[2], state[3], side)
    alpha_original = alpha
    beta_original = beta

    entry = _TT.get(key)
    tt_move = None
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

    moves, captures = _generate_moves(state, side)

    if not moves:
        return -MATE + ply

    # Quiescence: at the horizon, continue all mandatory captures.
    if depth <= 0 and not captures:
        return _evaluate(state, side)

    _order_moves(moves, state, side, ply, tt_move)

    next_depth = depth - 1 if depth > 0 else 0
    best_value = -INF
    best_move = moves[0]
    first = True

    for move in moves:
        child = _apply_move(state, side, move)

        if first:
            value = -_search(
                child, 1 - side, next_depth, -beta, -alpha, ply + 1
            )
            first = False
        else:
            value = -_search(
                child, 1 - side, next_depth, -alpha - 1, -alpha, ply + 1
            )
            if alpha < value < beta:
                value = -_search(
                    child, 1 - side, next_depth, -beta, -alpha, ply + 1
                )

        if value > best_value:
            best_value = value
            best_move = move

        if value > alpha:
            alpha = value

        if alpha >= beta:
            _record_killer(move, ply, max(1, depth), side)
            break

    if best_value <= alpha_original:
        flag = 2  # Upper bound
    elif best_value >= beta_original:
        flag = 1  # Lower bound
    else:
        flag = 0  # Exact

    old_entry = _TT.get(key)
    if old_entry is None or old_entry[0] <= depth:
        _TT[key] = (depth, best_value, flag, best_move)

    return best_value


def _root_search(state, side, moves, depth, preferred):
    _check_time()

    ordered = list(moves)
    _order_moves(ordered, state, side, 0, preferred)

    alpha = -INF
    beta = INF
    best_score = -INF
    best_move = ordered[0]
    first = True

    for move in ordered:
        _check_time()
        child = _apply_move(state, side, move)

        if first:
            score = -_search(
                child, 1 - side, depth - 1, -beta, -alpha, 1
            )
            first = False
        else:
            score = -_search(
                child, 1 - side, depth - 1, -alpha - 1, -alpha, 1
            )
            if alpha < score < beta:
                score = -_search(
                    child, 1 - side, depth - 1, -beta, -alpha, 1
                )

        if score > best_score:
            best_score = score
            best_move = move

        if score > alpha:
            alpha = score

    key = (state[0], state[1], state[2], state[3], side)
    _TT[key] = (depth, best_score, 0, best_move)
    return best_move, best_score


def policy(
    my_men,
    my_kings,
    opp_men,
    opp_kings,
    color
) -> tuple[tuple[int, int], tuple[int, int]]:
    global _TT, _HISTORY, _KILLERS, _DEADLINE, _NODES

    if color == "b":
        state = (
            _bits(my_men),
            _bits(my_kings),
            _bits(opp_men),
            _bits(opp_kings),
        )
        side = 0
    else:
        state = (
            _bits(opp_men),
            _bits(opp_kings),
            _bits(my_men),
            _bits(my_kings),
        )
        side = 1

    root_moves, _ = _generate_moves(state, side)

    # A terminal position should not be sent to the policy by the arena.
    if not root_moves:
        return ((0, 0), (0, 0))

    _TT = {}
    _HISTORY = {}
    _KILLERS = {}
    _NODES = 0
    _DEADLINE = time.perf_counter() + 0.90

    # Establish a legal fallback before any timed search.
    fallback_moves = list(root_moves)
    _order_moves(fallback_moves, state, side, 0, None)
    best_move = fallback_moves[0]

    if len(root_moves) > 1:
        depth = 1
        try:
            while depth <= 40:
                candidate, _ = _root_search(
                    state, side, root_moves, depth, best_move
                )
                best_move = candidate
                depth += 1
        except _SearchTimeout:
            pass

    src, dest = best_move[0], best_move[1]
    from_row, from_col = divmod(src, 8)
    to_row, to_col = divmod(dest, 8)
    return ((from_row, from_col), (to_row, to_col))
