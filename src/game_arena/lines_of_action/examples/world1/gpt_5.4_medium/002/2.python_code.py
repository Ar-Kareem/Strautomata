
import time

DIRS = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
]

NEIGHBORS = DIRS
WIN_SCORE = 10**9


def format_move(move):
    fr, fc, tr, tc = move
    return f"{fr},{fc}:{tr},{tc}"


def is_edge(r, c):
    return r == 0 or r == 7 or c == 0 or c == 7


def flip_board(board):
    return [[-board[r][c] for c in range(8)] for r in range(8)]


def apply_move_raw(board, move):
    fr, fc, tr, tc = move
    new_board = [row[:] for row in board]
    new_board[fr][fc] = 0
    new_board[tr][tc] = 1
    return new_board


def legal_moves(board):
    row_counts = [0] * 8
    col_counts = [0] * 8
    diag_counts = [0] * 15      # r - c + 7
    anti_counts = [0] * 15      # r + c

    for r in range(8):
        row = board[r]
        for c in range(8):
            if row[c] != 0:
                row_counts[r] += 1
                col_counts[c] += 1
                diag_counts[r - c + 7] += 1
                anti_counts[r + c] += 1

    moves = []
    for r in range(8):
        row = board[r]
        for c in range(8):
            if row[c] != 1:
                continue

            for dr, dc in DIRS:
                if dr == 0:
                    dist = row_counts[r]
                elif dc == 0:
                    dist = col_counts[c]
                elif dr == dc:
                    dist = diag_counts[r - c + 7]
                else:
                    dist = anti_counts[r + c]

                tr = r + dr * dist
                tc = c + dc * dist

                if not (0 <= tr < 8 and 0 <= tc < 8):
                    continue
                if board[tr][tc] == 1:
                    continue

                rr, cc = r, c
                ok = True
                for _ in range(1, dist):
                    rr += dr
                    cc += dc
                    if board[rr][cc] == -1:
                        ok = False
                        break

                if ok:
                    moves.append((r, c, tr, tc))

    return moves


def is_connected(board, val):
    positions = []
    for r in range(8):
        for c in range(8):
            if board[r][c] == val:
                positions.append((r, c))

    if len(positions) <= 1:
        return True

    pos_set = set(positions)
    stack = [positions[0]]
    seen = {positions[0]}

    while stack:
        r, c = stack.pop()
        for dr, dc in NEIGHBORS:
            nxt = (r + dr, c + dc)
            if nxt in pos_set and nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)

    return len(seen) == len(positions)


def terminal_score(board):
    my_conn = is_connected(board, 1)
    opp_conn = is_connected(board, -1)

    if my_conn and opp_conn:
        return -WIN_SCORE
    if my_conn:
        return WIN_SCORE
    if opp_conn:
        return -WIN_SCORE
    return None


def analyze_player(board, val):
    positions = []
    center = 0
    edge = 0
    sum_r = 0
    sum_c = 0
    min_r, min_c = 8, 8
    max_r, max_c = -1, -1

    for r in range(8):
        for c in range(8):
            if board[r][c] == val:
                positions.append((r, c))
                center += abs(2 * r - 7) + abs(2 * c - 7)
                if is_edge(r, c):
                    edge += 1
                sum_r += r
                sum_c += c
                if r < min_r:
                    min_r = r
                if r > max_r:
                    max_r = r
                if c < min_c:
                    min_c = c
                if c > max_c:
                    max_c = c

    n = len(positions)
    if n == 0:
        return (0, 0, 0, 0, 0, 0, 0, 0)

    pos_set = set(positions)

    adj = 0
    for r, c in positions:
        for dr, dc in NEIGHBORS:
            if (r + dr, c + dc) in pos_set:
                adj += 1
    adj //= 2

    remaining = set(pos_set)
    components = 0
    largest = 0

    while remaining:
        start = remaining.pop()
        components += 1
        size = 1
        stack = [start]

        while stack:
            r, c = stack.pop()
            for dr, dc in NEIGHBORS:
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    stack.append(nxt)
                    size += 1

        if size > largest:
            largest = size

    box_area = (max_r - min_r + 1) * (max_c - min_c + 1)

    spread = 0
    for r, c in positions:
        dr = r * n - sum_r
        dc = c * n - sum_c
        spread += dr * dr + dc * dc

    return (n, components, largest, box_area, center, edge, adj, spread)


def evaluate(board):
    term = terminal_score(board)
    if term is not None:
        return term

    my_n, my_comp, my_largest, my_box, my_center, my_edge, my_adj, my_spread = analyze_player(board, 1)
    op_n, op_comp, op_largest, op_box, op_center, op_edge, op_adj, op_spread = analyze_player(board, -1)

    score = 0
    score += 12000 * (op_comp - my_comp)
    score += 1000 * (my_largest - op_largest)
    score += 20 * ((my_largest * 100 // max(1, my_n)) - (op_largest * 100 // max(1, op_n)))
    score += 80 * (my_adj - op_adj)
    score += 40 * (op_box - my_box)
    score += 12 * (op_center - my_center)
    score += 10 * (op_edge - my_edge)
    score += (op_spread - my_spread) // 200

    return score


def move_order_score(board, move, pv_move=None):
    fr, fc, tr, tc = move
    score = 0

    if pv_move is not None and move == pv_move:
        score += 10**7

    if board[tr][tc] == -1:
        score += 10000

    src_center = abs(2 * fr - 7) + abs(2 * fc - 7)
    dst_center = abs(2 * tr - 7) + abs(2 * tc - 7)
    score += 20 * (src_center - dst_center)

    if is_edge(fr, fc) and not is_edge(tr, tc):
        score += 60
    if not is_edge(fr, fc) and is_edge(tr, tc):
        score -= 30

    return score


def order_moves(board, moves, pv_move=None):
    if len(moves) <= 1:
        return moves
    return sorted(moves, key=lambda m: move_order_score(board, m, pv_move), reverse=True)


def policy(board) -> str:
    board = [list(map(int, row)) for row in board]

    moves = legal_moves(board)
    if not moves:
        # Extremely unlikely in valid arena positions.
        # Return something deterministic if ever reached.
        return "0,0:0,0"

    fallback = moves[0]

    for move in moves:
        raw = apply_move_raw(board, move)
        if is_connected(raw, 1):
            return format_move(move)

    base_order = order_moves(board, moves)
    fallback = base_order[0]

    if len(base_order) == 1:
        return format_move(base_order[0])

    deadline = time.perf_counter() + 0.92
    node_counter = [0]

    class SearchTimeout(Exception):
        pass

    def check_time(force=False):
        node_counter[0] += 1
        if force or (node_counter[0] & 63) == 0:
            if time.perf_counter() >= deadline:
                raise SearchTimeout

    def negamax(pos, depth, alpha, beta):
        check_time()

        term = terminal_score(pos)
        if term is not None:
            return term

        if depth == 0:
            return evaluate(pos)

        moves_here = legal_moves(pos)
        if not moves_here:
            return -WIN_SCORE + 1

        ordered = order_moves(pos, moves_here)

        best = -WIN_SCORE
        for move in ordered:
            raw = apply_move_raw(pos, move)

            if is_connected(raw, 1):
                score = WIN_SCORE - 1
            else:
                child = flip_board(raw)
                score = -negamax(child, depth - 1, -beta, -alpha)

            if score > best:
                best = score
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break

        return best

    def root_search(pos, depth, pv_move):
        alpha = -WIN_SCORE
        beta = WIN_SCORE
        best_score = -WIN_SCORE
        best_move = fallback

        ordered = order_moves(pos, base_order, pv_move)

        for move in ordered:
            check_time()

            raw = apply_move_raw(pos, move)

            if is_connected(raw, 1):
                score = WIN_SCORE - 1
            else:
                child = flip_board(raw)
                score = -negamax(child, depth - 1, -beta, -alpha)

            if score > best_score:
                best_score = score
                best_move = move

            if score > alpha:
                alpha = score

        return best_move, best_score

    move_count = len(base_order)
    if move_count <= 8:
        max_depth = 5
    elif move_count <= 16:
        max_depth = 4
    else:
        max_depth = 3

    best_move = fallback
    pv_move = fallback

    for depth in range(1, max_depth + 1):
        try:
            check_time(force=True)
            candidate, _ = root_search(board, depth, pv_move)
            best_move = candidate
            pv_move = candidate
        except SearchTimeout:
            break

    return format_move(best_move)
