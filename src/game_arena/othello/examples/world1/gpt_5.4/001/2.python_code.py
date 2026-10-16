
import numpy as np
import time

DIRS = [(-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)]

INF = 10**18

# Positional weights: strong corners, discourage risky squares near corners.
PST = np.array([
    [120, -20,  20,   5,   5,  20, -20, 120],
    [-20, -40,  -5,  -5,  -5,  -5, -40, -20],
    [ 20,  -5,  15,   3,   3,  15,  -5,  20],
    [  5,  -5,   3,   3,   3,   3,  -5,   5],
    [  5,  -5,   3,   3,   3,   3,  -5,   5],
    [ 20,  -5,  15,   3,   3,  15,  -5,  20],
    [-20, -40,  -5,  -5,  -5,  -5, -40, -20],
    [120, -20,  20,   5,   5,  20, -20, 120],
], dtype=np.int32)

CORNERS = [(0, 0), (0, 7), (7, 0), (7, 7)]
X_SQUARES = {
    (1, 1): (0, 0),
    (1, 6): (0, 7),
    (6, 1): (7, 0),
    (6, 6): (7, 7),
}
C_SQUARES = {
    (0, 1): (0, 0), (1, 0): (0, 0),
    (0, 6): (0, 7), (1, 7): (0, 7),
    (6, 0): (7, 0), (7, 1): (7, 0),
    (6, 7): (7, 7), (7, 6): (7, 7),
}

def inside(r, c):
    return 0 <= r < 8 and 0 <= c < 8

def coord_to_str(move):
    r, c = move
    return chr(ord('a') + c) + str(r + 1)

def legal_moves(y, o):
    empty = (y | o) == 0
    moves = []
    for r in range(8):
        for c in range(8):
            if not empty[r, c]:
                continue
            ok = False
            for dr, dc in DIRS:
                rr, cc = r + dr, c + dc
                cnt = 0
                while inside(rr, cc) and o[rr, cc]:
                    rr += dr
                    cc += dc
                    cnt += 1
                if cnt > 0 and inside(rr, cc) and y[rr, cc]:
                    ok = True
                    break
            if ok:
                moves.append((r, c))
    return moves

def apply_move(y, o, move):
    r, c = move
    ny = y.copy()
    no = o.copy()
    ny[r, c] = 1
    for dr, dc in DIRS:
        rr, cc = r + dr, c + dc
        path = []
        while inside(rr, cc) and no[rr, cc]:
            path.append((rr, cc))
            rr += dr
            cc += dc
        if path and inside(rr, cc) and ny[rr, cc]:
            for pr, pc in path:
                no[pr, pc] = 0
                ny[pr, pc] = 1
    return ny, no

def count_frontier(y, o):
    occ = y | o
    cnt = 0
    ys = np.argwhere(y == 1)
    for r, c in ys:
        for dr, dc in DIRS:
            rr, cc = r + dr, c + dc
            if inside(rr, cc) and not occ[rr, cc]:
                cnt += 1
                break
    return cnt

def stable_corner_component(y, corner):
    r, c = corner
    if not y[r, c]:
        return 0
    total = 1
    # Along row from corner
    if c == 0:
        cc = 1
        while cc < 8 and y[r, cc]:
            total += 1
            cc += 1
    else:
        cc = 6
        while cc >= 0 and y[r, cc]:
            total += 1
            cc -= 1
    # Along col from corner
    if r == 0:
        rr = 1
        while rr < 8 and y[rr, c]:
            total += 1
            rr += 1
    else:
        rr = 6
        while rr >= 0 and y[rr, c]:
            total += 1
            rr -= 1
    return total

def evaluate(y, o):
    empties = 64 - int((y | o).sum())
    my_count = int(y.sum())
    op_count = int(o.sum())

    # Terminal / near-terminal preference
    my_moves = legal_moves(y, o)
    op_moves = legal_moves(o, y)
    if not my_moves and not op_moves:
        diff = my_count - op_count
        if diff > 0:
            return 10_000_000 + diff
        if diff < 0:
            return -10_000_000 + diff
        return 0

    score = 0

    # Positional score
    score += int((PST * y).sum() - (PST * o).sum())

    # Corner occupancy
    my_corners = sum(int(y[r, c]) for r, c in CORNERS)
    op_corners = sum(int(o[r, c]) for r, c in CORNERS)
    score += 800 * (my_corners - op_corners)

    # Corner-adjacent danger if corner unoccupied
    for (r, c), corner in X_SQUARES.items():
        cr, cc = corner
        if not y[cr, cc] and not o[cr, cc]:
            if y[r, c]:
                score -= 220
            elif o[r, c]:
                score += 220
    for (r, c), corner in C_SQUARES.items():
        cr, cc = corner
        if not y[cr, cc] and not o[cr, cc]:
            if y[r, c]:
                score -= 110
            elif o[r, c]:
                score += 110

    # Mobility
    score += 90 * (len(my_moves) - len(op_moves))

    # Potential mobility
    occ = y | o
    my_pmob = 0
    op_pmob = 0
    empties_pos = np.argwhere(occ == 0)
    for r, c in empties_pos:
        adj_y = False
        adj_o = False
        for dr, dc in DIRS:
            rr, cc = r + dr, c + dc
            if inside(rr, cc):
                if y[rr, cc]:
                    adj_y = True
                elif o[rr, cc]:
                    adj_o = True
        if adj_o:
            my_pmob += 1
        if adj_y:
            op_pmob += 1
    score += 12 * (my_pmob - op_pmob)

    # Frontier discs: fewer is better
    score += 25 * (count_frontier(o, y) - count_frontier(y, o))

    # Stability-inspired corner extensions
    my_stable = sum(stable_corner_component(y, cr) for cr in CORNERS)
    op_stable = sum(stable_corner_component(o, cr) for cr in CORNERS)
    score += 40 * (my_stable - op_stable)

    # Disc differential matters more late
    if empties <= 14:
        score += 60 * (my_count - op_count)
    elif empties <= 24:
        score += 18 * (my_count - op_count)
    else:
        score += 2 * (my_count - op_count)

    return score

def move_order_key(y, o, move):
    r, c = move
    key = 0
    # Corners first
    if (r, c) in CORNERS:
        key += 100000
    # Avoid risky near-corner squares unless corner owned
    if (r, c) in X_SQUARES:
        cr, cc = X_SQUARES[(r, c)]
        if not y[cr, cc]:
            key -= 5000
    if (r, c) in C_SQUARES:
        cr, cc = C_SQUARES[(r, c)]
        if not y[cr, cc]:
            key -= 2500
    key += int(PST[r, c]) * 10

    ny, no = apply_move(y, o, move)
    opp_moves = legal_moves(no, ny)
    key -= 80 * len(opp_moves)
    return key

def negamax(y, o, depth, alpha, beta, end_time):
    if time.perf_counter() >= end_time:
        raise TimeoutError

    my_moves = legal_moves(y, o)
    if depth == 0:
        return evaluate(y, o), None

    if not my_moves:
        op_moves = legal_moves(o, y)
        if not op_moves:
            return evaluate(y, o), None
        val, _ = negamax(o, y, depth, -beta, -alpha, end_time)
        return -val, None

    moves = sorted(my_moves, key=lambda m: move_order_key(y, o, m), reverse=True)

    best_move = moves[0]
    best_val = -INF

    for mv in moves:
        ny, no = apply_move(y, o, mv)
        val, _ = negamax(no, ny, depth - 1, -beta, -alpha, end_time)
        val = -val
        if val > best_val:
            best_val = val
            best_move = mv
        if best_val > alpha:
            alpha = best_val
        if alpha >= beta:
            break

    return best_val, best_move

def choose_depth(empties):
    if empties <= 10:
        return 12
    if empties <= 14:
        return 10
    if empties <= 20:
        return 7
    if empties <= 32:
        return 5
    return 4

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    y = (you.astype(np.uint8) != 0)
    o = (opponent.astype(np.uint8) != 0)

    moves = legal_moves(y, o)
    if not moves:
        return "pass"

    # Always keep a legal fallback.
    ordered = sorted(moves, key=lambda m: move_order_key(y, o, m), reverse=True)
    best_move = ordered[0]

    empties = 64 - int((y | o).sum())
    max_depth = choose_depth(empties)

    start = time.perf_counter()
    time_budget = 0.92
    end_time = start + time_budget

    # Iterative deepening.
    for depth in range(1, max_depth + 1):
        try:
            val, mv = negamax(y, o, depth, -INF, INF, end_time)
            if mv is not None:
                best_move = mv
        except TimeoutError:
            break

    return coord_to_str(best_move)
