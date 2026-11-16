
import time

# Board directions: dr, dc, line type
# line type: 0=row, 1=column, 2=\ diagonal, 3=/ diagonal
_DIRS = (
    (-1, 0, 1), (1, 0, 1),
    (0, -1, 0), (0, 1, 0),
    (-1, -1, 2), (1, 1, 2),
    (-1, 1, 3), (1, -1, 3),
)

_NEIGHBORS = []
for _sq in range(64):
    _r, _c = divmod(_sq, 8)
    _ns = []
    for _dr in (-1, 0, 1):
        for _dc in (-1, 0, 1):
            if _dr == 0 and _dc == 0:
                continue
            _rr, _cc = _r + _dr, _c + _dc
            if 0 <= _rr < 8 and 0 <= _cc < 8:
                _ns.append(_rr * 8 + _cc)
    _NEIGHBORS.append(tuple(_ns))

# Deterministic Zobrist values.
_MASK64 = (1 << 64) - 1
_zstate = 0x9E3779B97F4A7C15


def _next_random():
    global _zstate
    x = _zstate
    x ^= (x << 13) & _MASK64
    x ^= x >> 7
    x ^= (x << 17) & _MASK64
    _zstate = x & _MASK64
    return _zstate


_ZOBRIST = tuple((_next_random(), _next_random()) for _ in range(64))
_SIDE_HASH = _next_random()

_INF = 2_000_000
_MATE = 1_000_000
_MATE_BOUND = 900_000

_EXACT = 0
_LOWER = 1
_UPPER = 2

_deadline = 0.0
_nodes = 0
_tt = {}
_history = {}
_killers = {}


class _SearchTimeout(Exception):
    pass


def _piece_index(value):
    return 0 if value == 1 else 1


def _board_hash(board):
    h = 0
    for i, value in enumerate(board):
        if value:
            h ^= _ZOBRIST[i][_piece_index(value)]
    return h


def _generate_moves(board, side):
    row_count = [0] * 8
    col_count = [0] * 8
    diag_down = [0] * 15       # r-c+7
    diag_up = [0] * 15         # r+c

    for sq, value in enumerate(board):
        if value:
            r, c = divmod(sq, 8)
            row_count[r] += 1
            col_count[c] += 1
            diag_down[r - c + 7] += 1
            diag_up[r + c] += 1

    moves = []
    enemy = -side

    for src, value in enumerate(board):
        if value != side:
            continue

        r, c = divmod(src, 8)

        for dr, dc, line_type in _DIRS:
            if line_type == 0:
                distance = row_count[r]
            elif line_type == 1:
                distance = col_count[c]
            elif line_type == 2:
                distance = diag_down[r - c + 7]
            else:
                distance = diag_up[r + c]

            tr = r + dr * distance
            tc = c + dc * distance
            if not (0 <= tr < 8 and 0 <= tc < 8):
                continue

            dst = tr * 8 + tc
            if board[dst] == side:
                continue

            blocked = False
            for step in range(1, distance):
                mid = (r + dr * step) * 8 + (c + dc * step)
                if board[mid] == enemy:
                    blocked = True
                    break

            if not blocked:
                moves.append((src, dst))

    return moves


def _is_connected(board, side):
    start = -1
    count = 0

    for i, value in enumerate(board):
        if value == side:
            count += 1
            if start < 0:
                start = i

    if count == 0:
        return False
    if count == 1:
        return True

    seen = 1 << start
    stack = [start]
    reached = 0

    while stack:
        sq = stack.pop()
        reached += 1
        for nxt in _NEIGHBORS[sq]:
            bit = 1 << nxt
            if not (seen & bit) and board[nxt] == side:
                seen |= bit
                stack.append(nxt)

    return reached == count


def _group_quality(board, side):
    positions = [i for i, value in enumerate(board) if value == side]
    n = len(positions)

    if n == 0:
        return -100000

    seen = 0
    components = []

    for start in positions:
        start_bit = 1 << start
        if seen & start_bit:
            continue

        seen |= start_bit
        stack = [start]
        component = []

        while stack:
            sq = stack.pop()
            component.append(sq)

            for nxt in _NEIGHBORS[sq]:
                bit = 1 << nxt
                if not (seen & bit) and board[nxt] == side:
                    seen |= bit
                    stack.append(nxt)

        components.append(component)

    component_count = len(components)
    largest = max(len(comp) for comp in components)

    # Minimum spanning-tree distance between disconnected components.
    gap = 0
    if component_count > 1:
        used = [False] * component_count
        best_distance = [99] * component_count
        used[0] = True

        for j in range(1, component_count):
            d = 99
            for a in components[0]:
                ar, ac = divmod(a, 8)
                for b in components[j]:
                    br, bc = divmod(b, 8)
                    candidate = max(abs(ar - br), abs(ac - bc)) - 1
                    if candidate < d:
                        d = candidate
            best_distance[j] = d

        for _ in range(component_count - 1):
            chosen = -1
            chosen_distance = 99
            for j in range(component_count):
                if not used[j] and best_distance[j] < chosen_distance:
                    chosen = j
                    chosen_distance = best_distance[j]

            if chosen < 0:
                break

            used[chosen] = True
            gap += chosen_distance

            for j in range(component_count):
                if used[j]:
                    continue

                d = best_distance[j]
                for a in components[chosen]:
                    ar, ac = divmod(a, 8)
                    for b in components[j]:
                        br, bc = divmod(b, 8)
                        candidate = max(abs(ar - br), abs(ac - bc)) - 1
                        if candidate < d:
                            d = candidate
                best_distance[j] = d

    adjacency = 0
    pair_distance = 0
    center_penalty = 0

    min_r, max_r = 7, 0
    min_c, max_c = 7, 0

    for i, a in enumerate(positions):
        ar, ac = divmod(a, 8)
        center_penalty += abs(2 * ar - 7) + abs(2 * ac - 7)
        min_r = min(min_r, ar)
        max_r = max(max_r, ar)
        min_c = min(min_c, ac)
        max_c = max(max_c, ac)

        for b in positions[i + 1:]:
            br, bc = divmod(b, 8)
            d = max(abs(ar - br), abs(ac - bc))
            pair_distance += d
            if d == 1:
                adjacency += 1

    span = (max_r - min_r) + (max_c - min_c)

    return (
        -1050 * (component_count - 1)
        - 140 * gap
        + (260 * largest) // n
        + 28 * adjacency
        - 10 * (pair_distance // n)
        - 3 * center_penalty
        - 8 * span
        + 12 * n
    )


def _evaluate(board, side):
    return _group_quality(board, side) - _group_quality(board, -side)


def _move_order_score(board, side, move, preferred, ply):
    src, dst = move
    score = _history.get((side, src, dst), 0)

    if move == preferred:
        score += 1_000_000

    if board[dst] == -side:
        score += 100_000

    killers = _killers.get(ply)
    if killers:
        if move == killers[0]:
            score += 30_000
        elif len(killers) > 1 and move == killers[1]:
            score += 20_000

    old_friends = 0
    for sq in _NEIGHBORS[src]:
        if board[sq] == side:
            old_friends += 1

    new_friends = 0
    for sq in _NEIGHBORS[dst]:
        if sq != src and board[sq] == side:
            new_friends += 1

    score += 100 * new_friends - 45 * old_friends

    sr, sc = divmod(src, 8)
    dr, dc = divmod(dst, 8)
    old_center = abs(2 * sr - 7) + abs(2 * sc - 7)
    new_center = abs(2 * dr - 7) + abs(2 * dc - 7)
    score += 5 * (old_center - new_center)

    return score


def _order_moves(board, side, moves, preferred=None, ply=0):
    moves.sort(
        key=lambda move: _move_order_score(
            board, side, move, preferred, ply
        ),
        reverse=True,
    )


def _store_score(score, ply):
    if score > _MATE_BOUND:
        return score + ply
    if score < -_MATE_BOUND:
        return score - ply
    return score


def _load_score(score, ply):
    if score > _MATE_BOUND:
        return score - ply
    if score < -_MATE_BOUND:
        return score + ply
    return score


def _record_killer(move, ply):
    killers = _killers.setdefault(ply, [])
    if move in killers:
        return
    killers.insert(0, move)
    if len(killers) > 2:
        killers.pop()


def _search(board, side, depth, alpha, beta, ply, board_hash, passed=False):
    global _nodes

    _nodes += 1
    if (_nodes & 127) == 0 and time.perf_counter() >= _deadline:
        raise _SearchTimeout

    if depth <= 0:
        return _evaluate(board, side)

    key = board_hash ^ (_SIDE_HASH if side == -1 else 0)
    preferred = None
    alpha_input = alpha
    beta_input = beta

    entry = _tt.get(key)
    if entry is not None:
        stored_depth, stored_score, flag, preferred = entry
        if stored_depth >= depth:
            score = _load_score(stored_score, ply)
            if flag == _EXACT:
                return score
            if flag == _LOWER:
                alpha = max(alpha, score)
            else:
                beta = min(beta, score)
            if alpha >= beta:
                return score

    moves = _generate_moves(board, side)

    if not moves:
        if passed:
            return _evaluate(board, side)
        return -_search(
            board, -side, depth - 1, -beta, -alpha,
            ply + 1, board_hash, True
        )

    _order_moves(board, side, moves, preferred, ply)

    best_score = -_INF
    best_move = moves[0]

    for src, dst in moves:
        captured = board[dst]

        new_hash = board_hash
        new_hash ^= _ZOBRIST[src][_piece_index(side)]
        if captured:
            new_hash ^= _ZOBRIST[dst][_piece_index(captured)]
        new_hash ^= _ZOBRIST[dst][_piece_index(side)]

        board[src] = 0
        board[dst] = side

        try:
            if _is_connected(board, side):
                score = _MATE - ply
            elif captured and _is_connected(board, -side):
                score = -_MATE + ply
            else:
                score = -_search(
                    board, -side, depth - 1, -beta, -alpha,
                    ply + 1, new_hash, False
                )
        except _SearchTimeout:
            board[src] = side
            board[dst] = captured
            raise

        board[src] = side
        board[dst] = captured

        if score > best_score:
            best_score = score
            best_move = (src, dst)

        if score > alpha:
            alpha = score

        if alpha >= beta:
            if captured == 0:
                _history[(side, src, dst)] = (
                    _history.get((side, src, dst), 0) + depth * depth
                )
                _record_killer((src, dst), ply)
            break

    if best_score <= alpha_input:
        flag = _UPPER
    elif best_score >= beta_input:
        flag = _LOWER
    else:
        flag = _EXACT

    _tt[key] = (
        depth,
        _store_score(best_score, ply),
        flag,
        best_move,
    )

    return best_score


def _root_search(board, depth, board_hash, previous_best):
    moves = _generate_moves(board, 1)
    _order_moves(board, 1, moves, previous_best, 0)

    best_move = moves[0]
    best_score = -_INF
    alpha = -_INF

    for src, dst in moves:
        if time.perf_counter() >= _deadline:
            raise _SearchTimeout

        captured = board[dst]

        new_hash = board_hash
        new_hash ^= _ZOBRIST[src][0]
        if captured:
            new_hash ^= _ZOBRIST[dst][_piece_index(captured)]
        new_hash ^= _ZOBRIST[dst][0]

        board[src] = 0
        board[dst] = 1

        try:
            if _is_connected(board, 1):
                score = _MATE
            elif captured and _is_connected(board, -1):
                score = -_MATE
            else:
                score = -_search(
                    board, -1, depth - 1,
                    -_INF, -alpha, 1, new_hash, False
                )
        except _SearchTimeout:
            board[src] = 1
            board[dst] = captured
            raise

        board[src] = 1
        board[dst] = captured

        if score > best_score:
            best_score = score
            best_move = (src, dst)

        if score > alpha:
            alpha = score

        # No result can be better than an immediate win.
        if score >= _MATE:
            return best_move, best_score

    return best_move, best_score


def policy(board) -> str:
    global _deadline, _nodes, _tt, _history, _killers

    flat = [int(board[r][c]) for r in range(8) for c in range(8)]
    legal_moves = _generate_moves(flat, 1)

    # Valid arena positions should always have a legal move. This branch only
    # provides a correctly formatted response for an invalid/pass position.
    if not legal_moves:
        return "0,0:0,0"

    best_move = legal_moves[0]
    board_hash = _board_hash(flat)

    _tt = {}
    _history = {}
    _killers = {}
    _nodes = 0
    _deadline = time.perf_counter() + 0.92

    depth = 1
    while depth <= 10:
        try:
            candidate, score = _root_search(
                flat, depth, board_hash, best_move
            )
            best_move = candidate

            if score >= _MATE - 100:
                break

            depth += 1
        except _SearchTimeout:
            break

    src, dst = best_move
    sr, sc = divmod(src, 8)
    dr, dc = divmod(dst, 8)
    return f"{sr},{sc}:{dr},{dc}"
