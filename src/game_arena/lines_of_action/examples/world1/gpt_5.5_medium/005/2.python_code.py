
import time

N = 8
WIN = 10000000
INF = 100000000

DIRS = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
]


class Timeout(Exception):
    pass


def policy(board) -> str:
    start = time.perf_counter()
    deadline = start + 0.92

    b = [[int(board[r][c]) for c in range(N)] for r in range(N)]
    moves = gen_moves(b)

    if not moves:
        return "0,0:0,0"

    root_scores = {}
    best_move = moves[0]
    best_score = -INF

    for m in moves:
        played = apply_move_no_flip(b, m)
        my_conn = is_connected_color(played, 1)
        opp_conn = is_connected_color(played, -1)

        if my_conn:
            return move_to_str(m)

        if opp_conn:
            s = -WIN
        else:
            child = flip_board(played)
            s = -evaluate(child)

        root_scores[m] = s
        if s > best_score:
            best_score = s
            best_move = m

    max_depth = 5
    tt = {}

    for depth in range(1, max_depth + 1):
        try:
            ordered = sorted(
                moves,
                key=lambda mv: (mv == best_move, root_scores.get(mv, 0), order_score(b, mv)),
                reverse=True,
            )

            local_best = best_move
            local_score = -INF
            alpha = -INF
            beta = INF

            for m in ordered:
                if time.perf_counter() > deadline:
                    raise Timeout()

                child = make_move(b, m)
                val = -search(child, depth - 1, -beta, -alpha, deadline, tt)

                if val > local_score:
                    local_score = val
                    local_best = m

                if val > alpha:
                    alpha = val

            best_move = local_best
            best_score = local_score

            if best_score > WIN // 2:
                break

        except Timeout:
            break

    return move_to_str(best_move)


def move_to_str(m):
    return f"{m[0]},{m[1]}:{m[2]},{m[3]}"


def precompute_counts(board):
    row = [0] * N
    col = [0] * N
    d1 = [0] * 15
    d2 = [0] * 15

    for r in range(N):
        for c in range(N):
            if board[r][c] != 0:
                row[r] += 1
                col[c] += 1
                d1[r - c + 7] += 1
                d2[r + c] += 1

    return row, col, d1, d2


def gen_moves(board):
    row, col, d1, d2 = precompute_counts(board)
    moves = []

    for r in range(N):
        for c in range(N):
            if board[r][c] != 1:
                continue

            for dr, dc in DIRS:
                if dr == 0:
                    dist = row[r]
                elif dc == 0:
                    dist = col[c]
                elif dr == dc:
                    dist = d1[r - c + 7]
                else:
                    dist = d2[r + c]

                tr = r + dr * dist
                tc = c + dc * dist

                if tr < 0 or tr >= N or tc < 0 or tc >= N:
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


def apply_move_no_flip(board, m):
    r, c, tr, tc = m
    nb = [row[:] for row in board]
    nb[r][c] = 0
    nb[tr][tc] = 1
    return nb


def flip_board(board):
    return [[-board[r][c] for c in range(N)] for r in range(N)]


def make_move(board, m):
    r, c, tr, tc = m
    nb = [row[:] for row in board]
    nb[r][c] = 0
    nb[tr][tc] = 1

    for i in range(N):
        row = nb[i]
        for j in range(N):
            row[j] = -row[j]

    return nb


def search(board, depth, alpha, beta, deadline, tt):
    if time.perf_counter() > deadline:
        raise Timeout()

    term = terminal_score(board)
    if term is not None:
        if term > 0:
            return term + depth
        return term - depth

    if depth <= 0:
        return evaluate(board)

    key = None
    if depth >= 2:
        key = (depth, tuple(x for row in board for x in row))
        found = tt.get(key)
        if found is not None:
            return found

    moves = gen_moves(board)
    if not moves:
        return -WIN + depth

    moves.sort(key=lambda mv: order_score(board, mv), reverse=True)

    best = -INF
    completed = True

    for m in moves:
        child = make_move(board, m)
        val = -search(child, depth - 1, -beta, -alpha, deadline, tt)

        if val > best:
            best = val

        if val > alpha:
            alpha = val

        if alpha >= beta:
            completed = False
            break

    if completed and key is not None:
        tt[key] = best

    return best


def terminal_score(board):
    my_conn = is_connected_color(board, 1)
    opp_conn = is_connected_color(board, -1)

    # If both are connected after the previous move, the previous mover wins.
    # In this perspective, the previous mover is the opponent.
    if opp_conn:
        return -WIN
    if my_conn:
        return WIN

    return None


def get_coords(board, color):
    coords = []
    for r in range(N):
        for c in range(N):
            if board[r][c] == color:
                coords.append((r, c))
    return coords


def is_connected_color(board, color):
    coords = get_coords(board, color)
    n = len(coords)

    if n <= 1:
        return True

    sr, sc = coords[0]
    visited = [[False] * N for _ in range(N)]
    visited[sr][sc] = True
    stack = [(sr, sc)]
    count = 0

    while stack:
        r, c = stack.pop()
        count += 1

        for dr, dc in DIRS:
            nr = r + dr
            nc = c + dc

            if 0 <= nr < N and 0 <= nc < N:
                if not visited[nr][nc] and board[nr][nc] == color:
                    visited[nr][nc] = True
                    stack.append((nr, nc))

    return count == n


def component_info(board, color):
    coords = get_coords(board, color)
    n = len(coords)

    if n == 0:
        return 0, 0, 0

    visited = [[False] * N for _ in range(N)]
    components = 0
    largest = 0

    for sr, sc in coords:
        if visited[sr][sc]:
            continue

        components += 1
        visited[sr][sc] = True
        stack = [(sr, sc)]
        size = 0

        while stack:
            r, c = stack.pop()
            size += 1

            for dr, dc in DIRS:
                nr = r + dr
                nc = c + dc

                if 0 <= nr < N and 0 <= nc < N:
                    if not visited[nr][nc] and board[nr][nc] == color:
                        visited[nr][nc] = True
                        stack.append((nr, nc))

        if size > largest:
            largest = size

    return n, components, largest


def feature_score(board, color):
    coords = get_coords(board, color)
    n = len(coords)

    if n == 0:
        return -WIN // 2

    if n == 1:
        return WIN // 2

    _, comps, largest = component_info(board, color)

    min_r = min(r for r, _ in coords)
    max_r = max(r for r, _ in coords)
    min_c = min(c for _, c in coords)
    max_c = max(c for _, c in coords)
    area = (max_r - min_r + 1) * (max_c - min_c + 1)

    pair_dist = 0
    pair_count = 0
    for i in range(n):
        r1, c1 = coords[i]
        for j in range(i + 1, n):
            r2, c2 = coords[j]
            pair_dist += max(abs(r1 - r2), abs(c1 - c2))
            pair_count += 1

    avg_dist = pair_dist / pair_count if pair_count else 0

    center = 0.0
    edge_count = 0
    adjacency = 0

    for r, c in coords:
        center += 6.0 - abs(r - 3.5) - abs(c - 3.5)

        if r == 0 or r == 7 or c == 0 or c == 7:
            edge_count += 1

        # Count each friendly adjacency once.
        for dr, dc in ((1, 0), (0, 1), (1, 1), (1, -1)):
            nr = r + dr
            nc = c + dc
            if 0 <= nr < N and 0 <= nc < N and board[nr][nc] == color:
                adjacency += 1

    center /= n

    score = 0.0
    score += 1400.0 * (largest / n)
    score -= 420.0 * comps
    score -= 34.0 * avg_dist
    score -= 8.0 * area
    score += 42.0 * adjacency
    score += 12.0 * center
    score -= 18.0 * edge_count

    return score


def evaluate(board):
    term = terminal_score(board)
    if term is not None:
        return term

    my = feature_score(board, 1)
    opp = feature_score(board, -1)

    return int(my - opp)


def order_score(board, m):
    r, c, tr, tc = m
    score = 0

    if board[tr][tc] == -1:
        score += 500

    adj = 0
    for dr, dc in DIRS:
        nr = tr + dr
        nc = tc + dc
        if 0 <= nr < N and 0 <= nc < N:
            if (nr, nc) != (r, c) and board[nr][nc] == 1:
                adj += 1

    old_adj = 0
    for dr, dc in DIRS:
        nr = r + dr
        nc = c + dc
        if 0 <= nr < N and 0 <= nc < N:
            if board[nr][nc] == 1:
                old_adj += 1

    score += 80 * adj
    score += 25 * max(0, adj - old_adj)

    center_dist = abs(tr - 3.5) + abs(tc - 3.5)
    score += int(40 - 8 * center_dist)

    if tr == 0 or tr == 7 or tc == 0 or tc == 7:
        score -= 35

    return score
