
import time
import math
import numpy as np

DIRS = ((-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1))

N = 6
TIME_LIMIT = 0.92


def policy(board) -> str:
    start = time.time()
    b = np.array(board, copy=True)
    fallback = None

    try:
        moves = gen_moves(b, 1)
        if not moves:
            return "0,0:0,0:0,0"

        fallback = move_to_str(moves[0])

        # Immediate tactical win: opponent has no legal move after this.
        best_quick = None
        best_quick_score = -10**9
        ordered = order_moves(b, moves, 1, limit=80)
        for m in ordered:
            nb = apply_move(b, m, 1)
            opp_count = count_moves_capped(nb, 2, 1)
            if opp_count == 0:
                return move_to_str(m)
            sc = evaluate(nb)
            if sc > best_quick_score:
                best_quick_score = sc
                best_quick = m
            if time.time() - start > TIME_LIMIT * 0.25:
                break

        best = best_quick if best_quick is not None else moves[0]
        move_count = len(moves)

        # Choose depth based on branching. 6x6 is small but branching can still spike.
        if move_count <= 18:
            max_depth = 3
        elif move_count <= 45:
            max_depth = 2
        else:
            max_depth = 1

        # Iterative deepening for robustness.
        for depth in range(1, max_depth + 1):
            if time.time() - start > TIME_LIMIT:
                break
            val, bm = search_root(b, depth, start)
            if bm is not None:
                best = bm

        return move_to_str(best)

    except Exception:
        if fallback:
            return fallback
        try:
            ms = gen_moves(b, 1)
            if ms:
                return move_to_str(ms[0])
        except Exception:
            pass
        return "0,0:0,0:0,0"


def move_to_str(m):
    return f"{m[0]},{m[1]}:{m[2]},{m[3]}:{m[4]},{m[5]}"


def inb(r, c):
    return 0 <= r < N and 0 <= c < N


def ray_squares(board, r, c):
    out = []
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        while 0 <= nr < N and 0 <= nc < N and board[nr, nc] == 0:
            out.append((nr, nc))
            nr += dr
            nc += dc
    return out


def gen_moves(board, player):
    moves = []
    pieces = np.argwhere(board == player)
    for fr, fc in pieces:
        fr = int(fr); fc = int(fc)
        for dr, dc in DIRS:
            tr, tc = fr + dr, fc + dc
            while inb(tr, tc) and board[tr, tc] == 0:
                # Temporarily move for arrow generation.
                board[fr, fc] = 0
                board[tr, tc] = player
                for adr, adc in DIRS:
                    ar, ac = tr + adr, tc + adc
                    while inb(ar, ac) and board[ar, ac] == 0:
                        moves.append((fr, fc, tr, tc, ar, ac))
                        ar += adr
                        ac += adc
                board[tr, tc] = 0
                board[fr, fc] = player
                tr += dr
                tc += dc
    return moves


def count_moves_capped(board, player, cap):
    cnt = 0
    pieces = np.argwhere(board == player)
    for fr, fc in pieces:
        fr = int(fr); fc = int(fc)
        for dr, dc in DIRS:
            tr, tc = fr + dr, fc + dc
            while inb(tr, tc) and board[tr, tc] == 0:
                board[fr, fc] = 0
                board[tr, tc] = player
                for adr, adc in DIRS:
                    ar, ac = tr + adr, tc + adc
                    while inb(ar, ac) and board[ar, ac] == 0:
                        cnt += 1
                        if cnt >= cap:
                            board[tr, tc] = 0
                            board[fr, fc] = player
                            return cnt
                        ar += adr
                        ac += adc
                board[tr, tc] = 0
                board[fr, fc] = player
                tr += dr
                tc += dc
    return cnt


def apply_move(board, m, player):
    nb = board.copy()
    fr, fc, tr, tc, ar, ac = m
    nb[fr, fc] = 0
    nb[tr, tc] = player
    nb[ar, ac] = -1
    return nb


def do_move_inplace(board, m, player):
    fr, fc, tr, tc, ar, ac = m
    board[fr, fc] = 0
    board[tr, tc] = player
    board[ar, ac] = -1


def undo_move_inplace(board, m, player):
    fr, fc, tr, tc, ar, ac = m
    board[ar, ac] = 0
    board[tr, tc] = 0
    board[fr, fc] = player


def search_root(board, depth, start):
    alpha = -10**9
    beta = 10**9
    best = None
    moves = gen_moves(board, 1)
    moves = order_moves(board, moves, 1, limit=70 if depth >= 2 else 120)

    for m in moves:
        if time.time() - start > TIME_LIMIT:
            break
        do_move_inplace(board, m, 1)
        if count_moves_capped(board, 2, 1) == 0:
            undo_move_inplace(board, m, 1)
            return 10**8, m
        val = alphabeta(board, depth - 1, alpha, beta, 2, start)
        undo_move_inplace(board, m, 1)
        if val > alpha:
            alpha = val
            best = m
    return alpha, best


def alphabeta(board, depth, alpha, beta, player, start):
    if time.time() - start > TIME_LIMIT:
        return evaluate(board)

    legal_exists = count_moves_capped(board, player, 1)
    if legal_exists == 0:
        return -10**7 if player == 1 else 10**7

    if depth <= 0:
        return evaluate(board)

    moves = gen_moves(board, player)
    moves = order_moves(board, moves, player, limit=45 if depth >= 2 else 65)

    if player == 1:
        v = -10**9
        for m in moves:
            do_move_inplace(board, m, 1)
            sc = alphabeta(board, depth - 1, alpha, beta, 2, start)
            undo_move_inplace(board, m, 1)
            if sc > v:
                v = sc
            if v > alpha:
                alpha = v
            if alpha >= beta or time.time() - start > TIME_LIMIT:
                break
        return v
    else:
        v = 10**9
        for m in moves:
            do_move_inplace(board, m, 2)
            sc = alphabeta(board, depth - 1, alpha, beta, 1, start)
            undo_move_inplace(board, m, 2)
            if sc < v:
                v = sc
            if v < beta:
                beta = v
            if alpha >= beta or time.time() - start > TIME_LIMIT:
                break
        return v


def order_moves(board, moves, player, limit=None):
    if not moves:
        return moves

    scored = []
    opponent = 3 - player
    for m in moves:
        fr, fc, tr, tc, ar, ac = m
        # Prefer central/active landings, arrows near opponent, and maintaining own mobility.
        center = -((tr - 2.5) ** 2 + (tc - 2.5) ** 2)
        arrow_center = -0.25 * ((ar - 2.5) ** 2 + (ac - 2.5) ** 2)
        opp_pressure = 0
        for pr, pc in np.argwhere(board == opponent):
            d = max(abs(int(pr) - ar), abs(int(pc) - ac))
            opp_pressure += 5 - d
        own_escape = 0
        # Approximate landing mobility after vacating from and before arrow.
        board[fr, fc] = 0
        board[tr, tc] = player
        board[ar, ac] = -1
        own_escape = len(ray_squares(board, tr, tc))
        board[ar, ac] = 0
        board[tr, tc] = 0
        board[fr, fc] = player
        scored.append((center * 3 + arrow_center + opp_pressure * 1.5 + own_escape * 2, m))

    scored.sort(reverse=True, key=lambda x: x[0])
    ordered = [m for _, m in scored]
    if limit is not None and len(ordered) > limit:
        return ordered[:limit]
    return ordered


def queen_distance_map(board, player):
    dist = np.full((N, N), 99, dtype=np.int16)
    frontier = []
    for r, c in np.argwhere(board == player):
        r = int(r); c = int(c)
        dist[r, c] = 0
        frontier.append((r, c))

    q = frontier[:]
    head = 0
    while head < len(q):
        r, c = q[head]
        head += 1
        nd = dist[r, c] + 1
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            while inb(nr, nc) and board[nr, nc] == 0:
                if nd < dist[nr, nc]:
                    dist[nr, nc] = nd
                    q.append((nr, nc))
                nr += dr
                nc += dc
    return dist


def mobility_simple(board, player):
    total = 0
    for r, c in np.argwhere(board == player):
        total += len(ray_squares(board, int(r), int(c)))
    return total


def evaluate(board):
    # Terminal-ish mobility check, capped for speed.
    my_has = count_moves_capped(board, 1, 1)
    op_has = count_moves_capped(board, 2, 1)
    if my_has == 0:
        return -10**7
    if op_has == 0:
        return 10**7

    my_qmob = mobility_simple(board, 1)
    op_qmob = mobility_simple(board, 2)

    # Legal move mobility capped gives tactical freedom without full expensive counts.
    my_moves = count_moves_capped(board, 1, 80)
    op_moves = count_moves_capped(board, 2, 80)

    d1 = queen_distance_map(board, 1)
    d2 = queen_distance_map(board, 2)

    terr = 0
    reach = 0
    for r in range(N):
        for c in range(N):
            if board[r, c] == 0:
                a = d1[r, c]
                o = d2[r, c]
                if a < o:
                    terr += 1
                elif o < a:
                    terr -= 1
                if a < 99:
                    reach += 1
                if o < 99:
                    reach -= 1
                if a < 99 and o < 99:
                    terr += max(-3, min(3, int(o) - int(a))) * 0.25

    # Slight preference for occupying useful central squares.
    center_score = 0.0
    for r, c in np.argwhere(board == 1):
        center_score -= ((int(r) - 2.5) ** 2 + (int(c) - 2.5) ** 2) * 0.4
    for r, c in np.argwhere(board == 2):
        center_score += ((int(r) - 2.5) ** 2 + (int(c) - 2.5) ** 2) * 0.4

    return (my_moves - op_moves) * 3.0 + (my_qmob - op_qmob) * 5.0 + terr * 18.0 + reach * 6.0 + center_score
