
import time
import math
import numpy as np

DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1),
        (-1, -1), (-1, 1), (1, -1), (1, 1)]

N = 6
TIME_LIMIT = 0.92


def policy(board) -> str:
    start_time = time.time()
    b = board.copy()

    root_moves = list(generate_moves(b, 1))
    if not root_moves:
        return "0,0:0,0:0,0"

    # Always keep a legal fallback.
    best_move = root_moves[0]
    best_score = -10**18

    # Fast one-ply ordering.
    scored = []
    for mv in root_moves:
        do_move(b, mv, 1)
        s = evaluate(b)
        undo_move(b, mv, 1)
        scored.append((s + quick_move_bonus(b, mv, 1), mv))
        if time.time() - start_time > TIME_LIMIT * 0.35:
            break

    if scored:
        scored.sort(reverse=True, key=lambda x: x[0])
        best_move = scored[0][1]
        root_moves = [m for _, m in scored] + [m for m in root_moves if m not in set(x[1] for x in scored)]

    # Iterative deepening. Depth 2 is usually reliable within time;
    # depth 3 is attempted when branching is small.
    for depth in (1, 2, 3):
        if time.time() - start_time > TIME_LIMIT:
            break

        current_best = best_move
        current_score = -10**18
        alpha = -10**18
        beta = 10**18

        # Limit very large root branching after ordering.
        if depth >= 2:
            move_list = root_moves[:140]
        else:
            move_list = root_moves

        completed = True

        for mv in move_list:
            if time.time() - start_time > TIME_LIMIT:
                completed = False
                break

            do_move(b, mv, 1)
            val = -negamax(b, 2, depth - 1, -beta, -alpha, start_time)
            undo_move(b, mv, 1)

            if val > current_score:
                current_score = val
                current_best = mv
            if val > alpha:
                alpha = val

        if completed and current_score > -10**17:
            best_move = current_best
            best_score = current_score

    return move_to_str(best_move)


def inside(r, c):
    return 0 <= r < N and 0 <= c < N


def ray_destinations(board, r, c):
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        while inside(nr, nc) and board[nr, nc] == 0:
            yield nr, nc
            nr += dr
            nc += dc


def generate_moves(board, player):
    pieces = np.argwhere(board == player)
    for fr, fc in pieces:
        fr = int(fr)
        fc = int(fc)

        for tr, tc in ray_destinations(board, fr, fc):
            board[fr, fc] = 0
            board[tr, tc] = player

            for ar, ac in ray_destinations(board, tr, tc):
                yield (fr, fc, tr, tc, ar, ac)

            board[tr, tc] = 0
            board[fr, fc] = player


def has_move(board, player):
    pieces = np.argwhere(board == player)
    for r, c in pieces:
        r = int(r)
        c = int(c)
        for _ in ray_destinations(board, r, c):
            return True
    return False


def do_move(board, mv, player):
    fr, fc, tr, tc, ar, ac = mv
    board[fr, fc] = 0
    board[tr, tc] = player
    board[ar, ac] = -1


def undo_move(board, mv, player):
    fr, fc, tr, tc, ar, ac = mv
    board[ar, ac] = 0
    board[tr, tc] = 0
    board[fr, fc] = player


def negamax(board, player, depth, alpha, beta, start_time):
    if time.time() - start_time > TIME_LIMIT:
        return side_eval(board, player)

    if not has_move(board, player):
        return -1000000 - depth

    if depth <= 0:
        return side_eval(board, player)

    opponent = 3 - player
    moves = ordered_limited_moves(board, player, depth)

    best = -10**18
    for mv in moves:
        if time.time() - start_time > TIME_LIMIT:
            break

        do_move(board, mv, player)
        val = -negamax(board, opponent, depth - 1, -beta, -alpha, start_time)
        undo_move(board, mv, player)

        if val > best:
            best = val
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break

    return best if best > -10**17 else side_eval(board, player)


def ordered_limited_moves(board, player, depth):
    moves = []
    limit = 80 if depth >= 2 else 120

    for mv in generate_moves(board, player):
        moves.append((quick_move_bonus(board, mv, player), mv))

    moves.sort(reverse=True, key=lambda x: x[0])
    return [m for _, m in moves[:limit]]


def quick_move_bonus(board, mv, player):
    fr, fc, tr, tc, ar, ac = mv
    opp = 3 - player

    # Prefer arrows close to opponent amazons and moves that keep our amazon mobile.
    bonus = 0.0

    for r, c in np.argwhere(board == opp):
        d = max(abs(int(r) - ar), abs(int(c) - ac))
        if d == 1:
            bonus += 7.0
        elif d == 2:
            bonus += 3.0
        elif d == 3:
            bonus += 1.0

    # Landing squares with more exits are usually safer.
    board[fr, fc] = 0
    board[tr, tc] = player
    exits = 0
    for _ in ray_destinations(board, tr, tc):
        exits += 1
    board[tr, tc] = 0
    board[fr, fc] = player

    bonus += 0.25 * exits

    # Centralization is useful on 6x6.
    bonus -= 0.15 * (abs(tr - 2.5) + abs(tc - 2.5))

    return bonus


def side_eval(board, player):
    val = evaluate(board)
    return val if player == 1 else -val


def evaluate(board):
    # Positive is good for player 1, negative for player 2.
    m1 = mobility(board, 1)
    m2 = mobility(board, 2)

    t = territory_score(board)
    c = component_score(board)

    return 7.0 * (m1 - m2) + 3.0 * t + 1.5 * c


def mobility(board, player):
    total = 0
    for r, c in np.argwhere(board == player):
        r = int(r)
        c = int(c)
        for _ in ray_destinations(board, r, c):
            total += 1
    return total


def queen_distances(board, player):
    dist = [[99 for _ in range(N)] for _ in range(N)]
    q = []

    for r, c in np.argwhere(board == player):
        r = int(r)
        c = int(c)
        dist[r][c] = 0
        q.append((r, c))

    head = 0
    while head < len(q):
        r, c = q[head]
        head += 1
        nd = dist[r][c] + 1

        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            while inside(nr, nc):
                if board[nr, nc] != 0 and board[nr, nc] != player:
                    break

                if board[nr, nc] == 0 and nd < dist[nr][nc]:
                    dist[nr][nc] = nd
                    q.append((nr, nc))

                nr += dr
                nc += dc

    return dist


def territory_score(board):
    d1 = queen_distances(board, 1)
    d2 = queen_distances(board, 2)

    score = 0.0
    for r in range(N):
        for c in range(N):
            if board[r, c] != 0:
                continue

            a = d1[r][c]
            b = d2[r][c]

            if a < b:
                score += 1.0
                if b < 99:
                    score += 0.15 * (b - a)
            elif b < a:
                score -= 1.0
                if a < 99:
                    score -= 0.15 * (a - b)

    return score


def component_score(board):
    seen = [[False for _ in range(N)] for _ in range(N)]
    score = 0.0

    for sr in range(N):
        for sc in range(N):
            if seen[sr][sc] or board[sr, sc] == -1:
                continue

            stack = [(sr, sc)]
            seen[sr][sc] = True
            empties = 0
            p1 = 0
            p2 = 0

            while stack:
                r, c = stack.pop()
                if board[r, c] == 0:
                    empties += 1
                elif board[r, c] == 1:
                    p1 += 1
                elif board[r, c] == 2:
                    p2 += 1

                for dr, dc in DIRS:
                    nr, nc = r + dr, c + dc
                    if inside(nr, nc) and not seen[nr][nc] and board[nr, nc] != -1:
                        seen[nr][nc] = True
                        stack.append((nr, nc))

            if p1 and not p2:
                score += empties + 2 * p1
            elif p2 and not p1:
                score -= empties + 2 * p2

    return score


def move_to_str(mv):
    fr, fc, tr, tc, ar, ac = mv
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"
