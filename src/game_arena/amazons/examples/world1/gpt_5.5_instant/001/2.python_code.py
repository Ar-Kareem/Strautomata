
import time
import math
import random
import numpy as np

DIRS = ((-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1))

N = 6


def _inside(r, c):
    return 0 <= r < N and 0 <= c < N


def _ray_moves(board, r, c):
    """Squares reachable by queen move from (r,c) through empty cells."""
    res = []
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        while 0 <= nr < N and 0 <= nc < N and board[nr, nc] == 0:
            res.append((nr, nc))
            nr += dr
            nc += dc
    return res


def _legal_moves(board, player=1, limit=None):
    """
    Generate legal moves as tuples (fr,fc,tr,tc,ar,ac).
    If limit is given, stop after that many.
    """
    moves = []
    amazons = np.argwhere(board == player)
    for fr, fc in amazons:
        fr = int(fr); fc = int(fc)
        tos = _ray_moves(board, fr, fc)
        for tr, tc in tos:
            # simulate amazon move for arrow generation
            board[fr, fc] = 0
            board[tr, tc] = player
            arrows = _ray_moves(board, tr, tc)
            for ar, ac in arrows:
                moves.append((fr, fc, tr, tc, ar, ac))
                if limit is not None and len(moves) >= limit:
                    board[tr, tc] = 0
                    board[fr, fc] = player
                    return moves
            board[tr, tc] = 0
            board[fr, fc] = player
    return moves


def _apply(board, mv, player):
    fr, fc, tr, tc, ar, ac = mv
    nb = board.copy()
    nb[fr, fc] = 0
    nb[tr, tc] = player
    nb[ar, ac] = -1
    return nb


def _format(mv):
    fr, fc, tr, tc, ar, ac = mv
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"


def _mobility(board, player):
    total = 0
    for r, c in np.argwhere(board == player):
        total += len(_ray_moves(board, int(r), int(c)))
    return total


def _reachable_dist(board, starts):
    """Queen-move BFS distance map through empty cells, starting from amazon squares."""
    dist = [[99] * N for _ in range(N)]
    q = []
    for r, c in starts:
        r = int(r); c = int(c)
        dist[r][c] = 0
        q.append((r, c))
    head = 0
    while head < len(q):
        r, c = q[head]
        head += 1
        nd = dist[r][c] + 1
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            while 0 <= nr < N and 0 <= nc < N:
                if board[nr, nc] != 0:
                    break
                if dist[nr][nc] > nd:
                    dist[nr][nc] = nd
                    q.append((nr, nc))
                nr += dr
                nc += dc
    return dist


def _territory_score(board):
    my_starts = np.argwhere(board == 1)
    op_starts = np.argwhere(board == 2)
    md = _reachable_dist(board, my_starts)
    od = _reachable_dist(board, op_starts)

    terr = 0
    near = 0
    for r in range(N):
        for c in range(N):
            if board[r, c] == 0:
                if md[r][c] < od[r][c]:
                    terr += 1
                elif od[r][c] < md[r][c]:
                    terr -= 1
                if md[r][c] < 99 and od[r][c] < 99:
                    near += (od[r][c] - md[r][c]) * 0.15
                elif md[r][c] < 99:
                    near += 0.5
                elif od[r][c] < 99:
                    near -= 0.5
    return terr + near


def _evaluate(board):
    my_mob = _mobility(board, 1)
    op_mob = _mobility(board, 2)
    terr = _territory_score(board)

    my_count_moves = len(_legal_moves(board, 1, limit=80))
    op_count_moves = len(_legal_moves(board, 2, limit=80))

    if op_mob == 0:
        return 100000.0
    if my_mob == 0:
        return -100000.0

    return (
        5.0 * terr +
        2.4 * (my_mob - op_mob) +
        0.35 * (my_count_moves - op_count_moves)
    )


def _move_order_score(board, mv, player):
    """Cheap move ordering: prefer reducing opponent mobility and increasing ours."""
    nb = _apply(board, mv, player)
    if player == 1:
        return _evaluate(nb)
    else:
        return -_evaluate(nb)


def _ordered_moves(board, player, max_moves=120):
    moves = _legal_moves(board, player)
    if not moves:
        return []
    # Score all if manageable; otherwise use a cheap subset ordering.
    scored = []
    for mv in moves:
        scored.append((_move_order_score(board, mv, player), mv))
    scored.sort(reverse=True, key=lambda x: x[0])
    return [m for _, m in scored[:max_moves]]


def _minimax(board, depth, alpha, beta, player, deadline):
    if time.time() > deadline:
        raise TimeoutError

    moves = _ordered_moves(board, player, max_moves=75 if depth >= 2 else 120)
    if not moves:
        # side to move loses
        return -100000.0 if player == 1 else 100000.0

    if depth == 0:
        return _evaluate(board)

    if player == 1:
        val = -1e18
        for mv in moves:
            nb = _apply(board, mv, 1)
            val = max(val, _minimax(nb, depth - 1, alpha, beta, 2, deadline))
            alpha = max(alpha, val)
            if beta <= alpha:
                break
        return val
    else:
        val = 1e18
        for mv in moves:
            nb = _apply(board, mv, 2)
            val = min(val, _minimax(nb, depth - 1, alpha, beta, 1, deadline))
            beta = min(beta, val)
            if beta <= alpha:
                break
        return val


def _choose_move(board):
    start = time.time()
    deadline = start + 0.92

    legal = _legal_moves(board, 1)
    if not legal:
        # Robust fallback; environment should not request this in terminal states.
        return "0,0:0,0:0,0"

    best = legal[0]

    # Immediate winning moves.
    instant = []
    for mv in legal:
        nb = _apply(board, mv, 1)
        if not _legal_moves(nb, 2, limit=1):
            return mv
        instant.append((_move_order_score(board, mv, 1), mv))

    instant.sort(reverse=True, key=lambda x: x[0])
    ordered_root = [m for _, m in instant[:140]]
    best = ordered_root[0]

    # Static best as fallback.
    best_score = instant[0][0]

    # Iterative deepening: depth 1 then 2, maybe 3 if branching is tiny.
    depths = [1, 2]
    if len(legal) < 45:
        depths.append(3)

    try:
        for depth in depths:
            if time.time() > deadline:
                break
            cur_best = best
            cur_score = -1e18
            alpha = -1e18
            beta = 1e18

            # Narrow root list for deeper depths.
            root_moves = ordered_root
            if depth >= 2:
                root_moves = ordered_root[:80]
            if depth >= 3:
                root_moves = ordered_root[:35]

            for mv in root_moves:
                if time.time() > deadline:
                    raise TimeoutError
                nb = _apply(board, mv, 1)
                if not _legal_moves(nb, 2, limit=1):
                    return mv
                sc = _minimax(nb, depth - 1, alpha, beta, 2, deadline)
                if sc > cur_score:
                    cur_score = sc
                    cur_best = mv
                alpha = max(alpha, cur_score)
            best = cur_best
            best_score = cur_score
    except TimeoutError:
        pass
    except Exception:
        # Never risk failing to output a legal move.
        pass

    return best


def policy(board) -> str:
    """
    Return a legal Amazons move for player 1 on a 6x6 numpy board.
    """
    try:
        b = np.array(board, copy=True)
        mv = _choose_move(b)
        if isinstance(mv, str):
            return mv
        return _format(mv)
    except Exception:
        # Final legality-safe fallback: generate the first legal move directly.
        try:
            b = np.array(board, copy=True)
            moves = _legal_moves(b, 1, limit=1)
            if moves:
                return _format(moves[0])
        except Exception:
            pass
        # Should only occur if no legal move exists despite contract.
        return "0,0:0,0:0,0"
