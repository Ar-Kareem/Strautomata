
import numpy as np
import time
import random

DIRS = (
    (-1, 0), (1, 0), (0, -1), (0, 1),
    (-1, -1), (-1, 1), (1, -1), (1, 1)
)

N = 6
CENTER = ((N - 1) / 2.0, (N - 1) / 2.0)


def _inside(r, c):
    return 0 <= r < N and 0 <= c < N


def _ray_squares(board, r, c):
    """All empty queen-reachable squares from r,c on current board."""
    out = []
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        while 0 <= nr < N and 0 <= nc < N and board[nr, nc] == 0:
            out.append((nr, nc))
            nr += dr
            nc += dc
    return out


def _legal_moves(board, player=1, limit=None):
    """Generate legal moves as tuples (fr,fc,tr,tc,ar,ac)."""
    moves = []
    pieces = np.argwhere(board == player)
    for fr, fc in pieces:
        fr = int(fr); fc = int(fc)
        for dr, dc in DIRS:
            tr, tc = fr + dr, fc + dc
            while _inside(tr, tc) and board[tr, tc] == 0:
                # Temporarily move amazon.
                board[fr, fc] = 0
                board[tr, tc] = player
                for adr, adc in DIRS:
                    ar, ac = tr + adr, tc + adc
                    while _inside(ar, ac) and board[ar, ac] == 0:
                        moves.append((fr, fc, tr, tc, ar, ac))
                        if limit is not None and len(moves) >= limit:
                            board[tr, tc] = 0
                            board[fr, fc] = player
                            return moves
                        ar += adr
                        ac += adc
                board[tr, tc] = 0
                board[fr, fc] = player
                tr += dr
                tc += dc
    return moves


def _count_amazon_mobility(board, player):
    total = 0
    pieces = np.argwhere(board == player)
    for r, c in pieces:
        total += len(_ray_squares(board, int(r), int(c)))
    return total


def _distance_maps(board, player):
    """Queen-move BFS distance from all player amazons."""
    dist = np.full((N, N), 99, dtype=np.int16)
    q = []
    for r, c in np.argwhere(board == player):
        r = int(r); c = int(c)
        dist[r, c] = 0
        q.append((r, c))
    head = 0
    while head < len(q):
        r, c = q[head]
        head += 1
        nd = dist[r, c] + 1
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            while _inside(nr, nc) and board[nr, nc] == 0:
                if nd < dist[nr, nc]:
                    dist[nr, nc] = nd
                    q.append((nr, nc))
                nr += dr
                nc += dc
    return dist


def _territory_score(board):
    myd = _distance_maps(board, 1)
    opd = _distance_maps(board, 2)
    score = 0.0
    for r in range(N):
        for c in range(N):
            if board[r, c] == 0:
                if myd[r, c] < opd[r, c]:
                    score += 1.0
                elif opd[r, c] < myd[r, c]:
                    score -= 1.0
                elif myd[r, c] < 99:
                    score += 0.12
    return score


def _component_space(board, player):
    """Approximate space controlled by components containing each player's amazons."""
    seen = np.zeros((N, N), dtype=np.bool_)
    my_space = 0
    op_space = 0
    for sr in range(N):
        for sc in range(N):
            if board[sr, sc] == -1 or seen[sr, sc]:
                continue
            # Flood component through non-arrow cells.
            stack = [(sr, sc)]
            seen[sr, sc] = True
            cells = 0
            has_my = False
            has_op = False
            while stack:
                r, c = stack.pop()
                cells += 1
                if board[r, c] == 1:
                    has_my = True
                elif board[r, c] == 2:
                    has_op = True
                for dr, dc in DIRS:
                    nr, nc = r + dr, c + dc
                    if _inside(nr, nc) and not seen[nr, nc] and board[nr, nc] != -1:
                        seen[nr, nc] = True
                        stack.append((nr, nc))
            if has_my and not has_op:
                my_space += cells
            elif has_op and not has_my:
                op_space += cells
    return my_space - op_space


def _center_bonus(board):
    val = 0.0
    for player, sign in ((1, 1), (2, -1)):
        for r, c in np.argwhere(board == player):
            d = abs(float(r) - CENTER[0]) + abs(float(c) - CENTER[1])
            val += sign * (3.5 - d) * 0.08
    return val


def _evaluate(board):
    my_mob = _count_amazon_mobility(board, 1)
    op_mob = _count_amazon_mobility(board, 2)

    # Terminal / near-terminal values.
    if op_mob == 0:
        return 100000.0 + my_mob
    if my_mob == 0:
        return -100000.0 - op_mob

    score = 0.0
    score += 4.2 * (my_mob - op_mob)
    score += 2.3 * _territory_score(board)
    score += 1.4 * _component_space(board, 1)
    score += _center_bonus(board)
    return score


def _apply_move(board, mv, player):
    fr, fc, tr, tc, ar, ac = mv
    board[fr, fc] = 0
    board[tr, tc] = player
    board[ar, ac] = -1


def _undo_move(board, mv, player):
    fr, fc, tr, tc, ar, ac = mv
    board[ar, ac] = 0
    board[tr, tc] = 0
    board[fr, fc] = player


def _move_string(mv):
    fr, fc, tr, tc, ar, ac = mv
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"


def _quick_move_score(board, mv):
    """Score move after applying; includes arrow blocking and landing mobility."""
    fr, fc, tr, tc, ar, ac = mv
    _apply_move(board, mv, 1)
    s = _evaluate(board)

    # Prefer arrows adjacent/near opponent and moves preserving our mobility.
    adj_op = 0
    for dr, dc in DIRS:
        rr, cc = ar + dr, ac + dc
        if _inside(rr, cc) and board[rr, cc] == 2:
            adj_op += 1
    s += 1.0 * adj_op

    # Prefer landing squares with escape routes.
    s += 0.35 * len(_ray_squares(board, tr, tc))

    _undo_move(board, mv, 1)
    return s


def _ordered_moves(board, player, max_moves=None):
    moves = _legal_moves(board, player)
    if not moves:
        return []
    if player == 1:
        scored = [(_quick_move_score(board, m), m) for m in moves]
        scored.sort(reverse=True, key=lambda x: x[0])
    else:
        # For opponent, sort by how bad it is for us.
        scored = []
        for m in moves:
            _apply_move(board, m, 2)
            scored.append((_evaluate(board), m))
            _undo_move(board, m, 2)
        scored.sort(key=lambda x: x[0])
    if max_moves is not None:
        scored = scored[:max_moves]
    return [m for _, m in scored]


def _search(board, depth, alpha, beta, player, deadline):
    if time.time() > deadline:
        return _evaluate(board)

    mymob = _count_amazon_mobility(board, 1)
    opmob = _count_amazon_mobility(board, 2)
    if opmob == 0:
        return 100000.0 + mymob
    if mymob == 0:
        return -100000.0 - opmob
    if depth <= 0:
        return _evaluate(board)

    # Keep branching controlled for 6x6 and 1-second limit.
    max_children = 18 if depth >= 2 else 32
    moves = _ordered_moves(board, player, max_children)
    if not moves:
        return -100000.0 if player == 1 else 100000.0

    if player == 1:
        val = -1e18
        for m in moves:
            _apply_move(board, m, 1)
            val = max(val, _search(board, depth - 1, alpha, beta, 2, deadline))
            _undo_move(board, m, 1)
            alpha = max(alpha, val)
            if beta <= alpha or time.time() > deadline:
                break
        return val
    else:
        val = 1e18
        for m in moves:
            _apply_move(board, m, 2)
            val = min(val, _search(board, depth - 1, alpha, beta, 1, deadline))
            _undo_move(board, m, 2)
            beta = min(beta, val)
            if beta <= alpha or time.time() > deadline:
                break
        return val


def policy(board) -> str:
    start = time.time()
    deadline = start + 0.92

    # Work on a small mutable int array.
    b = np.array(board, dtype=np.int8, copy=True)

    legal = _legal_moves(b, 1)
    if not legal:
        # Robust fallback; environment should not request this in terminal states.
        return "0,0:0,0:0,0"

    if len(legal) == 1:
        return _move_string(legal[0])

    # Immediate winning move: after our move opponent has no mobility.
    best = None
    best_score = -1e18

    # One-ply ordering.
    scored = []
    for m in legal:
        sc = _quick_move_score(b, m)
        scored.append((sc, m))
    scored.sort(reverse=True, key=lambda x: x[0])

    best = scored[0][1]
    best_score = scored[0][0]

    # If branching is huge, trust heuristic, but still inspect top moves with shallow search.
    top = [m for _, m in scored[:24]]

    # Check immediate wins among good candidates first, then all if time remains.
    for m in top:
        _apply_move(b, m, 1)
        if _count_amazon_mobility(b, 2) == 0:
            _undo_move(b, m, 1)
            return _move_string(m)
        _undo_move(b, m, 1)

    # Adaptive minimax.
    branch = len(legal)
    if branch <= 45:
        depth = 3
        candidates = top[:18]
    elif branch <= 100:
        depth = 2
        candidates = top[:22]
    else:
        depth = 2
        candidates = top[:14]

    for m in candidates:
        if time.time() > deadline:
            break
        _apply_move(b, m, 1)
        val = _search(b, depth - 1, -1e18, 1e18, 2, deadline)
        _undo_move(b, m, 1)

        # Slightly mix in one-ply score to stabilize.
        val += 0.01 * _quick_move_score(b, m)

        if val > best_score:
            best_score = val
            best = m

    # Final legality safety check. If somehow corrupted, return first generated legal.
    if best is None:
        best = legal[0]

    return _move_string(best)
