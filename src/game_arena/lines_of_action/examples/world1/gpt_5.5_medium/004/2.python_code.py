
import time

BOARD_SIZE = 8
WIN_SCORE = 1_000_000
INF = 10_000_000

DIRECTIONS = (
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
)

NEIGHBORS = DIRECTIONS

PAIR_DIRS = (
    (0, 1),
    (1, -1),
    (1, 0),
    (1, 1),
)


class SearchTimeout(Exception):
    pass


def move_to_string(move):
    fr, fc, tr, tc = move
    return f"{fr},{fc}:{tr},{tc}"


def generate_moves(board, side):
    row_counts = [0] * 8
    col_counts = [0] * 8
    diag_counts = [0] * 15      # r - c + 7
    anti_counts = [0] * 15      # r + c
    pieces = []

    for r in range(8):
        row = board[r]
        for c in range(8):
            if row[c] != 0:
                row_counts[r] += 1
                col_counts[c] += 1
                diag_counts[r - c + 7] += 1
                anti_counts[r + c] += 1
                if row[c] == side:
                    pieces.append((r, c))

    moves = []
    enemy = -side

    for r, c in pieces:
        for dr, dc in DIRECTIONS:
            if dr == 0:
                distance = row_counts[r]
            elif dc == 0:
                distance = col_counts[c]
            elif dr == dc:
                distance = diag_counts[r - c + 7]
            else:
                distance = anti_counts[r + c]

            tr = r + dr * distance
            tc = c + dc * distance

            if not (0 <= tr < 8 and 0 <= tc < 8):
                continue

            if board[tr][tc] == side:
                continue

            blocked = False
            for step in range(1, distance):
                rr = r + dr * step
                cc = c + dc * step
                if board[rr][cc] == enemy:
                    blocked = True
                    break

            if not blocked:
                moves.append((r, c, tr, tc))

    return moves


def apply_move(board, move, side):
    fr, fc, tr, tc = move
    captured = board[tr][tc]
    board[fr][fc] = 0
    board[tr][tc] = side
    return captured


def undo_move(board, move, side, captured):
    fr, fc, tr, tc = move
    board[fr][fc] = side
    board[tr][tc] = captured


def is_connected(board, side):
    total = 0
    start = None

    for r in range(8):
        for c in range(8):
            if board[r][c] == side:
                total += 1
                if start is None:
                    start = (r, c)

    if total == 0:
        return False
    if total == 1:
        return True

    visited = [[False] * 8 for _ in range(8)]
    stack = [start]
    visited[start[0]][start[1]] = True
    seen = 0

    while stack:
        r, c = stack.pop()
        seen += 1

        for dr, dc in NEIGHBORS:
            nr = r + dr
            nc = c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                if not visited[nr][nc] and board[nr][nc] == side:
                    visited[nr][nc] = True
                    stack.append((nr, nc))

    return seen == total


def terminal_score(board, last_mover, depth_remaining):
    own_connected = is_connected(board, 1)
    opp_connected = is_connected(board, -1)

    if own_connected and opp_connected:
        if last_mover == 1:
            return WIN_SCORE + depth_remaining * 100
        else:
            return -WIN_SCORE - depth_remaining * 100

    if own_connected:
        return WIN_SCORE + depth_remaining * 100

    if opp_connected:
        return -WIN_SCORE - depth_remaining * 100

    return None


def structure_features(board, side):
    positions = []
    occupied = [[False] * 8 for _ in range(8)]

    for r in range(8):
        for c in range(8):
            if board[r][c] == side:
                positions.append((r, c))
                occupied[r][c] = True

    n = len(positions)

    if n == 0:
        return -10000.0

    if n == 1:
        return 10000.0

    visited = [[False] * 8 for _ in range(8)]
    components = 0
    largest = 0

    for sr, sc in positions:
        if visited[sr][sc]:
            continue

        components += 1
        count = 0
        stack = [(sr, sc)]
        visited[sr][sc] = True

        while stack:
            r, c = stack.pop()
            count += 1

            for dr, dc in NEIGHBORS:
                nr = r + dr
                nc = c + dc
                if 0 <= nr < 8 and 0 <= nc < 8:
                    if not visited[nr][nc] and occupied[nr][nc]:
                        visited[nr][nc] = True
                        stack.append((nr, nc))

        if count > largest:
            largest = count

    min_r = min(r for r, _ in positions)
    max_r = max(r for r, _ in positions)
    min_c = min(c for _, c in positions)
    max_c = max(c for _, c in positions)

    box_area = (max_r - min_r + 1) * (max_c - min_c + 1)

    pair_distance = 0
    pair_count = 0
    for i in range(n):
        r1, c1 = positions[i]
        for j in range(i + 1, n):
            r2, c2 = positions[j]
            pair_distance += max(abs(r1 - r2), abs(c1 - c2))
            pair_count += 1

    avg_pair_distance = pair_distance / pair_count if pair_count else 0.0

    center_distance = 0.0
    for r, c in positions:
        center_distance += abs(r - 3.5) + abs(c - 3.5)
    center_distance /= n

    adjacent_edges = 0
    for r, c in positions:
        for dr, dc in PAIR_DIRS:
            nr = r + dr
            nc = c + dc
            if 0 <= nr < 8 and 0 <= nc < 8 and occupied[nr][nc]:
                adjacent_edges += 1

    score = 0.0

    # The main goal is connectivity.
    score -= 1200.0 * (components - 1)
    score += 700.0 * (largest / n)

    # Prefer dense, mutually close formations.
    score += 45.0 * adjacent_edges
    score -= 55.0 * avg_pair_distance
    score -= 10.0 * box_area

    # Mild preference for central formations.
    score -= 4.0 * center_distance

    # Tiny stability preference.
    score += 2.0 * n

    return score


def evaluate(board):
    return structure_features(board, 1) - structure_features(board, -1)


def move_order_score(board, move, side):
    fr, fc, tr, tc = move

    score = 0.0

    if board[tr][tc] == -side:
        score += 1000.0

    neighbor_count = 0
    for dr, dc in NEIGHBORS:
        nr = tr + dr
        nc = tc + dc
        if 0 <= nr < 8 and 0 <= nc < 8 and board[nr][nc] == side:
            neighbor_count += 1

    old_center = abs(fr - 3.5) + abs(fc - 3.5)
    new_center = abs(tr - 3.5) + abs(tc - 3.5)

    score += 80.0 * neighbor_count
    score += 5.0 * (old_center - new_center)

    return score


def policy(board) -> str:
    # Convert possible numpy arrays or tuples into a mutable plain Python board.
    b = [list(map(int, row)) for row in board]

    legal_moves = generate_moves(b, 1)

    # In a valid non-terminal Lines of Action position this should not happen.
    # If it does, no legal move string exists; return a syntactically valid fallback.
    if not legal_moves:
        return "0,0:0,0"

    # Always have a legal move ready in case time expires.
    best_completed_move = legal_moves[0]

    # First, take an immediate winning move.
    for move in legal_moves:
        captured = apply_move(b, move, 1)
        score = terminal_score(b, 1, 0)
        undo_move(b, move, 1, captured)

        if score is not None and score > 0:
            return move_to_string(move)

    start_time = time.perf_counter()
    deadline = start_time + 0.92
    nodes = 0

    def check_time():
        if time.perf_counter() > deadline:
            raise SearchTimeout()

    def alphabeta(depth, alpha, beta, side):
        nonlocal nodes

        nodes += 1
        if (nodes & 255) == 0:
            check_time()

        term = terminal_score(b, -side, depth)
        if term is not None:
            return term

        if depth <= 0:
            return evaluate(b)

        moves = generate_moves(b, side)
        if not moves:
            return evaluate(b)

        moves.sort(key=lambda m: move_order_score(b, m, side), reverse=True)

        if side == 1:
            value = -INF

            for move in moves:
                captured = apply_move(b, move, side)
                score = alphabeta(depth - 1, alpha, beta, -side)
                undo_move(b, move, side, captured)

                if score > value:
                    value = score
                if value > alpha:
                    alpha = value
                if alpha >= beta:
                    break

            return value

        else:
            value = INF

            for move in moves:
                captured = apply_move(b, move, side)
                score = alphabeta(depth - 1, alpha, beta, -side)
                undo_move(b, move, side, captured)

                if score < value:
                    value = score
                if value < beta:
                    beta = value
                if alpha >= beta:
                    break

            return value

    ordered_root = sorted(
        legal_moves,
        key=lambda m: move_order_score(b, m, 1),
        reverse=True,
    )

    max_depth = 5

    for depth in range(1, max_depth + 1):
        try:
            check_time()

            alpha = -INF
            beta = INF
            depth_best_move = ordered_root[0]
            depth_best_score = -INF
            scored_moves = []

            for move in ordered_root:
                check_time()

                captured = apply_move(b, move, 1)
                score = alphabeta(depth - 1, alpha, beta, -1)
                undo_move(b, move, 1, captured)

                scored_moves.append((score, move))

                if score > depth_best_score:
                    depth_best_score = score
                    depth_best_move = move

                if score > alpha:
                    alpha = score

            best_completed_move = depth_best_move

            # Reorder root moves for the next iteration.
            scored_moves.sort(key=lambda x: x[0], reverse=True)
            ordered_root = [m for _, m in scored_moves]

            # No need to search deeper if a forced immediate/near win is found.
            if depth_best_score > WIN_SCORE // 2:
                break

        except SearchTimeout:
            break

    return move_to_string(best_completed_move)
