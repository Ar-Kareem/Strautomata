
import time
from collections import deque

SIZE = 6
DIRS = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
]
WIN_SCORE = 1_000_000


class SearchTimeout(Exception):
    pass


def format_move(m):
    fr, fc, tr, tc, ar, ac = m
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"


def inside(r, c):
    return 0 <= r < SIZE and 0 <= c < SIZE


def has_any_destination(board, who=1):
    # A player has a legal move iff one amazon has at least one queen destination.
    # An arrow can always be shot back to the vacated square.
    for r in range(SIZE):
        row = board[r]
        for c in range(SIZE):
            if row[c] == who:
                for dr, dc in DIRS:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < SIZE and 0 <= nc < SIZE and board[nr][nc] == 0:
                        return True
    return False


def count_destinations(board, who=1):
    cnt = 0
    for r in range(SIZE):
        row = board[r]
        for c in range(SIZE):
            if row[c] != who:
                continue
            for dr, dc in DIRS:
                nr, nc = r + dr, c + dc
                while 0 <= nr < SIZE and 0 <= nc < SIZE and board[nr][nc] == 0:
                    cnt += 1
                    nr += dr
                    nc += dc
    return cnt


def count_empties(board):
    s = 0
    for r in range(SIZE):
        row = board[r]
        for c in range(SIZE):
            if row[c] == 0:
                s += 1
    return s


def generate_all_moves(board):
    moves = []
    append_move = moves.append

    for fr in range(SIZE):
        row = board[fr]
        for fc in range(SIZE):
            if row[fc] != 1:
                continue

            for dr, dc in DIRS:
                tr, tc = fr + dr, fc + dc
                while 0 <= tr < SIZE and 0 <= tc < SIZE and board[tr][tc] == 0:
                    # Arrow rays from landing square; vacated from-square is treated as empty.
                    for adr, adc in DIRS:
                        ar, ac = tr + adr, tc + adc
                        while 0 <= ar < SIZE and 0 <= ac < SIZE:
                            if ar == fr and ac == fc:
                                append_move((fr, fc, tr, tc, ar, ac))
                                ar += adr
                                ac += adc
                                continue
                            if board[ar][ac] != 0:
                                break
                            append_move((fr, fc, tr, tc, ar, ac))
                            ar += adr
                            ac += adc

                    tr += dr
                    tc += dc

    return moves


def apply_move_and_flip(board, move):
    fr, fc, tr, tc, ar, ac = move
    nb = [row[:] for row in board]

    nb[fr][fc] = 0
    nb[tr][tc] = 1
    nb[ar][ac] = -1

    # Swap players so the next side to move is again represented as 1.
    for r in range(SIZE):
        row = nb[r]
        for c in range(SIZE):
            v = row[c]
            if v == 1:
                row[c] = 2
            elif v == 2:
                row[c] = 1
    return nb


def queen_distances(board, who):
    inf = 99
    dist = [[inf] * SIZE for _ in range(SIZE)]
    q = deque()

    for r in range(SIZE):
        row = board[r]
        for c in range(SIZE):
            if row[c] == who:
                dist[r][c] = 0
                q.append((r, c))

    while q:
        r, c = q.popleft()
        nd = dist[r][c] + 1

        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            while 0 <= nr < SIZE and 0 <= nc < SIZE and board[nr][nc] == 0:
                if dist[nr][nc] > nd:
                    dist[nr][nc] = nd
                    q.append((nr, nc))
                nr += dr
                nc += dc

    return dist


def territory_score(board):
    d1 = queen_distances(board, 1)
    d2 = queen_distances(board, 2)
    inf = 99
    score = 0.0

    for r in range(SIZE):
        row = board[r]
        for c in range(SIZE):
            if row[c] != 0:
                continue
            a = d1[r][c]
            b = d2[r][c]

            if a < b:
                score += 1.0
            elif b < a:
                score -= 1.0

            if a < inf:
                score += 0.25 / (a + 1.0)
            if b < inf:
                score -= 0.25 / (b + 1.0)

    return score


def quick_eval(board):
    my_mob = count_destinations(board, 1)
    if my_mob == 0:
        return -WIN_SCORE
    opp_mob = count_destinations(board, 2)
    if opp_mob == 0:
        return WIN_SCORE
    return 6.0 * (my_mob - opp_mob)


def evaluate(board):
    my_mob = count_destinations(board, 1)
    if my_mob == 0:
        return -WIN_SCORE
    opp_mob = count_destinations(board, 2)
    if opp_mob == 0:
        return WIN_SCORE

    empties = count_empties(board)
    terr = territory_score(board)

    if empties > 16:
        return 4.0 * (my_mob - opp_mob) + 1.8 * terr
    elif empties > 9:
        return 5.0 * (my_mob - opp_mob) + 1.4 * terr
    else:
        return 6.0 * (my_mob - opp_mob) + 1.0 * terr


def negamax(board, depth, alpha, beta, deadline):
    if time.perf_counter() >= deadline:
        raise SearchTimeout

    if not has_any_destination(board, 1):
        return -WIN_SCORE - depth

    if depth == 0:
        return evaluate(board)

    moves = generate_all_moves(board)
    if not moves:
        return -WIN_SCORE - depth

    best = -2 * WIN_SCORE

    # Do explicit move ordering only when there is still deeper search underneath.
    if depth >= 2 and len(moves) > 1:
        ordered = []
        for m in moves:
            child = apply_move_and_flip(board, m)
            if not has_any_destination(child, 1):
                return WIN_SCORE + depth
            ordered.append((-quick_eval(child), child))

        ordered.sort(key=lambda x: x[0], reverse=True)

        # Beam limit for safety when branching spikes.
        if len(ordered) > 36:
            ordered = ordered[:24]

        for _, child in ordered:
            val = -negamax(child, depth - 1, -beta, -alpha, deadline)
            if val > best:
                best = val
            if val > alpha:
                alpha = val
            if alpha >= beta:
                break
    else:
        for m in moves:
            child = apply_move_and_flip(board, m)
            if not has_any_destination(child, 1):
                val = WIN_SCORE + depth
            else:
                val = -negamax(child, depth - 1, -beta, -alpha, deadline)

            if val > best:
                best = val
            if val > alpha:
                alpha = val
            if alpha >= beta:
                break

    return best


def policy(board) -> str:
    try:
        if hasattr(board, "tolist"):
            board = board.tolist()
        else:
            board = [list(row) for row in board]

        deadline = time.perf_counter() + 0.93

        moves = generate_all_moves(board)
        if not moves:
            return "0,0:0,0:0,0"
        if len(moves) == 1:
            return format_move(moves[0])

        scored = []
        for m in moves:
            child = apply_move_and_flip(board, m)
            if not has_any_destination(child, 1):
                return format_move(m)
            scored.append((-quick_eval(child), m, child))

        scored.sort(key=lambda x: x[0], reverse=True)
        best_move = scored[0][1]
        best_score = -2 * WIN_SCORE

        n = len(scored)
        empties = count_empties(board)

        if n <= 16 or (empties <= 12 and n <= 30):
            depth = 3
        else:
            depth = 2

        if depth == 2:
            if n > 150:
                scored = scored[:24]
            elif n > 100:
                scored = scored[:32]
            elif n > 70:
                scored = scored[:48]
        else:
            if n > 28:
                scored = scored[:24]

        alpha = -2 * WIN_SCORE
        beta = 2 * WIN_SCORE

        for _, m, child in scored:
            if time.perf_counter() >= deadline:
                break
            try:
                val = -negamax(child, depth - 1, -beta, -alpha, deadline)
            except SearchTimeout:
                break

            if val > best_score:
                best_score = val
                best_move = m
            if val > alpha:
                alpha = val

        return format_move(best_move)

    except Exception:
        # Safety fallback: still try to return a legal move.
        try:
            if hasattr(board, "tolist"):
                b = board.tolist()
            else:
                b = [list(row) for row in board]
            moves = generate_all_moves(b)
            if moves:
                return format_move(moves[0])
        except Exception:
            pass
        return "0,0:0,0:0,0"
