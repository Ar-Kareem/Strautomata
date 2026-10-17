
import time
from collections import deque
import numpy as np

N = 6
DIRS = [(-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)]

WIN_SCORE = 1_000_000


class SearchTimeout(Exception):
    pass


def in_bounds(r, c):
    return 0 <= r < N and 0 <= c < N


def get_amazons(board, player):
    pts = np.argwhere(board == player)
    return [(int(r), int(c)) for r, c in pts]


def gen_reachable_from(board, r, c, vacated=None):
    """
    Generate queen-reachable empty squares from (r,c).
    If vacated is provided, that square is treated as empty.
    """
    if vacated is None:
        vr, vc = -1, -1
    else:
        vr, vc = vacated

    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        while 0 <= nr < N and 0 <= nc < N:
            cell = board[nr, nc]
            if cell != 0 and not (nr == vr and nc == vc):
                break
            yield (nr, nc)
            nr += dr
            nc += dc


def generate_moves(board, player):
    moves = []
    for fr, fc in get_amazons(board, player):
        for tr, tc in gen_reachable_from(board, fr, fc):
            for ar, ac in gen_reachable_from(board, tr, tc, vacated=(fr, fc)):
                moves.append((fr, fc, tr, tc, ar, ac))
    return moves


def count_moves(board, player, cap=None):
    count = 0
    for fr, fc in get_amazons(board, player):
        for tr, tc in gen_reachable_from(board, fr, fc):
            for _ in gen_reachable_from(board, tr, tc, vacated=(fr, fc)):
                count += 1
                if cap is not None and count >= cap:
                    return count
    return count


def apply_move(board, move, player):
    fr, fc, tr, tc, ar, ac = move
    nb = board.copy()
    nb[fr, fc] = 0
    nb[tr, tc] = player
    nb[ar, ac] = -1
    return nb


def queen_distances(board, player):
    """
    Minimum number of queen moves for player's amazons to reach each empty cell.
    Occupied/blocked cells remain -1 except source amazons are 0 internally.
    """
    dist = [[-1] * N for _ in range(N)]
    q = deque()

    for r, c in get_amazons(board, player):
        dist[r][c] = 0
        q.append((r, c))

    while q:
        r, c = q.popleft()
        nd = dist[r][c] + 1

        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            while 0 <= nr < N and 0 <= nc < N:
                if board[nr, nc] != 0:
                    break
                if dist[nr][nc] == -1:
                    dist[nr][nc] = nd
                    q.append((nr, nc))
                nr += dr
                nc += dc

    return dist


def territory_score(board):
    d1 = queen_distances(board, 1)
    d2 = queen_distances(board, 2)

    score = 0
    for r in range(N):
        for c in range(N):
            if board[r, c] != 0:
                continue
            a = d1[r][c]
            b = d2[r][c]
            if a == -1 and b == -1:
                continue
            if b == -1 or (a != -1 and a < b):
                score += 1
            elif a == -1 or (b != -1 and b < a):
                score -= 1
    return score


def evaluate(board):
    empties = int(np.sum(board == 0))

    if empties > 18:
        mob_cap = 120
        mw, tw = 3, 1
    elif empties > 10:
        mob_cap = 180
        mw, tw = 2, 2
    else:
        mob_cap = 400
        mw, tw = 1, 4

    m1 = count_moves(board, 1, cap=mob_cap)
    m2 = count_moves(board, 2, cap=mob_cap)

    if m1 == 0 and m2 > 0:
        return -WIN_SCORE
    if m2 == 0 and m1 > 0:
        return WIN_SCORE
    if m1 == 0 and m2 == 0:
        return 0

    terr = territory_score(board)
    return mw * (m1 - m2) + tw * terr


def quick_evaluate(board):
    """
    Faster rough evaluation for move ordering.
    """
    m1 = count_moves(board, 1, cap=40)
    m2 = count_moves(board, 2, cap=40)
    return m1 - m2


def order_moves(board, moves, player, deadline):
    scored = []
    maximize = (player == 1)

    for mv in moves:
        if time.perf_counter() > deadline:
            raise SearchTimeout
        nb = apply_move(board, mv, player)
        s = quick_evaluate(nb)
        if not maximize:
            s = -s
        scored.append((s, mv))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [mv for _, mv in scored]


def node_limit(depth, move_count, empties):
    if move_count <= 12:
        return move_count

    if depth >= 3:
        return min(move_count, 10 if empties > 12 else 18)
    if depth == 2:
        return min(move_count, 14 if empties > 12 else 22)
    return min(move_count, 20 if empties > 12 else 32)


def alphabeta(board, depth, player, alpha, beta, deadline):
    if time.perf_counter() > deadline:
        raise SearchTimeout

    if depth == 0:
        return evaluate(board)

    moves = generate_moves(board, player)
    if not moves:
        return -WIN_SCORE + depth if player == 1 else WIN_SCORE - depth

    empties = int(np.sum(board == 0))
    ordered = order_moves(board, moves, player, deadline)
    ordered = ordered[:node_limit(depth, len(ordered), empties)]

    if player == 1:
        value = -10**18
        for mv in ordered:
            nb = apply_move(board, mv, 1)
            value = max(value, alphabeta(nb, depth - 1, 2, alpha, beta, deadline))
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value
    else:
        value = 10**18
        for mv in ordered:
            nb = apply_move(board, mv, 2)
            value = min(value, alphabeta(nb, depth - 1, 1, alpha, beta, deadline))
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value


def format_move(move):
    fr, fc, tr, tc, ar, ac = move
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"


def fallback_move(board):
    moves = generate_moves(board, 1)
    if moves:
        return format_move(moves[0])

    # No legal move exists; return syntactically valid dummy.
    # The environment says this should normally not happen.
    return "0,0:0,0:0,0"


def policy(board) -> str:
    board = np.asarray(board)
    deadline = time.perf_counter() + 0.95

    root_moves = generate_moves(board, 1)
    if not root_moves:
        return fallback_move(board)
    if len(root_moves) == 1:
        return format_move(root_moves[0])

    # Immediate win check + quick scoring for fallback/root ordering
    scored = []
    best_quick_move = root_moves[0]
    best_quick_score = -10**18

    try:
        for mv in root_moves:
            if time.perf_counter() > deadline:
                raise SearchTimeout
            nb = apply_move(board, mv, 1)

            # Immediate terminal win
            if count_moves(nb, 2, cap=1) == 0:
                return format_move(mv)

            s = quick_evaluate(nb)
            scored.append((s, mv))
            if s > best_quick_score:
                best_quick_score = s
                best_quick_move = mv
    except SearchTimeout:
        return format_move(best_quick_move)

    scored.sort(key=lambda x: x[0], reverse=True)
    ordered_root = [mv for _, mv in scored]

    empties = int(np.sum(board == 0))
    if empties <= 8:
        max_depth = 4
    elif empties <= 14:
        max_depth = 3
    else:
        max_depth = 2

    def root_limit(depth, total, empties_):
        if total <= 12:
            return total
        if depth == 1:
            return min(total, 40 if empties_ > 12 else 80)
        if depth == 2:
            return min(total, 20 if empties_ > 12 else 40)
        if depth == 3:
            return min(total, 12 if empties_ > 12 else 24)
        return min(total, 10 if empties_ > 12 else 18)

    best_move = best_quick_move
    best_score = -10**18

    try:
        for depth in range(1, max_depth + 1):
            current_best_move = best_move
            current_best_score = -10**18

            candidates = ordered_root[:root_limit(depth, len(ordered_root), empties)]
            alpha = -10**18
            beta = 10**18

            depth_scored = []

            for mv in candidates:
                if time.perf_counter() > deadline:
                    raise SearchTimeout
                nb = apply_move(board, mv, 1)
                score = alphabeta(nb, depth - 1, 2, alpha, beta, deadline)
                depth_scored.append((score, mv))

                if score > current_best_score:
                    current_best_score = score
                    current_best_move = mv
                alpha = max(alpha, current_best_score)

                if current_best_score >= WIN_SCORE // 2:
                    best_move = current_best_move
                    return format_move(best_move)

            # Reorder root moves using completed depth results
            seen = {mv: sc for sc, mv in depth_scored}
            rescored = []
            for mv in ordered_root:
                rescored.append((seen.get(mv, -10**17), mv))
            rescored.sort(key=lambda x: x[0], reverse=True)
            ordered_root = [mv for _, mv in rescored]

            best_move = current_best_move
            best_score = current_best_score

    except SearchTimeout:
        pass

    return format_move(best_move)
