
import time

DIRS = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
]

LINK_DIRS = ((0, 1), (1, 0), (1, 1), (1, -1))

CENTER_DIST = [
    [((2 * r - 7) ** 2 + (2 * c - 7) ** 2) for c in range(8)]
    for r in range(8)
]

WIN = 10_000_000
INF = 10**18


class TimeoutSearch(Exception):
    pass


def board_key(board):
    return bytes(v + 1 for row in board for v in row)


def move_to_str(move):
    return f"{move[0]},{move[1]}:{move[2]},{move[3]}"


def line_counts(board):
    row_counts = [0] * 8
    col_counts = [0] * 8
    diag_main = [0] * 15     # r - c + 7
    diag_anti = [0] * 15     # r + c

    for r in range(8):
        br = board[r]
        for c in range(8):
            if br[c] != 0:
                row_counts[r] += 1
                col_counts[c] += 1
                diag_main[r - c + 7] += 1
                diag_anti[r + c] += 1
    return row_counts, col_counts, diag_main, diag_anti


def generate_moves(board):
    row_counts, col_counts, diag_main, diag_anti = line_counts(board)
    moves = []

    for r in range(8):
        br = board[r]
        for c in range(8):
            if br[c] != 1:
                continue

            for dr, dc in DIRS:
                if dr == 0:
                    dist = row_counts[r]
                elif dc == 0:
                    dist = col_counts[c]
                elif dr == dc:
                    dist = diag_main[r - c + 7]
                else:
                    dist = diag_anti[r + c]

                tr = r + dr * dist
                tc = c + dc * dist

                if tr < 0 or tr > 7 or tc < 0 or tc > 7:
                    continue
                if board[tr][tc] == 1:
                    continue

                blocked = False
                rr = r + dr
                cc = c + dc
                for _ in range(dist - 1):
                    if board[rr][cc] == -1:
                        blocked = True
                        break
                    rr += dr
                    cc += dc

                if not blocked:
                    moves.append((r, c, tr, tc))

    return moves


def apply_move(board, move):
    fr, fc, tr, tc = move
    nb = [row[:] for row in board]
    nb[fr][fc] = 0
    nb[tr][tc] = 1
    return nb


def flip_board(board):
    return [[-v for v in row] for row in board]


def is_connected(board, player):
    start = None
    total = 0

    for r in range(8):
        br = board[r]
        for c in range(8):
            if br[c] == player:
                total += 1
                if start is None:
                    start = (r, c)

    if total == 0:
        return False
    if total == 1:
        return True

    visited = [[False] * 8 for _ in range(8)]
    sr, sc = start
    visited[sr][sc] = True
    stack = [start]
    seen_count = 1

    while stack:
        r, c = stack.pop()
        for dr, dc in DIRS:
            rr = r + dr
            cc = c + dc
            if 0 <= rr < 8 and 0 <= cc < 8:
                if not visited[rr][cc] and board[rr][cc] == player:
                    visited[rr][cc] = True
                    seen_count += 1
                    stack.append((rr, cc))

    return seen_count == total


def component_stats(board, player):
    positions = []
    n = 0
    rs = 0.0
    cs = 0.0
    edge_count = 0
    center_sum = 0
    min_r = 8
    min_c = 8
    max_r = -1
    max_c = -1

    for r in range(8):
        br = board[r]
        for c in range(8):
            if br[c] == player:
                positions.append((r, c))
                n += 1
                rs += r
                cs += c
                center_sum += CENTER_DIST[r][c]
                if r == 0 or r == 7 or c == 0 or c == 7:
                    edge_count += 1
                if r < min_r:
                    min_r = r
                if r > max_r:
                    max_r = r
                if c < min_c:
                    min_c = c
                if c > max_c:
                    max_c = c

    if n == 0:
        return 0, 0, 0, 0, 0, 0.0, 0, 0

    avg_r = rs / n
    avg_c = cs / n
    spread = 0.0
    for r, c in positions:
        dr = r - avg_r
        dc = c - avg_c
        spread += dr * dr + dc * dc

    visited = [[False] * 8 for _ in range(8)]
    components = 0
    largest = 0

    for r, c in positions:
        if visited[r][c]:
            continue
        components += 1
        visited[r][c] = True
        stack = [(r, c)]
        size = 0

        while stack:
            x, y = stack.pop()
            size += 1
            for dr, dc in DIRS:
                xx = x + dr
                yy = y + dc
                if 0 <= xx < 8 and 0 <= yy < 8:
                    if not visited[xx][yy] and board[xx][yy] == player:
                        visited[xx][yy] = True
                        stack.append((xx, yy))

        if size > largest:
            largest = size

    links = 0
    for r, c in positions:
        for dr, dc in LINK_DIRS:
            rr = r + dr
            cc = c + dc
            if 0 <= rr < 8 and 0 <= cc < 8 and board[rr][cc] == player:
                links += 1

    area = (max_r - min_r + 1) * (max_c - min_c + 1)
    return n, components, largest, edge_count, center_sum, spread, links, area


def evaluate(board):
    my_n, my_comp, my_largest, my_edge, my_center, my_spread, my_links, my_area = component_stats(board, 1)
    op_n, op_comp, op_largest, op_edge, op_center, op_spread, op_links, op_area = component_stats(board, -1)

    if my_n == 0:
        return -WIN // 2
    if op_n == 0:
        return WIN // 2

    if my_comp == 1 and op_comp != 1:
        return WIN // 2
    if op_comp == 1 and my_comp != 1:
        return -WIN // 2

    score = 0.0
    score += 300.0 * (op_comp - my_comp)
    score += 35.0 * (my_largest - op_largest)
    score += 16.0 * (my_links - op_links)
    score += 10.0 * (op_edge - my_edge)
    score += 5.0 * (op_area - my_area)
    score += 1.0 * (op_center - my_center)
    score += 4.0 * (op_spread - my_spread)
    return score


def adjacent_count(board, r, c, ignore=None):
    cnt = 0
    for dr, dc in DIRS:
        rr = r + dr
        cc = c + dc
        if 0 <= rr < 8 and 0 <= cc < 8:
            if ignore is not None and rr == ignore[0] and cc == ignore[1]:
                continue
            if board[rr][cc] == 1:
                cnt += 1
    return cnt


def move_order_score(board, move):
    fr, fc, tr, tc = move
    score = 0.0

    if board[tr][tc] == -1:
        score += 20.0

    dest_adj = adjacent_count(board, tr, tc, ignore=(fr, fc))
    src_adj = adjacent_count(board, fr, fc)

    score += 12.0 * dest_adj
    score -= 4.0 * src_adj
    score += 0.5 * (CENTER_DIST[fr][fc] - CENTER_DIST[tr][tc])

    if fr == 0 or fr == 7 or fc == 0 or fc == 7:
        score += 3.0
    if tr == 0 or tr == 7 or tc == 0 or tc == 7:
        score -= 3.0

    return score


def order_moves(board, moves, pref_move=None):
    if len(moves) <= 1:
        return moves
    moves.sort(
        key=lambda m: ((pref_move is not None and m == pref_move), move_order_score(board, m)),
        reverse=True,
    )
    return moves


def policy(board) -> str:
    board = [list(map(int, row)) for row in board]

    root_moves = generate_moves(board)
    if not root_moves:
        for r in range(8):
            for c in range(8):
                if board[r][c] == 1:
                    return f"{r},{c}:{r},{c}"
        return "0,0:0,0"

    root_moves = order_moves(board, root_moves[:])
    best_move = root_moves[0]

    for mv in root_moves:
        nb = apply_move(board, mv)
        if is_connected(nb, 1):
            return move_to_str(mv)

    branch = len(root_moves)
    if branch <= 8:
        max_depth = 5
    elif branch <= 16:
        max_depth = 4
    elif branch <= 34:
        max_depth = 3
    else:
        max_depth = 2

    deadline = time.perf_counter() + 0.92
    tt_score = {}
    tt_move = {}
    node_counter = 0

    def touch():
        nonlocal node_counter
        node_counter += 1
        if (node_counter & 63) == 0 and time.perf_counter() >= deadline:
            raise TimeoutSearch

    def negamax(pos, depth, alpha, beta, ply):
        touch()

        bkey = board_key(pos)
        cached = tt_score.get((bkey, depth))
        if cached is not None:
            return cached

        if depth <= 0:
            val = evaluate(pos)
            tt_score[(bkey, depth)] = val
            return val

        moves = generate_moves(pos)
        if not moves:
            val = -WIN + ply
            tt_score[(bkey, depth)] = val
            return val

        pref = tt_move.get(bkey)
        moves = order_moves(pos, moves, pref)

        best = -INF
        bestm = None

        for mv in moves:
            nb = apply_move(pos, mv)

            if is_connected(nb, 1):
                score = WIN - ply
            elif is_connected(nb, -1):
                score = -WIN + ply
            else:
                score = -negamax(flip_board(nb), depth - 1, -beta, -alpha, ply + 1)

            if score > best:
                best = score
                bestm = mv
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break

        if bestm is not None:
            tt_move[bkey] = bestm
        tt_score[(bkey, depth)] = best
        return best

    def search_root(depth, pref_move):
        alpha = -INF
        beta = INF
        best = -INF
        bestm = None

        moves = order_moves(board, root_moves[:], pref_move)

        for mv in moves:
            touch()
            nb = apply_move(board, mv)

            if is_connected(nb, 1):
                score = WIN
            elif is_connected(nb, -1):
                score = -WIN
            else:
                score = -negamax(flip_board(nb), depth - 1, -beta, -alpha, 1)

            if score > best:
                best = score
                bestm = mv
            if best > alpha:
                alpha = best

        return best, bestm

    pv_move = best_move

    try:
        for depth in range(1, max_depth + 1):
            score, mv = search_root(depth, pv_move)
            if mv is not None:
                best_move = mv
                pv_move = mv
            if abs(score) >= WIN - 10:
                break
    except TimeoutSearch:
        pass

    return move_to_str(best_move)
