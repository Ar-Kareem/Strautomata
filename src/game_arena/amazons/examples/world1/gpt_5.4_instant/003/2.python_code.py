
import time
import math
import numpy as np

# Directions for queen movement
DIRS = [(-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)]

INF = 10**18


def in_bounds(r, c):
    return 0 <= r < 6 and 0 <= c < 6


def find_pieces(board, player):
    pts = np.argwhere(board == player)
    return [(int(r), int(c)) for r, c in pts]


def ray_moves(board, r, c):
    # Legal destination squares for a queen-like move from (r,c)
    out = []
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        while 0 <= nr < 6 and 0 <= nc < 6 and board[nr, nc] == 0:
            out.append((nr, nc))
            nr += dr
            nc += dc
    return out


def ray_moves_after_move(board, from_r, from_c, to_r, to_c):
    # Arrow squares after moving amazon from -> to.
    # Treat from as empty and to as occupied by moved amazon before shooting.
    out = []
    for dr, dc in DIRS:
        nr, nc = to_r + dr, to_c + dc
        while 0 <= nr < 6 and 0 <= nc < 6:
            if nr == from_r and nc == from_c:
                out.append((nr, nc))
            elif board[nr, nc] == 0:
                out.append((nr, nc))
            else:
                break
            nr += dr
            nc += dc
    return out


def legal_moves(board, player):
    moves = []
    pieces = find_pieces(board, player)
    for fr, fc in pieces:
        tos = ray_moves(board, fr, fc)
        for tr, tc in tos:
            arrs = ray_moves_after_move(board, fr, fc, tr, tc)
            for ar, ac in arrs:
                moves.append((fr, fc, tr, tc, ar, ac))
    return moves


def apply_move(board, move, player):
    fr, fc, tr, tc, ar, ac = move
    nb = board.copy()
    nb[fr, fc] = 0
    nb[tr, tc] = player
    nb[ar, ac] = -1
    return nb


def move_to_str(move):
    fr, fc, tr, tc, ar, ac = move
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"


def count_mobility(board, player):
    total = 0
    for r, c in find_pieces(board, player):
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            while 0 <= nr < 6 and 0 <= nc < 6 and board[nr, nc] == 0:
                total += 1
                nr += dr
                nc += dc
    return total


def queen_distance_map(board, starts):
    # Multi-source expansion where one queen move along any unobstructed ray costs 1.
    dist = np.full((6, 6), 99, dtype=np.int16)
    frontier = []
    for r, c in starts:
        dist[r, c] = 0
        frontier.append((r, c))
    head = 0
    while head < len(frontier):
        r, c = frontier[head]
        head += 1
        nd = dist[r, c] + 1
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            while 0 <= nr < 6 and 0 <= nc < 6 and board[nr, nc] == 0:
                if nd < dist[nr, nc]:
                    dist[nr, nc] = nd
                    frontier.append((nr, nc))
                nr += dr
                nc += dc
    return dist


def territory_score(board):
    my_starts = find_pieces(board, 1)
    op_starts = find_pieces(board, 2)
    d1 = queen_distance_map(board, my_starts)
    d2 = queen_distance_map(board, op_starts)

    score = 0.0
    empties = np.argwhere(board == 0)
    for r, c in empties:
        a = int(d1[r, c])
        b = int(d2[r, c])
        if a < b:
            score += 1.0
            score += 0.15 * max(0, b - a - 1)
        elif b < a:
            score -= 1.0
            score -= 0.15 * max(0, a - b - 1)
        else:
            if a < 99:
                score += 0.05
    return score


def evaluate(board):
    my_moves = count_mobility(board, 1)
    op_moves = count_mobility(board, 2)

    # Terminal-like handling
    if my_moves == 0 and op_moves == 0:
        return 0.0
    if op_moves == 0:
        return 1e7
    if my_moves == 0:
        return -1e7

    terr = territory_score(board)

    # Light local-space heuristic around each amazon
    my_pieces = find_pieces(board, 1)
    op_pieces = find_pieces(board, 2)

    def local_free(pieces):
        s = 0
        for r, c in pieces:
            for dr, dc in DIRS:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 6 and 0 <= nc < 6 and board[nr, nc] == 0:
                    s += 1
        return s

    local = local_free(my_pieces) - local_free(op_pieces)

    return 3.0 * (my_moves - op_moves) + 8.0 * terr + 0.8 * local


def move_heuristic(board, move):
    nb = apply_move(board, move, 1)
    # Cheap but informative ordering/evaluation
    my_mob = count_mobility(nb, 1)
    op_mob = count_mobility(nb, 2)
    fr, fc, tr, tc, ar, ac = move

    # Prefer longer relocations and arrows that block central/open squares
    move_len = max(abs(tr - fr), abs(tc - fc))
    arrow_len = max(abs(ar - tr), abs(ac - tc))
    center_bonus = 5 - (abs(ar - 2.5) + abs(ac - 2.5))

    return 2.5 * (my_mob - op_mob) + 0.6 * move_len + 0.3 * arrow_len + 0.4 * center_bonus


def order_moves(board, moves, maximizing_player):
    if not moves:
        return moves
    if maximizing_player:
        scored = [(move_heuristic(board, m), m) for m in moves]
        scored.sort(key=lambda x: x[0], reverse=True)
    else:
        # For opponent, estimate by flipping perspective cheaply
        scored = []
        for m in moves:
            nb = apply_move(board, m, 2)
            val = count_mobility(nb, 2) - count_mobility(nb, 1)
            scored.append((val, m))
        scored.sort(key=lambda x: x[0], reverse=True)
    return [m for _, m in scored]


class SearchTimeout(Exception):
    pass


def alphabeta(board, depth, alpha, beta, player, start_time, time_limit):
    if time.time() - start_time > time_limit:
        raise SearchTimeout

    moves = legal_moves(board, player)

    if depth == 0 or not moves:
        if not moves:
            # Current player cannot move => loses
            return (-1e7 if player == 1 else 1e7), None
        return evaluate(board), None

    maximizing = (player == 1)
    moves = order_moves(board, moves, maximizing)

    best_move = moves[0]

    if maximizing:
        value = -INF
        for m in moves:
            nb = apply_move(board, m, 1)
            child_val, _ = alphabeta(nb, depth - 1, alpha, beta, 2, start_time, time_limit)
            if child_val > value:
                value = child_val
                best_move = m
            if value > alpha:
                alpha = value
            if alpha >= beta:
                break
        return value, best_move
    else:
        value = INF
        for m in moves:
            nb = apply_move(board, m, 2)
            child_val, _ = alphabeta(nb, depth - 1, alpha, beta, 1, start_time, time_limit)
            if child_val < value:
                value = child_val
                best_move = m
            if value < beta:
                beta = value
            if alpha >= beta:
                break
        return value, best_move


def choose_fallback(board):
    moves = legal_moves(board, 1)
    if not moves:
        return "0,0:0,0:0,0"
    best = None
    best_score = -INF
    # Heuristic-only selection
    for m in moves:
        s = move_heuristic(board, m)
        if s > best_score:
            best_score = s
            best = m
    return move_to_str(best)


def policy(board) -> str:
    try:
        board = np.asarray(board)
        my_moves = legal_moves(board, 1)
        if not my_moves:
            return "0,0:0,0:0,0"

        # Immediate fallback
        fallback = max(my_moves, key=lambda m: move_heuristic(board, m))

        start_time = time.time()
        time_limit = 0.92

        best_move = fallback

        # If branching is huge, pre-trim candidates for root
        root_moves = order_moves(board, my_moves, True)
        if len(root_moves) > 80:
            root_moves = root_moves[:80]
        elif len(root_moves) > 50:
            root_moves = root_moves[:60]

        # Iterative deepening
        depth = 1
        while True:
            if time.time() - start_time > time_limit:
                break

            current_best = best_move
            current_best_val = -INF
            alpha, beta = -INF, INF

            try:
                for m in root_moves:
                    if time.time() - start_time > time_limit:
                        raise SearchTimeout
                    nb = apply_move(board, m, 1)
                    val, _ = alphabeta(nb, depth - 1, alpha, beta, 2, start_time, time_limit)
                    if val > current_best_val:
                        current_best_val = val
                        current_best = m
                    if val > alpha:
                        alpha = val
                best_move = current_best
                depth += 1
                if depth > 4 and len(root_moves) > 25:
                    break
                if depth > 5:
                    break
            except SearchTimeout:
                break

        return move_to_str(best_move)

    except Exception:
        # Robustness: always try to return a legal move
        try:
            return choose_fallback(np.asarray(board))
        except Exception:
            return "0,0:0,0:0,0"
