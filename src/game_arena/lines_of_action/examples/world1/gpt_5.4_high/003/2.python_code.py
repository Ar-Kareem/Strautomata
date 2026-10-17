
import time

BOARD_SIZE = 8
WIN_SCORE = 1_000_000
INF = 1_000_000_000

DIRECTIONS = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
]

NEIGHBORS = [[] for _ in range(64)]
EDGE = [0] * 64
CENTER_BONUS = [0] * 64

for r in range(8):
    for c in range(8):
        idx = r * 8 + c
        EDGE[idx] = 1 if (r == 0 or r == 7 or c == 0 or c == 7) else 0
        # Higher is better; center is less negative than edge.
        CENTER_BONUS[idx] = -((2 * r - 7) ** 2 + (2 * c - 7) ** 2)
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < 8 and 0 <= nc < 8:
                    NEIGHBORS[idx].append((nr, nc))


class SearchTimeout(Exception):
    pass


def format_move(move):
    return f"{move[0]},{move[1]}:{move[2]},{move[3]}"


def generate_moves(board, player):
    row_counts = [0] * 8
    col_counts = [0] * 8
    diag1_counts = [0] * 15   # r - c + 7
    diag2_counts = [0] * 15   # r + c
    pieces = []

    for r in range(8):
        row = board[r]
        for c in range(8):
            v = row[c]
            if v != 0:
                row_counts[r] += 1
                col_counts[c] += 1
                diag1_counts[r - c + 7] += 1
                diag2_counts[r + c] += 1
                if v == player:
                    pieces.append((r, c))

    opp = -player
    moves = []

    for r, c in pieces:
        row_dist = row_counts[r]
        col_dist = col_counts[c]
        d1_dist = diag1_counts[r - c + 7]
        d2_dist = diag2_counts[r + c]

        candidates = (
            (-1, 0, col_dist),
            (1, 0, col_dist),
            (0, -1, row_dist),
            (0, 1, row_dist),
            (-1, -1, d1_dist),
            (1, 1, d1_dist),
            (-1, 1, d2_dist),
            (1, -1, d2_dist),
        )

        for dr, dc, dist in candidates:
            tr = r + dr * dist
            tc = c + dc * dist

            if not (0 <= tr < 8 and 0 <= tc < 8):
                continue
            if board[tr][tc] == player:
                continue

            rr, cc = r + dr, c + dc
            blocked = False
            for _ in range(dist - 1):
                if board[rr][cc] == opp:
                    blocked = True
                    break
                rr += dr
                cc += dc

            if not blocked:
                moves.append((r, c, tr, tc))

    return moves


def is_connected(board, player):
    positions = []
    for r in range(8):
        row = board[r]
        for c in range(8):
            if row[c] == player:
                positions.append((r, c))

    if len(positions) <= 1:
        return True

    remaining = set(positions)
    start = positions[0]
    remaining.remove(start)
    stack = [start]

    while stack:
        r, c = stack.pop()
        for nr, nc in NEIGHBORS[r * 8 + c]:
            if (nr, nc) in remaining:
                remaining.remove((nr, nc))
                stack.append((nr, nc))

    return not remaining


def side_stats(positions):
    n = len(positions)
    if n == 0:
        return (0, 0, 0, 0, 0, 0, 0)
    if n == 1:
        r, c = positions[0]
        return (1, 1, 0, 0, EDGE[r * 8 + c], 0, 0)

    posset = set(positions)

    min_r = 8
    max_r = -1
    min_c = 8
    max_c = -1
    sum_r = 0
    sum_c = 0
    adj = 0
    isolated = 0
    edge_count = 0

    for r, c in positions:
        idx = r * 8 + c
        if EDGE[idx]:
            edge_count += 1
        if r < min_r:
            min_r = r
        if r > max_r:
            max_r = r
        if c < min_c:
            min_c = c
        if c > max_c:
            max_c = c
        sum_r += r
        sum_c += c

        neigh = 0
        for nbr in NEIGHBORS[idx]:
            if nbr in posset:
                neigh += 1
        adj += neigh
        if neigh == 0:
            isolated += 1

    remaining = posset.copy()
    components = 0
    largest = 0

    while remaining:
        start = remaining.pop()
        components += 1
        size = 1
        stack = [start]

        while stack:
            r, c = stack.pop()
            for nbr in NEIGHBORS[r * 8 + c]:
                if nbr in remaining:
                    remaining.remove(nbr)
                    stack.append(nbr)
                    size += 1

        if size > largest:
            largest = size

    span = (max_r - min_r) + (max_c - min_c)

    # Scaled Manhattan dispersion around centroid; smaller is better.
    dispersion = 0
    for r, c in positions:
        dispersion += abs(r * n - sum_r) + abs(c * n - sum_c)
    dispersion //= n

    return (components, largest, isolated, adj, edge_count, span, dispersion)


def evaluate(board, player):
    my_positions = []
    opp_positions = []

    for r in range(8):
        row = board[r]
        for c in range(8):
            v = row[c]
            if v == player:
                my_positions.append((r, c))
            elif v == -player:
                opp_positions.append((r, c))

    my_comp, my_largest, my_iso, my_adj, my_edge, my_span, my_disp = side_stats(my_positions)
    op_comp, op_largest, op_iso, op_adj, op_edge, op_span, op_disp = side_stats(opp_positions)

    score = 0
    score += 300 * (op_comp - my_comp)
    score += 80 * (my_largest - op_largest)
    score += 18 * (op_iso - my_iso)
    score += 7 * (my_adj - op_adj)
    score += 8 * (op_edge - my_edge)
    score += 14 * (op_span - my_span)
    score += 4 * (op_disp - my_disp)

    return score


def order_moves(board, player, moves, ply, killer, history, pv_move=None):
    opp = -player
    k1 = None
    k2 = None
    if ply < len(killer):
        k1, k2 = killer[ply]

    scored = []

    for mv in moves:
        fr, fc, tr, tc = mv
        idx_from = fr * 8 + fc
        idx_to = tr * 8 + tc

        s = history.get(mv, 0)

        if pv_move is not None and mv == pv_move:
            s += 300000
        if mv == k1:
            s += 200000
        elif mv == k2:
            s += 180000

        if board[tr][tc] == opp:
            s += 5000

        dest_friends = 0
        dest_enemies = 0
        for nr, nc in NEIGHBORS[idx_to]:
            if nr == fr and nc == fc:
                continue
            cell = board[nr][nc]
            if cell == player:
                dest_friends += 1
            elif cell == opp:
                dest_enemies += 1

        src_friends = 0
        for nr, nc in NEIGHBORS[idx_from]:
            if board[nr][nc] == player:
                src_friends += 1

        s += 30 * dest_friends
        s -= 8 * dest_enemies

        if src_friends == 0 and dest_friends > 0:
            s += 40

        s += CENTER_BONUS[idx_to] - CENTER_BONUS[idx_from]

        if EDGE[idx_from] and not EDGE[idx_to]:
            s += 12
        elif not EDGE[idx_from] and EDGE[idx_to]:
            s -= 8

        scored.append((s, mv))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [mv for _, mv in scored]


def negamax(board, depth, alpha, beta, player, ply, deadline, killer, history, node_counter):
    node_counter[0] += 1
    if (node_counter[0] & 127) == 0 and time.perf_counter() >= deadline:
        raise SearchTimeout

    # Previous mover is -player. If that side connected, current side already lost.
    if is_connected(board, -player):
        return -WIN_SCORE + ply
    if is_connected(board, player):
        return WIN_SCORE - ply

    if depth == 0:
        return evaluate(board, player)

    moves = generate_moves(board, player)
    if not moves:
        return evaluate(board, player)

    moves = order_moves(board, player, moves, ply, killer, history, None)

    best = -INF
    opp = -player

    for mv in moves:
        fr, fc, tr, tc = mv
        captured = board[tr][tc]
        board[fr][fc] = 0
        board[tr][tc] = player

        try:
            val = -negamax(board, depth - 1, -beta, -alpha, opp, ply + 1, deadline, killer, history, node_counter)
        finally:
            board[fr][fc] = player
            board[tr][tc] = captured

        if val > best:
            best = val
        if best > alpha:
            alpha = best

        if alpha >= beta:
            if ply < len(killer):
                if killer[ply][0] != mv:
                    killer[ply][1] = killer[ply][0]
                    killer[ply][0] = mv
            history[mv] = history.get(mv, 0) + depth * depth
            break

    return best


def search_root(board, legal_moves, depth, deadline, killer, history, pv_move, node_counter):
    alpha = -INF
    beta = INF
    best_val = -INF
    best_move = legal_moves[0]

    moves = order_moves(board, 1, legal_moves[:], 0, killer, history, pv_move)

    for mv in moves:
        if time.perf_counter() >= deadline:
            raise SearchTimeout

        fr, fc, tr, tc = mv
        captured = board[tr][tc]
        board[fr][fc] = 0
        board[tr][tc] = 1

        try:
            val = -negamax(board, depth - 1, -beta, -alpha, -1, 1, deadline, killer, history, node_counter)
        finally:
            board[fr][fc] = 1
            board[tr][tc] = captured

        if val > best_val:
            best_val = val
            best_move = mv
        if val > alpha:
            alpha = val

    return best_val, best_move


def policy(board) -> str:
    # Work on a mutable local copy.
    b = [list(map(int, row)) for row in board]

    legal = generate_moves(b, 1)
    if not legal:
        # Should not happen in normal LOA positions.
        return "0,0:0,0"

    fallback_move = legal[0]
    best_move = fallback_move

    try:
        if len(legal) == 1:
            return format_move(legal[0])

        # Immediate tactical win check.
        for mv in legal:
            fr, fc, tr, tc = mv
            captured = b[tr][tc]
            b[fr][fc] = 0
            b[tr][tc] = 1
            try:
                if is_connected(b, 1):
                    return format_move(mv)
            finally:
                b[fr][fc] = 1
                b[tr][tc] = captured

        total_pieces = 0
        for r in range(8):
            for c in range(8):
                if b[r][c] != 0:
                    total_pieces += 1

        if total_pieces >= 20:
            max_depth = 4
        elif total_pieces >= 14:
            max_depth = 5
        elif total_pieces >= 10:
            max_depth = 6
        else:
            max_depth = 7

        if len(legal) <= 8:
            max_depth += 1
        elif len(legal) >= 28 and max_depth > 4:
            max_depth -= 1

        if max_depth > 8:
            max_depth = 8

        deadline = time.perf_counter() + 0.94
        history = {}
        killer = [[None, None] for _ in range(max_depth + 10)]
        node_counter = [0]

        ordered = order_moves(b, 1, legal[:], 0, killer, history, None)
        if ordered:
            best_move = ordered[0]

        pv_move = best_move
        best_val = -INF

        for depth in range(1, max_depth + 1):
            val, mv = search_root(b, legal, depth, deadline, killer, history, pv_move, node_counter)
            best_val = val
            best_move = mv
            pv_move = mv

            if abs(best_val) >= WIN_SCORE // 2:
                break

    except SearchTimeout:
        pass
    except Exception:
        return format_move(fallback_move)

    return format_move(best_move)
