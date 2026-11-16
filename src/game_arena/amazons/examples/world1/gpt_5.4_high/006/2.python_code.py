
import time
from collections import deque

N = 6
ME = 1
OPP = 2
EMPTY = 0
ARROW = -1
WIN_SCORE = 1_000_000.0

DIRS = (
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
)

CENTER = (
    (0, 1, 2, 2, 1, 0),
    (1, 2, 3, 3, 2, 1),
    (2, 3, 4, 4, 3, 2),
    (2, 3, 4, 4, 3, 2),
    (1, 2, 3, 3, 2, 1),
    (0, 1, 2, 2, 1, 0),
)


class _Timeout(Exception):
    pass


def _in_bounds(r, c):
    return 0 <= r < N and 0 <= c < N


def _positions(board, player):
    out = []
    for r in range(N):
        row = board[r]
        for c in range(N):
            if row[c] == player:
                out.append((r, c))
    return out


def _iter_reachable(board, r, c):
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        while 0 <= nr < N and 0 <= nc < N and board[nr][nc] == EMPTY:
            yield nr, nc
            nr += dr
            nc += dc


def _has_any_move(board, player):
    # Any legal destination implies at least one legal full move,
    # because the amazon can always shoot back to its vacated square.
    for fr, fc in _positions(board, player):
        board[fr][fc] = EMPTY
        try:
            for _ in _iter_reachable(board, fr, fc):
                return True
        finally:
            board[fr][fc] = player
    return False


def _generate_moves(board, player):
    moves = []
    for fr, fc in _positions(board, player):
        board[fr][fc] = EMPTY
        try:
            for tr, tc in _iter_reachable(board, fr, fc):
                board[tr][tc] = player
                try:
                    for ar, ac in _iter_reachable(board, tr, tc):
                        moves.append((fr, fc, tr, tc, ar, ac))
                finally:
                    board[tr][tc] = EMPTY
        finally:
            board[fr][fc] = player
    return moves


def _apply_move(board, move, player):
    fr, fc, tr, tc, ar, ac = move
    board[fr][fc] = EMPTY
    board[tr][tc] = player
    board[ar][ac] = ARROW


def _undo_move(board, move, player):
    fr, fc, tr, tc, ar, ac = move
    board[ar][ac] = EMPTY
    board[tr][tc] = EMPTY
    board[fr][fc] = player


def _count_empty(board):
    cnt = 0
    for r in range(N):
        row = board[r]
        for c in range(N):
            if row[c] == EMPTY:
                cnt += 1
    return cnt


def _mobility_features(board):
    reach1 = reach2 = 0
    adj1 = adj2 = 0
    center = 0

    for r in range(N):
        row = board[r]
        for c in range(N):
            v = row[c]
            if v != ME and v != OPP:
                continue

            if v == ME:
                center += CENTER[r][c]
            else:
                center -= CENTER[r][c]

            for dr, dc in DIRS:
                nr, nc = r + dr, c + dc
                if 0 <= nr < N and 0 <= nc < N and board[nr][nc] == EMPTY:
                    if v == ME:
                        adj1 += 1
                    else:
                        adj2 += 1

                while 0 <= nr < N and 0 <= nc < N and board[nr][nc] == EMPTY:
                    if v == ME:
                        reach1 += 1
                    else:
                        reach2 += 1
                    nr += dr
                    nc += dc

    return reach1, reach2, adj1, adj2, center


def _queen_distances(board, player):
    INF = 99
    dist = [[INF] * N for _ in range(N)]
    q = deque()

    for r, c in _positions(board, player):
        for nr, nc in _iter_reachable(board, r, c):
            if dist[nr][nc] > 1:
                dist[nr][nc] = 1
                q.append((nr, nc))

    while q:
        r, c = q.popleft()
        nd = dist[r][c] + 1
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            while 0 <= nr < N and 0 <= nc < N and board[nr][nc] == EMPTY:
                if dist[nr][nc] > nd:
                    dist[nr][nc] = nd
                    q.append((nr, nc))
                nr += dr
                nc += dc

    return dist


def _territory_score(board):
    d1 = _queen_distances(board, ME)
    d2 = _queen_distances(board, OPP)
    s = 0.0

    for r in range(N):
        for c in range(N):
            if board[r][c] != EMPTY:
                continue
            a = d1[r][c]
            b = d2[r][c]

            if a < b:
                s += 1.0
            elif b < a:
                s -= 1.0

            va = 0.0 if a >= 99 else 1.0 / (1.0 + a)
            vb = 0.0 if b >= 99 else 1.0 / (1.0 + b)
            s += 0.25 * (va - vb)

    return s


def _chamber_score(board):
    comp = [[-1] * N for _ in range(N)]
    sizes = []
    cid = 0

    for r in range(N):
        for c in range(N):
            if board[r][c] != EMPTY or comp[r][c] != -1:
                continue

            q = deque([(r, c)])
            comp[r][c] = cid
            sz = 1

            while q:
                x, y = q.popleft()
                for dr, dc in DIRS:
                    nx, ny = x + dr, y + dc
                    if (
                        0 <= nx < N and 0 <= ny < N and
                        board[nx][ny] == EMPTY and comp[nx][ny] == -1
                    ):
                        comp[nx][ny] = cid
                        sz += 1
                        q.append((nx, ny))

            sizes.append(sz)
            cid += 1

    if cid == 0:
        return 0

    access1 = [False] * cid
    access2 = [False] * cid

    for r, c in _positions(board, ME):
        for nr, nc in _iter_reachable(board, r, c):
            access1[comp[nr][nc]] = True

    for r, c in _positions(board, OPP):
        for nr, nc in _iter_reachable(board, r, c):
            access2[comp[nr][nc]] = True

    score = 0
    for i, sz in enumerate(sizes):
        if access1[i] and not access2[i]:
            score += sz
        elif access2[i] and not access1[i]:
            score -= sz

    return score


def _quick_eval(board):
    r1, r2, a1, a2, center = _mobility_features(board)
    return 0.28 * (r1 - r2) + 0.95 * (a1 - a2) + 0.12 * center


def _static_eval(board):
    r1, r2, a1, a2, center = _mobility_features(board)
    chamber = _chamber_score(board)
    terr = _territory_score(board)
    return (
        2.6 * chamber +
        1.0 * terr +
        0.22 * (r1 - r2) +
        0.55 * (a1 - a2) +
        0.08 * center
    )


def _beam_limit(num_moves, depth):
    if num_moves <= 10:
        return num_moves
    if depth >= 3:
        return min(num_moves, 8)
    if depth == 2:
        return min(num_moves, 10)
    return min(num_moves, 16)


def _root_limit(num_moves, depth):
    if depth >= 4:
        return min(num_moves, 8)
    if depth == 3:
        return min(num_moves, 12)
    return min(num_moves, 16)


def _ordered_moves(board, moves, player, limit, deadline):
    scored = []
    rev = (player == ME)

    for i, m in enumerate(moves):
        if (i & 15) == 0 and time.perf_counter() > deadline:
            raise _Timeout

        _apply_move(board, m, player)
        try:
            s = _quick_eval(board)
        finally:
            _undo_move(board, m, player)

        scored.append((s, m))

    scored.sort(key=lambda x: x[0], reverse=rev)
    if len(scored) > limit:
        scored = scored[:limit]
    return [m for _, m in scored]


def _search(board, depth, player, alpha, beta, deadline):
    if time.perf_counter() > deadline:
        raise _Timeout

    if depth == 0:
        if not _has_any_move(board, player):
            return (WIN_SCORE if player == OPP else -WIN_SCORE)
        if time.perf_counter() < deadline - 0.01:
            return _static_eval(board)
        return _quick_eval(board)

    moves = _generate_moves(board, player)
    if not moves:
        return (WIN_SCORE + depth) if player == OPP else (-WIN_SCORE - depth)

    moves = _ordered_moves(board, moves, player, _beam_limit(len(moves), depth), deadline)

    if player == ME:
        value = -float("inf")
        for m in moves:
            if time.perf_counter() > deadline:
                raise _Timeout
            _apply_move(board, m, ME)
            try:
                child = _search(board, depth - 1, OPP, alpha, beta, deadline)
            finally:
                _undo_move(board, m, ME)

            if child > value:
                value = child
            if value > alpha:
                alpha = value
            if alpha >= beta:
                break
        return value

    else:
        value = float("inf")
        for m in moves:
            if time.perf_counter() > deadline:
                raise _Timeout
            _apply_move(board, m, OPP)
            try:
                child = _search(board, depth - 1, ME, alpha, beta, deadline)
            finally:
                _undo_move(board, m, OPP)

            if child < value:
                value = child
            if value < beta:
                beta = value
            if alpha >= beta:
                break
        return value


def _format_move(move):
    fr, fc, tr, tc, ar, ac = move
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"


def policy(board) -> str:
    board = board.tolist() if hasattr(board, "tolist") else [list(row) for row in board]
    original = [row[:] for row in board]

    try:
        moves = _generate_moves(board, ME)
        if not moves:
            for r, c in _positions(original, ME):
                return f"{r},{c}:{r},{c}:{r},{c}"
            return "0,0:0,0:0,0"

        first_legal = moves[0]
        empties = _count_empty(board)

        if empties <= 6 or len(moves) <= 8:
            depth = 4
        elif empties <= 12 or len(moves) <= 20:
            depth = 3
        else:
            depth = 2

        deadline = time.perf_counter() + 0.94

        scored = []
        for i, m in enumerate(moves):
            if (i & 15) == 0 and time.perf_counter() > deadline:
                break

            _apply_move(board, m, ME)
            try:
                if not _has_any_move(board, OPP):
                    return _format_move(m)
                s = _quick_eval(board)
            finally:
                _undo_move(board, m, ME)

            scored.append((s, m))

        if not scored:
            return _format_move(first_legal)

        scored.sort(key=lambda x: x[0], reverse=True)
        candidates = [m for _, m in scored[:_root_limit(len(scored), depth)]]

        best_move = candidates[0]
        best_score = -float("inf")
        alpha = -float("inf")
        beta = float("inf")

        for m in candidates:
            if time.perf_counter() > deadline:
                break

            try:
                _apply_move(board, m, ME)
                try:
                    score = _search(board, depth - 1, OPP, alpha, beta, deadline)
                finally:
                    _undo_move(board, m, ME)
            except _Timeout:
                break

            if score > best_score:
                best_score = score
                best_move = m

            if score > alpha:
                alpha = score

            if score >= WIN_SCORE / 2:
                return _format_move(m)

        return _format_move(best_move)

    except Exception:
        fallback_board = [row[:] for row in original]
        fallback_moves = _generate_moves(fallback_board, ME)
        if fallback_moves:
            return _format_move(fallback_moves[0])

        for r, c in _positions(original, ME):
            return f"{r},{c}:{r},{c}:{r},{c}"
        return "0,0:0,0:0,0"
