
import numpy as np

DIRS = [(-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)]

N = 6


def inside(r, c):
    return 0 <= r < N and 0 <= c < N


def ray_moves(board, r, c):
    res = []
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        while inside(nr, nc) and board[nr, nc] == 0:
            res.append((nr, nc))
            nr += dr
            nc += dc
    return res


def apply_move(board, move, player=1):
    fr, fc, tr, tc, ar, ac = move
    nb = board.copy()
    nb[fr, fc] = 0
    nb[tr, tc] = player
    nb[ar, ac] = -1
    return nb


def legal_moves(board, player=1, limit=None):
    pieces = np.argwhere(board == player)
    moves = []
    for fr, fc in pieces:
        tos = ray_moves(board, fr, fc)
        for tr, tc in tos:
            temp = board.copy()
            temp[fr, fc] = 0
            temp[tr, tc] = player
            for ar, ac in ray_moves(temp, tr, tc):
                moves.append((int(fr), int(fc), int(tr), int(tc), int(ar), int(ac)))
                if limit is not None and len(moves) >= limit:
                    return moves
    return moves


def mobility(board, player):
    pieces = np.argwhere(board == player)
    total = 0
    for r, c in pieces:
        total += len(ray_moves(board, int(r), int(c)))
    return total


def reachability_score(board):
    my_dist = multi_source_steps(board, 1)
    op_dist = multi_source_steps(board, 2)
    score = 0.0
    for r in range(N):
        for c in range(N):
            if board[r, c] != 0:
                continue
            md = my_dist[r][c]
            od = op_dist[r][c]
            if md < od:
                score += 1.0
            elif md > od:
                score -= 1.0
            elif md < 999:
                score += 0.1 if md > 0 else 0.0
    return score


def multi_source_steps(board, player):
    INF = 999
    dist = [[INF] * N for _ in range(N)]
    starts = np.argwhere(board == player)
    frontier = []
    for r, c in starts:
        r = int(r); c = int(c)
        dist[r][c] = 0
        frontier.append((r, c))
    head = 0
    while head < len(frontier):
        r, c = frontier[head]
        head += 1
        nd = dist[r][c] + 1
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            while inside(nr, nc) and board[nr, nc] == 0:
                if dist[nr][nc] > nd:
                    dist[nr][nc] = nd
                    frontier.append((nr, nc))
                nr += dr
                nc += dc
    return dist


def center_bonus(r, c):
    return -((r - 2.5) ** 2 + (c - 2.5) ** 2)


def evaluate(board):
    my_moves = legal_moves(board, 1, limit=2000)
    op_moves = legal_moves(board, 2, limit=2000)

    if not my_moves:
        return -1e9
    if not op_moves:
        return 1e9

    my_mob = mobility(board, 1)
    op_mob = mobility(board, 2)

    my_pos = np.argwhere(board == 1)
    op_pos = np.argwhere(board == 2)

    pos_score = 0.0
    for r, c in my_pos:
        pos_score += 0.15 * center_bonus(int(r), int(c))
    for r, c in op_pos:
        pos_score -= 0.15 * center_bonus(int(r), int(c))

    terr = reachability_score(board)

    return 4.0 * (my_mob - op_mob) + 2.0 * terr + pos_score + 0.05 * (len(my_moves) - len(op_moves))


def quick_move_score(board, move):
    fr, fc, tr, tc, ar, ac = move
    nb = apply_move(board, move, 1)

    op_mob = mobility(nb, 2)
    my_mob = mobility(nb, 1)

    score = 3.0 * (my_mob - op_mob)
    score += 0.2 * center_bonus(tr, tc)

    # Encourage arrows that constrain nearby lanes around opponent pieces
    opps = np.argwhere(nb == 2)
    near = 0
    for r, c in opps:
        r = int(r); c = int(c)
        d = max(abs(ar - r), abs(ac - c))
        if d <= 2:
            near += (3 - d)
    score += 0.8 * near

    # Slight preference for keeping moved amazon flexible
    temp = nb.copy()
    temp[tr, tc] = 1
    score += 0.3 * len(ray_moves(temp, tr, tc))

    return score


def ordered_moves(board, player, max_consider=None):
    moves = legal_moves(board, player)
    if not moves:
        return moves

    if player == 1:
        scored = [(quick_move_score(board, m), m) for m in moves]
        scored.sort(key=lambda x: x[0], reverse=True)
    else:
        # For opponent ordering, estimate from their perspective by swapping labels
        scored = []
        for m in moves:
            nb = apply_move(board, m, 2)
            val = mobility(nb, 2) - mobility(nb, 1)
            scored.append((val, m))
        scored.sort(key=lambda x: x[0], reverse=True)

    ordered = [m for _, m in scored]
    if max_consider is not None and len(ordered) > max_consider:
        ordered = ordered[:max_consider]
    return ordered


def minimax(board, depth, alpha, beta, maximizing):
    if depth == 0:
        return evaluate(board)

    player = 1 if maximizing else 2
    moves = ordered_moves(board, player, max_consider=24 if depth >= 2 else 40)

    if not moves:
        return -1e9 if maximizing else 1e9

    if maximizing:
        value = -1e18
        for m in moves:
            nb = apply_move(board, m, 1)
            value = max(value, minimax(nb, depth - 1, alpha, beta, False))
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value
    else:
        value = 1e18
        for m in moves:
            nb = apply_move(board, m, 2)
            value = min(value, minimax(nb, depth - 1, alpha, beta, True))
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value


def move_to_str(move):
    fr, fc, tr, tc, ar, ac = move
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"


def policy(board) -> str:
    board = np.asarray(board)
    moves = legal_moves(board, 1)
    if not moves:
        # Robust fallback; environment says this should not happen.
        return "0,0:0,0:0,0"

    # Safe fallback is always legal because taken from generated moves.
    fallback = moves[0]

    ordered = ordered_moves(board, 1, max_consider=30)

    # Dynamic depth based on branching factor.
    total = len(moves)
    if total <= 8:
        depth = 3
    elif total <= 25:
        depth = 2
    else:
        depth = 1

    best_move = fallback
    best_val = -1e18

    try:
        if depth == 1:
            for m in ordered:
                nb = apply_move(board, m, 1)
                v = evaluate(nb)
                if v > best_val:
                    best_val = v
                    best_move = m
        else:
            for m in ordered:
                nb = apply_move(board, m, 1)
                v = minimax(nb, depth - 1, -1e18, 1e18, False)
                if v > best_val:
                    best_val = v
                    best_move = m
    except Exception:
        best_move = fallback

    return move_to_str(best_move)
