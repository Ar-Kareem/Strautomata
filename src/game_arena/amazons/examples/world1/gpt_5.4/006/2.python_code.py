
import numpy as np
import time

# 6x6 Amazons policy

DIRS = [(-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)]

INF = 10**18

def inside(r, c):
    return 0 <= r < 6 and 0 <= c < 6

def iter_ray(board, r, c):
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        while inside(nr, nc) and board[nr, nc] == 0:
            yield nr, nc
            nr += dr
            nc += dc

def get_amazons(board, player):
    ps = np.argwhere(board == player)
    return [(int(r), int(c)) for r, c in ps]

def legal_moves(board, player):
    moves = []
    amazons = get_amazons(board, player)
    for fr, fc in amazons:
        for tr, tc in iter_ray(board, fr, fc):
            b2 = board.copy()
            b2[fr, fc] = 0
            b2[tr, tc] = player
            for ar, ac in iter_ray(b2, tr, tc):
                moves.append((fr, fc, tr, tc, ar, ac))
    return moves

def apply_move(board, move, player):
    fr, fc, tr, tc, ar, ac = move
    b = board.copy()
    b[fr, fc] = 0
    b[tr, tc] = player
    b[ar, ac] = -1
    return b

def mobility(board, player):
    total = 0
    for r, c in get_amazons(board, player):
        for _ in iter_ray(board, r, c):
            total += 1
    return total

def flood_dist(board, starts):
    dist = np.full((6, 6), 99, dtype=np.int16)
    from collections import deque
    q = deque()
    for r, c in starts:
        dist[r, c] = 0
        q.append((r, c))
    while q:
        r, c = q.popleft()
        nd = dist[r, c] + 1
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            while inside(nr, nc) and board[nr, nc] == 0:
                if dist[nr, nc] > nd:
                    dist[nr, nc] = nd
                    q.append((nr, nc))
                nr += dr
                nc += dc
    return dist

def territory_score(board):
    my_amz = get_amazons(board, 1)
    op_amz = get_amazons(board, 2)
    if not my_amz and not op_amz:
        return 0.0
    d1 = flood_dist(board, my_amz)
    d2 = flood_dist(board, op_amz)
    score = 0.0
    empties = np.argwhere(board == 0)
    for r, c in empties:
        a = int(d1[r, c])
        b = int(d2[r, c])
        if a < b:
            score += 1.0
        elif a > b:
            score -= 1.0
        elif a < 99:
            score += 0.1
    return score

def centrality(move):
    _, _, tr, tc, ar, ac = move
    center = 2.5
    # Prefer landing somewhat central, arrow somewhat constraining
    return -((tr - center) ** 2 + (tc - center) ** 2) * 0.15 - ((ar - center) ** 2 + (ac - center) ** 2) * 0.03

def evaluate(board):
    my_moves = legal_moves(board, 1)
    op_moves = legal_moves(board, 2)

    if not my_moves:
        return -1e9
    if not op_moves:
        return 1e9

    my_mob = len(my_moves)
    op_mob = len(op_moves)

    # Local mobility is cheaper than full move count meaningfully, but we already have counts here.
    terr = territory_score(board)

    return 4.0 * (my_mob - op_mob) + 1.5 * terr

def order_moves(board, moves, player):
    scored = []
    opp = 2 if player == 1 else 1
    for mv in moves:
        b = apply_move(board, mv, player)
        my_m = mobility(b, player)
        op_m = mobility(b, opp)
        score = 3.0 * (my_m - op_m) + centrality(mv)
        scored.append((score, mv))
    scored.sort(reverse=True, key=lambda x: x[0])
    return [mv for _, mv in scored]

def minimax(board, depth, alpha, beta, player, start_time, time_limit):
    if time.time() - start_time > time_limit:
        raise TimeoutError

    moves = legal_moves(board, player)

    if depth == 0:
        val = evaluate(board)
        return val, None

    if not moves:
        if player == 1:
            return -1e9, None
        else:
            return 1e9, None

    moves = order_moves(board, moves, player)
    # Beam a little at deeper levels to keep speed under control
    if depth >= 2 and len(moves) > 24:
        moves = moves[:24]
    if depth >= 3 and len(moves) > 16:
        moves = moves[:16]

    best_move = moves[0]

    if player == 1:
        value = -INF
        for mv in moves:
            b = apply_move(board, mv, 1)
            child_val, _ = minimax(b, depth - 1, alpha, beta, 2, start_time, time_limit)
            if child_val > value:
                value = child_val
                best_move = mv
            alpha = max(alpha, value)
            if beta <= alpha:
                break
        return value, best_move
    else:
        value = INF
        for mv in moves:
            b = apply_move(board, mv, 2)
            child_val, _ = minimax(b, depth - 1, alpha, beta, 1, start_time, time_limit)
            if child_val < value:
                value = child_val
                best_move = mv
            beta = min(beta, value)
            if beta <= alpha:
                break
        return value, best_move

def move_to_string(move):
    fr, fc, tr, tc, ar, ac = move
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"

def safe_first_legal(board):
    moves = legal_moves(board, 1)
    if moves:
        return move_to_string(moves[0])
    # Robust fallback; environment should not call in terminal positions.
    my_amz = get_amazons(board, 1)
    if my_amz:
        r, c = my_amz[0]
        return f"{r},{c}:{r},{c}:{r},{c}"
    return "0,0:0,0:0,0"

def policy(board) -> str:
    board = np.asarray(board)
    start_time = time.time()
    time_limit = 0.92

    moves = legal_moves(board, 1)
    if not moves:
        return safe_first_legal(board)

    # Immediate tactical heuristic ranking
    ordered = order_moves(board, moves, 1)
    best_heur = ordered[0]

    # Adaptive search depth based on branching factor
    n = len(ordered)
    if n <= 10:
        depth = 3
    elif n <= 30:
        depth = 2
    else:
        depth = 1

    best_move = best_heur

    try:
        val, mv = minimax(board, depth, -INF, INF, 1, start_time, time_limit)
        if mv is not None:
            best_move = mv
    except TimeoutError:
        best_move = best_heur
    except Exception:
        best_move = best_heur

    # Final legality assurance
    try:
        legal_set = set(legal_moves(board, 1))
        if best_move in legal_set:
            return move_to_string(best_move)
        if best_heur in legal_set:
            return move_to_string(best_heur)
        return move_to_string(next(iter(legal_set)))
    except Exception:
        return safe_first_legal(board)
