
import time

N = 6
DIRS = (
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
)
INF = 99
WIN = 1000000
DEADLINE = 0.0


class MoveTimeout(Exception):
    pass


def in_bounds(r, c):
    return 0 <= r < N and 0 <= c < N


def check_time():
    if time.perf_counter() > DEADLINE:
        raise MoveTimeout()


def format_move(m):
    fr, fc, tr, tc, ar, ac = m
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"


def apply_move(board, m, piece):
    fr, fc, tr, tc, ar, ac = m
    board[fr, fc] = 0
    board[tr, tc] = piece
    board[ar, ac] = -1


def undo_move(board, m, piece):
    fr, fc, tr, tc, ar, ac = m
    board[ar, ac] = 0
    board[tr, tc] = 0
    board[fr, fc] = piece


def queen_mobility(board, piece):
    total = 0
    for r in range(N):
        for c in range(N):
            if board[r, c] == piece:
                for dr, dc in DIRS:
                    nr, nc = r + dr, c + dc
                    while in_bounds(nr, nc) and board[nr, nc] == 0:
                        total += 1
                        nr += dr
                        nc += dc
    return total


def local_liberty(board, piece):
    total = 0
    for r in range(N):
        for c in range(N):
            if board[r, c] == piece:
                for dr, dc in DIRS:
                    nr, nc = r + dr, c + dc
                    if in_bounds(nr, nc) and board[nr, nc] == 0:
                        total += 1
    return total


def generate_moves(board, piece):
    moves = []
    for fr in range(N):
        for fc in range(N):
            if board[fr, fc] != piece:
                continue

            for dr, dc in DIRS:
                tr, tc = fr + dr, fc + dc
                while in_bounds(tr, tc) and board[tr, tc] == 0:
                    board[fr, fc] = 0
                    board[tr, tc] = piece

                    for adr, adc in DIRS:
                        ar, ac = tr + adr, tc + adc
                        while in_bounds(ar, ac) and board[ar, ac] == 0:
                            moves.append((fr, fc, tr, tc, ar, ac))
                            ar += adr
                            ac += adc

                    board[tr, tc] = 0
                    board[fr, fc] = piece

                    tr += dr
                    tc += dc
    return moves


def queen_distances(board, piece):
    dist = [[INF for _ in range(N)] for _ in range(N)]
    q = []

    for r in range(N):
        for c in range(N):
            if board[r, c] == piece:
                dist[r][c] = 0
                q.append((r, c))

    head = 0
    while head < len(q):
        r, c = q[head]
        head += 1
        nd = dist[r][c] + 1

        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            while in_bounds(nr, nc) and board[nr, nc] == 0:
                if nd < dist[nr][nc]:
                    dist[nr][nc] = nd
                    q.append((nr, nc))
                nr += dr
                nc += dc

    return dist


def evaluate(board):
    m1 = queen_mobility(board, 1)
    if m1 == 0:
        return -WIN
    m2 = queen_mobility(board, 2)
    if m2 == 0:
        return WIN

    d1 = queen_distances(board, 1)
    d2 = queen_distances(board, 2)

    territory = 0.0
    for r in range(N):
        for c in range(N):
            if board[r, c] != 0:
                continue
            a = d1[r][c]
            b = d2[r][c]

            if a < b:
                territory += 2.0 if b >= INF else 1.0 + 0.25 * (b - a)
            elif b < a:
                territory -= 2.0 if a >= INF else 1.0 + 0.25 * (a - b)

    lib = local_liberty(board, 1) - local_liberty(board, 2)

    return 25.0 * territory + 4.0 * (m1 - m2) + 2.0 * lib


def quick_score(board):
    m1 = queen_mobility(board, 1)
    if m1 == 0:
        return -WIN
    m2 = queen_mobility(board, 2)
    if m2 == 0:
        return WIN
    return 6.0 * (m1 - m2) + 2.0 * (local_liberty(board, 1) - local_liberty(board, 2))


def order_and_limit(board, moves, side, limit):
    if not moves:
        return moves

    scored = []
    piece = side
    for i, m in enumerate(moves):
        if (i & 31) == 0:
            check_time()
        apply_move(board, m, piece)
        s = quick_score(board)
        undo_move(board, m, piece)
        scored.append((s, m))

    scored.sort(key=lambda x: x[0], reverse=(side == 1))
    return [m for _, m in scored[:limit]]


def search(board, depth, side, alpha, beta):
    check_time()

    moves = generate_moves(board, side)
    if not moves:
        return -WIN if side == 1 else WIN

    if depth <= 0:
        return evaluate(board)

    if depth <= 1:
        limit = 44
    else:
        limit = 26

    moves = order_and_limit(board, moves, side, min(limit, len(moves)))

    if side == 1:
        best = -WIN * 2
        for m in moves:
            apply_move(board, m, 1)
            val = search(board, depth - 1, 2, alpha, beta)
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
            val = search(board, depth - 1, 1, alpha, beta)
            undo_move(board, m, 2)

            if val < best:
                best = val
            if best < beta:
                beta = best
            if alpha >= beta:
                break
        return best


def root_limit(depth, n):
    if depth == 1:
        return n if n <= 260 else 260
    if depth == 2:
        return n if n <= 80 else 80
    return n if n <= 30 else 30


def root_search(board, ordered_moves, depth):
    limit = root_limit(depth, len(ordered_moves))
    considered = ordered_moves[:limit]
    rest = ordered_moves[limit:]

    best_move = considered[0]
    best_val = -WIN * 2
    scored = []
    alpha = -WIN * 2
    beta = WIN * 2

    for i, m in enumerate(considered):
        if (i & 7) == 0:
            check_time()

        apply_move(board, m, 1)
        if depth == 1:
            val = evaluate(board)
        else:
            val = search(board, depth - 1, 2, alpha, beta)
        undo_move(board, m, 1)

        scored.append((val, m))

        if val > best_val:
            best_val = val
            best_move = m
        if val > alpha:
            alpha = val

    scored.sort(key=lambda x: x[0], reverse=True)
    new_order = [m for _, m in scored] + rest
    return best_move, best_val, new_order


def policy(board) -> str:
    global DEADLINE
    DEADLINE = time.perf_counter() + 0.92

    # Work on a private copy because search mutates and undoes positions.
    b = board.copy()

    root_moves = generate_moves(b, 1)
    if not root_moves:
        # The arena should not call us here. No legal move exists.
        return "0,0:0,0:0,0"

    fallback = root_moves[0]

    # Initial legal move ordering. If time runs out, fallback remains legal.
    try:
        scored = []
        for i, m in enumerate(root_moves):
            if (i & 31) == 0:
                check_time()

            apply_move(b, m, 1)
            s = quick_score(b)
            undo_move(b, m, 1)

            # Immediate win: opponent has no move.
            if s >= WIN:
                return format_move(m)

            scored.append((s, m))

        scored.sort(key=lambda x: x[0], reverse=True)
        ordered = [m for _, m in scored]
        fallback = ordered[0]
    except MoveTimeout:
        return format_move(fallback)

    best = fallback

    # Iterative deepening: keep the best completed result.
    for depth in (1, 2, 3):
        try:
            check_time()
            bm, val, ordered = root_search(b, ordered, depth)
            best = bm

            if val >= WIN * 0.9:
                break
        except MoveTimeout:
            break

    return format_move(best)
