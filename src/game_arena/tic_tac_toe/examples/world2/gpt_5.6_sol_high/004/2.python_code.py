
import time

_ALL = (1 << 16) - 1
_INF = 1_000_000
_WIN = 100_000

# Four rows, four columns, and two diagonals.
_WIN_MASKS = tuple(
    [0xF << (4 * r) for r in range(4)]
    + [sum(1 << (4 * r + c) for r in range(4)) for c in range(4)]
    + [0x8421, 0x1248]
)

_CELL_LINES = tuple(
    tuple(mask for mask in _WIN_MASKS if mask & (1 << cell))
    for cell in range(16)
)

# TT entry: depth, value, flag, preferred move bit.
# flag: 0 exact, 1 lower bound, 2 upper bound.
_TT = {}
_deadline = 0.0
_nodes = 0


class _SearchTimeout(Exception):
    pass


def _check_time():
    global _nodes
    _nodes += 1
    if (_nodes & 511) == 0 and time.perf_counter() >= _deadline:
        raise _SearchTimeout


def _has_win(bits):
    for mask in _WIN_MASKS:
        if bits & mask == mask:
            return True
    return False


def _winning_cells(player, empty):
    """Empty cells on which player wins immediately."""
    wins = 0
    for mask in _WIN_MASKS:
        if (player & mask).bit_count() == 3:
            wins |= mask & empty
    return wins


def _forking_cells(player, opponent, empty):
    """Moves that create at least two distinct immediate winning moves."""
    result = 0
    candidates = empty
    while candidates:
        bit = candidates & -candidates
        candidates ^= bit
        remaining = empty ^ bit
        if _winning_cells(player | bit, remaining).bit_count() >= 2:
            result |= bit
    return result


def _evaluate(player, opponent, empty):
    # Symmetric static evaluation, suitable for negamax.
    weights = (0, 4, 28, 420, _WIN)
    score = 0

    for mask in _WIN_MASKS:
        p_count = (player & mask).bit_count()
        o_count = (opponent & mask).bit_count()

        if o_count == 0:
            score += weights[p_count]
        if p_count == 0:
            score -= weights[o_count]

    # Reward intersecting two-in-a-row structures, which are fork precursors.
    cells = empty
    while cells:
        bit = cells & -cells
        cells ^= bit
        idx = bit.bit_length() - 1
        p_builders = 0
        o_builders = 0

        for mask in _CELL_LINES[idx]:
            if not (opponent & mask) and (player & mask).bit_count() == 2:
                p_builders += 1
            if not (player & mask) and (opponent & mask).bit_count() == 2:
                o_builders += 1

        score += 10 * (p_builders * p_builders - o_builders * o_builders)

    return score


def _order_moves(player, opponent, candidates, empty, preferred=0,
                 opponent_forks=0):
    ranked = []
    bits = candidates

    while bits:
        bit = bits & -bits
        bits ^= bit
        idx = bit.bit_length() - 1
        score = 0

        if bit == preferred:
            score += 1_000_000
        if bit & opponent_forks:
            score += 1_200

        for mask in _CELL_LINES[idx]:
            if not (opponent & mask):
                count = (player & mask).bit_count()
                score += (0, 8, 70, 5000)[count]
            if not (player & mask):
                count = (opponent & mask).bit_count()
                score += (0, 7, 60, 4500)[count]

        remaining = empty ^ bit
        threats = _winning_cells(player | bit, remaining).bit_count()
        if threats == 1:
            score += 600
        elif threats >= 2:
            score += 12_000

        # Deterministic tie breaking.
        ranked.append((score, -idx, bit))

    ranked.sort(reverse=True)
    return [item[2] for item in ranked]


def _search(player, opponent, empty, depth, alpha, beta):
    _check_time()

    if _has_win(opponent):
        return -_WIN
    if empty == 0:
        return 0

    requested_depth = max(depth, 0)
    key = player | (opponent << 16)
    entry = _TT.get(key)
    preferred = 0

    original_alpha = alpha
    original_beta = beta

    if entry is not None:
        stored_depth, stored_value, flag, preferred = entry
        if stored_depth >= requested_depth:
            if flag == 0:
                return stored_value
            if flag == 1:
                alpha = max(alpha, stored_value)
            else:
                beta = min(beta, stored_value)
            if alpha >= beta:
                return stored_value

    # A direct win is exact regardless of nominal search depth.
    own_wins = _winning_cells(player, empty)
    if own_wins:
        return _WIN

    enemy_wins = _winning_cells(opponent, empty)
    enemy_win_count = enemy_wins.bit_count()

    # Two distinct immediate threats cannot both be blocked.
    if enemy_win_count >= 2:
        return -_WIN

    if enemy_win_count == 0:
        # With no immediate enemy win, a double threat is a forced win.
        forks = _forking_cells(player, opponent, empty)
        if forks:
            return _WIN

    # Continue through forced tactical sequences even at the horizon.
    if depth <= 0 and enemy_win_count == 0:
        return _evaluate(player, opponent, empty)

    candidates = enemy_wins if enemy_win_count == 1 else empty
    moves = _order_moves(player, opponent, candidates, empty, preferred)

    best_value = -_INF
    best_move = moves[0]
    first = True

    for bit in moves:
        new_empty = empty ^ bit

        if first:
            value = -_search(
                opponent, player | bit, new_empty, depth - 1,
                -beta, -alpha
            )
            first = False
        else:
            # Principal-variation search: first try a narrow window.
            value = -_search(
                opponent, player | bit, new_empty, depth - 1,
                -alpha - 1, -alpha
            )
            if alpha < value < beta:
                value = -_search(
                    opponent, player | bit, new_empty, depth - 1,
                    -beta, -alpha
                )

        if value > best_value:
            best_value = value
            best_move = bit

        if value > alpha:
            alpha = value
        if alpha >= beta or best_value == _WIN:
            break

    if best_value <= original_alpha:
        flag = 2
    elif best_value >= original_beta:
        flag = 1
    else:
        flag = 0

    old = _TT.get(key)
    if old is None or requested_depth >= old[0]:
        _TT[key] = (requested_depth, best_value, flag, best_move)

    return best_value


def _root_search(player, opponent, empty, depth, preferred, opponent_forks):
    moves = _order_moves(
        player, opponent, empty, empty, preferred, opponent_forks
    )

    alpha = -_INF
    best_value = -_INF
    best_move = moves[0]
    first = True

    for bit in moves:
        if time.perf_counter() >= _deadline:
            raise _SearchTimeout

        new_empty = empty ^ bit

        if first:
            value = -_search(
                opponent, player | bit, new_empty, depth - 1,
                -_INF, _INF
            )
            first = False
        else:
            value = -_search(
                opponent, player | bit, new_empty, depth - 1,
                -alpha - 1, -alpha
            )
            if value > alpha:
                value = -_search(
                    opponent, player | bit, new_empty, depth - 1,
                    -_INF, -alpha
                )

        if value > best_value:
            best_value = value
            best_move = bit

        if value > alpha:
            alpha = value
        if best_value == _WIN:
            break

    return best_value, best_move


def _bit_to_move(bit):
    index = bit.bit_length() - 1
    return index // 4, index % 4


def policy(board: list[list[int]]) -> tuple[int, int]:
    global _deadline, _nodes

    player = 0
    opponent = 0

    for row in range(4):
        for col in range(4):
            value = board[row][col]
            bit = 1 << (4 * row + col)
            if value == 1:
                player |= bit
            elif value == -1:
                opponent |= bit

    empty = _ALL ^ (player | opponent)

    # Valid game states supplied to a policy always have a legal move.
    if empty == 0:
        return 0, 0

    fallback = empty & -empty

    # Strong symmetric opening without spending search time.
    if empty == _ALL:
        return 1, 1

    # Immediate win has priority over every defensive action.
    wins = _winning_cells(player, empty)
    if wins:
        choices = _order_moves(player, opponent, wins, empty)
        return _bit_to_move(choices[0])

    # An immediate enemy win must be blocked. If there are several, the
    # position is lost against perfect play, but choose the best legal block.
    enemy_wins = _winning_cells(opponent, empty)
    if enemy_wins:
        choices = _order_moves(player, opponent, enemy_wins, empty)
        return _bit_to_move(choices[0])

    # A fork wins by producing two different immediate threats.
    forks = _forking_cells(player, opponent, empty)
    if forks:
        choices = _order_moves(player, opponent, forks, empty)
        return _bit_to_move(choices[0])

    # Keep memory bounded across repeated arena calls.
    if len(_TT) > 400_000:
        _TT.clear()

    _nodes = 0
    _deadline = time.perf_counter() + 0.90

    best_move = fallback
    opponent_forks = _forking_cells(opponent, player, empty)
    remaining = empty.bit_count()

    # A cached move from an earlier related position is useful for ordering.
    root_entry = _TT.get(player | (opponent << 16))
    if root_entry is not None and (root_entry[3] & empty):
        best_move = root_entry[3]

    for depth in range(1, remaining + 1):
        try:
            value, move = _root_search(
                player, opponent, empty, depth,
                best_move, opponent_forks
            )
        except _SearchTimeout:
            break

        if move & empty:
            best_move = move

        # These are proven outcomes, not heuristic values.
        if abs(value) == _WIN or depth == remaining:
            break

    # Defensive legality check; best_move is normally already legal.
    if not (best_move & empty):
        best_move = fallback

    return _bit_to_move(best_move)
