
from itertools import product
from time import perf_counter


# Bitboard layout:
# bit (i * 9 + j * 3 + k) represents board[i][j][k].
FULL_MASK = (1 << 27) - 1
CENTER_INDEX = 13
CENTER_BIT = 1 << CENTER_INDEX

WIN_SCORE = 100000
INF = 1000000

# Transposition-table flags.
EXACT = 0
LOWER = 1
UPPER = -1


def _build_lines():
    """Construct all 49 straight winning lines in a 3x3x3 cube."""
    result = set()

    for x, y, z in product(range(3), repeat=3):
        for dx, dy, dz in product((-1, 0, 1), repeat=3):
            if dx == 0 and dy == 0 and dz == 0:
                continue

            ax, ay, az = x - dx, y - dy, z - dz
            cx, cy, cz = x + dx, y + dy, z + dz

            if not (
                0 <= ax < 3 and 0 <= ay < 3 and 0 <= az < 3
                and 0 <= cx < 3 and 0 <= cy < 3 and 0 <= cz < 3
            ):
                continue

            a = ax * 9 + ay * 3 + az
            b = x * 9 + y * 3 + z
            c = cx * 9 + cy * 3 + cz
            result.add(tuple(sorted((a, b, c))))

    return tuple(sum(1 << p for p in line) for line in sorted(result))


LINES = _build_lines()

CELL_LINES = [[] for _ in range(27)]
for line_mask in LINES:
    bits = line_mask
    while bits:
        bit = bits & -bits
        bits -= bit
        CELL_LINES[bit.bit_length() - 1].append(line_mask)

CELL_VALUE = tuple(len(CELL_LINES[index]) for index in range(27))


# Per-call search state.
_deadline = 0.0
_nodes = 0
_tt = {}
_history = [0] * 27


class _SearchTimeout(Exception):
    pass


def _winning_moves(own, opponent):
    """Return a bit mask of cells that immediately complete an own line."""
    result = 0
    for line in LINES:
        if opponent & line:
            continue
        occupied = own & line
        if occupied.bit_count() == 2:
            result |= line & ~(own | opponent)
    return result


def _created_threat_count(own, opponent, move):
    """
    Count distinct open lines that become immediate threats after move.

    Distinct lines through an empty cell have distinct remaining target cells,
    so two such lines constitute a genuine fork.
    """
    index = move.bit_length() - 1
    count = 0

    for line in CELL_LINES[index]:
        if opponent & line:
            continue
        if (own & line).bit_count() == 1:
            count += 1

    return count


def _evaluate(own, opponent):
    """Static evaluation from the perspective of the side to move."""
    occupied = own | opponent
    empty = FULL_MASK ^ occupied

    own_setups = [0] * 27
    opp_setups = [0] * 27
    score = 0

    line_weight = (0, 5, 70, 10000)

    for line in LINES:
        own_count = (own & line).bit_count()
        opp_count = (opponent & line).bit_count()

        if opp_count == 0:
            score += line_weight[own_count]

            if own_count == 1:
                cells = line & empty
                while cells:
                    bit = cells & -cells
                    cells -= bit
                    own_setups[bit.bit_length() - 1] += 1

        if own_count == 0:
            score -= line_weight[opp_count]

            if opp_count == 1:
                cells = line & empty
                while cells:
                    bit = cells & -cells
                    cells -= bit
                    opp_setups[bit.bit_length() - 1] += 1

    own_fork_power = 0
    opp_fork_power = 0
    own_best = 0
    opp_best = 0

    cells = empty
    while cells:
        bit = cells & -cells
        cells -= bit
        index = bit.bit_length() - 1

        own_count = own_setups[index]
        opp_count = opp_setups[index]

        own_best = max(own_best, own_count)
        opp_best = max(opp_best, opp_count)

        if own_count >= 2:
            own_fork_power += own_count * (own_count - 1)
        if opp_count >= 2:
            opp_fork_power += opp_count * (opp_count - 1)

    score += 110 * (own_fork_power - opp_fork_power)
    score += 30 * (own_best - opp_best)

    # A fork available to the side to move is especially valuable.
    if own_best >= 2:
        score += 2200 + 100 * own_best
    if opp_best >= 2:
        score -= 1800 + 100 * opp_best

    return score


def _move_order_score(own, opponent, move, tt_move):
    index = move.bit_length() - 1
    score = _history[index] + 15 * CELL_VALUE[index]

    if move == tt_move:
        score += 1000000

    own_threats = 0

    for line in CELL_LINES[index]:
        if not (opponent & line):
            count = (own & line).bit_count()
            if count == 1:
                own_threats += 1
                score += 350
            elif count == 0:
                score += 12

        if not (own & line):
            count = (opponent & line).bit_count()
            if count == 1:
                score += 55
            elif count == 2:
                score += 5000

    if own_threats >= 2:
        score += 30000 + 2000 * own_threats

    return score


def _ordered_moves(own, opponent, allowed=0, tt_move=0):
    empty = FULL_MASK ^ (own | opponent)
    if allowed:
        empty &= allowed

    moves = []
    while empty:
        move = empty & -empty
        empty -= move
        moves.append(move)

    moves.sort(
        key=lambda move: _move_order_score(
            own, opponent, move, tt_move
        ),
        reverse=True,
    )
    return moves


def _check_time():
    global _nodes
    _nodes += 1
    if (_nodes & 255) == 0 and perf_counter() >= _deadline:
        raise _SearchTimeout


def _search(own, opponent, depth, alpha, beta, ply, qleft):
    """Negamax search from the perspective of the side represented by own."""
    _check_time()

    empty = FULL_MASK ^ (own | opponent)
    if not empty:
        return 0

    # Winning immediately is always best.
    wins = _winning_moves(own, opponent)
    if wins:
        return WIN_SCORE - ply

    # Count the opponent's immediate winning cells.
    opponent_wins = _winning_moves(opponent, own)
    threat_count = opponent_wins.bit_count()

    # Two distinct winning cells cannot both be blocked.
    if threat_count >= 2:
        return -WIN_SCORE + ply + 1

    forced_move = opponent_wins if threat_count == 1 else 0

    # At the nominal horizon, continue mandatory tactical responses.
    if depth <= 0:
        if forced_move and qleft > 0:
            return -_search(
                opponent,
                own | forced_move,
                0,
                -beta,
                -alpha,
                ply + 1,
                qleft - 1,
            )
        return _evaluate(own, opponent)

    key = own | (opponent << 27)
    alpha_start = alpha
    beta_start = beta
    tt_move = 0

    entry = _tt.get(key)
    if entry is not None:
        stored_depth, stored_value, flag, tt_move = entry
        if stored_depth >= depth:
            if flag == EXACT:
                return stored_value
            if flag == LOWER:
                alpha = max(alpha, stored_value)
            else:
                beta = min(beta, stored_value)
            if alpha >= beta:
                return stored_value

    allowed = forced_move if forced_move else 0
    moves = _ordered_moves(own, opponent, allowed, tt_move)

    best_value = -INF
    best_move = 0

    for move in moves:
        value = -_search(
            opponent,
            own | move,
            depth - 1,
            -beta,
            -alpha,
            ply + 1,
            qleft,
        )

        if value > best_value:
            best_value = value
            best_move = move

        if value > alpha:
            alpha = value

        if alpha >= beta:
            index = move.bit_length() - 1
            _history[index] += depth * depth
            break

    if best_value <= alpha_start:
        flag = UPPER
    elif best_value >= beta_start:
        flag = LOWER
    else:
        flag = EXACT

    if len(_tt) < 300000:
        _tt[key] = (depth, best_value, flag, best_move)

    return best_value


def _root_search(own, opponent, depth):
    """Search one fully completed iterative-deepening root."""
    entry = _tt.get(own | (opponent << 27))
    tt_move = entry[3] if entry is not None else 0
    moves = _ordered_moves(own, opponent, 0, tt_move)

    alpha = -INF
    beta = INF
    best_value = -INF
    best_move = moves[0]

    for move in moves:
        value = -_search(
            opponent,
            own | move,
            depth - 1,
            -beta,
            -alpha,
            1,
            4,
        )

        if value > best_value:
            best_value = value
            best_move = move

        if value > alpha:
            alpha = value

    return best_value, best_move


def _to_tuple(move):
    index = move.bit_length() - 1
    return index // 9, (index % 9) // 3, index % 3


def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    global _deadline, _nodes, _tt, _history

    own = 0
    opponent = 0

    for i in range(3):
        for j in range(3):
            for k in range(3):
                value = board[i][j][k]
                bit = 1 << (i * 9 + j * 3 + k)
                if value == 1:
                    own |= bit
                elif value == -1:
                    opponent |= bit

    empty = FULL_MASK ^ (own | opponent)

    # Legal game states presented to a policy always have an empty cell.
    # This fallback also ensures a tuple is returned for malformed full boards.
    if not empty:
        return (0, 0, 0)

    fallback = empty & -empty

    # Strong and symmetry-preserving opening.
    stone_count = (own | opponent).bit_count()
    if stone_count == 0:
        return (1, 1, 1)

    if stone_count == 1:
        if empty & CENTER_BIT:
            return (1, 1, 1)

        # If the opponent owns the center, take a corner.
        corners = (
            0, 2, 6, 8,
            18, 20, 24, 26,
        )
        for index in corners:
            move = 1 << index
            if empty & move:
                return _to_tuple(move)

    # Never overlook an immediate win.
    wins = _winning_moves(own, opponent)
    if wins:
        return _to_tuple(wins & -wins)

    # An immediate opposing win must be blocked. If there are several,
    # the position is already lost, but a legal move is still returned.
    opponent_wins = _winning_moves(opponent, own)
    if opponent_wins.bit_count() == 1:
        return _to_tuple(opponent_wins)

    _tt = {}
    _history = [0] * 27
    _nodes = 0
    _deadline = perf_counter() + 0.88

    ordered = _ordered_moves(own, opponent)
    if ordered:
        fallback = ordered[0]

    # A move creating two simultaneous winning cells is a forced win.
    if not opponent_wins:
        fork_moves = []
        cells = empty
        while cells:
            move = cells & -cells
            cells -= move
            count = _created_threat_count(own, opponent, move)
            if count >= 2:
                fork_moves.append((count, CELL_VALUE[move.bit_length() - 1], move))

        if fork_moves:
            fork_moves.sort(reverse=True)
            return _to_tuple(fork_moves[0][2])

    best_move = fallback
    remaining = empty.bit_count()

    # Iterative deepening guarantees that only completed search depths replace
    # the current answer.
    try:
        for depth in range(1, remaining + 1):
            value, move = _root_search(own, opponent, depth)
            best_move = move

            # A proven forced result does not need deeper investigation.
            if abs(value) >= WIN_SCORE - 40:
                break

            if perf_counter() >= _deadline:
                break

    except _SearchTimeout:
        pass

    # Defensive validation preserves legality even if search state is damaged.
    if not (best_move & empty):
        best_move = empty & -empty

    return _to_tuple(best_move)
