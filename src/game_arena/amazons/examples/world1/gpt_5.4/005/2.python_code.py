
import time
import math
import numpy as np

DIRS = [(-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)]

INF = 10**18


def in_bounds(r, c):
    return 0 <= r < 6 and 0 <= c < 6


def find_amazons(board, player):
    pos = np.argwhere(board == player)
    return [tuple(x) for x in pos]


def ray_moves(board, r, c):
    res = []
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        while 0 <= nr < 6 and 0 <= nc < 6 and board[nr, nc] == 0:
            res.append((nr, nc))
            nr += dr
            nc += dc
    return res


def legal_moves(board, player):
    amazons = find_amazons(board, player)
    moves = []
    for fr, fc in amazons:
        for tr, tc in ray_moves(board, fr, fc):
            board[fr, fc] = 0
            board[tr, tc] = player
            for ar, ac in ray_moves(board, tr, tc):
                moves.append((fr, fc, tr, tc, ar, ac))
            board[tr, tc] = 0
            board[fr, fc] = player
    return moves


def mobility_count(board, player):
    total = 0
    for r, c in find_amazons(board, player):
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            while 0 <= nr < 6 and 0 <= nc < 6 and board[nr, nc] == 0:
                total += 1
                nr += dr
                nc += dc
    return total


def amazon_liberties(board, r, c):
    cnt = 0
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 6 and 0 <= nc < 6 and board[nr, nc] == 0:
            cnt += 1
    return cnt


def territory_bfs(board, starts):
    dist = np.full((6, 6), 99, dtype=np.int16)
    q = []
    head = 0
    for r, c in starts:
        dist[r, c] = 0
        q.append((r, c))
    while head < len(q):
        r, c = q[head]
        head += 1
        nd = dist[r, c] + 1
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            while 0 <= nr < 6 and 0 <= nc < 6 and board[nr, nc] == 0:
                if dist[nr, nc] > nd:
                    dist[nr, nc] = nd
                    q.append((nr, nc))
                nr += dr
                nc += dc
    return dist


def evaluate(board):
    my_ams = find_amazons(board, 1)
    op_ams = find_amazons(board, 2)

    my_moves = mobility_count(board, 1)
    op_moves = mobility_count(board, 2)

    if my_moves == 0 and op_moves == 0:
        return 0
    if op_moves == 0:
        return 10**9
    if my_moves == 0:
        return -10**9

    my_lib = sum(amazon_liberties(board, r, c) for r, c in my_ams)
    op_lib = sum(amazon_liberties(board, r, c) for r, c in op_ams)

    d1 = territory_bfs(board, my_ams)
    d2 = territory_bfs(board, op_ams)
    terr = 0
    for r in range(6):
        for c in range(6):
            if board[r, c] != 0:
                continue
            if d1[r, c] < d2[r, c]:
                terr += 1
            elif d2[r, c] < d1[r, c]:
                terr -= 1

    # Pressure: low-liberty opponent amazons are good targets
    op_trapped = sum(max(0, 4 - amazon_liberties(board, r, c)) for r, c in op_ams)
    my_trapped = sum(max(0, 4 - amazon_liberties(board, r, c)) for r, c in my_ams)

    return (
        8 * (my_moves - op_moves)
        + 5 * terr
        + 2 * (my_lib - op_lib)
        + 6 * (op_trapped - my_trapped)
    )


def apply_move(board, mv, player):
    fr, fc, tr, tc, ar, ac = mv
    board[fr, fc] = 0
    board[tr, tc] = player
    board[ar, ac] = -1


def undo_move(board, mv, player):
    fr, fc, tr, tc, ar, ac = mv
    board[ar, ac] = 0
    board[tr, tc] = 0
    board[fr, fc] = player


def move_heuristic(board, mv, player):
    fr, fc, tr, tc, ar, ac = mv
    opp = 2 if player == 1 else 1

    center_before = abs(fr - 2.5) + abs(fc - 2.5)
    center_after = abs(tr - 2.5) + abs(tc - 2.5)
    central_gain = center_before - center_after

    # Temporarily inspect resulting board lightly
    board[fr, fc] = 0
    board[tr, tc] = player
    board[ar, ac] = -1

    my_loc = amazon_liberties(board, tr, tc)
    opp_lib = 0
    for r, c in find_amazons(board, opp):
        opp_lib += amazon_liberties(board, r, c)

    board[ar, ac] = 0
    board[tr, tc] = 0
    board[fr, fc] = player

    # Arrow near opponent tends to be useful
    near_opp = 0
    for r, c in find_amazons(board, opp):
        d = max(abs(ar - r), abs(ac - c))
        near_opp += max(0, 3 - d)

    return 10 * central_gain + 4 * my_loc - opp_lib + 3 * near_opp


def ordered_moves(board, player, limit=None):
    moves = legal_moves(board, player)
    if not moves:
        return moves
    scored = [(move_heuristic(board, mv, player), mv) for mv in moves]
    scored.sort(key=lambda x: x[0], reverse=True)
    if limit is not None and len(scored) > limit:
        scored = scored[:limit]
    return [mv for _, mv in scored]


def alphabeta(board, depth, alpha, beta, player, start_time, time_limit, root=False):
    if time.time() - start_time > time_limit:
        raise TimeoutError

    my_turn = (player == 1)
    moves = ordered_moves(board, player, limit=28 if depth >= 2 else None)

    if depth == 0 or not moves:
        if not moves:
            # Current player cannot move: loss for side to move
            return (-10**9 if my_turn else 10**9), None
        return evaluate(board), None

    best_move = moves[0]

    if player == 1:
        value = -INF
        for mv in moves:
            apply_move(board, mv, 1)
            score, _ = alphabeta(board, depth - 1, alpha, beta, 2, start_time, time_limit)
            undo_move(board, mv, 1)
            if score > value:
                value = score
                best_move = mv
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value, best_move
    else:
        value = INF
        for mv in moves:
            apply_move(board, mv, 2)
            score, _ = alphabeta(board, depth - 1, alpha, beta, 1, start_time, time_limit)
            undo_move(board, mv, 2)
            if score < value:
                value = score
                best_move = mv
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value, best_move


def move_to_str(mv):
    fr, fc, tr, tc, ar, ac = mv
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"


def policy(board) -> str:
    board = np.array(board, copy=True)

    # Robust legal fallback
    all_moves = legal_moves(board, 1)
    if not all_moves:
        return "0,0:0,0:0,0"

    # Fast single-ply tactical precheck:
    # prefer moves that immediately leave opponent with no move.
    best_fallback = ordered_moves(board, 1, limit=1)[0]
    candidate_moves = ordered_moves(board, 1, limit=24)

    for mv in candidate_moves[:10]:
        apply_move(board, mv, 1)
        opp_moves = legal_moves(board, 2)
        undo_move(board, mv, 1)
        if not opp_moves:
            return move_to_str(mv)

    start_time = time.time()
    time_limit = 0.92

    best_move = best_fallback

    # Iterative deepening
    for depth in [1, 2, 3]:
        try:
            _, mv = alphabeta(board, depth, -INF, INF, 1, start_time, time_limit, root=True)
            if mv is not None:
                best_move = mv
        except TimeoutError:
            break

    return move_to_str(best_move)
