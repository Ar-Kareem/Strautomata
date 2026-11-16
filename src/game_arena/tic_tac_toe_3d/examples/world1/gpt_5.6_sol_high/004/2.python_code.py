
import time

# ---------------------------------------------------------------------------
# Board geometry
# ---------------------------------------------------------------------------

FULL = (1 << 27) - 1
WIN_SCORE = 100000
INF = 10 ** 9

LINES = []
CELL_LINES = [[] for _ in range(27)]


def _index(i, j, k):
    return i * 9 + j * 3 + k


# One representative from each pair of opposite directions.
_directions = []
for di in (-1, 0, 1):
    for dj in (-1, 0, 1):
        for dk in (-1, 0, 1):
            if di == dj == dk == 0:
                continue
            direction = (di, dj, dk)
            for component in direction:
                if component:
                    if component == 1:
                        _directions.append(direction)
                    break

for di, dj, dk in _directions:
    starts_i = (0,) if di == 1 else ((2,) if di == -1 else (0, 1, 2))
    starts_j = (0,) if dj == 1 else ((2,) if dj == -1 else (0, 1, 2))
    starts_k = (0,) if dk == 1 else ((2,) if dk == -1 else (0, 1, 2))

    for i in starts_i:
        for j in starts_j:
            for k in starts_k:
                cells = (
                    _index(i, j, k),
                    _index(i + di, j + dj, k + dk),
                    _index(i + 2 * di, j + 2 * dj, k + 2 * dk),
                )
                mask = 0
                for cell in cells:
                    mask |= 1 << cell
                LINES.append(mask)

LINES = tuple(LINES)

for line in LINES:
    bits = line
    while bits:
        bit = bits & -bits
        CELL_LINES[bit.bit_length() - 1].append(line)
        bits ^= bit

CELL_LINES = tuple(tuple(x) for x in CELL_LINES)

# Search globals, reset for every policy call.
DEADLINE = 0.0
NODES = 0
TT = {}


class _SearchTimeout(Exception):
    pass


def _to_move(bit):
    idx = bit.bit_length() - 1
    return idx // 9, (idx // 3) % 3, idx % 3


def _winning_cells(me, opponent, empty):
    """Return all empty cells that immediately complete one of me's lines."""
    result = 0
    for line in LINES:
        if not (line & opponent) and (line & me).bit_count() == 2:
            result |= line & empty
    return result


def _find_fork(me, opponent, empty):
    """
    Return a move that creates at least two distinct immediate winning
    threats, or zero if no such move exists.
    """
    counts = [0] * 27

    for line in LINES:
        if line & opponent:
            continue
        if (line & me).bit_count() != 1:
            continue

        possible_moves = line & empty
        while possible_moves:
            bit = possible_moves & -possible_moves
            idx = bit.bit_length() - 1
            counts[idx] += 1
            if counts[idx] >= 2:
                return bit
            possible_moves ^= bit

    return 0


def _evaluate(me, opponent, empty):
    """
    Static evaluation from the point of view of the side to move.

    Open lines, intersecting attack lines, positional influence, and
    potential opponent forks are all represented.
    """
    score = 0
    my_pressure = [0] * 27
    op_pressure = [0] * 27
    weights = (0, 4, 70, 0)

    for line in LINES:
        mine = (line & me).bit_count()
        theirs = (line & opponent).bit_count()

        if theirs == 0:
            score += weights[mine]
            if mine == 1:
                cells = line & empty
                while cells:
                    bit = cells & -cells
                    my_pressure[bit.bit_length() - 1] += 1
                    cells ^= bit

        if mine == 0:
            score -= weights[theirs]
            if theirs == 1:
                cells = line & empty
                while cells:
                    bit = cells & -cells
                    op_pressure[bit.bit_length() - 1] += 1
                    cells ^= bit

    cells = empty
    while cells:
        bit = cells & -cells
        idx = bit.bit_length() - 1
        a = my_pressure[idx]
        b = op_pressure[idx]

        score += 7 * (a * a - b * b)

        if a >= 2:
            score += 450 + 100 * (a - 2)
        if b >= 2:
            score -= 500 + 120 * (b - 2)

        cells ^= bit

    # Keep heuristic values clearly separate from proven wins and losses.
    if score > 20000:
        return 20000
    if score < -20000:
        return -20000
    return score


def _move_score(bit, me, opponent, tt_move):
    if bit == tt_move:
        return 10000000

    idx = bit.bit_length() - 1
    score = len(CELL_LINES[idx]) * 5

    for line in CELL_LINES[idx]:
        mine = (line & me).bit_count()
        theirs = (line & opponent).bit_count()

        if theirs == 0:
            if mine == 2:
                score += 100000
            elif mine == 1:
                score += 140
            else:
                score += 6

        if mine == 0:
            if theirs == 2:
                score += 90000
            elif theirs == 1:
                score += 115

    return score


def _ordered_moves(empty, me, opponent, tt_move=0):
    moves = []
    cells = empty

    while cells:
        bit = cells & -cells
        idx = bit.bit_length() - 1
        score = _move_score(bit, me, opponent, tt_move)
        # Prefer lower indices when scores are equal for determinism.
        moves.append((score, -idx, bit))
        cells ^= bit

    moves.sort(reverse=True)
    return [item[2] for item in moves]


def _search(me, opponent, depth, alpha, beta, ply):
    """
    Negamax alpha-beta search.

    Forced blocks do not consume depth. This extends tactical sequences
    naturally without making quiet portions of the tree too expensive.
    """
    global NODES

    NODES += 1
    if (NODES & 255) == 0 and time.perf_counter() >= DEADLINE:
        raise _SearchTimeout

    occupied = me | opponent
    empty = FULL ^ occupied

    if not empty:
        return 0

    my_wins = _winning_cells(me, opponent, empty)
    if my_wins:
        return WIN_SCORE - ply

    opponent_wins = _winning_cells(opponent, me, empty)
    threat_count = opponent_wins.bit_count()

    # Two distinct opponent winning cells cannot both be blocked.
    if threat_count >= 2:
        return -WIN_SCORE + ply + 1

    key = (me, opponent)
    tt_move = 0
    entry = TT.get(key)

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

    window_alpha = alpha
    window_beta = beta

    if threat_count == 1:
        # The only non-losing action is the forced block. Forced tactical
        # moves do not reduce the selective search depth.
        moves = [opponent_wins & -opponent_wins]
        next_depth = depth
    else:
        fork = _find_fork(me, opponent, empty)
        if fork:
            # Play fork, opponent blocks one threat, then win with the other.
            return WIN_SCORE - ply - 2

        if depth <= 0:
            return _evaluate(me, opponent, empty)

        moves = _ordered_moves(empty, me, opponent, tt_move)
        next_depth = depth - 1

    best_value = -INF
    best_move = moves[0]

    for bit in moves:
        value = -_search(
            opponent,
            me | bit,
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

    if best_value <= window_alpha:
        flag = 2  # Upper bound
    elif best_value >= window_beta:
        flag = 1  # Lower bound
    else:
        flag = 0  # Exact value

    old = TT.get(key)
    if old is None or depth >= old[0]:
        TT[key] = (depth, best_value, flag, best_move)

    return best_value


def _root_search(me, opponent, empty, depth, preferred):
    alpha = -INF
    beta = INF
    best_value = -INF
    best_move = preferred

    moves = _ordered_moves(empty, me, opponent, preferred)

    for bit in moves:
        value = -_search(
            opponent,
            me | bit,
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

        # Any value in the mate range is a proven forced win. There is no
        # need to spend the remaining time comparing winning alternatives.
        if value > 90000:
            return best_move, value

    return best_move, best_value


def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    global DEADLINE, NODES, TT

    me = 0
    opponent = 0
    legal_bits = []

    for i in range(3):
        for j in range(3):
            for k in range(3):
                value = board[i][j][k]
                bit = 1 << _index(i, j, k)

                if value == 1:
                    me |= bit
                elif value == -1:
                    opponent |= bit
                elif value == 0:
                    legal_bits.append(bit)

    # A valid nonterminal call always has at least one legal action.
    if not legal_bits:
        return 0, 0, 0

    empty = 0
    for bit in legal_bits:
        empty |= bit

    # This remains a legal fallback even if the timed search is interrupted.
    fallback = legal_bits[0]

    # Immediate tactical win.
    wins = _winning_cells(me, opponent, empty)
    if wins:
        return _to_move(wins & -wins)

    # Immediate defense. With multiple threats the game is already lost,
    # but occupying one of them is still the best legal continuation.
    opponent_wins = _winning_cells(opponent, me, empty)
    if opponent_wins:
        return _to_move(opponent_wins & -opponent_wins)

    # A fork is a mathematically forced win.
    fork = _find_fork(me, opponent, empty)
    if fork:
        return _to_move(fork)

    occupied_count = (me | opponent).bit_count()
    center = 1 << _index(1, 1, 1)

    # Strong and symmetric opening policy.
    if occupied_count == 0 and (empty & center):
        return 1, 1, 1

    if occupied_count == 1:
        if empty & center:
            return 1, 1, 1

        # If the center was taken, all corners are symmetry-equivalent and
        # have the greatest remaining line participation.
        for idx in (0, 2, 6, 8, 18, 20, 24, 26):
            bit = 1 << idx
            if empty & bit:
                return _to_move(bit)

    TT = {}
    NODES = 0
    DEADLINE = time.perf_counter() + 0.93

    initial_order = _ordered_moves(empty, me, opponent)
    best_move = initial_order[0] if initial_order else fallback

    try:
        # Depth counts quiet choices; forced tactical replies are extended.
        for depth in range(1, 13):
            move, value = _root_search(
                me, opponent, empty, depth, best_move
            )
            best_move = move

            if value > 90000 or value < -90000:
                break

            if time.perf_counter() >= DEADLINE:
                break

    except _SearchTimeout:
        pass
    except Exception:
        # Preserve the legal fallback under any unexpected runtime issue.
        if not (best_move & empty):
            best_move = fallback

    if not (best_move & empty):
        best_move = fallback

    return _to_move(best_move)
