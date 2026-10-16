
import time

BOARD_SIZE = 8
WIN_SCORE = 10_000_000
TIME_LIMIT = 0.92

DIRS8 = [(-1, -1), (-1, 0), (-1, 1),
         (0, -1),           (0, 1),
         (1, -1),  (1, 0),  (1, 1)]

LINK_DIRS = [(1, 0), (0, 1), (1, 1), (1, -1)]

CENTER_DIST2 = [[(2 * r - 7) * (2 * r - 7) + (2 * c - 7) * (2 * c - 7)
                 for c in range(BOARD_SIZE)]
                for r in range(BOARD_SIZE)]

EDGE = [[1 if (r == 0 or r == 7 or c == 0 or c == 7) else 0
         for c in range(BOARD_SIZE)]
        for r in range(BOARD_SIZE)]

NEIGHBORS = [[[] for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
for r in range(BOARD_SIZE):
    for c in range(BOARD_SIZE):
        lst = []
        for dr, dc in DIRS8:
            nr, nc = r + dr, c + dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                lst.append((nr, nc))
        NEIGHBORS[r][c] = lst


class SearchTimeout(Exception):
    pass


_DEADLINE = 0.0
_NODE_COUNTER = 0


def _check_time():
    global _NODE_COUNTER
    _NODE_COUNTER += 1
    if (_NODE_COUNTER & 127) == 0 and time.perf_counter() >= _DEADLINE:
        raise SearchTimeout


def _line_counts(board):
    row_counts = [0] * BOARD_SIZE
    col_counts = [0] * BOARD_SIZE
    diag_counts = [0] * 15       # r - c + 7
    adiag_counts = [0] * 15      # r + c

    for r in range(BOARD_SIZE):
        row = board[r]
        for c in range(BOARD_SIZE):
            if row[c] != 0:
                row_counts[r] += 1
                col_counts[c] += 1
                diag_counts[r - c + 7] += 1
                adiag_counts[r + c] += 1
    return row_counts, col_counts, diag_counts, adiag_counts


def _generate_moves(board, side):
    row_counts, col_counts, diag_counts, adiag_counts = _line_counts(board)
    moves = []

    for r in range(BOARD_SIZE):
        row = board[r]
        for c in range(BOARD_SIZE):
            if row[c] != side:
                continue

            for dr, dc in DIRS8:
                if dr == 0:
                    dist = row_counts[r]
                elif dc == 0:
                    dist = col_counts[c]
                elif dr == dc:
                    dist = diag_counts[r - c + 7]
                else:
                    dist = adiag_counts[r + c]

                tr = r + dr * dist
                tc = c + dc * dist

                if not (0 <= tr < BOARD_SIZE and 0 <= tc < BOARD_SIZE):
                    continue
                if board[tr][tc] == side:
                    continue

                legal = True
                for k in range(1, dist):
                    mr = r + dr * k
                    mc = c + dc * k
                    if board[mr][mc] == -side:
                        legal = False
                        break

                if legal:
                    moves.append((r, c, tr, tc))

    return moves


def _apply_move(board, move):
    fr, fc, tr, tc = move
    captured = board[tr][tc]
    board[tr][tc] = board[fr][fc]
    board[fr][fc] = 0
    return captured


def _undo_move(board, move, captured):
    fr, fc, tr, tc = move
    board[fr][fc] = board[tr][tc]
    board[tr][tc] = captured


def _is_connected(board, side):
    pieces = []
    piece_set = set()

    for r in range(BOARD_SIZE):
        row = board[r]
        for c in range(BOARD_SIZE):
            if row[c] == side:
                pieces.append((r, c))
                piece_set.add((r, c))

    if len(pieces) <= 1:
        return True

    start = pieces[0]
    stack = [start]
    seen = {start}

    while stack:
        r, c = stack.pop()
        for nr, nc in NEIGHBORS[r][c]:
            if (nr, nc) in piece_set and (nr, nc) not in seen:
                seen.add((nr, nc))
                stack.append((nr, nc))

    return len(seen) == len(pieces)


def _terminal_value(board, side):
    my_conn = _is_connected(board, side)
    opp_conn = _is_connected(board, -side)

    if my_conn:
        if opp_conn:
            return -WIN_SCORE   # previous mover wins ties
        return WIN_SCORE
    if opp_conn:
        return -WIN_SCORE
    return None


def _analyze_side(board, side):
    pieces = []
    piece_set = set()

    sum_r = 0
    sum_c = 0
    sum_sq = 0
    center = 0
    edge = 0

    for r in range(BOARD_SIZE):
        row = board[r]
        for c in range(BOARD_SIZE):
            if row[c] == side:
                pieces.append((r, c))
                piece_set.add((r, c))
                sum_r += r
                sum_c += c
                sum_sq += r * r + c * c
                center += CENTER_DIST2[r][c]
                edge += EDGE[r][c]

    n = len(pieces)
    if n <= 1:
        return {
            "n": n,
            "components": 1 if n == 1 else 0,
            "largest": n,
            "spread": 0,
            "center": center,
            "edge": edge,
            "links": 0,
        }

    remaining = set(piece_set)
    components = 0
    largest = 0

    while remaining:
        start = next(iter(remaining))
        remaining.remove(start)
        stack = [start]
        size = 1

        while stack:
            r, c = stack.pop()
            for nr, nc in NEIGHBORS[r][c]:
                if (nr, nc) in remaining:
                    remaining.remove((nr, nc))
                    stack.append((nr, nc))
                    size += 1

        components += 1
        if size > largest:
            largest = size

    links = 0
    for r, c in pieces:
        for dr, dc in LINK_DIRS:
            nr, nc = r + dr, c + dc
            if (nr, nc) in piece_set:
                links += 1

    spread = n * sum_sq - sum_r * sum_r - sum_c * sum_c

    return {
        "n": n,
        "components": components,
        "largest": largest,
        "spread": spread,
        "center": center,
        "edge": edge,
        "links": links,
    }


def _evaluate(board, side):
    my = _analyze_side(board, side)
    opp = _analyze_side(board, -side)

    score = 0
    score += 900 * (opp["components"] - my["components"])
    score += 120 * (my["largest"] - opp["largest"])
    score += 20 * (my["links"] - opp["links"])
    score += (opp["spread"] - my["spread"]) // 3
    score += (opp["center"] - my["center"]) // 4
    score += 12 * (opp["edge"] - my["edge"])

    return score


def _move_order_score(board, side, move):
    fr, fc, tr, tc = move
    score = 0

    if board[tr][tc] == -side:
        score += 120

    score += (CENTER_DIST2[fr][fc] - CENTER_DIST2[tr][tc]) // 2

    friendly_adj = 0
    enemy_adj = 0
    for nr, nc in NEIGHBORS[tr][tc]:
        if nr == fr and nc == fc:
            continue
        v = board[nr][nc]
        if v == side:
            friendly_adj += 1
        elif v == -side:
            enemy_adj += 1

    score += 18 * friendly_adj
    score -= 4 * enemy_adj

    if EDGE[fr][fc]:
        score += 4
    if EDGE[tr][tc]:
        score -= 6

    return score


def _order_moves(board, side, moves):
    if len(moves) <= 1:
        return moves
    return sorted(moves, key=lambda m: _move_order_score(board, side, m), reverse=True)


def _negamax(board, depth, alpha, beta, side):
    _check_time()

    tv = _terminal_value(board, side)
    if tv is not None:
        return tv

    if depth == 0:
        return _evaluate(board, side)

    moves = _generate_moves(board, side)
    if not moves:
        # Pass turn if no legal moves.
        return -_negamax(board, depth - 1, -beta, -alpha, -side)

    moves = _order_moves(board, side, moves)

    best = -WIN_SCORE * 2
    for move in moves:
        captured = _apply_move(board, move)
        val = -_negamax(board, depth - 1, -beta, -alpha, -side)
        _undo_move(board, move, captured)

        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    return best


def _search_root(board, depth, moves):
    alpha = -WIN_SCORE * 2
    beta = WIN_SCORE * 2
    best_move = moves[0]
    best_score = -WIN_SCORE * 2
    scored = []

    for move in moves:
        if time.perf_counter() >= _DEADLINE:
            raise SearchTimeout

        captured = _apply_move(board, move)
        val = -_negamax(board, depth - 1, -beta, -alpha, -1)
        _undo_move(board, move, captured)

        scored.append((val, move))

        if val > best_score:
            best_score = val
            best_move = move
        if val > alpha:
            alpha = val

    scored.sort(key=lambda x: x[0], reverse=True)
    next_order = [m for _, m in scored]
    return best_score, best_move, next_order


def _format_move(move):
    fr, fc, tr, tc = move
    return f"{fr},{fc}:{tr},{tc}"


def policy(board) -> str:
    global _DEADLINE, _NODE_COUNTER

    b = [list(row) for row in board]
    moves = _generate_moves(b, 1)

    # The arena should provide positions with a legal move.
    # If not, we still avoid crashing.
    if not moves:
        # No legal move string exists under the required API.
        # Return a deterministic placeholder rather than raising.
        return "0,0:0,0"

    ordered_moves = _order_moves(b, 1, moves)
    best_move = ordered_moves[0]

    if len(ordered_moves) == 1:
        return _format_move(best_move)

    # Quick tactical scan for an immediate winning move.
    for move in ordered_moves:
        captured = _apply_move(b, move)
        tv = _terminal_value(b, -1)
        _undo_move(b, move, captured)
        if tv == -WIN_SCORE:
            return _format_move(move)

    _DEADLINE = time.perf_counter() + TIME_LIMIT
    _NODE_COUNTER = 0

    try:
        for depth in range(1, 7):
            score, move, ordered_moves = _search_root(b, depth, ordered_moves)
            best_move = move
            if abs(score) >= WIN_SCORE:
                break
    except SearchTimeout:
        pass

    return _format_move(best_move)
