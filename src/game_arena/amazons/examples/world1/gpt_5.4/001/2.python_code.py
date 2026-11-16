
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


def apply_move(board, move, player=1):
    fr, fc, tr, tc, ar, ac = move
    nb = board.copy()
    nb[fr, fc] = 0
    nb[tr, tc] = player
    nb[ar, ac] = -1
    return nb


def legal_moves(board, player=1):
    pieces = np.argwhere(board == player)
    moves = []
    for fr, fc in pieces:
        tos = queen_reach(board, fr, fc)
        if not tos:
            continue
        for tr, tc in tos:
            tmp = board.copy()
            tmp[fr, fc] = 0
            tmp[tr, tc] = player
            for ar, ac in queen_reach(tmp, tr, tc):
                moves.append((int(fr), int(fc), int(tr), int(tc), int(ar), int(ac)))
    return moves


def amazon_mobility(board, player):
    pieces = np.argwhere(board == player)
    total = 0
    per_piece = []
    for r, c in pieces:
        m = len(queen_reach(board, int(r), int(c)))
        total += m
        per_piece.append(m)
    return total, per_piece


def shortest_queen_steps(board, starts):
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
            while 0 <= nr < 6 and 0 <= nc < 6 and board[nr, nc] == 0:
                if dist[nr, nc] > nd:
                    dist[nr, nc] = nd
                    q.append((nr, nc))
                nr += dr
                nc += dc
    return dist


def territory_score(board):
    my_pos = [tuple(x) for x in np.argwhere(board == 1)]
    op_pos = [tuple(x) for x in np.argwhere(board == 2)]
    if not my_pos or not op_pos:
        return 0.0

    d1 = shortest_queen_steps(board, my_pos)
    d2 = shortest_queen_steps(board, op_pos)

    score = 0.0
    empties = np.argwhere(board == 0)
    for r, c in empties:
        a = d1[r, c]
        b = d2[r, c]
        if a < b:
            score += 1.0
        elif b < a:
            score -= 1.0
        elif a < 99:
            score += 0.1 if a == b else 0.0
    return score


def evaluate(board):
    my_moves = legal_moves(board, 1)
    op_moves = legal_moves(board, 2)

    if not my_moves and not op_moves:
        return 0.0
    if not my_moves:
        return -1e9
    if not op_moves:
        return 1e9

    my_mob, my_piece_mob = amazon_mobility(board, 1)
    op_mob, op_piece_mob = amazon_mobility(board, 2)

    terr = territory_score(board)

    my_trapped = sum(1 for x in my_piece_mob if x == 0)
    op_trapped = sum(1 for x in op_piece_mob if x == 0)

    score = 0.0
    score += 2.5 * (len(my_moves) - len(op_moves))
    score += 1.2 * (my_mob - op_mob)
    score += 3.0 * terr
    score += 18.0 * (op_trapped - my_trapped)
    return score


def move_order_key(board, move):
    nb = apply_move(board, move, 1)
    my_mob, _ = amazon_mobility(nb, 1)
    op_mob, op_piece = amazon_mobility(nb, 2)
    op_trapped = sum(1 for x in op_piece if x == 0)
    return (op_trapped * 1000) + (my_mob - 1.5 * op_mob)


def policy(board) -> str:
    try:
        board = np.asarray(board)
        moves = legal_moves(board, 1)
        if not moves:
            # Robust fallback; environment says this should not happen.
            # Return a syntactically valid string.
            return "0,0:0,0:0,0"

        # Preorder moves cheaply.
        if len(moves) > 1:
            scored = []
            for mv in moves:
                scored.append((move_order_key(board, mv), mv))
            scored.sort(reverse=True, key=lambda x: x[0])

            # Keep promising subset for deeper look.
            if len(scored) > 40:
                candidate_moves = [mv for _, mv in scored[:40]]
            else:
                candidate_moves = [mv for _, mv in scored]
        else:
            candidate_moves = moves

        best_move = candidate_moves[0]
        best_score = -INF

        # Adaptive depth-1 minimax with heuristic leaf eval.
        # Full opponent replies only on a reduced candidate set.
        for mv in candidate_moves:
            nb = apply_move(board, mv, 1)

            op_moves = legal_moves(nb, 2)
            if not op_moves:
                score = 1e9
            else:
                # Order opponent replies by how bad they look for us.
                if len(op_moves) > 1:
                    op_scored = []
                    for omv in op_moves:
                        rb = apply_move(nb, omv, 2)
                        # quick proxy from our perspective after opponent move
                        my_mob, _ = amazon_mobility(rb, 1)
                        op_mob, op_piece = amazon_mobility(rb, 2)
                        op_trapped = sum(1 for x in op_piece if x == 0)
                        proxy = (op_mob - my_mob) - 5 * op_trapped
                        op_scored.append((proxy, omv))
                    op_scored.sort(reverse=True, key=lambda x: x[0])

                    # Limit reply width for speed.
                    limit = 18 if len(candidate_moves) <= 16 else 12
                    op_candidates = [omv for _, omv in op_scored[:limit]]
                else:
                    op_candidates = op_moves

                worst = INF
                for omv in op_candidates:
                    rb = apply_move(nb, omv, 2)
                    val = evaluate(rb)
                    if val < worst:
                        worst = val
                score = worst

                # Small bonus for the position before reply to break ties.
                score += 0.15 * evaluate(nb)

            if score > best_score:
                best_score = score
                best_move = mv

        fr, fc, tr, tc, ar, ac = best_move
        return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"

    except Exception:
        # Strong legal fallback in case of any unexpected issue.
        board = np.asarray(board)
        pieces = np.argwhere(board == 1)
        for fr, fc in pieces:
            tos = queen_reach(board, int(fr), int(fc))
            for tr, tc in tos:
                tmp = board.copy()
                tmp[int(fr), int(fc)] = 0
                tmp[int(tr), int(tc)] = 1
                arrs = queen_reach(tmp, int(tr), int(tc))
                if arrs:
                    ar, ac = arrs[0]
                    return f"{int(fr)},{int(fc)}:{int(tr)},{int(tc)}:{int(ar)},{int(ac)}"
        return "0,0:0,0:0,0"
