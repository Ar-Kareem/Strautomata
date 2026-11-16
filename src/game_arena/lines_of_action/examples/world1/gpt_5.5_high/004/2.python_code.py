
import time

N = 8
WIN_SCORE = 1_000_000
INF = 1_000_000_000
TIME_LIMIT = 0.85

DIRS = (
    (-1, 0), (1, 0), (0, -1), (0, 1),
    (-1, -1), (1, 1), (-1, 1), (1, -1)
)

NEIGHBORS = (
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1)
)


class SearchTimeout(Exception):
    pass


def policy(board) -> str:
    """
    Return a legal Lines of Action move in the format:
    "from_row,from_col:to_row,to_col"
    """
    try:
        b = normalize_board(board)
        legal = generate_moves(b)

        if not legal:
            return "0,0:0,0"

        deadline = time.perf_counter() + TIME_LIMIT

        # If we can win immediately, do it.
        for m in order_moves_fast(b, legal):
            nb = make_move_unflipped(b, m)
            if connected_side(nb, 1):
                return move_to_string(m)

        ordered_root = static_order_root(b, legal, deadline)
        best_move = ordered_root[0]

        if len(ordered_root) == 1:
            return move_to_string(best_move)

        tt = {}
        nodes = [0]

        # Iterative deepening. Depth 3 is usually reached; deeper in quieter positions.
        for depth in range(1, 7):
            if time.perf_counter() > deadline:
                break
            try:
                score, candidate = search_root(
                    b, ordered_root, depth, deadline, tt, nodes, best_move
                )
                best_move = candidate

                # A forced/visible win is good enough.
                if score >= WIN_SCORE // 2:
                    break
            except SearchTimeout:
                break

        return move_to_string(best_move)

    except Exception:
        return fallback_move(board)


def normalize_board(board):
    return tuple(tuple(int(board[r][c]) for c in range(N)) for r in range(N))


def move_to_string(m):
    fr, fc, tr, tc = m
    return f"{fr},{fc}:{tr},{tc}"


def fallback_move(board):
    try:
        b = normalize_board(board)
        moves = generate_moves(b)
        if moves:
            return move_to_string(moves[0])
    except Exception:
        pass
    return "0,0:0,0"


def generate_moves(b):
    row_counts = [0] * N
    col_counts = [0] * N
    diag1_counts = [0] * 15  # r - c + 7
    diag2_counts = [0] * 15  # r + c

    for r in range(N):
        row = b[r]
        for c in range(N):
            if row[c] != 0:
                row_counts[r] += 1
                col_counts[c] += 1
                diag1_counts[r - c + 7] += 1
                diag2_counts[r + c] += 1

    moves = []

    for r in range(N):
        for c in range(N):
            if b[r][c] != 1:
                continue

            for dr, dc in DIRS:
                if dr == 0:
                    dist = row_counts[r]
                elif dc == 0:
                    dist = col_counts[c]
                elif dr == dc:
                    dist = diag1_counts[r - c + 7]
                else:
                    dist = diag2_counts[r + c]

                tr = r + dr * dist
                tc = c + dc * dist

                if tr < 0 or tr >= N or tc < 0 or tc >= N:
                    continue

                # Cannot land on our own piece.
                if b[tr][tc] == 1:
                    continue

                # Cannot jump over enemy pieces. Destination enemy is capturable.
                blocked = False
                for step in range(1, dist):
                    rr = r + dr * step
                    cc = c + dc * step
                    if b[rr][cc] == -1:
                        blocked = True
                        break

                if not blocked:
                    moves.append((r, c, tr, tc))

    return moves


def make_move_unflipped(b, m):
    fr, fc, tr, tc = m
    rows = list(b)

    if fr == tr:
        row = list(rows[fr])
        row[fc] = 0
        row[tc] = 1
        rows[fr] = tuple(row)
    else:
        row_from = list(rows[fr])
        row_to = list(rows[tr])
        row_from[fc] = 0
        row_to[tc] = 1
        rows[fr] = tuple(row_from)
        rows[tr] = tuple(row_to)

    return tuple(rows)


def flip_board(b):
    return tuple(tuple(-x for x in row) for row in b)


def count_and_connected(b, side):
    count = 0
    start = None

    for r in range(N):
        for c in range(N):
            if b[r][c] == side:
                count += 1
                if start is None:
                    start = (r, c)

    if count <= 1:
        return count, True

    seen = 1
    sr, sc = start
    visited = [[False] * N for _ in range(N)]
    visited[sr][sc] = True
    stack = [(sr, sc)]

    while stack:
        r, c = stack.pop()
        for dr, dc in NEIGHBORS:
            nr = r + dr
            nc = c + dc
            if 0 <= nr < N and 0 <= nc < N:
                if not visited[nr][nc] and b[nr][nc] == side:
                    visited[nr][nc] = True
                    seen += 1
                    if seen == count:
                        return count, True
                    stack.append((nr, nc))

    return count, False


def connected_side(b, side):
    n, conn = count_and_connected(b, side)
    return n > 0 and conn


def terminal_value(b, depth):
    my_n, my_conn = count_and_connected(b, 1)
    if my_n == 0:
        return -WIN_SCORE - depth

    op_n, op_conn = count_and_connected(b, -1)
    if op_n == 0:
        return WIN_SCORE + depth

    if my_conn:
        return WIN_SCORE + depth

    if op_conn:
        return -WIN_SCORE - depth

    return None


def stats_for_side(b, side):
    positions = []
    min_r = N
    max_r = -1
    min_c = N
    max_c = -1
    center_sum = 0
    edge_count = 0

    for r in range(N):
        for c in range(N):
            if b[r][c] == side:
                positions.append((r, c))
                if r < min_r:
                    min_r = r
                if r > max_r:
                    max_r = r
                if c < min_c:
                    min_c = c
                if c > max_c:
                    max_c = c
                center_sum += abs(2 * r - 7) + abs(2 * c - 7)
                if r == 0 or r == 7 or c == 0 or c == 7:
                    edge_count += 1

    n = len(positions)
    if n == 0:
        return (0, 0, 0, 700, 64, 64, 14, 100, 8)

    visited = [[False] * N for _ in range(N)]
    components = 0
    largest = 0

    for sr, sc in positions:
        if visited[sr][sc]:
            continue

        components += 1
        size = 1
        visited[sr][sc] = True
        stack = [(sr, sc)]

        while stack:
            r, c = stack.pop()
            for dr, dc in NEIGHBORS:
                nr = r + dr
                nc = c + dc
                if 0 <= nr < N and 0 <= nc < N:
                    if not visited[nr][nc] and b[nr][nc] == side:
                        visited[nr][nc] = True
                        size += 1
                        stack.append((nr, nc))

        if size > largest:
            largest = size

    if n >= 2:
        pair_sum = 0
        pair_count = n * (n - 1) // 2
        nearest_sum = 0

        for i in range(n):
            r1, c1 = positions[i]
            nearest = 99
            for j in range(n):
                if i == j:
                    continue
                r2, c2 = positions[j]
                d = max(abs(r1 - r2), abs(c1 - c2))
                if d < nearest:
                    nearest = d
                if j > i:
                    pair_sum += d
            nearest_sum += nearest

        pair_avg_100 = (pair_sum * 100) // pair_count
    else:
        pair_avg_100 = 0
        nearest_sum = 0

    area = (max_r - min_r + 1) * (max_c - min_c + 1)
    span = (max_r - min_r) + (max_c - min_c)

    return (
        n,
        components,
        largest,
        pair_avg_100,
        nearest_sum,
        area,
        span,
        center_sum,
        edge_count,
    )


def evaluate(b):
    term = terminal_value(b, 0)
    if term is not None:
        return term
    return evaluate_nonterminal(b)


def evaluate_nonterminal(b):
    my = stats_for_side(b, 1)
    op = stats_for_side(b, -1)

    (
        my_n,
        my_comp,
        my_largest,
        my_pair,
        my_near,
        my_area,
        my_span,
        my_center,
        my_edge,
    ) = my

    (
        op_n,
        op_comp,
        op_largest,
        op_pair,
        op_near,
        op_area,
        op_span,
        op_center,
        op_edge,
    ) = op

    if my_n == 0:
        return -WIN_SCORE
    if op_n == 0:
        return WIN_SCORE

    my_largest_pct = (my_largest * 100) // my_n
    op_largest_pct = (op_largest * 100) // op_n

    score = 0

    # Most important LOA feature: fewer connected components.
    score += 2200 * (op_comp - my_comp)

    # Prefer having more of our pieces in the largest connected mass.
    score += 10 * (my_largest_pct - op_largest_pct)

    # Prefer compact formations and make the opponent spread out.
    score += 6 * (op_pair - my_pair)
    score += 85 * (op_near - my_near)
    score += 18 * (op_area - my_area)
    score += 35 * (op_span - my_span)

    # Mild centralization/edge preference.
    score += 6 * (op_center - my_center)
    score += 20 * (op_edge - my_edge)

    # Tiny material term. Material is secondary in LOA.
    score += 4 * (my_n - op_n)

    return score


def fast_move_score(b, m):
    fr, fc, tr, tc = m
    score = 0

    if b[tr][tc] == -1:
        score += 45

    dest_adj = 0
    origin_adj = 0

    for dr, dc in NEIGHBORS:
        nr = tr + dr
        nc = tc + dc
        if 0 <= nr < N and 0 <= nc < N:
            if not (nr == fr and nc == fc) and b[nr][nc] == 1:
                dest_adj += 1

        nr = fr + dr
        nc = fc + dc
        if 0 <= nr < N and 0 <= nc < N:
            if b[nr][nc] == 1:
                origin_adj += 1

    dest_center = 14 - (abs(2 * tr - 7) + abs(2 * tc - 7))
    orig_center = 14 - (abs(2 * fr - 7) + abs(2 * fc - 7))

    score += 30 * dest_adj
    score += 4 * (8 - origin_adj)
    score += 2 * dest_center - orig_center

    return score


def order_moves_fast(b, moves, preferred=None):
    if len(moves) <= 1:
        return list(moves)

    scored = []
    for m in moves:
        s = fast_move_score(b, m)
        if preferred is not None and m == preferred:
            s += 100000
        scored.append((s, m))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [m for _, m in scored]


def has_immediate_win(b):
    for m in generate_moves(b):
        nb = make_move_unflipped(b, m)
        if connected_side(nb, 1):
            return True
    return False


def static_order_root(b, moves, deadline):
    scored = []
    check_threats = len(moves) <= 80

    for m in moves:
        nb = make_move_unflipped(b, m)

        if connected_side(nb, 1):
            s = WIN_SCORE * 2
        else:
            child = flip_board(nb)
            s = -evaluate(child)

            # Root-level tactical safety: avoid giving opponent an immediate win.
            if check_threats and time.perf_counter() < deadline - 0.18:
                if has_immediate_win(child):
                    s -= WIN_SCORE // 3

        s += fast_move_score(b, m)
        scored.append((s, m))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [m for _, m in scored]


def prioritize(moves, preferred):
    if preferred is None:
        return list(moves)
    if preferred not in moves:
        return list(moves)
    return [preferred] + [m for m in moves if m != preferred]


def search_root(b, root_moves, depth, deadline, tt, nodes, preferred):
    if time.perf_counter() > deadline:
        raise SearchTimeout()

    moves = prioritize(root_moves, preferred)

    best_score = -INF
    best_move = moves[0]
    alpha = -INF
    beta = INF

    for m in moves:
        if time.perf_counter() > deadline:
            raise SearchTimeout()

        nb = make_move_unflipped(b, m)

        # Mover wins ties/simultaneous connection by making own group connected.
        if connected_side(nb, 1):
            score = WIN_SCORE + depth
        else:
            child = flip_board(nb)
            score = -negamax(child, depth - 1, -beta, -alpha, deadline, tt, nodes)

        if score > best_score:
            best_score = score
            best_move = m

        if score > alpha:
            alpha = score

    return best_score, best_move


def negamax(b, depth, alpha, beta, deadline, tt, nodes):
    nodes[0] += 1
    if (nodes[0] & 1023) == 0 and time.perf_counter() > deadline:
        raise SearchTimeout()

    term = terminal_value(b, depth)
    if term is not None:
        return term

    if depth <= 0:
        return evaluate_nonterminal(b)

    alpha_orig = alpha
    beta_orig = beta

    key = (b, depth)
    entry = tt.get(key)
    tt_move = None

    if entry is not None:
        val, flag, tt_move = entry

        # flag: 0 exact, 1 lower bound, -1 upper bound
        if flag == 0:
            return val
        elif flag == 1:
            if val > alpha:
                alpha = val
        elif flag == -1:
            if val < beta:
                beta = val

        if alpha >= beta:
            return val

    moves = generate_moves(b)
    if not moves:
        return -WIN_SCORE - depth

    ordered = order_moves_fast(b, moves, tt_move)

    best_score = -INF
    best_move = ordered[0]

    for m in ordered:
        nb = make_move_unflipped(b, m)

        # Current mover wins immediately if this move connects them.
        if connected_side(nb, 1):
            score = WIN_SCORE + depth
        else:
            child = flip_board(nb)
            score = -negamax(child, depth - 1, -beta, -alpha, deadline, tt, nodes)

        if score > best_score:
            best_score = score
            best_move = m

        if score > alpha:
            alpha = score

        if alpha >= beta:
            break

    if best_score <= alpha_orig:
        flag = -1
    elif best_score >= beta_orig:
        flag = 1
    else:
        flag = 0

    tt[key] = (best_score, flag, best_move)
    return best_score
