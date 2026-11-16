
import numpy as np

# 8 queen directions
DIRS = [(-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)]

N = 6
INF = 10**18


def inside(r, c):
    return 0 <= r < N and 0 <= c < N


def ray_moves(board, r, c):
    """All reachable squares by queen move from (r,c) on current board."""
    out = []
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        while 0 <= nr < N and 0 <= nc < N and board[nr, nc] == 0:
            out.append((nr, nc))
            nr += dr
            nc += dc
    return out


def legal_moves(board, player=1):
    """Generate legal moves as tuples (fr,fc,tr,tc,ar,ac)."""
    amazons = np.argwhere(board == player)
    moves = []
    for fr, fc in amazons:
        tos = ray_moves(board, fr, fc)
        if not tos:
            continue
        for tr, tc in tos:
            board[fr, fc] = 0
            board[tr, tc] = player
            for ar, ac in ray_moves(board, tr, tc):
                moves.append((int(fr), int(fc), int(tr), int(tc), int(ar), int(ac)))
            board[tr, tc] = 0
            board[fr, fc] = player
    return moves


def apply_move(board, move, player=1):
    fr, fc, tr, tc, ar, ac = move
    nb = board.copy()
    nb[fr, fc] = 0
    nb[tr, tc] = player
    nb[ar, ac] = -1
    return nb


def swap_players(board):
    """Return board from opponent perspective: 1<->2."""
    nb = board.copy()
    nb[board == 1] = 2
    nb[board == 2] = 1
    return nb


def mobility_count(board, player):
    cnt = 0
    for r, c in np.argwhere(board == player):
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            while 0 <= nr < N and 0 <= nc < N and board[nr, nc] == 0:
                cnt += 1
                nr += dr
                nc += dc
    return cnt


def queen_distance_map(board, player):
    """
    Multi-source shortest queen-move distance to each empty square.
    Distance counts number of queen moves needed ignoring move-then-arrow dynamics.
    """
    dist = np.full((N, N), 99, dtype=np.int16)
    frontier = []
    for r, c in np.argwhere(board == player):
        dist[r, c] = 0
        frontier.append((int(r), int(c)))

    qi = 0
    while qi < len(frontier):
        r, c = frontier[qi]
        qi += 1
        nd = dist[r, c] + 1
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            while 0 <= nr < N and 0 <= nc < N:
                if board[nr, nc] != 0:
                    break
                if dist[nr, nc] < nd:
                    nr += dr
                    nc += dc
                    continue
                if dist[nr, nc] == 99:
                    dist[nr, nc] = nd
                    frontier.append((nr, nc))
                nr += dr
                nc += dc
    return dist


def territory_score(board):
    """
    Estimate territorial control by comparing queen distances from both sides.
    Positive is good for player 1.
    """
    d1 = queen_distance_map(board, 1)
    d2 = queen_distance_map(board, 2)
    score = 0.0
    empties = np.argwhere(board == 0)
    for r, c in empties:
        a = int(d1[r, c])
        b = int(d2[r, c])
        if a < b:
            score += 1.0
        elif a > b:
            score -= 1.0
        elif a != 99:
            score += 0.15 if a > 0 else 0.0
    return score


def amazon_liberties(board, player):
    """Sum of immediate queen destinations for each amazon."""
    s = 0
    for r, c in np.argwhere(board == player):
        s += len(ray_moves(board, int(r), int(c)))
    return s


def evaluate(board):
    my_moves = legal_moves(board, 1)
    if not my_moves:
        return -INF // 2
    opp_board = swap_players(board)
    opp_moves = legal_moves(opp_board, 1)
    if not opp_moves:
        return INF // 2

    my_mob = len(my_moves)
    opp_mob = len(opp_moves)

    my_lib = amazon_liberties(board, 1)
    opp_lib = amazon_liberties(board, 2)

    terr = territory_score(board)

    # Weighted combination
    score = (
        2.4 * (my_mob - opp_mob) +
        1.2 * (my_lib - opp_lib) +
        4.0 * terr
    )
    return score


def quick_move_score(board, move):
    """
    Fast move ordering heuristic without full opponent search.
    """
    fr, fc, tr, tc, ar, ac = move
    # centrality + local blocking + own mobility after move
    center = 2.5
    dist_center = abs(tr - center) + abs(tc - center)
    arrow_center = abs(ar - center) + abs(ac - center)

    nb = apply_move(board, move, 1)
    my_lib = amazon_liberties(nb, 1)
    opp_lib = amazon_liberties(nb, 2)

    # Prefer central amazon positions, arrows near useful contested areas
    return (
        1.0 * (opp_lib * -1 + my_lib) +
        0.4 * (-dist_center) +
        0.15 * (-arrow_center)
    )


def alphabeta(board, depth, alpha, beta, maximizing):
    if depth == 0:
        return evaluate(board)

    if maximizing:
        moves = legal_moves(board, 1)
        if not moves:
            return -INF // 2 + depth
        moves.sort(key=lambda m: quick_move_score(board, m), reverse=True)
        # Beam a bit to keep speed reliable
        if len(moves) > 40:
            moves = moves[:40]
        value = -INF
        for mv in moves:
            nb = apply_move(board, mv, 1)
            val = alphabeta(swap_players(nb), depth - 1, alpha, beta, False)
            if val > value:
                value = val
            if value > alpha:
                alpha = value
            if alpha >= beta:
                break
        return value
    else:
        moves = legal_moves(board, 1)  # board already swapped to side-to-move perspective
        if not moves:
            return INF // 2 - depth
        moves.sort(key=lambda m: quick_move_score(board, m), reverse=True)
        if len(moves) > 40:
            moves = moves[:40]
        value = INF
        for mv in moves:
            nb = apply_move(board, mv, 1)
            val = alphabeta(swap_players(nb), depth - 1, alpha, beta, True)
            if val < value:
                value = val
            if value < beta:
                beta = value
            if alpha >= beta:
                break
        return value


def move_to_str(m):
    return f"{m[0]},{m[1]}:{m[2]},{m[3]}:{m[4]},{m[5]}"


def policy(board) -> str:
    board = np.array(board, copy=True)
    try:
        moves = legal_moves(board, 1)
        if moves:
            fallback = moves[0]
        else:
            # Unexpected terminal call; return a syntactically valid string.
            return "0,0:0,0:0,0"

        # Order first by cheap heuristic
        moves.sort(key=lambda m: quick_move_score(board, m), reverse=True)

        # Dynamic depth by branching factor
        num = len(moves)
        if num <= 10:
            depth = 2
            beam = 10
        elif num <= 25:
            depth = 2
            beam = 16
        elif num <= 60:
            depth = 1
            beam = 20
        else:
            depth = 1
            beam = 12

        candidates = moves[:beam]
        best_move = fallback
        best_val = -INF

        for mv in candidates:
            nb = apply_move(board, mv, 1)
            val = alphabeta(swap_players(nb), depth, -INF, INF, False)
            if val > best_val:
                best_val = val
                best_move = mv

        return move_to_str(best_move)
    except Exception:
        # Ultimate safety net: try to produce any legal move.
        try:
            moves = legal_moves(board, 1)
            if moves:
                return move_to_str(moves[0])
        except Exception:
            pass
        return "0,0:0,0:0,0"
