
import math
import time
from collections import deque

BOARD_N = 8
DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]


def policy(board) -> str:
    start = time.time()
    b = [list(row) for row in board]

    moves = legal_moves(b, 1)
    if not moves:
        return "0,0:0,0"

    # Immediate win.
    best = None
    for mv in moves:
        nb = make_move(b, mv, 1)
        if connected(nb, 1):
            return fmt(mv)

    # Prefer captures / connectivity if time gets tight.
    best = choose_static(b, moves)

    # Iterative deepening within safe time.
    deadline = start + 0.90
    for depth in (2, 3):
        if time.time() > deadline:
            break
        try:
            val, mv = alphabeta_root(b, depth, deadline)
            if mv is not None:
                best = mv
        except TimeoutError:
            break

    return fmt(best)


def fmt(mv):
    r1, c1, r2, c2 = mv
    return f"{r1},{c1}:{r2},{c2}"


def inb(r, c):
    return 0 <= r < BOARD_N and 0 <= c < BOARD_N


def legal_moves(b, side):
    res = []
    for r in range(BOARD_N):
        for c in range(BOARD_N):
            if b[r][c] != side:
                continue
            for dr, dc in DIRS:
                cnt = line_count(b, r, c, dr, dc)
                tr, tc = r + dr * cnt, c + dc * cnt
                if not inb(tr, tc):
                    continue
                if b[tr][tc] == side:
                    continue
                # Cannot jump over enemy pieces.
                ok = True
                cr, cc = r + dr, c + dc
                while (cr, cc) != (tr, tc):
                    if b[cr][cc] == -side:
                        ok = False
                        break
                    cr += dr
                    cc += dc
                if ok:
                    res.append((r, c, tr, tc))
    return res


def line_count(b, r, c, dr, dc):
    cnt = 1

    rr, cc = r + dr, c + dc
    while inb(rr, cc):
        if b[rr][cc] != 0:
            cnt += 1
        rr += dr
        cc += dc

    rr, cc = r - dr, c - dc
    while inb(rr, cc):
        if b[rr][cc] != 0:
            cnt += 1
        rr -= dr
        cc -= dc

    return cnt


def make_move(b, mv, side):
    r1, c1, r2, c2 = mv
    nb = [row[:] for row in b]
    nb[r1][c1] = 0
    nb[r2][c2] = side
    return nb


def pieces(b, side):
    ps = []
    for r in range(BOARD_N):
        for c in range(BOARD_N):
            if b[r][c] == side:
                ps.append((r, c))
    return ps


def connected(b, side):
    ps = pieces(b, side)
    if len(ps) <= 1:
        return True
    seen = {ps[0]}
    q = deque([ps[0]])
    while q:
        r, c = q.popleft()
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if inb(nr, nc) and (nr, nc) not in seen and b[nr][nc] == side:
                seen.add((nr, nc))
                q.append((nr, nc))
    return len(seen) == len(ps)


def component_count_and_largest(b, side):
    ps = pieces(b, side)
    if not ps:
        return 0, 0
    unseen = set(ps)
    comps = 0
    largest = 0
    while unseen:
        comps += 1
        start = next(iter(unseen))
        unseen.remove(start)
        q = deque([start])
        size = 0
        while q:
            r, c = q.popleft()
            size += 1
            for dr, dc in DIRS:
                nr, nc = r + dr, c + dc
                if (nr, nc) in unseen:
                    unseen.remove((nr, nc))
                    q.append((nr, nc))
        largest = max(largest, size)
    return comps, largest


def avg_dist_to_center(ps):
    if not ps:
        return 0.0
    return sum(max(abs(r - 3.5), abs(c - 3.5)) for r, c in ps) / len(ps)


def avg_pair_dist(ps):
    n = len(ps)
    if n <= 1:
        return 0.0
    s = 0
    cnt = 0
    for i in range(n):
        r1, c1 = ps[i]
        for j in range(i + 1, n):
            r2, c2 = ps[j]
            s += max(abs(r1 - r2), abs(c1 - c2))
            cnt += 1
    return s / cnt


def adjacency_score(b, side):
    ps = pieces(b, side)
    s = 0
    for r, c in ps:
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if inb(nr, nc) and b[nr][nc] == side:
                s += 1
    return s / 2


def evaluate(b):
    if connected(b, 1):
        return 100000
    if connected(b, -1):
        return -100000

    myp = pieces(b, 1)
    opp = pieces(b, -1)
    my_comps, my_largest = component_count_and_largest(b, 1)
    op_comps, op_largest = component_count_and_largest(b, -1)

    my_moves = len(legal_moves(b, 1))
    op_moves = len(legal_moves(b, -1))

    score = 0
    # Main LOA goal: fewer components and bigger main group.
    score += 900 * (op_comps - my_comps)
    score += 120 * (my_largest - op_largest)

    # Compactness and adjacency are very important.
    score += 80 * (avg_pair_dist(opp) - avg_pair_dist(myp))
    score += 45 * (adjacency_score(b, 1) - adjacency_score(b, -1))

    # Capturing can help if it reduces opponent material, but not at expense of connectivity.
    score += 35 * (len(myp) - len(opp))

    # Central positions generally connect faster.
    score += 25 * (avg_dist_to_center(opp) - avg_dist_to_center(myp))

    # Mobility matters, but too much is less important than connectedness.
    score += 5 * (my_moves - op_moves)

    return score


def ordered_moves(b, side):
    mvs = legal_moves(b, side)

    def key(mv):
        r1, c1, r2, c2 = mv
        cap = 1 if b[r2][c2] == -side else 0
        nb = make_move(b, mv, side)
        comps, largest = component_count_and_largest(nb, side)
        cen = -max(abs(r2 - 3.5), abs(c2 - 3.5))
        win = 1 if connected(nb, side) else 0
        return (win, -comps, largest, cap, cen)

    mvs.sort(key=key, reverse=True)
    return mvs


def alphabeta_root(b, depth, deadline):
    best_val = -math.inf
    best_mv = None
    alpha = -math.inf
    beta = math.inf

    for mv in ordered_moves(b, 1):
        if time.time() > deadline:
            raise TimeoutError()
        nb = make_move(b, mv, 1)
        val = alphabeta(nb, depth - 1, alpha, beta, -1, deadline)
        if val > best_val:
            best_val = val
            best_mv = mv
        alpha = max(alpha, best_val)

    return best_val, best_mv


def alphabeta(b, depth, alpha, beta, side, deadline):
    if time.time() > deadline:
        raise TimeoutError()

    if connected(b, 1):
        return 100000 + depth
    if connected(b, -1):
        return -100000 - depth
    if depth <= 0:
        return evaluate(b)

    mvs = ordered_moves(b, side)
    if not mvs:
        return evaluate(b)

    if side == 1:
        val = -math.inf
        for mv in mvs:
            nb = make_move(b, mv, side)
            val = max(val, alphabeta(nb, depth - 1, alpha, beta, -side, deadline))
            alpha = max(alpha, val)
            if alpha >= beta:
                break
        return val
    else:
        val = math.inf
        for mv in mvs:
            nb = make_move(b, mv, side)
            val = min(val, alphabeta(nb, depth - 1, alpha, beta, -side, deadline))
            beta = min(beta, val)
            if alpha >= beta:
                break
        return val


def choose_static(b, moves):
    best = moves[0]
    best_score = -math.inf
    for mv in moves:
        nb = make_move(b, mv, 1)
        sc = evaluate(nb)

        r1, c1, r2, c2 = mv
        if b[r2][c2] == -1:
            sc += 20
        sc -= 2 * max(abs(r2 - 3.5), abs(c2 - 3.5))

        if sc > best_score:
            best_score = sc
            best = mv
    return best
