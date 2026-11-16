
import numpy as np

# 6x6 Amazons policy

DIRS = [(-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)]

INF = 10**9


def in_bounds(r, c):
    return 0 <= r < 6 and 0 <= c < 6


def iter_rays(board, r, c):
    """Yield all reachable squares from (r,c) by queen movement on current board."""
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        while in_bounds(nr, nc) and board[nr, nc] == 0:
            yield nr, nc
            nr += dr
            nc += dc


def legal_moves_for_player(board, player):
    """
    Return list of moves as tuples:
    (fr, fc, tr, tc, ar, ac)
    """
    moves = []
    pieces = np.argwhere(board == player)
    if len(pieces) == 0:
        return moves

    for fr, fc in pieces:
        for tr, tc in iter_rays(board, fr, fc):
            # make temporary move
            board[fr, fc] = 0
            board[tr, tc] = player

            for ar, ac in iter_rays(board, tr, tc):
                moves.append((fr, fc, tr, tc, ar, ac))

            # undo
            board[tr, tc] = 0
            board[fr, fc] = player
    return moves


def apply_move(board, move, player):
    fr, fc, tr, tc, ar, ac = move
    nb = board.copy()
    nb[fr, fc] = 0
    nb[tr, tc] = player
    nb[ar, ac] = -1
    return nb


def mobility_count(board, player):
    count = 0
    pieces = np.argwhere(board == player)
    for r, c in pieces:
        for _ in iter_rays(board, r, c):
            count += 1
    return count


def local_arrow_pressure(board, arrow_r, arrow_c):
    """Reward arrows near opponent and central-ish blocking."""
    score = 0.0
    opps = np.argwhere(board == 2)
    for r, c in opps:
        d = max(abs(r - arrow_r), abs(c - arrow_c))
        score += max(0, 3 - d)
    center_dist = abs(arrow_r - 2.5) + abs(arrow_c - 2.5)
    score += (5.0 - center_dist) * 0.15
    return score


def queen_distance_map(board, starts):
    """
    Multi-source queen-move distance map:
    each move can travel any distance along a clear ray.
    Obstacles are nonzero cells.
    """
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
            while in_bounds(nr, nc) and board[nr, nc] == 0:
                if dist[nr, nc] > nd:
                    dist[nr, nc] = nd
                    q.append((nr, nc))
                nr += dr
                nc += dc
    return dist


def territory_score(board):
    """
    Compare queen-distance reachability of empty cells.
    Positive is good for player 1.
    """
    my_pos = [tuple(x) for x in np.argwhere(board == 1)]
    op_pos = [tuple(x) for x in np.argwhere(board == 2)]
    if not my_pos and not op_pos:
        return 0.0
    myd = queen_distance_map(board, my_pos) if my_pos else np.full((6, 6), 99, dtype=np.int16)
    opd = queen_distance_map(board, op_pos) if op_pos else np.full((6, 6), 99, dtype=np.int16)

    score = 0.0
    empties = np.argwhere(board == 0)
    for r, c in empties:
        a = myd[r, c]
        b = opd[r, c]
        if a < b:
            score += 1.0
        elif b < a:
            score -= 1.0
        elif a < 99:
            score += 0.1  # slight tie preference if both can reach
    return score


def evaluate(board):
    """
    Static eval from player 1 perspective.
    """
    my_moves = legal_moves_for_player(board, 1)
    if not my_moves:
        return -INF
    op_moves = legal_moves_for_player(board, 2)
    if not op_moves:
        return INF

    my_mob = 0
    for r, c in np.argwhere(board == 1):
        for _ in iter_rays(board, r, c):
            my_mob += 1

    op_mob = 0
    for r, c in np.argwhere(board == 2):
        for _ in iter_rays(board, r, c):
            op_mob += 1

    terr = territory_score(board)
    return 4.0 * (len(my_moves) - len(op_moves)) + 1.5 * (my_mob - op_mob) + 3.0 * terr


def quick_move_score(board, move):
    """
    Fast heuristic for ranking candidate moves before deeper reply check.
    """
    fr, fc, tr, tc, ar, ac = move
    nb = apply_move(board, move, 1)

    # Immediate terminal checks
    op_legal = legal_moves_for_player(nb, 2)
    if not op_legal:
        return INF / 2

    my_mob = mobility_count(nb, 1)
    op_mob = mobility_count(nb, 2)
    terr = territory_score(nb)

    # Encourage moving toward center-ish regions if useful
    center_gain = (abs(fr - 2.5) + abs(fc - 2.5)) - (abs(tr - 2.5) + abs(tc - 2.5))
    pressure = local_arrow_pressure(nb, ar, ac)

    return 2.5 * (my_mob - op_mob) + 3.0 * terr + 0.35 * center_gain + 0.5 * pressure


def opponent_quick_score(board, move):
    """
    Rank opponent replies on resulting board, from opponent's perspective.
    Higher is better for opponent.
    """
    nb = apply_move(board, move, 2)
    my_legal = legal_moves_for_player(nb, 1)
    if not my_legal:
        return INF / 2  # great for opponent
    op_legal = legal_moves_for_player(nb, 2)
    if not op_legal:
        return -INF / 2

    # Evaluate from opponent perspective = negative of our viewpoint approximation
    my_mob = mobility_count(nb, 1)
    op_mob = mobility_count(nb, 2)
    terr = territory_score(nb)
    _, _, _, _, ar, ac = move
    pressure = local_arrow_pressure(nb, ar, ac)
    return 2.5 * (op_mob - my_mob) - 3.0 * terr + 0.5 * pressure


def move_to_str(move):
    fr, fc, tr, tc, ar, ac = move
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"


def policy(board) -> str:
    board = np.array(board, copy=True)
    try:
        legal = legal_moves_for_player(board, 1)
        if not legal:
            # Robust fallback; environment says this shouldn't happen.
            return "0,0:0,0:0,0"

        # Guaranteed legal fallback
        fallback = legal[0]

        # Rank our moves quickly
        scored = []
        for mv in legal:
            scored.append((quick_move_score(board, mv), mv))
        scored.sort(key=lambda x: x[0], reverse=True)

        # Search top candidates only for speed
        top_k = 12 if len(scored) > 12 else len(scored)
        best_move = scored[0][1]
        best_value = -INF

        for i in range(top_k):
            _, my_move = scored[i]
            nb = apply_move(board, my_move, 1)

            op_legal = legal_moves_for_player(nb, 2)
            if not op_legal:
                return move_to_str(my_move)

            # Opponent top replies
            op_scored = []
            for omv in op_legal:
                op_scored.append((opponent_quick_score(nb, omv), omv))
            op_scored.sort(key=lambda x: x[0], reverse=True)

            op_top_k = 8 if len(op_scored) > 8 else len(op_scored)

            worst_for_us = INF
            for j in range(op_top_k):
                _, op_move = op_scored[j]
                nb2 = apply_move(nb, op_move, 2)
                val = evaluate(nb2)
                if val < worst_for_us:
                    worst_for_us = val

            # If we sampled only top replies, combine with immediate heuristic
            combined = worst_for_us + 0.15 * scored[i][0]
            if combined > best_value:
                best_value = combined
                best_move = my_move

        return move_to_str(best_move)

    except Exception:
        # Must always return a legal move string if possible
        try:
            legal = legal_moves_for_player(np.array(board, copy=True), 1)
            if legal:
                return move_to_str(legal[0])
        except Exception:
            pass
        return "0,0:0,0:0,0"
