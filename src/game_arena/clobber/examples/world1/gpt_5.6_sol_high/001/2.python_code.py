
import time

# Board geometry: 5 rows x 6 columns.
ROWS = 5
COLS = 6
CELLS = ROWS * COLS
FULL = (1 << CELLS) - 1

LEFT_COL = sum(1 << (r * COLS) for r in range(ROWS))
RIGHT_COL = sum(1 << (r * COLS + COLS - 1) for r in range(ROWS))
TOP_ROW = (1 << COLS) - 1
BOTTOM_ROW = TOP_ROW << ((ROWS - 1) * COLS)

NOT_LEFT = FULL ^ LEFT_COL
NOT_RIGHT = FULL ^ RIGHT_COL
NOT_TOP = FULL ^ TOP_ROW
NOT_BOTTOM = FULL ^ BOTTOM_ROW

MATE = 30000
INF = 30001

# Neighbor mask for each individual square.
NEIGHBOR_MASKS = [0] * CELLS
for _r in range(ROWS):
    for _c in range(COLS):
        _i = _r * COLS + _c
        _mask = 0
        if _r > 0:
            _mask |= 1 << (_i - COLS)
        if _r + 1 < ROWS:
            _mask |= 1 << (_i + COLS)
        if _c > 0:
            _mask |= 1 << (_i - 1)
        if _c + 1 < COLS:
            _mask |= 1 << (_i + 1)
        NEIGHBOR_MASKS[_i] = _mask


class _SearchTimeout(Exception):
    pass


_deadline = 0.0
_nodes = 0
_tt = {}
_history = [0] * (CELLS * 32)
_killers = [[-1, -1] for _ in range(64)]


def _neighbors(bits):
    return (
        ((bits & NOT_TOP) >> COLS)
        | ((bits & NOT_BOTTOM) << COLS)
        | ((bits & NOT_RIGHT) << 1)
        | ((bits & NOT_LEFT) >> 1)
    ) & FULL


def _normalize(a, b):
    """
    Remove occupied components containing only one color. Such components
    can never participate in another move because pieces cannot enter empty
    squares.
    """
    boundary_a = a & _neighbors(b)
    if not boundary_a:
        return 0, 0

    boundary_b = b & _neighbors(a)
    occupied = a | b
    active = boundary_a | boundary_b

    if active != occupied:
        while True:
            expanded = active | (_neighbors(active) & occupied)
            if expanded == active:
                break
            active = expanded

    return a & active, b & active


def _generate_moves(a, b):
    """
    A move is encoded as source * 32 + destination.
    """
    moves = []

    # Up: destination = source - 6
    targets = (a >> COLS) & b
    while targets:
        bit = targets & -targets
        dst = bit.bit_length() - 1
        moves.append((dst + COLS) * 32 + dst)
        targets ^= bit

    # Right: destination = source + 1
    targets = ((a & NOT_RIGHT) << 1) & b
    while targets:
        bit = targets & -targets
        dst = bit.bit_length() - 1
        moves.append((dst - 1) * 32 + dst)
        targets ^= bit

    # Down: destination = source + 6
    targets = ((a & NOT_BOTTOM) << COLS) & b
    while targets:
        bit = targets & -targets
        dst = bit.bit_length() - 1
        moves.append((dst - COLS) * 32 + dst)
        targets ^= bit

    # Left: destination = source - 1
    targets = ((a & NOT_LEFT) >> 1) & b
    while targets:
        bit = targets & -targets
        dst = bit.bit_length() - 1
        moves.append((dst + 1) * 32 + dst)
        targets ^= bit

    return moves


def _apply_move(a, b, move):
    src = move >> 5
    dst = move & 31
    src_bit = 1 << src
    dst_bit = 1 << dst
    return (a ^ src_bit) | dst_bit, b ^ dst_bit


def _cross_edges(a, b):
    horizontal = (
        (((a & NOT_RIGHT) << 1) & b).bit_count()
        + (((b & NOT_RIGHT) << 1) & a).bit_count()
    )
    vertical = (
        (((a & NOT_BOTTOM) << COLS) & b).bit_count()
        + (((b & NOT_BOTTOM) << COLS) & a).bit_count()
    )
    return horizontal + vertical


def _occupied_edges(occupied):
    return (
        (((occupied & NOT_RIGHT) << 1) & occupied).bit_count()
        + (((occupied & NOT_BOTTOM) << COLS) & occupied).bit_count()
    )


def _simple_pair_result(a, b, move_count):
    """
    If every active component is one isolated unlike-colored edge, every
    move consumes exactly one component. The result is determined by parity.
    Return None when this test does not apply.
    """
    occupied = a | b
    if occupied.bit_count() != 2 * move_count:
        return None
    if _occupied_edges(occupied) != move_count:
        return None
    return MATE if move_count & 1 else -MATE


def _same_color_edges(bits):
    return (
        (((bits & NOT_RIGHT) << 1) & bits).bit_count()
        + (((bits & NOT_BOTTOM) << COLS) & bits).bit_count()
    )


def _child_cross_count(a, b, move, current_count):
    src = move >> 5
    dst = move & 31
    dst_bit = 1 << dst

    # All old cross edges incident to source or destination disappear.
    removed = (
        (NEIGHBOR_MASKS[src] & b).bit_count()
        + (NEIGHBOR_MASKS[dst] & a).bit_count()
        - 1
    )

    # The captured destination becomes ours and may contact other enemies.
    created = (NEIGHBOR_MASKS[dst] & (b ^ dst_bit)).bit_count()
    return current_count + created - removed


def _order_moves(a, b, moves, tt_move, ply, cross_count):
    if len(moves) <= 1:
        return moves

    killer1, killer2 = _killers[ply] if ply < len(_killers) else (-1, -1)

    def score(move):
        value = _history[move]

        if move == tt_move:
            value += 10_000_000
        elif move == killer1:
            value += 800_000
        elif move == killer2:
            value += 500_000

        child_count = _child_cross_count(a, b, move, cross_count)
        if child_count == 0:
            value += 5_000_000
        else:
            # Forcing moves tend to simplify the position and improve pruning.
            value -= child_count * 24

        dst = move & 31
        src = move >> 5

        # Prefer capturing well-connected pieces and vacating exposed pieces.
        value += (NEIGHBOR_MASKS[dst] & b).bit_count() * 8
        value += (NEIGHBOR_MASKS[src] & b).bit_count() * 4
        return value

    moves.sort(key=score, reverse=True)
    return moves


def _basic_evaluation(a, b, moves):
    move_count = len(moves)

    # Exact mate-in-one recognition at shallow leaves.
    if move_count <= 6:
        for move in moves:
            na, nb = _apply_move(a, b, move)
            if not (na & _neighbors(nb)):
                return MATE

    my_count = a.bit_count()
    enemy_count = b.bit_count()

    my_frontier = (a & _neighbors(b)).bit_count()
    enemy_frontier = (b & _neighbors(a)).bit_count()

    my_cohesion = _same_color_edges(a)
    enemy_cohesion = _same_color_edges(b)

    # More material is generally useful. A concentrated frontier is also
    # valuable: one piece contacting several enemies can often collapse an
    # entire active component with a single capture.
    value = 34 * (my_count - enemy_count)
    value += 12 * (enemy_frontier - my_frontier)
    value += 3 * (my_cohesion - enemy_cohesion)

    if value > 1200:
        return 1200
    if value < -1200:
        return -1200
    return value


def _qsearch(a, b, alpha, beta, remaining):
    """
    Tactical extension for positions with at most two legal captures.
    Such lines are inexpensive and are frequently solvable to completion.
    """
    global _nodes

    _nodes += 1
    if (_nodes & 1023) == 0 and time.perf_counter() >= _deadline:
        raise _SearchTimeout

    a, b = _normalize(a, b)
    if not a:
        return -MATE

    moves = _generate_moves(a, b)
    if not moves:
        return -MATE

    pair_value = _simple_pair_result(a, b, len(moves))
    if pair_value is not None:
        return pair_value

    if remaining <= 0 or len(moves) > 2:
        return _basic_evaluation(a, b, moves)

    moves = _order_moves(a, b, moves, -1, 0, len(moves))
    best = -INF

    for move in moves:
        na, nb = _apply_move(a, b, move)
        value = -_qsearch(nb, na, -beta, -alpha, remaining - 1)

        if value > best:
            best = value
        if value > alpha:
            alpha = value
        if alpha >= beta:
            break

    return best


def _negamax(a, b, depth, alpha, beta, ply):
    global _nodes

    _nodes += 1
    if (_nodes & 1023) == 0 and time.perf_counter() >= _deadline:
        raise _SearchTimeout

    a, b = _normalize(a, b)
    if not a:
        return -MATE

    key = (a, b)
    original_alpha = alpha
    original_beta = beta

    tt_move = -1
    entry = _tt.get(key)
    if entry is not None:
        stored_depth, stored_value, flag, tt_move = entry
        if stored_depth >= depth:
            if flag == 0:       # Exact
                return stored_value
            if flag == 1:       # Lower bound
                if stored_value > alpha:
                    alpha = stored_value
            else:               # Upper bound
                if stored_value < beta:
                    beta = stored_value
            if alpha >= beta:
                return stored_value

    moves = _generate_moves(a, b)
    if not moves:
        return -MATE

    move_count = len(moves)

    pair_value = _simple_pair_result(a, b, move_count)
    if pair_value is not None:
        return pair_value

    if depth <= 0:
        return _qsearch(a, b, alpha, beta, 10)

    moves = _order_moves(a, b, moves, tt_move, ply, move_count)

    best_value = -INF
    best_move = moves[0]

    for index, move in enumerate(moves):
        na, nb = _apply_move(a, b, move)
        full_child_depth = depth - 1

        if index == 0:
            value = -_negamax(
                nb, na, full_child_depth, -beta, -alpha, ply + 1
            )
        else:
            child_cross = _child_cross_count(a, b, move, move_count)
            reduced_depth = full_child_depth

            # Reduce late, non-forcing moves. Any move that looks promising
            # under the reduced search is immediately re-searched fully.
            if depth >= 4 and index >= 5 and child_cross > 1:
                reduced_depth -= 1
                if depth >= 7 and index >= 12:
                    reduced_depth -= 1
                if reduced_depth < 0:
                    reduced_depth = 0

            value = -_negamax(
                nb, na, reduced_depth, -alpha - 1, -alpha, ply + 1
            )

            if value > alpha and reduced_depth != full_child_depth:
                value = -_negamax(
                    nb, na, full_child_depth, -alpha - 1, -alpha, ply + 1
                )

            if value > alpha and value < beta:
                value = -_negamax(
                    nb, na, full_child_depth, -beta, -alpha, ply + 1
                )

        if value > best_value:
            best_value = value
            best_move = move

        if value > alpha:
            alpha = value

        if alpha >= beta:
            if ply < len(_killers) and move != _killers[ply][0]:
                _killers[ply][1] = _killers[ply][0]
                _killers[ply][0] = move
            _history[move] += depth * depth
            break

    if best_value <= original_alpha:
        flag = 2       # Upper bound
    elif best_value >= original_beta:
        flag = 1       # Lower bound
    else:
        flag = 0       # Exact

    old = _tt.get(key)
    if old is None or depth >= old[0]:
        _tt[key] = (depth, best_value, flag, best_move)

    return best_value


def _to_bitboard(board):
    bits = 0

    # Support both 5x6 nested arrays (including NumPy arrays) and flat
    # sequences of length 30.
    nested = True
    try:
        board[0][0]
    except (TypeError, IndexError, KeyError):
        nested = False

    if nested:
        for r in range(ROWS):
            for c in range(COLS):
                if int(board[r][c]):
                    bits |= 1 << (r * COLS + c)
    else:
        for i in range(CELLS):
            if int(board[i]):
                bits |= 1 << i

    return bits


def _format_move(move):
    src = move >> 5
    dst = move & 31
    row, col = divmod(src, COLS)
    delta = dst - src

    if delta == -COLS:
        direction = "U"
    elif delta == 1:
        direction = "R"
    elif delta == COLS:
        direction = "D"
    else:
        direction = "L"

    return f"{row},{col},{direction}"


def policy(you: list[int], opponent: list[int]) -> str:
    global _deadline, _nodes, _tt, _history, _killers

    a = _to_bitboard(you)
    b = _to_bitboard(opponent)

    legal_moves = _generate_moves(a, b)

    # A terminal position has no legal return value by definition. Arenas
    # should not call a policy after the game has ended.
    if not legal_moves:
        return "0,0,U"

    if len(legal_moves) == 1:
        return _format_move(legal_moves[0])

    _nodes = 0
    _tt = {}
    _history = [0] * (CELLS * 32)
    _killers = [[-1, -1] for _ in range(64)]

    # Establish a legal fallback before doing any timed work.
    root_cross = len(legal_moves)
    ordered_fallbacks = _order_moves(
        a, b, legal_moves[:], -1, 0, root_cross
    )
    best_move = ordered_fallbacks[0]

    # Leave a small safety margin for formatting and scheduler variability.
    _deadline = time.perf_counter() + 0.93

    root_a, root_b = _normalize(a, b)
    max_depth = max(1, (root_a | root_b).bit_count() - 1)

    try:
        for depth in range(1, max_depth + 1):
            value = _negamax(root_a, root_b, depth, -MATE, MATE, 0)

            entry = _tt.get((root_a, root_b))
            if entry is not None and entry[3] >= 0:
                candidate = entry[3]
                src = candidate >> 5
                dst = candidate & 31
                if (
                    (a & (1 << src))
                    and (b & (1 << dst))
                    and (NEIGHBOR_MASKS[src] & (1 << dst))
                ):
                    best_move = candidate

            # A forced win or loss has been solved exactly.
            if value == MATE or value == -MATE:
                break

            if time.perf_counter() >= _deadline:
                break

    except _SearchTimeout:
        pass

    return _format_move(best_move)
