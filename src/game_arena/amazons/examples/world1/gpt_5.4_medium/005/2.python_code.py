
import time
from collections import deque
import numpy as np

DIRS = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
]

CENTER = [
    [0, 1, 2, 2, 1, 0],
    [1, 2, 3, 3, 2, 1],
    [2, 3, 4, 4, 3, 2],
    [2, 3, 4, 4, 3, 2],
    [1, 2, 3, 3, 2, 1],
    [0, 1, 2, 2, 1, 0],
]

INF = 10**9


class SearchTimeout(Exception):
    pass


def format_move(m):
    return f"{m[0]},{m[1]}:{m[2]},{m[3]}:{m[4]},{m[5]}"


def ray_squares(board, r, c, vacate=None):
    if vacate is None:
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            while 0 <= nr < 6 and 0 <= nc < 6 and board[nr, nc] == 0:
                yield nr, nc
                nr += dr
                nc += dc
    else:
        vr, vc = vacate
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            while 0 <= nr < 6 and 0 <= nc < 6 and (board[nr, nc] == 0 or (nr == vr and nc == vc)):
                yield nr, nc
                nr += dr
                nc += dc


def generate_moves(board):
    moves = []
    for fr, fc in np.argwhere(board == 1):
        fr = int(fr)
        fc = int(fc)
        for tr, tc in ray_squares(board, fr, fc):
            for ar, ac in ray_squares(board, tr, tc, (fr, fc)):
                moves.append((fr, fc, tr, tc, ar, ac))
    return moves


def apply_and_swap(board, move):
    fr, fc, tr, tc, ar, ac = move
    nb = board.copy()
    nb[fr, fc] = 0
    nb[tr, tc] = 1
    nb[ar, ac] = -1
    ones = (nb == 1)
    twos = (nb == 2)
    nb[ones] = 2
    nb[twos] = 1
    return nb


def mobility_metrics(board, player):
    seen = [[False] * 6 for _ in range(6)]
    unique_count = 0
    total_count = 0
    for r, c in np.argwhere(board == player):
        r = int(r)
        c = int(c)
        for rr, cc in ray_squares(board, r, c):
            total_count += 1
            if not seen[rr][cc]:
                seen[rr][cc] = True
                unique_count += 1
    return unique_count, total_count


def queen_distance_map(board, player):
    dist = [[99] * 6 for _ in range(6)]
    q = deque()
    for r, c in np.argwhere(board == player):
        r = int(r)
        c = int(c)
        dist[r][c] = 0
        q.append((r, c))
    while q:
        r, c = q.popleft()
        nd = dist[r][c] + 1
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            while 0 <= nr < 6 and 0 <= nc < 6 and board[nr, nc] == 0:
                if dist[nr][nc] > nd:
                    dist[nr][nc] = nd
                    q.append((nr, nc))
                nr += dr
                nc += dc
    return dist


def center_score(board):
    s = 0
    for r, c in np.argwhere(board == 1):
        s += CENTER[int(r)][int(c)]
    for r, c in np.argwhere(board == 2):
        s -= CENTER[int(r)][int(c)]
    return s


def fast_eval(board, fast_cache):
    key = board.tobytes()
    val = fast_cache.get(key)
    if val is not None:
        return val
    u1, t1 = mobility_metrics(board, 1)
    u2, t2 = mobility_metrics(board, 2)
    val = 8 * (u1 - u2) + 3 * (t1 - t2) + center_score(board)
    fast_cache[key] = val
    return val


def static_eval(board, eval_cache):
    key = board.tobytes()
    val = eval_cache.get(key)
    if val is not None:
        return val

    empties = np.argwhere(board == 0)
    if len(empties) == 0:
        eval_cache[key] = 0
        return 0

    d1 = queen_distance_map(board, 1)
    d2 = queen_distance_map(board, 2)

    territory = 0
    margin = 0
    contested = 0

    for r, c in empties:
        r = int(r)
        c = int(c)
        a = d1[r][c]
        b = d2[r][c]
        if a < 99 and b < 99:
            contested += 1
        if a < b:
            territory += 1
            margin += 5 if b >= 99 else min(4, b - a)
        elif b < a:
            territory -= 1
            margin -= 5 if a >= 99 else min(4, a - b)

    u1, t1 = mobility_metrics(board, 1)
    u2, t2 = mobility_metrics(board, 2)

    terr_w = 24 if contested == 0 else 18
    val = terr_w * territory + 4 * (u1 - u2) + 2 * (t1 - t2) + 2 * margin + center_score(board)
    eval_cache[key] = val
    return val


def move_cap(depth, n_moves, empties):
    if depth >= 5:
        cap = 8
    elif depth == 4:
        cap = 10
    elif depth == 3:
        cap = 14
    elif depth == 2:
        cap = 22
    else:
        return None

    if empties <= 10:
        cap += 4
    elif empties >= 20:
        cap = max(8, cap - 2)

    return cap if n_moves > cap else None


def order_children(board, depth, end_time, eval_cache, fast_cache):
    if time.perf_counter() >= end_time:
        raise SearchTimeout

    moves = generate_moves(board)
    if not moves:
        return []

    empties = int(np.count_nonzero(board == 0))
    cap = move_cap(depth, len(moves), empties)
    use_static = depth <= 2 or len(moves) <= 14

    items = []
    scorer = static_eval if use_static else fast_eval

    for i, mv in enumerate(moves):
        if (i & 15) == 0 and time.perf_counter() >= end_time:
            raise SearchTimeout
        nb = apply_and_swap(board, mv)
        h = -scorer(nb, eval_cache if use_static else fast_cache)
        items.append((h, mv, nb))

    items.sort(key=lambda x: x[0], reverse=True)
    if cap is not None:
        items = items[:cap]
    return items


def search(board, depth, alpha, beta, end_time, tt, eval_cache, fast_cache):
    if time.perf_counter() >= end_time:
        raise SearchTimeout

    key = (board.tobytes(), depth)
    if key in tt:
        return tt[key]

    if depth <= 0:
        v = static_eval(board, eval_cache)
        tt[key] = v
        return v

    children = order_children(board, depth, end_time, eval_cache, fast_cache)
    if not children:
        return -100000 - depth

    best = -INF
    for i, (_, _, nb) in enumerate(children):
        if (i & 7) == 0 and time.perf_counter() >= end_time:
            raise SearchTimeout
        score = -search(nb, depth - 1, -beta, -alpha, end_time, tt, eval_cache, fast_cache)
        if score > best:
            best = score
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    tt[key] = best
    return best


def policy(board) -> str:
    board = np.asarray(board)
    moves = generate_moves(board)

    if not moves:
        return "0,0:0,0:0,0"
    if len(moves) == 1:
        return format_move(moves[0])

    start = time.perf_counter()
    end_time = start + 0.94

    eval_cache = {}
    fast_cache = {}
    tt = {}

    root_items = []
    use_static_root = len(moves) <= 140
    root_scorer = static_eval if use_static_root else fast_eval
    root_cache = eval_cache if use_static_root else fast_cache

    best_move = moves[0]

    for i, mv in enumerate(moves):
        if (i & 15) == 0 and time.perf_counter() >= end_time:
            break
        nb = apply_and_swap(board, mv)
        h = -root_scorer(nb, root_cache)
        root_items.append((h, mv, nb))

    if not root_items:
        return format_move(best_move)

    root_items.sort(key=lambda x: x[0], reverse=True)
    best_move = root_items[0][1]
    completed_best = best_move
    pv_move = best_move

    empties = int(np.count_nonzero(board == 0))
    m = len(moves)

    if empties <= 6 and m <= 12:
        max_depth = 6
    elif empties <= 10 and m <= 20:
        max_depth = 5
    elif empties <= 14 and m <= 50:
        max_depth = 4
    elif m <= 120:
        max_depth = 3
    else:
        max_depth = 2

    for depth in range(1, max_depth + 1):
        try:
            root_items.sort(key=lambda x: x[0], reverse=True)
            if pv_move is not None:
                for i, item in enumerate(root_items):
                    if item[1] == pv_move:
                        root_items.insert(0, root_items.pop(i))
                        break

            alpha = -INF
            current_best = None
            current_score = -INF
            rescored = []

            for i, (_, mv, nb) in enumerate(root_items):
                if (i & 3) == 0 and time.perf_counter() >= end_time:
                    raise SearchTimeout
                score = -search(nb, depth - 1, -INF, -alpha, end_time, tt, eval_cache, fast_cache)
                rescored.append((score, mv, nb))
                if score > current_score:
                    current_score = score
                    current_best = mv
                if score > alpha:
                    alpha = score

            if current_best is not None:
                completed_best = current_best
                pv_move = current_best
                root_items = rescored

        except SearchTimeout:
            break

    return format_move(completed_best)
