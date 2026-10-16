
import time

HEIGHT = 6
WIDTH = 7
STRIDE = HEIGHT + 1

BOARD_MASK = sum(((1 << HEIGHT) - 1) << (c * STRIDE) for c in range(WIDTH))
BOTTOM_MASK = sum(1 << (c * STRIDE) for c in range(WIDTH))
COLUMN_MASKS = [
    ((1 << HEIGHT) - 1) << (c * STRIDE) for c in range(WIDTH)
]

CENTER_ORDER = (3, 2, 4, 1, 5, 0, 6)
CENTER_RANK = (1, 3, 5, 7, 5, 3, 1)

MATE = 100000
INF = 200000

EXACT = 0
LOWER = 1
UPPER = 2

# key -> (depth, score, bound type, best move bit)
_TT = {}
_NODES = 0
_DEADLINE = 0.0


class _SearchTimeout(Exception):
    pass


def _make_lines():
    lines = []

    # Vertical
    for c in range(WIDTH):
        for r in range(HEIGHT - 3):
            line = 0
            for k in range(4):
                line |= 1 << (c * STRIDE + r + k)
            lines.append(line)

    # Horizontal
    for c in range(WIDTH - 3):
        for r in range(HEIGHT):
            line = 0
            for k in range(4):
                line |= 1 << ((c + k) * STRIDE + r)
            lines.append(line)

    # Rising diagonals
    for c in range(WIDTH - 3):
        for r in range(HEIGHT - 3):
            line = 0
            for k in range(4):
                line |= 1 << ((c + k) * STRIDE + r + k)
            lines.append(line)

    # Falling diagonals
    for c in range(WIDTH - 3):
        for r in range(3, HEIGHT):
            line = 0
            for k in range(4):
                line |= 1 << ((c + k) * STRIDE + r - k)
            lines.append(line)

    return tuple(lines)


WIN_LINES = _make_lines()


def _playable(mask):
    return (mask + BOTTOM_MASK) & BOARD_MASK


def _winning_positions(position, mask):
    """Empty cells which would complete four for position."""
    result = 0

    for direction in (1, STRIDE, STRIDE - 1, STRIDE + 1):
        result |= (
            (position << direction)
            & (position << (2 * direction))
            & (position << (3 * direction))
        )
        result |= (
            (position >> direction)
            & (position << direction)
            & (position << (2 * direction))
        )
        result |= (
            (position >> (2 * direction))
            & (position >> direction)
            & (position << direction)
        )
        result |= (
            (position >> (3 * direction))
            & (position >> (2 * direction))
            & (position >> direction)
        )

    return result & BOARD_MASK & ~mask


def _bit_to_col(move_bit):
    return (move_bit.bit_length() - 1) // STRIDE


def _tt_key(position, mask):
    return position | (mask << 49)


def _non_losing_moves(position, mask, possible):
    """
    Remove moves which allow an immediate opponent win.

    Returns (allowed_moves, forced_response), where forced_response is true
    when the opponent currently has a directly playable winning square.
    """
    opponent = mask ^ position
    opponent_wins = _winning_positions(opponent, mask)
    forced = possible & opponent_wins

    if forced:
        # Two directly playable wins cannot both be blocked.
        if forced & (forced - 1):
            return 0, True
        possible = forced

    # Do not play immediately below an opponent winning square.
    possible &= ~(opponent_wins >> 1)
    return possible, bool(forced)


def _evaluate(position, mask):
    opponent = mask ^ position
    score = 0
    weights = (0, 2, 12, 80, 5000)

    for line in WIN_LINES:
        own_count = (position & line).bit_count()
        opp_count = (opponent & line).bit_count()

        if opp_count == 0:
            score += weights[own_count]
        elif own_count == 0:
            score -= weights[opp_count]

    for col in range(WIDTH):
        column = COLUMN_MASKS[col]
        weight = CENTER_RANK[col]
        score += weight * (
            (position & column).bit_count()
            - (opponent & column).bit_count()
        )

    own_threats = _winning_positions(position, mask).bit_count()
    opp_threats = _winning_positions(opponent, mask).bit_count()
    score += 35 * (own_threats - opp_threats)

    if score > 9000:
        return 9000
    if score < -9000:
        return -9000
    return score


def _ordered_moves(moves, position, mask, tt_move=0):
    ordered = []

    while moves:
        move = moves & -moves
        moves ^= move

        col = _bit_to_col(move)
        new_mask = mask | move
        player_after_move = position | move
        threats = _winning_positions(player_after_move, new_mask)
        playable_after = _playable(new_mask)

        threat_count = threats.bit_count()
        playable_threats = (threats & playable_after).bit_count()

        priority = CENTER_RANK[col] * 10
        priority += threat_count * 25
        priority += playable_threats * 250

        if playable_threats >= 2:
            priority += 5000
        if move == tt_move:
            priority += 1000000

        ordered.append((priority, move))

    ordered.sort(reverse=True)
    return [move for _, move in ordered]


def _check_time():
    global _NODES
    _NODES += 1
    if (_NODES & 511) == 0 and time.perf_counter() >= _DEADLINE:
        raise _SearchTimeout


def _store_tt(key, depth, score, flag, best_move):
    old = _TT.get(key)
    if old is None or old[0] <= depth:
        _TT[key] = (depth, score, flag, best_move)


def _search(position, mask, depth, alpha, beta):
    _check_time()

    move_count = mask.bit_count()
    possible = _playable(mask)

    if possible == 0:
        return 0

    immediate_wins = _winning_positions(position, mask) & possible
    if immediate_wins:
        return MATE - (move_count + 1)

    allowed, forced = _non_losing_moves(position, mask, possible)

    if allowed == 0:
        # Whatever is played, the opponent wins on the next move.
        return -(MATE - (move_count + 2))

    if depth <= 0 and not forced:
        return _evaluate(position, mask)

    stored_depth = max(depth, 0)
    key = _tt_key(position, mask)
    alpha_original = alpha
    beta_original = beta
    tt_move = 0

    entry = _TT.get(key)
    if entry is not None:
        entry_depth, entry_score, entry_flag, tt_move = entry
        if entry_depth >= stored_depth:
            if entry_flag == EXACT:
                return entry_score
            if entry_flag == LOWER:
                alpha = max(alpha, entry_score)
            else:
                beta = min(beta, entry_score)
            if alpha >= beta:
                return entry_score

    moves = _ordered_moves(allowed, position, mask, tt_move)
    best_score = -INF
    best_move = moves[0]
    first = True

    next_depth = depth - 1 if depth > 0 else 0

    for move in moves:
        new_position = position ^ mask
        new_mask = mask | move

        if first:
            score = -_search(
                new_position, new_mask, next_depth, -beta, -alpha
            )
            first = False
        else:
            # Principal variation search.
            score = -_search(
                new_position, new_mask, next_depth, -alpha - 1, -alpha
            )
            if alpha < score < beta:
                score = -_search(
                    new_position, new_mask, next_depth, -beta, -alpha
                )

        if score > best_score:
            best_score = score
            best_move = move

        if score > alpha:
            alpha = score

        if alpha >= beta:
            break

    if best_score <= alpha_original:
        flag = UPPER
    elif best_score >= beta_original:
        flag = LOWER
    else:
        flag = EXACT

    _store_tt(key, stored_depth, best_score, flag, best_move)
    return best_score


def _search_root(position, mask, depth):
    possible = _playable(mask)
    allowed, _ = _non_losing_moves(position, mask, possible)

    # If all moves lose immediately, still examine and return a legal move.
    if allowed == 0:
        allowed = possible

    key = _tt_key(position, mask)
    entry = _TT.get(key)
    tt_move = entry[3] if entry is not None else 0

    moves = _ordered_moves(allowed, position, mask, tt_move)
    best_move = moves[0]
    best_score = -INF
    alpha = -INF

    for move in moves:
        if time.perf_counter() >= _DEADLINE:
            raise _SearchTimeout

        new_position = position ^ mask
        new_mask = mask | move

        score = -_search(
            new_position,
            new_mask,
            depth - 1,
            -INF,
            -alpha,
        )

        if score > best_score:
            best_score = score
            best_move = move

        if score > alpha:
            alpha = score

    _store_tt(key, depth, best_score, EXACT, best_move)
    return best_score, best_move


def policy(board: list[list[int]]) -> int:
    global _NODES, _DEADLINE

    position = 0
    mask = 0

    for board_row in range(HEIGHT):
        bit_row = HEIGHT - 1 - board_row
        for col in range(WIDTH):
            value = board[board_row][col]
            if value:
                bit = 1 << (col * STRIDE + bit_row)
                mask |= bit
                if value == 1:
                    position |= bit

    possible = _playable(mask)

    # A full board should not normally be passed to the policy.
    if possible == 0:
        return 0

    # Establish a legal fallback before doing any search.
    fallback = 0
    for col in CENTER_ORDER:
        move = possible & COLUMN_MASKS[col]
        if move:
            fallback = col
            break

    move_count = mask.bit_count()

    # The optimal and strategically strongest opening move.
    if move_count == 0:
        return 3

    # Always take an immediate win.
    wins = _winning_positions(position, mask) & possible
    if wins:
        for col in CENTER_ORDER:
            move = wins & COLUMN_MASKS[col]
            if move:
                return col

    # A single immediate opponent win must be blocked.
    opponent = mask ^ position
    opponent_wins = _winning_positions(opponent, mask) & possible
    if opponent_wins and not (opponent_wins & (opponent_wins - 1)):
        return _bit_to_col(opponent_wins)

    if len(_TT) > 500000:
        _TT.clear()

    _NODES = 0
    _DEADLINE = time.perf_counter() + 0.92

    best_col = fallback
    remaining = 42 - move_count

    try:
        for depth in range(1, remaining + 1):
            score, best_move = _search_root(position, mask, depth)
            best_col = _bit_to_col(best_move)

            # Mate-valued results are tactically proven.
            if abs(score) > MATE - 50:
                break

            if time.perf_counter() >= _DEADLINE:
                break
    except _SearchTimeout:
        pass

    # Defensive validation guarantees a legal return on every non-full board.
    if 0 <= best_col < WIDTH and (possible & COLUMN_MASKS[best_col]):
        return best_col

    return fallback
