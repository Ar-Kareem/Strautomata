
import time

ROWS = 6
COLS = 7
STRIDE = 7

COLUMN_MASKS = [0x3F << (c * STRIDE) for c in range(COLS)]
BOTTOM_MASK = sum(1 << (c * STRIDE) for c in range(COLS))
BOARD_MASK = sum(COLUMN_MASKS)

CENTER_ORDER = (3, 2, 4, 1, 5, 0, 6)
CENTER_VALUE = (1, 2, 3, 5, 3, 2, 1)

MATE = 1_000_000
INF = 2_000_000

EXACT = 0
LOWER = 1
UPPER = 2


def _make_winning_masks():
    masks = []
    directions = ((1, 0), (0, 1), (1, 1), (1, -1))

    for c in range(COLS):
        for r in range(ROWS):
            for dc, dr in directions:
                end_c = c + 3 * dc
                end_r = r + 3 * dr
                if 0 <= end_c < COLS and 0 <= end_r < ROWS:
                    mask = 0
                    for k in range(4):
                        cc = c + k * dc
                        rr = r + k * dr
                        mask |= 1 << (cc * STRIDE + rr)
                    masks.append(mask)

    return tuple(masks)


WINNING_MASKS = _make_winning_masks()

_deadline = 0.0
_nodes = 0
_tt = {}
_killers = [-1] * 64
_history = [0] * COLS
_root_preferred = 3


class _SearchTimeout(Exception):
    pass


def _possible_moves(occupied):
    return (occupied + BOTTOM_MASK) & BOARD_MASK


def _winning_positions(position):
    # Vertical wins only need the square immediately above three discs on a
    # valid gravity-respecting board.
    result = (
        (position << 1)
        & (position << 2)
        & (position << 3)
    )

    # Horizontal and both diagonal directions.
    for direction in (7, 6, 8):
        pair = (
            (position << direction)
            & (position << (2 * direction))
        )
        result |= pair & (position << (3 * direction))
        result |= pair & (position >> direction)

        pair = (
            (position >> direction)
            & (position >> (2 * direction))
        )
        result |= pair & (position >> (3 * direction))
        result |= pair & (position << direction)

    return result & BOARD_MASK


def _column_of(move_bit):
    return (move_bit.bit_length() - 1) // STRIDE


def _check_time(force=False):
    global _nodes
    _nodes += 1
    if force or (_nodes & 255) == 0:
        if time.perf_counter() >= _deadline:
            raise _SearchTimeout


def _position_key(player, opponent):
    return player | (opponent << 49)


def _store_tt(key, depth, value, flag, best_col):
    old = _tt.get(key)
    if old is None or depth >= old[0]:
        _tt[key] = (depth, value, flag, best_col)


def _evaluate(player, opponent):
    occupied = player | opponent
    score = 0

    for c in range(COLS):
        weight = CENTER_VALUE[c]
        score += weight * (
            (player & COLUMN_MASKS[c]).bit_count()
            - (opponent & COLUMN_MASKS[c]).bit_count()
        )

    values = (0, 1, 10, 65, 5000)

    for mask in WINNING_MASKS:
        player_count = (player & mask).bit_count()
        opponent_count = (opponent & mask).bit_count()

        if opponent_count == 0:
            score += values[player_count]
        elif player_count == 0:
            score -= values[opponent_count]

    empty = BOARD_MASK ^ occupied
    player_threats = _winning_positions(player) & empty
    opponent_threats = _winning_positions(opponent) & empty

    score += 12 * player_threats.bit_count()
    score -= 12 * opponent_threats.bit_count()

    return score


def _ordered_columns(possible, tt_col, ply):
    result = []

    if 0 <= tt_col < COLS and possible & COLUMN_MASKS[tt_col]:
        result.append(tt_col)

    killer = _killers[ply] if ply < len(_killers) else -1
    if (
        0 <= killer < COLS
        and killer not in result
        and possible & COLUMN_MASKS[killer]
    ):
        result.append(killer)

    remaining = [
        c for c in CENTER_ORDER
        if c not in result and possible & COLUMN_MASKS[c]
    ]

    remaining.sort(
        key=lambda c: (_history[c], CENTER_VALUE[c]),
        reverse=True
    )
    result.extend(remaining)
    return result


def _negamax(player, opponent, depth, alpha, beta, ply, qleft):
    _check_time()

    occupied = player | opponent
    possible = _possible_moves(occupied)

    if possible == 0:
        return 0

    player_wins = _winning_positions(player) & possible
    if player_wins:
        return MATE - ply

    opponent_wins = _winning_positions(opponent) & possible
    opponent_win_count = opponent_wins.bit_count()

    if opponent_win_count >= 2:
        return -MATE + ply + 1

    forced_move = opponent_wins if opponent_win_count == 1 else 0

    key = _position_key(player, opponent)
    alpha_original = alpha
    beta_original = beta
    tt_col = -1

    entry = _tt.get(key)
    if entry is not None:
        stored_depth, stored_value, stored_flag, tt_col = entry

        if stored_depth >= depth:
            if stored_flag == EXACT:
                return stored_value
            if stored_flag == LOWER:
                alpha = max(alpha, stored_value)
            elif stored_flag == UPPER:
                beta = min(beta, stored_value)

            if alpha >= beta:
                return stored_value

    if depth <= 0 and not forced_move:
        value = _evaluate(player, opponent)
        _store_tt(key, 0, value, EXACT, -1)
        return value

    if depth <= 0 and forced_move and qleft <= 0:
        return _evaluate(player, opponent)

    if forced_move:
        columns = [_column_of(forced_move)]
    else:
        columns = _ordered_columns(possible, tt_col, ply)

    best_value = -INF
    best_col = columns[0]
    first = True

    for col in columns:
        move = possible & COLUMN_MASKS[col]
        next_qleft = qleft - 1 if depth <= 0 else qleft

        if first:
            value = -_negamax(
                opponent,
                player | move,
                depth - 1,
                -beta,
                -alpha,
                ply + 1,
                next_qleft
            )
            first = False
        else:
            value = -_negamax(
                opponent,
                player | move,
                depth - 1,
                -alpha - 1,
                -alpha,
                ply + 1,
                next_qleft
            )

            if alpha < value < beta:
                value = -_negamax(
                    opponent,
                    player | move,
                    depth - 1,
                    -beta,
                    -alpha,
                    ply + 1,
                    next_qleft
                )

        if value > best_value:
            best_value = value
            best_col = col

        if value > alpha:
            alpha = value

        if alpha >= beta:
            if ply < len(_killers):
                _killers[ply] = col
            bonus_depth = max(depth, 1)
            _history[col] += bonus_depth * bonus_depth
            break

    if best_value <= alpha_original:
        flag = UPPER
    elif best_value >= beta_original:
        flag = LOWER
    else:
        flag = EXACT

    if depth >= 0:
        _store_tt(key, depth, best_value, flag, best_col)

    return best_value


def _root_search(player, opponent, depth):
    global _root_preferred

    _check_time(force=True)

    occupied = player | opponent
    possible = _possible_moves(occupied)

    columns = []
    if possible & COLUMN_MASKS[_root_preferred]:
        columns.append(_root_preferred)

    for c in CENTER_ORDER:
        if c not in columns and possible & COLUMN_MASKS[c]:
            columns.append(c)

    alpha = -INF
    beta = INF
    best_value = -INF
    best_col = columns[0]
    first = True

    for col in columns:
        _check_time(force=True)
        move = possible & COLUMN_MASKS[col]

        if first:
            value = -_negamax(
                opponent,
                player | move,
                depth - 1,
                -beta,
                -alpha,
                1,
                6
            )
            first = False
        else:
            value = -_negamax(
                opponent,
                player | move,
                depth - 1,
                -alpha - 1,
                -alpha,
                1,
                6
            )

            if alpha < value < beta:
                value = -_negamax(
                    opponent,
                    player | move,
                    depth - 1,
                    -beta,
                    -alpha,
                    1,
                    6
                )

        if value > best_value:
            best_value = value
            best_col = col

        if value > alpha:
            alpha = value

    _root_preferred = best_col
    return best_value, best_col


def policy(board: list[list[int]]) -> int:
    global _deadline, _nodes, _tt, _killers, _history, _root_preferred

    legal = [
        c for c in CENTER_ORDER
        if any(board[r][c] == 0 for r in range(ROWS))
    ]

    # A full board has no legal action, but valid arena calls should never
    # request a move in that state.
    if not legal:
        return 0

    fallback = legal[0]

    try:
        player = 0
        opponent = 0
        occupied_count = 0

        for board_row in range(ROWS):
            bit_row = ROWS - 1 - board_row
            for col in range(COLS):
                value = board[board_row][col]
                if value == 1:
                    player |= 1 << (col * STRIDE + bit_row)
                    occupied_count += 1
                elif value == -1:
                    opponent |= 1 << (col * STRIDE + bit_row)
                    occupied_count += 1

        occupied = player | opponent
        possible = _possible_moves(occupied)

        if possible == 0:
            return fallback

        # The solved opening move for standard Connect Four is the center.
        if occupied_count == 0 and 3 in legal:
            return 3

        player_wins = _winning_positions(player) & possible
        if player_wins:
            for col in CENTER_ORDER:
                if player_wins & COLUMN_MASKS[col] and col in legal:
                    return col

        opponent_wins = _winning_positions(opponent) & possible
        if opponent_wins.bit_count() == 1:
            forced_col = _column_of(opponent_wins)
            if forced_col in legal:
                return forced_col

        _deadline = time.perf_counter() + 0.94
        _nodes = 0
        _tt = {}
        _killers = [-1] * 64
        _history = [0] * COLS
        _root_preferred = fallback

        best_col = fallback
        empty_count = 42 - occupied_count

        for depth in range(1, empty_count + 1):
            try:
                score, candidate = _root_search(
                    player,
                    opponent,
                    depth
                )
            except _SearchTimeout:
                break

            if candidate in legal:
                best_col = candidate

            if score >= MATE - 100:
                break

            if depth >= empty_count:
                break

        return int(best_col if best_col in legal else fallback)

    except Exception:
        return int(fallback)
