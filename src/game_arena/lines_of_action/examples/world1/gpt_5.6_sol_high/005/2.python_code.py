
import time

BOARD_SIZE = 8
WIN_SCORE = 10_000_000
INF = 1_000_000_000

# Precompute king-neighborhoods for connectivity calculations.
_NEIGHBORS = []
for _p in range(64):
    _r, _c = divmod(_p, 8)
    _adj = []
    for _dr in (-1, 0, 1):
        for _dc in (-1, 0, 1):
            if _dr == 0 and _dc == 0:
                continue
            _rr, _cc = _r + _dr, _c + _dc
            if 0 <= _rr < 8 and 0 <= _cc < 8:
                _adj.append(_rr * 8 + _cc)
    _NEIGHBORS.append(tuple(_adj))
_NEIGHBORS = tuple(_NEIGHBORS)


def _make_zobrist():
    mask = (1 << 64) - 1
    state = 0xD1B54A32D192ED03
    result = [[], []]

    for side_index in range(2):
        for _ in range(64):
            state = (state + 0x9E3779B97F4A7C15) & mask
            z = state
            z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & mask
            z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & mask
            z ^= z >> 31
            result[side_index].append(z & mask)

    return tuple(tuple(row) for row in result)


_ZOBRIST = _make_zobrist()

_deadline = 0.0
_nodes = 0
_tt = {}
_history = {}
_killers = [[None, None] for _ in range(64)]


class _SearchTimeout(Exception):
    pass


def _generate_moves(board, side):
    """Generate every legal Lines of Action move for side."""
    row_count = [0] * 8
    col_count = [0] * 8
    diag_down_count = [0] * 15       # r-c+7
    diag_up_count = [0] * 15         # r+c

    for p, value in enumerate(board):
        if value:
            r, c = divmod(p, 8)
            row_count[r] += 1
            col_count[c] += 1
            diag_down_count[r - c + 7] += 1
            diag_up_count[r + c] += 1

    moves = []

    for source, value in enumerate(board):
        if value != side:
            continue

        r, c = divmod(source, 8)
        directions = (
            (0, 1, row_count[r]),
            (0, -1, row_count[r]),
            (1, 0, col_count[c]),
            (-1, 0, col_count[c]),
            (1, 1, diag_down_count[r - c + 7]),
            (-1, -1, diag_down_count[r - c + 7]),
            (1, -1, diag_up_count[r + c]),
            (-1, 1, diag_up_count[r + c]),
        )

        for dr, dc, distance in directions:
            tr = r + dr * distance
            tc = c + dc * distance

            if not (0 <= tr < 8 and 0 <= tc < 8):
                continue

            target = tr * 8 + tc
            if board[target] == side:
                continue

            blocked = False
            step = dr * 8 + dc
            square = source + step

            # Enemy pieces may not be jumped. The final enemy can be captured.
            for _ in range(1, distance):
                if board[square] == -side:
                    blocked = True
                    break
                square += step

            if not blocked:
                moves.append((source, target))

    return moves


def _connected(board, side):
    """Return whether all pieces belonging to side form one 8-connected group."""
    first = -1
    count = 0

    for p, value in enumerate(board):
        if value == side:
            count += 1
            if first < 0:
                first = p

    if count == 0:
        return False
    if count == 1:
        return True

    seen = 1 << first
    stack = [first]
    reached = 0

    while stack:
        p = stack.pop()
        reached += 1
        for q in _NEIGHBORS[p]:
            bit = 1 << q
            if board[q] == side and not (seen & bit):
                seen |= bit
                stack.append(q)

    return reached == count


def _side_stats(board, side):
    positions = [p for p, value in enumerate(board) if value == side]
    n = len(positions)

    if n == 0:
        return 0, 0, 0, 0, 0, 0, 0

    remaining = 0
    for p in positions:
        remaining |= 1 << p

    group_sizes = []

    while remaining:
        first_bit = remaining & -remaining
        first = first_bit.bit_length() - 1
        remaining ^= first_bit
        stack = [first]
        size = 0

        while stack:
            p = stack.pop()
            size += 1
            for q in _NEIGHBORS[p]:
                bit = 1 << q
                if remaining & bit:
                    remaining ^= bit
                    stack.append(q)

        group_sizes.append(size)

    edges = 0
    for p in positions:
        for q in _NEIGHBORS[p]:
            if q > p and board[q] == side:
                edges += 1

    sum_r = sum(p // 8 for p in positions)
    sum_c = sum(p & 7 for p in positions)

    deviation = 0
    centrality = 0
    min_r = min_c = 8
    max_r = max_c = -1

    for p in positions:
        r, c = divmod(p, 8)
        deviation += abs(r * n - sum_r) + abs(c * n - sum_c)
        centrality += abs(2 * r - 7) + abs(2 * c - 7)
        min_r = min(min_r, r)
        max_r = max(max_r, r)
        min_c = min(min_c, c)
        max_c = max(max_c, c)

    deviation //= n
    span = (max_r - min_r) + (max_c - min_c)

    return (
        n,
        len(group_sizes),
        max(group_sizes),
        sum(size * size for size in group_sizes),
        edges,
        deviation,
        centrality + 2 * span,
    )


def _side_strength(board, side):
    n, groups, largest, square_sum, edges, deviation, shape_cost = \
        _side_stats(board, side)

    if n == 0:
        return -50_000

    # Component count is the most important non-terminal feature.
    return (
        -700 * (groups - 1)
        + 115 * largest
        + 22 * square_sum
        + 28 * edges
        - 13 * deviation
        - 4 * shape_cost
        + 5 * n
    )


def _evaluate(board, side):
    return _side_strength(board, side) - _side_strength(board, -side)


def _ordered_moves(board, side, moves, preferred, ply):
    positions = [p for p, value in enumerate(board) if value == side]
    n = len(positions)
    sum_r = sum(p // 8 for p in positions)
    sum_c = sum(p & 7 for p in positions)

    killer1, killer2 = _killers[min(ply, 63)]
    scored = []

    for move in moves:
        source, target = move
        sr, sc = divmod(source, 8)
        tr, tc = divmod(target, 8)

        score = _history.get((side, source, target), 0)

        if move == preferred:
            score += 2_000_000
        if move == killer1:
            score += 30_000
        elif move == killer2:
            score += 20_000

        if board[target] == -side:
            score += 45_000

        destination_neighbors = 0
        source_neighbors = 0

        for q in _NEIGHBORS[target]:
            if q != source and board[q] == side:
                destination_neighbors += 1

        for q in _NEIGHBORS[source]:
            if q != target and board[q] == side:
                source_neighbors += 1

        score += 950 * destination_neighbors
        score -= 120 * source_neighbors

        if n:
            old_distance = abs(sr * n - sum_r) + abs(sc * n - sum_c)
            new_distance = abs(tr * n - sum_r) + abs(tc * n - sum_c)
            score += 35 * (old_distance - new_distance)

        # Slight preference for leaving the outer edge.
        score += 12 * (
            abs(2 * sr - 7) + abs(2 * sc - 7)
            - abs(2 * tr - 7) - abs(2 * tc - 7)
        )

        scored.append((score, move))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [move for _, move in scored]


def _next_hash(hash_value, side, source, target, captured):
    side_index = 1 if side == 1 else 0
    result = (
        hash_value
        ^ _ZOBRIST[side_index][source]
        ^ _ZOBRIST[side_index][target]
    )

    if captured:
        result ^= _ZOBRIST[1 - side_index][target]

    return result


def _store_tt(key, depth, score, flag, best_move):
    old = _tt.get(key)
    if old is None or depth >= old[0]:
        _tt[key] = (depth, score, flag, best_move)


def _search(board, side, depth, alpha, beta, ply, hash_value):
    global _nodes

    _nodes += 1
    if (_nodes & 63) == 0 and time.perf_counter() >= _deadline:
        raise _SearchTimeout

    if depth <= 0:
        return _evaluate(board, side)

    original_alpha = alpha
    original_beta = beta
    key = (hash_value, side)
    entry = _tt.get(key)
    preferred = None

    if entry is not None:
        stored_depth, stored_score, flag, preferred = entry

        if stored_depth >= depth:
            if flag == 0:
                return stored_score
            if flag == 1:
                alpha = max(alpha, stored_score)
            else:
                beta = min(beta, stored_score)

            if alpha >= beta:
                return stored_score

    moves = _generate_moves(board, side)
    if not moves:
        return -WIN_SCORE

    moves = _ordered_moves(board, side, moves, preferred, ply)
    best_score = -INF
    best_move = None

    for source, target in moves:
        captured = board[target]
        new_hash = _next_hash(
            hash_value, side, source, target, captured
        )

        board[source] = 0
        board[target] = side

        try:
            if _connected(board, side):
                score = WIN_SCORE
            elif captured and _connected(board, -side):
                score = -WIN_SCORE
            elif depth == 1:
                score = _evaluate(board, side)
            else:
                score = -_search(
                    board,
                    -side,
                    depth - 1,
                    -beta,
                    -alpha,
                    ply + 1,
                    new_hash,
                )
        finally:
            board[source] = side
            board[target] = captured

        if score > best_score:
            best_score = score
            best_move = (source, target)

        if score > alpha:
            alpha = score

        if alpha >= beta:
            if not captured:
                killer_slot = _killers[min(ply, 63)]
                move = (source, target)
                if killer_slot[0] != move:
                    killer_slot[1] = killer_slot[0]
                    killer_slot[0] = move

                history_key = (side, source, target)
                _history[history_key] = min(
                    500_000,
                    _history.get(history_key, 0) + depth * depth * 8,
                )
            break

    if best_score <= original_alpha:
        flag = 2  # Upper bound
    elif best_score >= original_beta:
        flag = 1  # Lower bound
    else:
        flag = 0  # Exact

    _store_tt(key, depth, best_score, flag, best_move)
    return best_score


def _root_search(board, hash_value, root_moves, depth, preferred):
    ordered = _ordered_moves(board, 1, root_moves, preferred, 0)
    alpha = -INF
    best_score = -INF
    best_move = ordered[0]

    for source, target in ordered:
        if time.perf_counter() >= _deadline:
            raise _SearchTimeout

        captured = board[target]
        new_hash = _next_hash(hash_value, 1, source, target, captured)

        board[source] = 0
        board[target] = 1

        try:
            if _connected(board, 1):
                score = WIN_SCORE
            elif captured and _connected(board, -1):
                score = -WIN_SCORE
            elif depth == 1:
                score = _evaluate(board, 1)
            else:
                score = -_search(
                    board,
                    -1,
                    depth - 1,
                    -INF,
                    -alpha,
                    1,
                    new_hash,
                )
        finally:
            board[source] = 1
            board[target] = captured

        if score > best_score:
            best_score = score
            best_move = (source, target)

        if score > alpha:
            alpha = score

    return best_score, best_move


def policy(board) -> str:
    global _deadline, _nodes, _tt, _history, _killers

    start_time = time.perf_counter()
    _deadline = start_time + 0.92
    _nodes = 0
    _tt = {}
    _history = {}
    _killers = [[None, None] for _ in range(64)]

    flat = [int(board[r][c]) for r in range(8) for c in range(8)]
    root_moves = _generate_moves(flat, 1)

    # Valid non-terminal LOA positions have at least one legal move.
    ordered = _ordered_moves(flat, 1, root_moves, None, 0)
    best_move = ordered[0]

    # Never spend search time overlooking a win available immediately.
    for source, target in ordered:
        captured = flat[target]
        flat[source] = 0
        flat[target] = 1
        wins = _connected(flat, 1)
        flat[source] = 1
        flat[target] = captured

        if wins:
            sr, sc = divmod(source, 8)
            tr, tc = divmod(target, 8)
            return f"{sr},{sc}:{tr},{tc}"

    hash_value = 0
    for p, value in enumerate(flat):
        if value == 1:
            hash_value ^= _ZOBRIST[1][p]
        elif value == -1:
            hash_value ^= _ZOBRIST[0][p]

    preferred = best_move

    # Iterative deepening always preserves the last fully completed result.
    for depth in range(1, 10):
        try:
            score, move = _root_search(
                flat, hash_value, root_moves, depth, preferred
            )
        except _SearchTimeout:
            break

        best_move = move
        preferred = move

        if score >= WIN_SCORE:
            break

    source, target = best_move
    sr, sc = divmod(source, 8)
    tr, tc = divmod(target, 8)
    return f"{sr},{sc}:{tr},{tc}"
