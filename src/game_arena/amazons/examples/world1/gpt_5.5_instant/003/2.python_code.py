
import numpy as np
import time
import math

DIRS = ((-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1))

N = 6


def _inb(r, c):
    return 0 <= r < N and 0 <= c < N


def _ray_squares(board, r, c):
    """All empty squares visible queen-like from r,c on current board."""
    out = []
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        while 0 <= nr < N and 0 <= nc < N and board[nr, nc] == 0:
            out.append((nr, nc))
            nr += dr
            nc += dc
    return out


def _legal_moves(board, player=1, limit=None):
    """Return legal moves as tuples (fr,fc,tr,tc,ar,ac)."""
    moves = []
    pieces = np.argwhere(board == player)
    for fr, fc in pieces:
        fr = int(fr); fc = int(fc)
        for tr, tc in _ray_squares(board, fr, fc):
            # Temporarily move amazon for arrow generation.
            board[fr, fc] = 0
            board[tr, tc] = player
            for ar, ac in _ray_squares(board, tr, tc):
                moves.append((fr, fc, tr, tc, ar, ac))
                if limit is not None and len(moves) >= limit:
                    board[tr, tc] = 0
                    board[fr, fc] = player
                    return moves
            board[tr, tc] = 0
            board[fr, fc] = player
    return moves


def _apply(board, mv, player=1):
    fr, fc, tr, tc, ar, ac = mv
    b = board.copy()
    b[fr, fc] = 0
    b[tr, tc] = player
    b[ar, ac] = -1
    return b


def _apply_inplace(board, mv, player):
    fr, fc, tr, tc, ar, ac = mv
    board[fr, fc] = 0
    board[tr, tc] = player
    board[ar, ac] = -1


def _undo_inplace(board, mv, player):
    fr, fc, tr, tc, ar, ac = mv
    board[ar, ac] = 0
    board[tr, tc] = 0
    board[fr, fc] = player


def _count_mobility(board, player):
    total = 0
    for r, c in np.argwhere(board == player):
        r = int(r); c = int(c)
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            while 0 <= nr < N and 0 <= nc < N and board[nr, nc] == 0:
                total += 1
                nr += dr
                nc += dc
    return total


def _reachable_area(board, player):
    """Number of empty cells reachable by at least one amazon queen ray."""
    seen = set()
    for r, c in np.argwhere(board == player):
        r = int(r); c = int(c)
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            while 0 <= nr < N and 0 <= nc < N and board[nr, nc] == 0:
                seen.add((nr, nc))
                nr += dr
                nc += dc
    return len(seen)


def _territory(board):
    """
    Approximate territory by BFS king-distance through empty cells from both sides.
    Lower distance owns a cell; ties are neutral/slightly mobility dependent.
    """
    from collections import deque
    dist1 = [[99] * N for _ in range(N)]
    dist2 = [[99] * N for _ in range(N)]

    q = deque()
    for r, c in np.argwhere(board == 1):
        r = int(r); c = int(c)
        dist1[r][c] = 0
        q.append((r, c))
    while q:
        r, c = q.popleft()
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if _inb(nr, nc) and board[nr, nc] == 0 and dist1[nr][nc] == 99:
                dist1[nr][nc] = dist1[r][c] + 1
                q.append((nr, nc))

    q = deque()
    for r, c in np.argwhere(board == 2):
        r = int(r); c = int(c)
        dist2[r][c] = 0
        q.append((r, c))
    while q:
        r, c = q.popleft()
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if _inb(nr, nc) and board[nr, nc] == 0 and dist2[nr][nc] == 99:
                dist2[nr][nc] = dist2[r][c] + 1
                q.append((nr, nc))

    score = 0
    for r in range(N):
        for c in range(N):
            if board[r, c] == 0:
                if dist1[r][c] < dist2[r][c]:
                    score += 1
                elif dist2[r][c] < dist1[r][c]:
                    score -= 1
    return score


def _heuristic(board):
    my_mob = _count_mobility(board, 1)
    op_mob = _count_mobility(board, 2)

    # Terminal / near terminal handling.
    if op_mob == 0:
        return 100000
    if my_mob == 0:
        return -100000

    my_area = _reachable_area(board, 1)
    op_area = _reachable_area(board, 2)
    terr = _territory(board)

    empty_count = int(np.sum(board == 0))
    # Mobility matters most early; territory increasingly matters late.
    terr_w = 3.0 if empty_count <= 14 else 1.4
    mob_w = 2.2 if empty_count > 14 else 1.3
    area_w = 1.2

    return mob_w * (my_mob - op_mob) + area_w * (my_area - op_area) + terr_w * terr


def _move_static_score(board, mv, player=1):
    """Fast ordering/evaluation after applying a candidate."""
    _apply_inplace(board, mv, player)
    if player == 1:
        score = _heuristic(board)
    else:
        score = -_heuristic(board)
    _undo_inplace(board, mv, player)
    return score


def _ordered_moves(board, player, max_moves=None):
    moves = _legal_moves(board, player)
    if not moves:
        return []
    # In huge early positions, full sorting is still okay on 6x6, but cap for search.
    scored = []
    for mv in moves:
        try:
            scored.append((_move_static_score(board, mv, player), mv))
        except Exception:
            scored.append((0, mv))
    scored.sort(reverse=True, key=lambda x: x[0])
    if max_moves is not None:
        scored = scored[:max_moves]
    return [m for _, m in scored]


def _alphabeta(board, depth, alpha, beta, player, end_time):
    if time.time() > end_time:
        raise TimeoutError

    # Legal-move terminal test via mobility is safe enough for Amazons here:
    # no reachable empty square means no move; otherwise likely has arrows, but generate at depth edges.
    if depth == 0:
        return _heuristic(board)

    # Limit branching for reliability.
    branch = 18 if depth >= 2 else 28
    moves = _ordered_moves(board, player, branch)
    if not moves:
        return -100000 if player == 1 else 100000

    if player == 1:
        val = -10**9
        for mv in moves:
            _apply_inplace(board, mv, 1)
            val = max(val, _alphabeta(board, depth - 1, alpha, beta, 2, end_time))
            _undo_inplace(board, mv, 1)
            alpha = max(alpha, val)
            if alpha >= beta:
                break
        return val
    else:
        val = 10**9
        for mv in moves:
            _apply_inplace(board, mv, 2)
            val = min(val, _alphabeta(board, depth - 1, alpha, beta, 1, end_time))
            _undo_inplace(board, mv, 2)
            beta = min(beta, val)
            if alpha >= beta:
                break
        return val


def _fmt(mv):
    fr, fc, tr, tc, ar, ac = mv
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"


def policy(board) -> str:
    """
    Return a legal Amazons move string for player 1 on a 6x6 board.
    """
    try:
        b = np.array(board, copy=True)
        legal = _legal_moves(b, 1)
        if not legal:
            # Environment should not call this, but return syntactically valid fallback.
            return "0,0:0,0:0,0"

        # Immediate winning move: leave opponent with no movement.
        best_mv = legal[0]
        best_score = -10**18

        # Static ordering.
        scored = []
        for mv in legal:
            _apply_inplace(b, mv, 1)
            op_mob = _count_mobility(b, 2)
            h = _heuristic(b)
            _undo_inplace(b, mv, 1)
            if op_mob == 0:
                return _fmt(mv)
            scored.append((h, mv))

        scored.sort(reverse=True, key=lambda x: x[0])
        best_score, best_mv = scored[0]

        start = time.time()
        end_time = start + 0.88

        # Choose depth based on branching / game phase.
        empties = int(np.sum(b == 0))
        if len(legal) <= 35 or empties <= 12:
            depth = 3
            candidates = [m for _, m in scored[:24]]
        elif len(legal) <= 120 or empties <= 20:
            depth = 2
            candidates = [m for _, m in scored[:32]]
        else:
            depth = 1
            candidates = [m for _, m in scored[:45]]

        # Root search.
        alpha = -10**9
        beta = 10**9
        for mv in candidates:
            if time.time() > end_time:
                break
            _apply_inplace(b, mv, 1)
            try:
                if depth <= 1:
                    val = _heuristic(b)
                else:
                    val = _alphabeta(b, depth - 1, alpha, beta, 2, end_time)
            except TimeoutError:
                _undo_inplace(b, mv, 1)
                break
            _undo_inplace(b, mv, 1)

            if val > best_score:
                best_score = val
                best_mv = mv
            alpha = max(alpha, best_score)

        return _fmt(best_mv)

    except Exception:
        # Absolute robustness: regenerate simply and return first legal move if possible.
        try:
            b = np.array(board, copy=True)
            moves = _legal_moves(b, 1, limit=1)
            if moves:
                return _fmt(moves[0])
        except Exception:
            pass
        return "0,0:0,0:0,0"
