
import time
from collections import deque
import numpy as np

DIRS = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
]

INF = 10**9


def in_bounds(r, c):
    return 0 <= r < 6 and 0 <= c < 6


def move_to_str(m):
    return f"{m[0]},{m[1]}:{m[2]},{m[3]}:{m[4]},{m[5]}"


def ray_squares(board, r, c):
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        while 0 <= nr < 6 and 0 <= nc < 6 and board[nr, nc] == 0:
            yield nr, nc
            nr += dr
            nc += dc


def has_any_move(board, player):
    positions = np.argwhere(board == player)
    for r, c in positions:
        # Any reachable empty square means some legal move exists.
        for _ in ray_squares(board, int(r), int(c)):
            return True
    return False


def legal_moves(board, player):
    moves = []
    positions = np.argwhere(board == player)

    for rr, cc in positions:
        r, c = int(rr), int(cc)

        # Vacate source for movement generation.
        board[r, c] = 0

        destinations = list(ray_squares(board, r, c))
        for tr, tc in destinations:
            board[tr, tc] = player
            for ar, ac in ray_squares(board, tr, tc):
                moves.append((r, c, tr, tc, ar, ac))
            board[tr, tc] = 0

        board[r, c] = player

    return moves


def apply_move(board, move, player):
    r, c, tr, tc, ar, ac = move
    board[r, c] = 0
    board[tr, tc] = player
    board[ar, ac] = -1


def undo_move(board, move, player):
    r, c, tr, tc, ar, ac = move
    board[ar, ac] = 0
    board[tr, tc] = 0
    board[r, c] = player


def mobility_count(board, player):
    total = 0
    positions = np.argwhere(board == player)
    for rr, cc in positions:
        r, c = int(rr), int(cc)
        for _ in ray_squares(board, r, c):
            total += 1
    return total


def queen_dist_map(board, starts):
    dist = [[INF] * 6 for _ in range(6)]
    q = deque()

    for rr, cc in starts:
        r, c = int(rr), int(cc)
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


def territory_score(board):
    my_pos = np.argwhere(board == 1)
    opp_pos = np.argwhere(board == 2)

    d1 = queen_dist_map(board, my_pos)
    d2 = queen_dist_map(board, opp_pos)

    score = 0.0
    for r in range(6):
        for c in range(6):
            if board[r, c] != 0:
                continue
            a = d1[r][c]
            b = d2[r][c]
            if a < b:
                score += 1.0
            elif b < a:
                score -= 1.0
    return score


def quick_eval(board):
    my_mob = mobility_count(board, 1)
    opp_mob = mobility_count(board, 2)

    # Territory matters a lot in Amazons on small boards.
    terr = territory_score(board)

    # Small extra pressure for trapping opponent amazons.
    opp_local = 0
    my_local = 0
    for rr, cc in np.argwhere(board == 2):
        opp_local += sum(1 for _ in ray_squares(board, int(rr), int(cc)))
    for rr, cc in np.argwhere(board == 1):
        my_local += sum(1 for _ in ray_squares(board, int(rr), int(cc)))

    return 2.0 * (my_mob - opp_mob) + 1.25 * terr + 0.15 * (my_local - opp_local)


def policy(board) -> str:
    board = np.array(board, copy=True)
    start = time.perf_counter()
    deadline = start + 0.92

    moves = legal_moves(board, 1)
    if not moves:
        # Should not happen per environment contract.
        return "0,0:0,0:0,0"
    if len(moves) == 1:
        return move_to_str(moves[0])

    best_move = moves[0]
    best_shallow = -INF
    scored = []

    # Shallow evaluation of all our moves.
    for mv in moves:
        apply_move(board, mv, 1)

        if not has_any_move(board, 2):
            score = 10**8
        else:
            score = quick_eval(board)

        undo_move(board, mv, 1)

        scored.append((score, mv))
        if score > best_shallow:
            best_shallow = score
            best_move = mv

        if time.perf_counter() > deadline:
            return move_to_str(best_move)

    scored.sort(key=lambda x: x[0], reverse=True)

    # Only deepen the most promising moves.
    top_k = 12 if len(scored) > 12 else len(scored)
    candidates = scored[:top_k]

    best_val = best_shallow

    for _, mv in candidates:
        if time.perf_counter() > deadline:
            break

        apply_move(board, mv, 1)

        opp_moves = legal_moves(board, 2)
        if not opp_moves:
            val = 10**8
            undo_move(board, mv, 1)
            if val > best_val:
                best_val = val
                best_move = mv
            continue

        # Score opponent replies from our perspective; opponent minimizes this.
        worst_reply_val = INF

        # If many replies, order them quickly so likely dangerous ones are seen first.
        opp_scored = []
        for omv in opp_moves:
            apply_move(board, omv, 2)

            if not has_any_move(board, 1):
                s = -10**8
            else:
                s = quick_eval(board)

            undo_move(board, omv, 2)
            opp_scored.append((s, omv))

            if time.perf_counter() > deadline:
                break

        opp_scored.sort(key=lambda x: x[0])  # opponent wants smallest score

        # Evaluate the most critical replies first; on this board often enough.
        reply_limit = 10 if len(opp_scored) > 10 else len(opp_scored)
        for i in range(reply_limit):
            s, _ = opp_scored[i]
            if s < worst_reply_val:
                worst_reply_val = s
            if worst_reply_val <= best_val:
                # Alpha-like cutoff for move selection.
                break

        undo_move(board, mv, 1)

        if worst_reply_val > best_val:
            best_val = worst_reply_val
            best_move = mv

    return move_to_str(best_move)
