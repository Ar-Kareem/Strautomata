
import time
import math

DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]


def policy(board) -> str:
    start = time.time()
    limit = 0.92

    b = [row[:] for row in board]
    moves = legal_moves(b, 1)
    if not moves:
        return "0,0:0,0"

    # Always keep a legal fallback.
    best_move = moves[0]

    # Immediate win.
    for mv in moves:
        nb = apply_move(b, mv, 1)
        if connected(nb, 1):
            return fmt(mv)

    # Prefer captures / central moves for ordering.
    moves = order_moves(b, moves, 1)

    # Iterative deepening. Depth 3 is usually safe; depth 4 sometimes possible.
    max_depth = 4
    best_score = -10**18

    for depth in range(1, max_depth + 1):
        if time.time() - start > limit:
            break
        alpha = -10**18
        beta = 10**18
        local_best = best_move
        local_score = -10**18
        completed = True

        for mv in moves:
            if time.time() - start > limit:
                completed = False
                break
            nb = apply_move(b, mv, 1)
            sc = alphabeta(nb, depth - 1, -1, alpha, beta, start, limit)
            if sc > local_score:
                local_score = sc
                local_best = mv
            if sc > alpha:
                alpha = sc

        if completed:
            best_move = local_best
            best_score = local_score
        else:
            break

    return fmt(best_move)


def fmt(mv):
    r1, c1, r2, c2 = mv
    return f"{r1},{c1}:{r2},{c2}"


def inb(r, c):
    return 0 <= r < 8 and 0 <= c < 8


def legal_moves(b, side):
    res = []
    for r in range(8):
        for c in range(8):
            if b[r][c] == side:
                for dr, dc in DIRS:
                    n = line_count(b, r, c, dr, dc)
                    r2 = r + dr * n
                    c2 = c + dc * n
                    if not inb(r2, c2):
                        continue
                    if b[r2][c2] == side:
                        continue
                    blocked = False
                    # Enemy pieces may not be jumped over. Destination may be enemy.
                    for k in range(1, n):
                        rr = r + dr * k
                        cc = c + dc * k
                        if b[rr][cc] == -side:
                            blocked = True
                            break
                    if not blocked:
                        res.append((r, c, r2, c2))
    return res


def line_count(b, r, c, dr, dc):
    # Count all pieces on the full row/column/diagonal corresponding to direction.
    cnt = 0
    rr, cc = r, c
    while inb(rr - dr, cc - dc):
        rr -= dr
        cc -= dc
    while inb(rr, cc):
        if b[rr][cc] != 0:
            cnt += 1
        rr += dr
        cc += dc
    return cnt


def apply_move(b, mv, side):
    r1, c1, r2, c2 = mv
    nb = [row[:] for row in b]
    nb[r1][c1] = 0
    nb[r2][c2] = side
    return nb


def piece_positions(b, side):
    return [(r, c) for r in range(8) for c in range(8) if b[r][c] == side]


def connected(b, side):
    ps = piece_positions(b, side)
    if len(ps) <= 1:
        return True
    seen = set([ps[0]])
    stack = [ps[0]]
    while stack:
        r, c = stack.pop()
        for dr, dc in DIRS:
            rr, cc = r + dr, c + dc
            if inb(rr, cc) and b[rr][cc] == side and (rr, cc) not in seen:
                seen.add((rr, cc))
                stack.append((rr, cc))
    return len(seen) == len(ps)


def components_and_largest(b, side):
    ps = piece_positions(b, side)
    if not ps:
        return 0, 0
    unvisited = set(ps)
    comps = 0
    largest = 0
    while unvisited:
        comps += 1
        start = next(iter(unvisited))
        unvisited.remove(start)
        stack = [start]
        size = 0
        while stack:
            r, c = stack.pop()
            size += 1
            for dr, dc in DIRS:
                rr, cc = r + dr, c + dc
                if (rr, cc) in unvisited:
                    unvisited.remove((rr, cc))
                    stack.append((rr, cc))
        largest = max(largest, size)
    return comps, largest


def avg_chebyshev_to_centroid(ps):
    if len(ps) <= 1:
        return 0.0
    cr = sum(r for r, c in ps) / len(ps)
    cc = sum(c for r, c in ps) / len(ps)
    return sum(max(abs(r - cr), abs(c - cc)) for r, c in ps) / len(ps)


def adjacency_count(b, side):
    total = 0
    for r, c in piece_positions(b, side):
        for dr, dc in DIRS:
            rr, cc = r + dr, c + dc
            if inb(rr, cc) and b[rr][cc] == side:
                total += 1
    return total // 2


def centrality(ps):
    if not ps:
        return 0.0
    return sum(3.5 - max(abs(r - 3.5), abs(c - 3.5)) for r, c in ps) / len(ps)


def evaluation(b):
    if connected(b, 1):
        return 1000000
    if connected(b, -1):
        return -1000000

    myp = piece_positions(b, 1)
    opp = piece_positions(b, -1)

    my_comp, my_largest = components_and_largest(b, 1)
    op_comp, op_largest = components_and_largest(b, -1)

    my_n = len(myp)
    op_n = len(opp)

    my_spread = avg_chebyshev_to_centroid(myp)
    op_spread = avg_chebyshev_to_centroid(opp)

    my_adj = adjacency_count(b, 1)
    op_adj = adjacency_count(b, -1)

    # Mobility is useful, but less important than connectivity.
    my_mob = len(legal_moves(b, 1))
    op_mob = len(legal_moves(b, -1))

    score = 0
    score += 520 * (op_comp - my_comp)
    score += 85 * (my_largest - op_largest)
    score += 55 * (op_spread - my_spread)
    score += 22 * (my_adj - op_adj)
    score += 18 * (op_n - my_n)  # Capturing can help by reducing opponent material.
    score += 7 * (centrality(myp) - centrality(opp))
    score += 2 * (my_mob - op_mob)
    return score


def order_moves(b, moves, side):
    def key(mv):
        r1, c1, r2, c2 = mv
        capture = 1 if b[r2][c2] == -side else 0
        center = -max(abs(r2 - 3.5), abs(c2 - 3.5))
        nb = apply_move(b, mv, side)
        comps, largest = components_and_largest(nb, side)
        return (connected(nb, side), capture, -comps, largest, center)
    return sorted(moves, key=key, reverse=True)


def alphabeta(b, depth, side, alpha, beta, start, limit):
    if time.time() - start > limit:
        return evaluation(b)

    if connected(b, 1):
        return 1000000 + depth
    if connected(b, -1):
        return -1000000 - depth
    if depth <= 0:
        return evaluation(b)

    moves = legal_moves(b, side)
    if not moves:
        return evaluation(b)

    moves = order_moves(b, moves, side)

    if side == 1:
        value = -10**18
        for mv in moves:
            nb = apply_move(b, mv, side)
            value = max(value, alphabeta(nb, depth - 1, -side, alpha, beta, start, limit))
            alpha = max(alpha, value)
            if alpha >= beta or time.time() - start > limit:
                break
        return value
    else:
        value = 10**18
        for mv in moves:
            nb = apply_move(b, mv, side)
            value = min(value, alphabeta(nb, depth - 1, -side, alpha, beta, start, limit))
            beta = min(beta, value)
            if alpha >= beta or time.time() - start > limit:
                break
        return value
