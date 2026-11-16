
import time


class TimeoutException(Exception):
    pass


TIME_LIMIT = 0.85
WIN = 1000000
INF = 1000000000

# Precompute 8-neighbour indices for the flat 64-cell board.
NEIGHBORS = [[] for _ in range(64)]
for r in range(8):
    for c in range(8):
        i = r * 8 + c
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr = r + dr
                nc = c + dc
                if 0 <= nr < 8 and 0 <= nc < 8:
                    NEIGHBORS[i].append(nr * 8 + nc)

# Directions: (delta_row, delta_col, line_type)
# line_type is one of: row, col, diag1 (r-c constant), diag2 (r+c constant)
DIRS = [
    (0, 1, 'row'),
    (0, -1, 'row'),
    (1, 0, 'col'),
    (-1, 0, 'col'),
    (1, 1, 'diag1'),
    (-1, -1, 'diag1'),
    (1, -1, 'diag2'),
    (-1, 1, 'diag2'),
]


def legal_moves(board):
    """Generate all legal moves for the side to move (+1)."""
    row_counts = [0] * 8
    col_counts = [0] * 8
    diag1_counts = {}
    diag2_counts = {}

    for r in range(8):
        for c in range(8):
            i = r * 8 + c
            if board[i] != 0:
                row_counts[r] += 1
                col_counts[c] += 1
                diag1_counts[r - c] = diag1_counts.get(r - c, 0) + 1
                diag2_counts[r + c] = diag2_counts.get(r + c, 0) + 1

    moves = []
    for idx in range(64):
        if board[idx] != 1:
            continue

        r = idx // 8
        c = idx % 8

        for dr, dc, typ in DIRS:
            if typ == 'row':
                total = row_counts[r]
            elif typ == 'col':
                total = col_counts[c]
            elif typ == 'diag1':
                total = diag1_counts[r - c]
            else:
                total = diag2_counts[r + c]

            tr = r + dr * total
            tc = c + dc * total

            if tr < 0 or tr >= 8 or tc < 0 or tc >= 8:
                continue

            tidx = tr * 8 + tc
            if board[tidx] == 1:
                continue

            step = dr * 8 + dc
            valid = True
            for k in range(1, total):
                if board[idx + k * step] == -1:
                    valid = False
                    break

            if valid:
                moves.append((r, c, tr, tc))

    return moves


def is_connected(board, color):
    """Return True if all pieces of the given color form one 8-connected group."""
    first = -1
    total = 0
    for i in range(64):
        if board[i] == color:
            total += 1
            if first == -1:
                first = i

    if total == 0:
        return False
    if total == 1:
        return True

    visited = [False] * 64
    visited[first] = True
    stack = [first]
    found = 1

    while stack:
        idx = stack.pop()
        for ni in NEIGHBORS[idx]:
            if board[ni] == color and not visited[ni]:
                visited[ni] = True
                found += 1
                if found == total:
                    return True
                stack.append(ni)

    return found == total


def color_stats(board, color):
    """Return (component_count, avg_distance_from_centroid, piece_count)."""
    positions = []
    for i in range(64):
        if board[i] == color:
            positions.append(i)

    n = len(positions)
    if n == 0:
        return 0, 0.0, 0
    if n == 1:
        return 1, 0.0, 1

    visited = [False] * 64
    comps = 0

    for i in positions:
        if not visited[i]:
            comps += 1
            stack = [i]
            visited[i] = True
            while stack:
                idx = stack.pop()
                for ni in NEIGHBORS[idx]:
                    if board[ni] == color and not visited[ni]:
                        visited[ni] = True
                        stack.append(ni)

    sum_r = 0
    sum_c = 0
    for i in positions:
        sum_r += i // 8
        sum_c += i % 8

    mean_r = sum_r / n
    mean_c = sum_c / n

    sq = 0.0
    for i in positions:
        r = i // 8
        c = i % 8
        sq += (r - mean_r) * (r - mean_r) + (c - mean_c) * (c - mean_c)

    return comps, sq / n, n


def evaluate(board):
    """Evaluate from the perspective of the side to move (+1)."""
    own_comp, own_avg, own_n = color_stats(board, 1)

    if own_n == 0:
        return -WIN
    if own_comp == 1:
        return WIN

    opp_comp, opp_avg, opp_n = color_stats(board, -1)

    if opp_n == 0:
        return WIN
    if opp_comp == 1:
        return -WIN

    score = 1000.0 * (opp_comp - own_comp)
    score += 10.0 * (opp_avg - own_avg)
    score += 2.0 * (opp_n - own_n)

    return score


def order_score(board, move):
    """Cheap move-ordering heuristic: captures first, then central moves."""
    _, _, tr, tc = move
    tidx = tr * 8 + tc

    score = 0.0
    if board[tidx] == -1:
        score += 1000.0

    # Prefer moving toward the centre.
    score -= abs(tr - 3.5) + abs(tc - 3.5)
    return score


def negamax(board, depth, alpha, beta, deadline):
    """Negamax with alpha-beta pruning."""
    if time.time() > deadline:
        raise TimeoutException()

    if depth == 0:
        return evaluate(board)

    moves = legal_moves(board)
    if not moves:
        return -WIN

    moves.sort(key=lambda m: order_score(board, m), reverse=True)

    value = -INF

    for move in moves:
        if time.time() > deadline:
            raise TimeoutException()

        fr, fc, tr, tc = move
        fidx = fr * 8 + fc
        tidx = tr * 8 + tc

        new_board = board.copy()
        captured = (new_board[tidx] == -1)
        new_board[fidx] = 0
        new_board[tidx] = 1

        # The moving side wins immediately.
        if is_connected(new_board, 1):
            return WIN

        # Capturing the last opponent piece also wins immediately.
        if captured and new_board.count(-1) == 0:
            return WIN

        # If the capture connected all opponent pieces, this move loses.
        if captured and is_connected(new_board, -1):
            score = -WIN
        else:
            child = [-x for x in new_board]
            score = -negamax(child, depth - 1, -beta, -alpha, deadline)

        if score > value:
            value = score
        if value > alpha:
            alpha = value
        if alpha >= beta:
            break

    return value


def search_root(board, depth, deadline):
    """Search root and return the best move and score."""
    moves = legal_moves(board)
    if not moves:
        return None, -WIN

    moves.sort(key=lambda m: order_score(board, m), reverse=True)

    alpha = -INF
    beta = INF
    best_move = None

    for move in moves:
        if time.time() > deadline:
            raise TimeoutException()

        fr, fc, tr, tc = move
        fidx = fr * 8 + fc
        tidx = tr * 8 + tc

        new_board = board.copy()
        captured = (new_board[tidx] == -1)
        new_board[fidx] = 0
        new_board[tidx] = 1

        if is_connected(new_board, 1):
            score = WIN
        elif captured and new_board.count(-1) == 0:
            score = WIN
        elif captured and is_connected(new_board, -1):
            score = -WIN
        else:
            child = [-x for x in new_board]
            score = -negamax(child, depth - 1, -beta, -alpha, deadline)

        if score > alpha:
            alpha = score
            best_move = move

        if alpha >= beta or alpha >= WIN:
            break

    return best_move, alpha


def policy(board):
    """Return the next move string for the current player."""
    flat = [board[r][c] for r in range(8) for c in range(8)]

    legal = legal_moves(flat)
    if not legal:
        # Extremely unlikely fallback. In normal LOA positions legal moves exist.
        for i in range(64):
            if flat[i] == 1:
                r = i // 8
                c = i % 8
                for dr, dc in ((0, 1), (1, 0), (1, 1), (0, -1), (-1, 0), (-1, -1), (1, -1), (-1, 1)):
                    nr = r + dr
                    nc = c + dc
                    if 0 <= nr < 8 and 0 <= nc < 8 and flat[nr * 8 + nc] != 1:
                        return f"{r},{c}:{nr},{nc}"
        return "0,0:1,1"

    best_move = legal[0]
    start_time = time.time()
    deadline = start_time + TIME_LIMIT

    depth = 1
    try:
        while True:
            if time.time() > deadline:
                break

            move, score = search_root(flat, depth, deadline)
            if move is not None:
                best_move = move

            if score >= WIN:
                break

            depth += 1
            if depth > 20:
                break
    except TimeoutException:
        pass

    fr, fc, tr, tc = best_move
    return f"{fr},{fc}:{tr},{tc}"
