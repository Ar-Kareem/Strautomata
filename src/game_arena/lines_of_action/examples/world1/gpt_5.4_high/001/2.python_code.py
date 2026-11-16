
import time

SIZE = 8
DIRS = [(-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)]

WIN = 10 ** 9
INF = 10 ** 12

DEADLINE = 0.0
NODE_COUNTER = 0


class SearchTimeout(Exception):
    pass


def move_to_str(move):
    r, c, tr, tc = move
    return f"{r},{c}:{tr},{tc}"


def negate_board(board):
    return [[-x for x in row] for row in board]


def apply_move(board, move):
    r, c, tr, tc = move
    b = [row[:] for row in board]
    b[r][c] = 0
    b[tr][tc] = 1
    return b


def make_child(board, move):
    # Apply move, then switch perspective so side-to-move is again encoded as +1.
    b = apply_move(board, move)
    for r in range(SIZE):
        row = b[r]
        for c in range(SIZE):
            row[c] = -row[c]
    return b


def generate_moves(board):
    # Assumes side to move is encoded as +1.
    row_counts = [0] * SIZE
    col_counts = [0] * SIZE
    diag_counts = [0] * 15       # r - c + 7
    anti_counts = [0] * 15       # r + c
    pieces = []

    for r in range(SIZE):
        row = board[r]
        for c in range(SIZE):
            v = row[c]
            if v != 0:
                row_counts[r] += 1
                col_counts[c] += 1
                diag_counts[r - c + 7] += 1
                anti_counts[r + c] += 1
                if v == 1:
                    pieces.append((r, c))

    moves = []
    for r, c in pieces:
        for dr, dc in DIRS:
            if dr == 0:
                steps = row_counts[r]
            elif dc == 0:
                steps = col_counts[c]
            elif dr == dc:
                steps = diag_counts[r - c + 7]
            else:
                steps = anti_counts[r + c]

            tr = r + dr * steps
            tc = c + dc * steps

            if not (0 <= tr < SIZE and 0 <= tc < SIZE):
                continue
            if board[tr][tc] == 1:
                continue

            rr = r + dr
            cc = c + dc
            legal = True
            for _ in range(1, steps):
                if board[rr][cc] == -1:
                    legal = False
                    break
                rr += dr
                cc += dc

            if legal:
                moves.append((r, c, tr, tc))

    return moves


def is_connected(board, side):
    first = None
    count = 0

    for r in range(SIZE):
        row = board[r]
        for c in range(SIZE):
            if row[c] == side:
                count += 1
                if first is None:
                    first = (r, c)

    if count == 0:
        return False
    if count == 1:
        return True

    stack = [first]
    seen = {first}
    reached = 1

    while stack:
        r, c = stack.pop()
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < SIZE and 0 <= nc < SIZE and board[nr][nc] == side:
                p = (nr, nc)
                if p not in seen:
                    seen.add(p)
                    stack.append(p)
                    reached += 1

    return reached == count


def side_metrics(board, side):
    positions = []
    edge = 0
    center = 0
    sumr = 0
    sumc = 0
    sumsq = 0
    minr = SIZE
    minc = SIZE
    maxr = -1
    maxc = -1

    for r in range(SIZE):
        row = board[r]
        for c in range(SIZE):
            if row[c] == side:
                positions.append((r, c))
                sumr += r
                sumc += c
                sumsq += r * r + c * c
                center += abs(2 * r - 7) + abs(2 * c - 7)
                if r == 0 or r == 7 or c == 0 or c == 7:
                    edge += 1
                if r < minr:
                    minr = r
                if r > maxr:
                    maxr = r
                if c < minc:
                    minc = c
                if c > maxc:
                    maxc = c

    n = len(positions)
    if n == 0:
        return (0, 0, 0, 0, 0, 0, 0, 0)

    remaining = set(positions)
    comps = 0
    largest = 0

    while remaining:
        start = remaining.pop()
        comps += 1
        size = 1
        stack = [start]

        while stack:
            r, c = stack.pop()
            for dr, dc in DIRS:
                p = (r + dr, c + dc)
                if p in remaining:
                    remaining.remove(p)
                    stack.append(p)
                    size += 1

        if size > largest:
            largest = size

    pos_set = set(positions)
    adj_pairs = 0
    for r, c in positions:
        if r + 1 < SIZE and (r + 1, c) in pos_set:
            adj_pairs += 1
        if c + 1 < SIZE and (r, c + 1) in pos_set:
            adj_pairs += 1
        if r + 1 < SIZE and c + 1 < SIZE and (r + 1, c + 1) in pos_set:
            adj_pairs += 1
        if r + 1 < SIZE and c - 1 >= 0 and (r + 1, c - 1) in pos_set:
            adj_pairs += 1

    bbox = (maxr - minr + 1) * (maxc - minc + 1)
    spread = n * sumsq - sumr * sumr - sumc * sumc

    return (n, comps, largest, edge, center, spread, bbox, adj_pairs)


def terminal_status(board):
    # If both sides are connected, the side that just moved wins.
    # At this node, that is the side encoded as -1, so check -1 first.
    if is_connected(board, -1):
        return -WIN
    if is_connected(board, 1):
        return WIN
    return None


def adjacent_friends_except(board, r, c, ex_r, ex_c):
    cnt = 0
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < SIZE and 0 <= nc < SIZE:
            if nr == ex_r and nc == ex_c:
                continue
            if board[nr][nc] == 1:
                cnt += 1
    return cnt


def move_order_score(board, move):
    r, c, tr, tc = move
    score = 0

    if board[tr][tc] == -1:
        score += 80

    score += 12 * adjacent_friends_except(board, tr, tc, r, c)
    score -= 4 * adjacent_friends_except(board, r, c, tr, tc)

    src_center = abs(2 * r - 7) + abs(2 * c - 7)
    dst_center = abs(2 * tr - 7) + abs(2 * tc - 7)
    score += src_center - dst_center

    if r == 0 or r == 7 or c == 0 or c == 7:
        score += 4
    if tr == 0 or tr == 7 or tc == 0 or tc == 7:
        score -= 4

    return score


def ordered_moves(board, moves):
    if len(moves) <= 1:
        return moves
    scored = [(move_order_score(board, m), m) for m in moves]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [m for _, m in scored]


def evaluate(board):
    own_n, own_comp, own_largest, own_edge, own_center, own_spread, own_bbox, own_adj = side_metrics(board, 1)
    opp_n, opp_comp, opp_largest, opp_edge, opp_center, opp_spread, opp_bbox, opp_adj = side_metrics(board, -1)

    if own_n == 0:
        return -WIN // 2
    if opp_n == 0:
        return WIN // 2

    own_ratio = (10 * own_largest) // own_n
    opp_ratio = (10 * opp_largest) // opp_n

    score = 0
    score += 300 * (opp_comp - own_comp)
    score += 100 * (own_ratio - opp_ratio)
    score += 8 * (own_adj - opp_adj)
    score += 4 * (opp_bbox - own_bbox)
    score += 3 * (opp_edge - own_edge)
    score += 2 * (opp_n - own_n)  # fewer opponent pieces can help them connect
    score += (opp_center - own_center)
    score += (opp_spread - own_spread) // 8

    return score


def check_time():
    global NODE_COUNTER
    NODE_COUNTER += 1
    if (NODE_COUNTER & 255) == 0 and time.perf_counter() >= DEADLINE:
        raise SearchTimeout


def negamax(board, depth, alpha, beta, ply):
    check_time()

    term = terminal_status(board)
    if term is not None:
        return term - ply if term > 0 else term + ply

    if depth == 0:
        return evaluate(board)

    moves = generate_moves(board)

    if not moves:
        # Pass-like handling if a no-move position appears.
        child = negate_board(board)
        return -negamax(child, depth - 1, -beta, -alpha, ply + 1)

    moves = ordered_moves(board, moves)

    best = -INF
    for m in moves:
        child = make_child(board, m)
        score = -negamax(child, depth - 1, -beta, -alpha, ply + 1)

        if score > best:
            best = score
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    return best


def search_root(board, moves, depth, pv_move):
    if pv_move in moves:
        ordered = [pv_move] + [m for m in moves if m != pv_move]
    else:
        ordered = moves

    best_move = ordered[0]
    best_score = -INF
    alpha = -INF
    beta = INF

    for m in ordered:
        if time.perf_counter() >= DEADLINE:
            raise SearchTimeout

        child = make_child(board, m)
        score = -negamax(child, depth - 1, -beta, -alpha, 1)

        if score > best_score:
            best_score = score
            best_move = m
        if score > alpha:
            alpha = score

    return best_score, best_move


def policy(board) -> str:
    global DEADLINE, NODE_COUNTER

    board = [list(map(int, row)) for row in board]

    moves = generate_moves(board)
    if not moves:
        # Should be unreachable in the arena; included only as a hard fallback.
        return "0,0:0,0"
    if len(moves) == 1:
        return move_to_str(moves[0])

    # Heuristic base ordering.
    base_order = ordered_moves(board, moves)

    # Immediate win check, and deprioritize moves that instantly connect the opponent.
    safe_moves = []
    risky_moves = []

    for m in base_order:
        after = apply_move(board, m)
        if is_connected(after, 1):
            return move_to_str(m)
        if is_connected(after, -1):
            risky_moves.append(m)
        else:
            safe_moves.append(m)

    moves = safe_moves + risky_moves if safe_moves else base_order

    best_move = moves[0]
    pv_move = best_move

    own_info = side_metrics(board, 1)
    opp_info = side_metrics(board, -1)
    own_comp = own_info[1]
    opp_comp = opp_info[1]

    max_depth = 3
    if len(moves) <= 20:
        max_depth = 4
    if len(moves) <= 12 or own_comp <= 2 or opp_comp <= 2:
        max_depth = 5
    if len(moves) <= 8:
        max_depth = 6

    DEADLINE = time.perf_counter() + 0.92
    NODE_COUNTER = 0

    try:
        for depth in range(1, max_depth + 1):
            score, move = search_root(board, moves, depth, pv_move)
            if move is not None:
                best_move = move
                pv_move = move

            if abs(score) >= WIN - 1000:
                break
    except SearchTimeout:
        pass

    return move_to_str(best_move)
