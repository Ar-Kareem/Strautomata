
import time
import random

SIZE = 8
DIRS = (
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
)

CENTER = [[7 - max(abs(2 * r - 7), abs(2 * c - 7)) for c in range(SIZE)] for r in range(SIZE)]

WIN_SCORE = 100_000_000
INF = 10**18

EXACT = 0
LOWER = 1
UPPER = 2

_rng = random.Random(0)
ZOBRIST = [[[ _rng.getrandbits(64) for _ in range(2)] for _ in range(SIZE)] for _ in range(SIZE)]

TT = {}
DEADLINE = 0.0
NODE_COUNTER = 0


class SearchTimeout(Exception):
    pass


def compute_hash(board):
    h = 0
    for r in range(SIZE):
        row = board[r]
        for c in range(SIZE):
            v = row[c]
            if v == 1:
                h ^= ZOBRIST[r][c][0]
            elif v == -1:
                h ^= ZOBRIST[r][c][1]
    return h


def update_hash(h, fr, fc, tr, tc, color, captured):
    idx = 0 if color == 1 else 1
    h ^= ZOBRIST[fr][fc][idx]
    if captured == 1:
        h ^= ZOBRIST[tr][tc][0]
    elif captured == -1:
        h ^= ZOBRIST[tr][tc][1]
    h ^= ZOBRIST[tr][tc][idx]
    return h


def check_time():
    if time.perf_counter() >= DEADLINE:
        raise SearchTimeout


def count_adjacent(board, r, c, color):
    cnt = 0
    for dr, dc in DIRS:
        nr = r + dr
        nc = c + dc
        if 0 <= nr < SIZE and 0 <= nc < SIZE and board[nr][nc] == color:
            cnt += 1
    return cnt


def count_adjacent_after_move(board, fr, fc, tr, tc, color):
    cnt = 0
    for dr, dc in DIRS:
        nr = tr + dr
        nc = tc + dc
        if 0 <= nr < SIZE and 0 <= nc < SIZE:
            if nr == fr and nc == fc:
                continue
            if board[nr][nc] == color:
                cnt += 1
    return cnt


def generate_moves(board, color, pref_move=None):
    row_counts = [0] * SIZE
    col_counts = [0] * SIZE
    diag_counts = [0] * (2 * SIZE - 1)      # r-c+7
    anti_counts = [0] * (2 * SIZE - 1)      # r+c
    pieces = []

    for r in range(SIZE):
        row = board[r]
        rc = 0
        for c in range(SIZE):
            v = row[c]
            if v != 0:
                rc += 1
                col_counts[c] += 1
                diag_counts[r - c + 7] += 1
                anti_counts[r + c] += 1
                if v == color:
                    pieces.append((r, c))
        row_counts[r] = rc

    scored = []
    for r, c in pieces:
        src_neighbors = count_adjacent(board, r, c, color)
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
            if not (0 <= tr < SIZE and 0 <= tc < SIZE):
                continue
            if board[tr][tc] == color:
                continue

            rr = r + dr
            cc = c + dc
            blocked = False
            while rr != tr or cc != tc:
                if board[rr][cc] == -color:
                    blocked = True
                    break
                rr += dr
                cc += dc
            if blocked:
                continue

            move = (r, c, tr, tc)
            score = 0
            if pref_move is not None and move == pref_move:
                score += 1_000_000

            captured = board[tr][tc]
            if captured == -color:
                score += 300

            dst_neighbors = count_adjacent_after_move(board, r, c, tr, tc, color)
            score += 45 * dst_neighbors
            score += 12 * (CENTER[tr][tc] - CENTER[r][c])

            if src_neighbors == 0 and dst_neighbors > 0:
                score += 120
            if dst_neighbors == 0:
                score -= 50

            scored.append((score, move))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [m for _, m in scored]


def is_connected(board, color):
    start_r = -1
    start_c = -1
    total = 0

    for r in range(SIZE):
        row = board[r]
        for c in range(SIZE):
            if row[c] == color:
                total += 1
                if start_r == -1:
                    start_r = r
                    start_c = c

    if total <= 1:
        return True

    seen = [[False] * SIZE for _ in range(SIZE)]
    stack = [(start_r, start_c)]
    seen[start_r][start_c] = True
    count = 1

    while stack:
        r, c = stack.pop()
        for dr, dc in DIRS:
            nr = r + dr
            nc = c + dc
            if 0 <= nr < SIZE and 0 <= nc < SIZE:
                if not seen[nr][nc] and board[nr][nc] == color:
                    seen[nr][nc] = True
                    count += 1
                    if count == total:
                        return True
                    stack.append((nr, nc))

    return False


def side_stats(positions):
    n = len(positions)
    if n == 0:
        return (0, 1, 0, 0, 0, 0, 0, 0, 0, 0)
    if n == 1:
        r, c = positions[0]
        border = 1 if (r == 0 or r == 7 or c == 0 or c == 7) else 0
        return (1, 1, 1, 0, 0, 0, border, CENTER[r][c], 1, 0)

    posset = set(positions)

    adjacency = 0
    isolated = 0
    border = 0
    center_total = 0

    min_r = 7
    max_r = 0
    min_c = 7
    max_c = 0

    for r, c in positions:
        if r < min_r:
            min_r = r
        if r > max_r:
            max_r = r
        if c < min_c:
            min_c = c
        if c > max_c:
            max_c = c

        if r == 0 or r == 7 or c == 0 or c == 7:
            border += 1
        center_total += CENTER[r][c]

        neigh = 0
        for dr, dc in DIRS:
            if (r + dr, c + dc) in posset:
                neigh += 1
        adjacency += neigh
        if neigh == 0:
            isolated += 1

    adjacency //= 2
    bbox_area = (max_r - min_r + 1) * (max_c - min_c + 1)

    pair_sum = 0
    for i in range(n):
        r1, c1 = positions[i]
        for j in range(i + 1, n):
            r2, c2 = positions[j]
            dr = abs(r1 - r2)
            dc = abs(c1 - c2)
            pair_sum += dr if dr > dc else dc

    unseen = set(posset)
    components = []
    largest = None
    largest_size = 0

    while unseen:
        start = unseen.pop()
        comp = [start]
        stack = [start]
        while stack:
            r, c = stack.pop()
            for dr, dc in DIRS:
                np = (r + dr, c + dc)
                if np in unseen:
                    unseen.remove(np)
                    stack.append(np)
                    comp.append(np)
        components.append(comp)
        if len(comp) > largest_size:
            largest_size = len(comp)
            largest = comp

    comp_count = len(components)
    connect_dist = 0
    if comp_count > 1:
        for comp in components:
            if comp is largest:
                continue
            best = 8
            for r1, c1 in comp:
                for r2, c2 in largest:
                    dr = abs(r1 - r2)
                    dc = abs(c1 - c2)
                    d = dr if dr > dc else dc
                    if d < best:
                        best = d
                    if best == 1:
                        break
                if best == 1:
                    break
            connect_dist += best

    return (n, comp_count, largest_size, connect_dist, isolated, adjacency, border, center_total, bbox_area, pair_sum)


def evaluate(board, player):
    my_pos = []
    opp_pos = []

    for r in range(SIZE):
        row = board[r]
        for c in range(SIZE):
            v = row[c]
            if v == player:
                my_pos.append((r, c))
            elif v == -player:
                opp_pos.append((r, c))

    my = side_stats(my_pos)
    opp = side_stats(opp_pos)

    my_n, my_comp, my_largest, my_connect, my_isol, my_adj, my_border, my_center, my_bbox, my_pair = my
    opp_n, opp_comp, opp_largest, opp_connect, opp_isol, opp_adj, opp_border, opp_center, opp_bbox, opp_pair = opp

    if my_comp == 1 and opp_comp == 1:
        return -WIN_SCORE
    if my_comp == 1:
        return WIN_SCORE
    if opp_comp == 1:
        return -WIN_SCORE

    my_frac = 100 if my_n <= 1 else (100 * my_largest) // my_n
    opp_frac = 100 if opp_n <= 1 else (100 * opp_largest) // opp_n

    score = 0
    score += 1200 * (opp_comp - my_comp)
    score += 8 * (my_frac - opp_frac)
    score += 90 * (opp_connect - my_connect)
    score += 40 * (opp_isol - my_isol)
    score += 18 * (my_adj - opp_adj)
    score += 5 * (opp_pair - my_pair)
    score += 8 * (opp_bbox - my_bbox)
    score += 8 * (opp_border - my_border)
    score += 4 * (my_center - opp_center)
    score += 6 * (opp_n - my_n)

    return score


def negamax(board, player, depth, alpha, beta, h):
    global NODE_COUNTER, TT

    NODE_COUNTER += 1
    if (NODE_COUNTER & 511) == 0:
        check_time()

    alpha_orig = alpha
    beta_orig = beta

    tt_key = (h, player)
    entry = TT.get(tt_key)
    tt_move = None
    if entry is not None:
        e_depth, e_flag, e_value, e_move = entry
        tt_move = e_move
        if e_depth >= depth:
            if e_flag == EXACT:
                return e_value
            elif e_flag == LOWER:
                if e_value > alpha:
                    alpha = e_value
            else:
                if e_value < beta:
                    beta = e_value
            if alpha >= beta:
                return e_value

    if depth == 0:
        return evaluate(board, player)

    moves = generate_moves(board, player, pref_move=tt_move)
    if not moves:
        return evaluate(board, player)

    best = -INF
    best_move = moves[0]

    for fr, fc, tr, tc in moves:
        captured = board[tr][tc]
        board[fr][fc] = 0
        board[tr][tc] = player
        nh = update_hash(h, fr, fc, tr, tc, player, captured)

        try:
            if is_connected(board, player):
                score = WIN_SCORE
            elif captured == -player and is_connected(board, -player):
                score = -WIN_SCORE
            else:
                score = -negamax(board, -player, depth - 1, -beta, -alpha, nh)
        finally:
            board[fr][fc] = player
            board[tr][tc] = captured

        if score > best:
            best = score
            best_move = (fr, fc, tr, tc)

        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    flag = EXACT
    if best <= alpha_orig:
        flag = UPPER
    elif best >= beta_orig:
        flag = LOWER

    old = TT.get(tt_key)
    if old is None or depth >= old[0]:
        TT[tt_key] = (depth, flag, best, best_move)

    return best


def search_root(board, depth, h, pref_move=None):
    check_time()

    entry = TT.get((h, 1))
    tt_move = entry[3] if entry is not None else None
    if tt_move is None:
        tt_move = pref_move

    moves = generate_moves(board, 1, pref_move=tt_move)
    if not moves:
        return -INF, None

    alpha = -INF
    beta = INF
    best_score = -INF
    best_move = moves[0]

    for fr, fc, tr, tc in moves:
        check_time()

        captured = board[tr][tc]
        board[fr][fc] = 0
        board[tr][tc] = 1
        nh = update_hash(h, fr, fc, tr, tc, 1, captured)

        try:
            if is_connected(board, 1):
                score = WIN_SCORE
            elif captured == -1 and is_connected(board, -1):
                score = -WIN_SCORE
            else:
                score = -negamax(board, -1, depth - 1, -beta, -alpha, nh)
        finally:
            board[fr][fc] = 1
            board[tr][tc] = captured

        if score > best_score:
            best_score = score
            best_move = (fr, fc, tr, tc)

        if best_score > alpha:
            alpha = best_score

    return best_score, best_move


def move_to_str(move):
    fr, fc, tr, tc = move
    return f"{fr},{fc}:{tr},{tc}"


def policy(board) -> str:
    global DEADLINE, NODE_COUNTER, TT

    b = [list(map(int, row)) for row in board]
    TT = {}
    NODE_COUNTER = 0
    DEADLINE = time.perf_counter() + 0.92

    root_hash = compute_hash(b)
    root_moves = generate_moves(b, 1)

    # In valid LOA positions this should not happen, but keep a deterministic fallback.
    if not root_moves:
        # Try one more time without preference logic assumptions.
        root_moves = generate_moves(b, 1, pref_move=None)
        if not root_moves:
            # Last-resort impossible fallback for malformed positions.
            return "0,0:0,0"

    best_move = root_moves[0]

    if len(root_moves) == 1:
        return move_to_str(best_move)

    # Immediate winning move?
    for fr, fc, tr, tc in root_moves:
        captured = b[tr][tc]
        b[fr][fc] = 0
        b[tr][tc] = 1
        try:
            if is_connected(b, 1):
                return move_to_str((fr, fc, tr, tc))
        finally:
            b[fr][fc] = 1
            b[tr][tc] = captured

    pv_move = best_move
    depth = 1

    while depth <= 16:
        try:
            check_time()
            score, move = search_root(b, depth, root_hash, pref_move=pv_move)
            if move is not None:
                best_move = move
                pv_move = move
            if abs(score) >= WIN_SCORE:
                break
            depth += 1
        except SearchTimeout:
            break

    return move_to_str(best_move)
