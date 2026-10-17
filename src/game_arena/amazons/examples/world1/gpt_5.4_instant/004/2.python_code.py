
import numpy as np

DIRS = [(-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)]

INF = 10**18

def in_bounds(r, c):
    return 0 <= r < 6 and 0 <= c < 6

def queen_reach(board, r, c):
    out = []
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        while 0 <= nr < 6 and 0 <= nc < 6 and board[nr, nc] == 0:
            out.append((nr, nc))
            nr += dr
            nc += dc
    return out

def count_ray_moves(board, r, c):
    s = 0
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        while 0 <= nr < 6 and 0 <= nc < 6 and board[nr, nc] == 0:
            s += 1
            nr += dr
            nc += dc
    return s

def generate_moves(board, player):
    amazons = np.argwhere(board == player)
    moves = []
    for fr, fc in amazons:
        fr = int(fr); fc = int(fc)
        dests = queen_reach(board, fr, fc)
        if not dests:
            continue
        board[fr, fc] = 0
        for tr, tc in dests:
            board[tr, tc] = player
            for ar, ac in queen_reach(board, tr, tc):
                moves.append((fr, fc, tr, tc, ar, ac))
            board[tr, tc] = 0
        board[fr, fc] = player
    return moves

def mobility(board, player):
    amazons = np.argwhere(board == player)
    total = 0
    for r, c in amazons:
        total += count_ray_moves(board, int(r), int(c))
    return total

def local_territory(board, player):
    # Lightweight territorial estimate: nearby reachability over empty graph.
    dist = np.full((6, 6), 99, dtype=np.int16)
    frontier = []
    for r, c in np.argwhere(board == player):
        r = int(r); c = int(c)
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
                if dist[nr, nc] > nd:
                    dist[nr, nc] = nd
                    frontier.append((nr, nc))
                nr += dr
                nc += dc
    return dist

def evaluate(board):
    my_moves = mobility(board, 1)
    opp_moves = mobility(board, 2)

    if my_moves == 0 and opp_moves == 0:
        return 0
    if my_moves == 0:
        return -10_000_000
    if opp_moves == 0:
        return 10_000_000

    d1 = local_territory(board, 1)
    d2 = local_territory(board, 2)

    terr = 0
    empty_cells = np.argwhere(board == 0)
    for r, c in empty_cells:
        a = d1[r, c]
        b = d2[r, c]
        if a < b:
            terr += 1
        elif b < a:
            terr -= 1

    # Penalize trapped amazons / reward trapping opponent.
    my_trap = 0
    for r, c in np.argwhere(board == 1):
        m = count_ray_moves(board, int(r), int(c))
        if m <= 2:
            my_trap += (3 - m)
    opp_trap = 0
    for r, c in np.argwhere(board == 2):
        m = count_ray_moves(board, int(r), int(c))
        if m <= 2:
            opp_trap += (3 - m)

    return 12 * (my_moves - opp_moves) + 5 * terr + 18 * (opp_trap - my_trap)

def apply_move(board, move, player):
    fr, fc, tr, tc, ar, ac = move
    board[fr, fc] = 0
    board[tr, tc] = player
    board[ar, ac] = -1

def undo_move(board, move, player):
    fr, fc, tr, tc, ar, ac = move
    board[ar, ac] = 0
    board[tr, tc] = 0
    board[fr, fc] = player

def move_order_key(board, move, player):
    fr, fc, tr, tc, ar, ac = move
    opp = 2 if player == 1 else 1

    # Fast heuristic: centrality, destination mobility, arrow restriction.
    center = 5 - (abs(tr - 2.5) + abs(tc - 2.5))
    board[fr, fc] = 0
    board[tr, tc] = player
    dest_mob = count_ray_moves(board, tr, tc)
    # Arrow local blocking value
    block = 0
    for dr, dc in DIRS:
        nr, nc = ar + dr, ac + dc
        if 0 <= nr < 6 and 0 <= nc < 6 and board[nr, nc] == opp:
            block += 2
        elif 0 <= nr < 6 and 0 <= nc < 6 and board[nr, nc] == 0:
            block += 0.2
    board[tr, tc] = 0
    board[fr, fc] = player
    return dest_mob + center + block

def ordered_moves(board, player, limit=None):
    moves = generate_moves(board, player)
    if not moves:
        return moves
    scored = [(move_order_key(board, m, player), m) for m in moves]
    scored.sort(key=lambda x: x[0], reverse=True)
    if limit is not None and len(scored) > limit:
        scored = scored[:limit]
    return [m for _, m in scored]

def alphabeta(board, depth, alpha, beta, player):
    moves = ordered_moves(board, player, limit=24 if depth >= 2 else None)

    if depth == 0 or not moves:
        if not moves:
            return (-10_000_000 if player == 1 else 10_000_000), None
        return evaluate(board), None

    if player == 1:
        best_val = -INF
        best_move = moves[0]
        for m in moves:
            apply_move(board, m, 1)
            val, _ = alphabeta(board, depth - 1, alpha, beta, 2)
            undo_move(board, m, 1)
            if val > best_val:
                best_val = val
                best_move = m
            if best_val > alpha:
                alpha = best_val
            if alpha >= beta:
                break
        return best_val, best_move
    else:
        best_val = INF
        best_move = moves[0]
        for m in moves:
            apply_move(board, m, 2)
            val, _ = alphabeta(board, depth - 1, alpha, beta, 1)
            undo_move(board, m, 2)
            if val < best_val:
                best_val = val
                best_move = m
            if best_val < beta:
                beta = best_val
            if alpha >= beta:
                break
        return best_val, best_move

def format_move(m):
    fr, fc, tr, tc, ar, ac = m
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"

def legal_fallback(board):
    moves = generate_moves(board, 1)
    if moves:
        return format_move(moves[0])

    # Extra-robust fallback in case of unexpected state.
    amazons = np.argwhere(board == 1)
    for fr, fc in amazons:
        fr = int(fr); fc = int(fc)
        for dr, dc in DIRS:
            nr, nc = fr + dr, fc + dc
            while in_bounds(nr, nc) and board[nr, nc] == 0:
                board[fr, fc] = 0
                board[nr, nc] = 1
                for adr, adc in DIRS:
                    ar, ac = nr + adr, nc + adc
                    while in_bounds(ar, ac) and board[ar, ac] == 0:
                        board[nr, nc] = 0
                        board[fr, fc] = 1
                        return f"{fr},{fc}:{nr},{nc}:{ar},{ac}"
                    ar += adr
                    ac += adc
                board[nr, nc] = 0
                board[fr, fc] = 1
                nr += dr
                nc += dc

    # Should never happen if environment is valid.
    return "0,0:0,0:0,0"

def policy(board) -> str:
    board = np.array(board, copy=True)

    try:
        root_moves = ordered_moves(board, 1)
        if not root_moves:
            return legal_fallback(board)

        # Adaptive depth based on branching factor.
        n = len(root_moves)
        if n <= 10:
            depth = 3
        elif n <= 30:
            depth = 2
        else:
            depth = 2

        # Root search with a slightly wider root beam.
        root_list = root_moves[:32] if len(root_moves) > 32 else root_moves
        best_val = -INF
        best_move = root_list[0]

        alpha, beta = -INF, INF
        for m in root_list:
            apply_move(board, m, 1)
            val, _ = alphabeta(board, depth - 1, alpha, beta, 2)
            undo_move(board, m, 1)
            if val > best_val:
                best_val = val
                best_move = m
            if best_val > alpha:
                alpha = best_val

        return format_move(best_move)
    except Exception:
        return legal_fallback(board)
