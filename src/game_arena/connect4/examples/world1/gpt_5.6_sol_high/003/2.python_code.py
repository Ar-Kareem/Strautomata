
import time

# Bitboard layout:
# Each column occupies seven bits: six playable cells plus one sentinel bit.
# The least significant bit of a column is its bottom cell.

HEIGHT = 6
WIDTH = 7
STRIDE = 7

BOTTOM = tuple(1 << (c * STRIDE) for c in range(WIDTH))
COLUMN_MASK = tuple(((1 << HEIGHT) - 1) << (c * STRIDE)
                    for c in range(WIDTH))
BOTTOM_ALL = sum(BOTTOM)
BOARD_MASK = sum(COLUMN_MASK)

CENTER_ORDER = (3, 2, 4, 1, 5, 0, 6)
COLUMN_VALUE = (0, 2, 4, 7, 4, 2, 0)
ORDER_BONUS = (1, 5, 6, 7, 4, 3, 2)

WIN_SCORE = 1_000_000
INF = 2_000_000

# Generate all 69 possible four-cell lines.
_lines = []

# Horizontal
for r in range(HEIGHT):
    for c in range(WIDTH - 3):
        m = 0
        for i in range(4):
            m |= 1 << ((c + i) * STRIDE + r)
        _lines.append(m)

# Vertical
for c in range(WIDTH):
    for r in range(HEIGHT - 3):
        m = 0
        for i in range(4):
            m |= 1 << (c * STRIDE + r + i)
        _lines.append(m)

# Rising diagonal
for c in range(WIDTH - 3):
    for r in range(HEIGHT - 3):
        m = 0
        for i in range(4):
            m |= 1 << ((c + i) * STRIDE + r + i)
        _lines.append(m)

# Falling diagonal
for c in range(WIDTH - 3):
    for r in range(3, HEIGHT):
        m = 0
        for i in range(4):
            m |= 1 << ((c + i) * STRIDE + r - i)
        _lines.append(m)

LINES = tuple(_lines)
CENTER_MASK = COLUMN_MASK[3]

_deadline = 0.0
_nodes = 0
_tt = {}


class _SearchTimeout(Exception):
    pass


def _possible(mask):
    """Return a bitboard containing the legal drop cell in every open column."""
    return (mask + BOTTOM_ALL) & BOARD_MASK


def _winning_positions(position, mask):
    """Return empty cells which would complete four for position."""
    result = (
        (position << 1)
        & (position << 2)
        & (position << 3)
    )

    for shift in (6, 7, 8):
        pair = (position << shift) & (position << (2 * shift))
        result |= pair & (position << (3 * shift))
        result |= pair & (position >> shift)

        pair = (position >> shift) & (position >> (2 * shift))
        result |= pair & (position << shift)
        result |= pair & (position >> (3 * shift))

    return result & BOARD_MASK & ~mask


def _immediate_wins(position, mask):
    """Return currently playable winning cells."""
    return _winning_positions(position, mask) & _possible(mask)


def _evaluate(player, opponent):
    """Static evaluation from player's perspective."""
    score = 0
    values = (0, 2, 12, 85, 20000)

    for line in LINES:
        own = (player & line).bit_count()
        enemy = (opponent & line).bit_count()

        if enemy == 0:
            score += values[own]
        elif own == 0:
            score -= values[enemy]

    # Extra preference for center-column occupation.
    score += 7 * (
        (player & CENTER_MASK).bit_count()
        - (opponent & CENTER_MASK).bit_count()
    )

    return score


def _column_of(bit):
    return (bit.bit_length() - 1) // STRIDE


def _ordered_moves(player, opponent, mask, tt_move=0):
    """
    Generate and order legal moves.

    If at least one move avoids giving the opponent an immediate win,
    immediately losing moves are discarded.
    """
    possible = _possible(mask)
    safe = []
    unsafe = []

    for c in CENTER_ORDER:
        bit = possible & COLUMN_MASK[c]
        if not bit:
            continue

        new_mask = mask | bit
        new_player = player | bit

        opponent_replies = _immediate_wins(opponent, new_mask).bit_count()
        future_wins = _immediate_wins(new_player, new_mask).bit_count()

        score = COLUMN_VALUE[c] * 10 + ORDER_BONUS[c]

        # Moves making one threat are useful; moves making two are forks.
        score += future_wins * 500
        if future_wins >= 2:
            score += 5000

        if bit == tt_move:
            score += 100000

        item = (score, bit)

        if opponent_replies:
            # If every move loses immediately, prefer the move that gives
            # the opponent the fewest winning replies.
            item = (score - 10000 - 1000 * opponent_replies, bit)
            unsafe.append(item)
        else:
            safe.append(item)

    moves = safe if safe else unsafe
    moves.sort(reverse=True)
    return [bit for _, bit in moves]


def _negamax(player, opponent, mask, depth, alpha, beta, ply):
    global _nodes

    _nodes += 1
    if (_nodes & 255) == 0 and time.perf_counter() >= _deadline:
        raise _SearchTimeout

    possible = _possible(mask)
    if not possible:
        return 0

    # A direct win is always best.
    own_wins = _immediate_wins(player, mask)
    if own_wins:
        return WIN_SCORE - ply - 1

    # Two distinct opponent winning cells cannot both be blocked.
    opponent_wins = _immediate_wins(opponent, mask)
    opponent_win_count = opponent_wins.bit_count()
    if opponent_win_count >= 2:
        return -WIN_SCORE + ply + 2

    key = player | (opponent << 49)
    original_alpha = alpha
    tt_move = 0

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

    # Extend forced blocks even at the nominal horizon.
    if opponent_win_count == 1:
        moves = [opponent_wins]
    elif depth <= 0:
        value = _evaluate(player, opponent)
        if len(_tt) < 450000:
            _tt[key] = (0, value, 0, 0)
        return value
    else:
        moves = _ordered_moves(player, opponent, mask, tt_move)

    if not moves:
        return 0

    best_value = -INF
    best_move = moves[0]

    for bit in moves:
        new_mask = mask | bit

        if depth > 0:
            next_depth = depth - 1
        else:
            # This occurs only during a forced tactical extension.
            next_depth = 0

        value = -_negamax(
            opponent,
            player | bit,
            new_mask,
            next_depth,
            -beta,
            -alpha,
            ply + 1,
        )

        if value > best_value:
            best_value = value
            best_move = bit

        if value > alpha:
            alpha = value

        if alpha >= beta:
            break

    if best_value <= original_alpha:
        flag = 2  # Upper bound
    elif best_value >= beta:
        flag = 1  # Lower bound
    else:
        flag = 0  # Exact

    if len(_tt) < 450000:
        _tt[key] = (depth, best_value, flag, best_move)

    return best_value


def _root_search(player, opponent, mask, depth, preferred_move):
    moves = _ordered_moves(player, opponent, mask, preferred_move)
    if not moves:
        return 0, 0

    best_value = -INF
    best_move = moves[0]
    alpha = -INF
    beta = INF

    for bit in moves:
        if time.perf_counter() >= _deadline:
            raise _SearchTimeout

        value = -_negamax(
            opponent,
            player | bit,
            mask | bit,
            depth - 1,
            -beta,
            -alpha,
            1,
        )

        if value > best_value:
            best_value = value
            best_move = bit

        if value > alpha:
            alpha = value

    return best_value, best_move


def policy(board: list[list[int]]) -> int:
    """
    Return a legal column index for the current player.
    """
    global _deadline, _nodes, _tt

    # Establish a guaranteed legal fallback before doing any search.
    legal_columns = [
        c for c in CENTER_ORDER
        if any(board[r][c] == 0 for r in range(HEIGHT))
    ]

    # A full board has no legal action; normal game engines never call policy
    # in this state.
    if not legal_columns:
        return 0

    fallback_column = legal_columns[0]

    try:
        player = 0
        opponent = 0

        for r in range(HEIGHT):
            bit_row = HEIGHT - 1 - r
            for c in range(WIDTH):
                bit = 1 << (c * STRIDE + bit_row)
                if board[r][c] == 1:
                    player |= bit
                elif board[r][c] == -1:
                    opponent |= bit

        mask = player | opponent
        possible = _possible(mask)

        # On valid gravity-respecting boards, this always agrees with the
        # legal-column fallback above.
        if not possible:
            return fallback_column

        # Win immediately whenever possible.
        wins = _immediate_wins(player, mask)
        if wins:
            for c in CENTER_ORDER:
                if wins & COLUMN_MASK[c]:
                    return c

        # Mandatory immediate blocks.
        opponent_wins = _immediate_wins(opponent, mask)
        threat_count = opponent_wins.bit_count()

        if threat_count == 1:
            c = _column_of(opponent_wins)
            if c in legal_columns:
                return c
            return fallback_column

        if threat_count >= 2:
            # The position is theoretically lost, but blocking one threat
            # still gives an imperfect opponent the greatest chance to err.
            best_column = fallback_column
            best_score = -INF

            for c in CENTER_ORDER:
                bit = opponent_wins & COLUMN_MASK[c]
                if bit:
                    value = _evaluate(player | bit, opponent)
                    value += COLUMN_VALUE[c]
                    if value > best_score:
                        best_score = value
                        best_column = c

            return best_column

        _tt = {}
        _nodes = 0
        _deadline = time.perf_counter() + 0.90

        initial_moves = _ordered_moves(player, opponent, mask)
        if not initial_moves:
            return fallback_column

        best_bit = initial_moves[0]
        best_column = _column_of(best_bit)

        if best_column not in legal_columns:
            best_column = fallback_column

        # If there is only one non-losing move, no search is required.
        if len(initial_moves) == 1:
            return best_column

        remaining = 42 - mask.bit_count()

        # Iterative deepening always leaves the last fully completed result
        # available if the time limit is reached.
        for depth in range(1, remaining + 1):
            try:
                score, move = _root_search(
                    player, opponent, mask, depth, best_bit
                )
            except _SearchTimeout:
                break

            if move:
                candidate = _column_of(move)
                if candidate in legal_columns:
                    best_bit = move
                    best_column = candidate

            # A mate score found by a complete iteration is conclusive.
            if abs(score) >= WIN_SCORE - 100:
                break

        return best_column

    except Exception:
        # Preserve legality even if an unexpected malformed position is given.
        return fallback_column
