
import time

N = 6
DIRS = (
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
)

WIN = 10_000_000
INF = 99
TIME_LIMIT = 0.92

NODES = 0


def inb(r, c):
    return 0 <= r < N and 0 <= c < N


def fmt(m):
    fr, fc, tr, tc, ar, ac = m
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"


def pieces(board, side):
    out = []
    for r in range(N):
        for c in range(N):
            if board[r, c] == side:
                out.append((r, c))
    return out


def ray_squares(board, r, c):
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        while 0 <= nr < N and 0 <= nc < N and board[nr, nc] == 0:
            yield nr, nc
            nr += dr
            nc += dc


def generate_moves(board, side):
    moves = []
    ps = pieces(board, side)
    for fr, fc in ps:
        for tr, tc in ray_squares(board, fr, fc):
            board[fr, fc] = 0
            board[tr, tc] = side
            for ar, ac in ray_squares(board, tr, tc):
                moves.append((fr, fc, tr, tc, ar, ac))
            board[tr, tc] = 0
            board[fr, fc] = side
    return moves


def apply_move(board, m, side):
    fr, fc, tr, tc, ar, ac = m
    board[fr, fc] = 0
    board[tr, tc] = side
    board[ar, ac] = -1


def undo_move(board, m, side):
    fr, fc, tr, tc, ar, ac = m
    board[ar, ac] = 0
    board[tr, tc] = 0
    board[fr, fc] = side


def mobility_count(board, side):
    total = 0
    for r, c in pieces(board, side):
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            while 0 <= nr < N and 0 <= nc < N and board[nr, nc] == 0:
                total += 1
                nr += dr
                nc += dc
    return total


def has_any_move(board, side):
    for r, c in pieces(board, side):
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < N and 0 <= nc < N and board[nr, nc] == 0:
                return True
    return False


def queen_distances(board, side):
    dist = [[INF] * N for _ in range(N)]
    q = []
    for r, c in pieces(board, side):
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


def evaluate(board):
    m1 = mobility_count(board, 1)
    m2 = mobility_count(board, 2)

    if m1 == 0 and m2 == 0:
        return 0
    if m1 == 0:
        return -WIN // 2
    if m2 == 0:
        return WIN // 2

    d1 = queen_distances(board, 1)
    d2 = queen_distances(board, 2)

    territory = 0.0
    empty_count = 0

    for r in range(N):
        for c in range(N):
            if board[r, c] != 0:
                continue
            empty_count += 1
            a = d1[r][c]
            b = d2[r][c]

            if a < b:
                territory += 1.0
                if b < INF:
                    territory += 0.12 * min(4, b - a)
                else:
                    territory += 0.45
            elif b < a:
                territory -= 1.0
                if a < INF:
                    territory -= 0.12 * min(4, a - b)
                else:
                    territory -= 0.45
            elif a < INF:
                territory += 0.03 * (m1 - m2) / max(1, m1 + m2)

    # Territory is the most important feature; mobility helps before regions split.
    return int(115 * territory + 7 * (m1 - m2))


def clear_line(board, r1, c1, r2, c2):
    dr = r2 - r1
    dc = c2 - c1

    if dr != 0:
        dr = 1 if dr > 0 else -1
    if dc != 0:
        dc = 1 if dc > 0 else -1

    if not (r1 == r2 or c1 == c2 or abs(r2 - r1) == abs(c2 - c1)):
        return False

    r, c = r1 + dr, c1 + dc
    while (r, c) != (r2, c2):
        if board[r, c] != 0:
            return False
        r += dr
        c += dc
    return True


def virtual_ray_count(board, r, c, free_cell, blocked_cell):
    total = 0
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        while 0 <= nr < N and 0 <= nc < N:
            if (nr, nc) == blocked_cell:
                break
            if (nr, nc) == free_cell or board[nr, nc] == 0:
                total += 1
            else:
                break
            nr += dr
            nc += dc
    return total


def quick_move_score(board, m, side):
    fr, fc, tr, tc, ar, ac = m
    opp = 3 - side

    score = 0.0

    # Prefer landing squares with future freedom.
    score += 1.8 * virtual_ray_count(board, tr, tc, (fr, fc), (ar, ac))

    # Mild central preference.
    score -= 0.7 * (abs(tr - 2.5) + abs(tc - 2.5))

    # Arrows near / visible to opponent amazons are usually restrictive.
    for er, ec in pieces(board, opp):
        d = max(abs(ar - er), abs(ac - ec))
        score += max(0, 6 - d) * 2.2
        if clear_line(board, er, ec, ar, ac):
            score += 8.0

    # Avoid spending arrows on squares mainly useful to us.
    for sr, sc in pieces(board, side):
        if (sr, sc) == (fr, fc):
            sr, sc = tr, tc
        d = max(abs(ar - sr), abs(ac - sc))
        score -= max(0, 4 - d) * 0.8

    return score


def ordered_limited_moves(board, side, depth):
    moves = generate_moves(board, side)
    if not moves:
        return moves

    if depth >= 4:
        limit = 18
    elif depth == 3:
        limit = 24
    elif depth == 2:
        limit = 36
    else:
        limit = 60

    if len(moves) > limit:
        moves.sort(key=lambda m: quick_move_score(board, m, side), reverse=True)
        moves = moves[:limit]
    else:
        moves.sort(key=lambda m: quick_move_score(board, m, side), reverse=True)

    return moves


def search(board, depth, side, alpha, beta, deadline):
    global NODES
    NODES += 1
    if (NODES & 255) == 0 and time.perf_counter() > deadline:
        raise TimeoutError

    if depth <= 0:
        return evaluate(board)

    moves = ordered_limited_moves(board, side, depth)

    if not moves:
        if side == 1:
            return -WIN - depth
        else:
            return WIN + depth

    if side == 1:
        best = -WIN * 2
        for m in moves:
            apply_move(board, m, 1)
            val = search(board, depth - 1, 2, alpha, beta, deadline)
            undo_move(board, m, 1)

            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
        return best
    else:
        best = WIN * 2
        for m in moves:
            apply_move(board, m, 2)
            val = search(board, depth - 1, 1, alpha, beta, deadline)
            undo_move(board, m, 2)

            if val < best:
                best = val
            if best < beta:
                beta = best
            if alpha >= beta:
                break
        return best


def policy(board) -> str:
    global NODES
    NODES = 0
    deadline = time.perf_counter() + TIME_LIMIT

    root_moves = generate_moves(board, 1)

    # No legal move exists. The environment should not call us in this state.
    if not root_moves:
        return "0,0:0,0:0,0"

    best_move = root_moves[0]

    scored = []
    try:
        for i, m in enumerate(root_moves):
            if (i & 63) == 0 and time.perf_counter() > deadline:
                raise TimeoutError

            apply_move(board, m, 1)
            sc = evaluate(board)
            undo_move(board, m, 1)

            # Small tie-break from cheap move geometry.
            sc += 0.15 * quick_move_score(board, m, 1)
            scored.append((sc, m))

        scored.sort(key=lambda x: x[0], reverse=True)
        best_move = scored[0][1]

        # Take immediate terminal wins.
        if scored[0][0] > WIN // 3:
            return fmt(best_move)

    except TimeoutError:
        if scored:
            scored.sort(key=lambda x: x[0], reverse=True)
            best_move = scored[0][1]
        return fmt(best_move)

    # Iterative deepening over the most promising root moves.
    depth_plans = (
        (2, 90),
        (3, 45),
        (4, 24),
        (5, 14),
    )

    for depth, root_limit in depth_plans:
        if time.perf_counter() > deadline:
            break

        candidates = [m for _, m in scored[:min(root_limit, len(scored))]]
        iter_best = best_move
        iter_best_val = -WIN * 2
        alpha = -WIN * 2
        beta = WIN * 2
        completed = False

        try:
            for m in candidates:
                if time.perf_counter() > deadline:
                    raise TimeoutError

                apply_move(board, m, 1)
                val = search(board, depth - 1, 2, alpha, beta, deadline)
                undo_move(board, m, 1)

                if val > iter_best_val:
                    iter_best_val = val
                    iter_best = m
                if val > alpha:
                    alpha = val

            completed = True

        except TimeoutError:
            completed = False

        if completed:
            best_move = iter_best
            if iter_best_val > WIN // 2:
                break
        else:
            break

    return fmt(best_move)
