
import time
from collections import deque

N = 8
DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]


def policy(board) -> str:
    b = [list(row) for row in board]
    moves = legal_moves(b, 1)
    if not moves:
        return "0,0:0,0"  # Should never happen in normal LOA positions.

    # Immediate win.
    for mv in moves:
        nb = make_move(b, mv, 1)
        if connected(nb, 1):
            return fmt(mv)

    end_time = time.time() + 0.88

    # If only one move, return it.
    if len(moves) == 1:
        return fmt(moves[0])

    # Order moves using static evaluation.
    moves = order_moves(b, moves, 1)

    best = moves[0]
    best_score = -10**18

    # Adaptive search depth. LOA branching can be high, so keep within 1s.
    piece_count = count_pieces(b, 1) + count_pieces(b, -1)
    if len(moves) <= 10:
        max_depth = 3
    elif len(moves) <= 28 and piece_count <= 18:
        max_depth = 3
    else:
        max_depth = 2

    alpha = -10**18
    beta = 10**18

    try:
        for mv in moves:
            if time.time() > end_time:
                break
            nb = make_move(b, mv, 1)

            # Avoid moves giving opponent immediate connection, unless no better exists.
            score = -alphabeta(nb, max_depth - 1, -beta, -alpha, -1, end_time)

            if score > best_score:
                best_score = score
                best = mv
            if score > alpha:
                alpha = score
    except TimeoutError:
        pass

    return fmt(best)


def fmt(mv):
    r1, c1, r2, c2 = mv
    return f"{r1},{c1}:{r2},{c2}"


def inb(r, c):
    return 0 <= r < N and 0 <= c < N


def count_line(board, r, c, dr, dc):
    # Count pieces on the full row/col/diagonal containing (r,c) in direction (dr,dc).
    rr, cc = r, c
    while inb(rr - dr, cc - dc):
        rr -= dr
        cc -= dc
    cnt = 0
    while inb(rr, cc):
        if board[rr][cc] != 0:
            cnt += 1
        rr += dr
        cc += dc
    return cnt


def legal_moves(board, side):
    res = []
    for r in range(N):
        row = board[r]
        for c in range(N):
            if row[c] != side:
                continue
            for dr, dc in DIRS:
                dist = count_line(board, r, c, dr, dc)
                tr = r + dr * dist
                tc = c + dc * dist
                if not inb(tr, tc):
                    continue
                if board[tr][tc] == side:
                    continue

                # Cannot jump over enemy pieces. Friendly pieces may be jumped.
                blocked = False
                rr, cc = r + dr, c + dc
                while (rr, cc) != (tr, tc):
                    if board[rr][cc] == -side:
                        blocked = True
                        break
                    rr += dr
                    cc += dc
                if not blocked:
                    res.append((r, c, tr, tc))
    return res


def make_move(board, mv, side):
    r1, c1, r2, c2 = mv
    nb = [row[:] for row in board]
    nb[r1][c1] = 0
    nb[r2][c2] = side
    return nb


def count_pieces(board, side):
    return sum(1 for r in range(N) for c in range(N) if board[r][c] == side)


def positions(board, side):
    return [(r, c) for r in range(N) for c in range(N) if board[r][c] == side]


def connected(board, side):
    ps = positions(board, side)
    if len(ps) <= 1:
        return True

    start = ps[0]
    seen = {start}
    q = deque([start])

    while q:
        r, c = q.popleft()
        for dr, dc in DIRS:
            rr, cc = r + dr, c + dc
            if inb(rr, cc) and board[rr][cc] == side and (rr, cc) not in seen:
                seen.add((rr, cc))
                q.append((rr, cc))
    return len(seen) == len(ps)


def component_info(board, side):
    ps = positions(board, side)
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
                rr, cc = r + dr, c + dc
                if (rr, cc) in unseen:
                    unseen.remove((rr, cc))
                    q.append((rr, cc))
        if size > largest:
            largest = size

    return comps, largest


def distance_stats(board, side):
    ps = positions(board, side)
    n = len(ps)
    if n <= 1:
        return 0, 0

    # Chebyshev distances are relevant because LOA connectivity is 8-neighbor.
    total = 0
    maxd = 0
    pairs = 0
    for i in range(n):
        r1, c1 = ps[i]
        for j in range(i + 1, n):
            r2, c2 = ps[j]
            d = max(abs(r1 - r2), abs(c1 - c2))
            total += d
            if d > maxd:
                maxd = d
            pairs += 1
    return total / pairs, maxd


def center_score(board, side):
    ps = positions(board, side)
    if not ps:
        return -100
    # Prefer central compact formations.
    s = 0.0
    for r, c in ps:
        s -= abs(r - 3.5) + abs(c - 3.5)
    return s


def mobility(board, side):
    return len(legal_moves(board, side))


def evaluate(board):
    # Positive is good for side 1, negative is good for side -1.
    if connected(board, 1):
        return 1000000
    if connected(board, -1):
        return -1000000

    return side_eval(board, 1) - side_eval(board, -1)


def side_eval(board, side):
    ps = positions(board, side)
    n = len(ps)
    if n <= 1:
        return 100000

    comps, largest = component_info(board, side)
    avgd, maxd = distance_stats(board, side)

    score = 0.0
    score -= comps * 900.0
    score += largest * 120.0
    score -= avgd * 75.0
    score -= maxd * 35.0
    score += center_score(board, side) * 10.0
    score += n * 35.0  # Having more pieces is usually useful, but connectivity matters more.
    score += min(mobility(board, side), 40) * 5.0

    # Reward pieces with friendly neighbors.
    neighbor_bonus = 0
    for r, c in ps:
        cnt = 0
        for dr, dc in DIRS:
            rr, cc = r + dr, c + dc
            if inb(rr, cc) and board[rr][cc] == side:
                cnt += 1
        neighbor_bonus += cnt
    score += neighbor_bonus * 25.0

    return score


def alphabeta(board, depth, alpha, beta, side, end_time):
    if time.time() > end_time:
        raise TimeoutError

    if connected(board, 1):
        return 1000000 + depth
    if connected(board, -1):
        return -1000000 - depth
    if depth <= 0:
        return evaluate(board)

    moves = legal_moves(board, side)
    if not moves:
        return evaluate(board)

    moves = order_moves(board, moves, side)

    if side == 1:
        value = -10**18
        for mv in moves:
            nb = make_move(board, mv, side)
            value = max(value, alphabeta(nb, depth - 1, alpha, beta, -side, end_time))
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value
    else:
        value = 10**18
        for mv in moves:
            nb = make_move(board, mv, side)
            value = min(value, alphabeta(nb, depth - 1, alpha, beta, -side, end_time))
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value


def order_moves(board, moves, side):
    scored = []
    for mv in moves:
        r1, c1, r2, c2 = mv
        capture = 1 if board[r2][c2] == -side else 0
        nb = make_move(board, mv, side)

        if connected(nb, side):
            s = 10**9
        else:
            comps, largest = component_info(nb, side)
            avgd, maxd = distance_stats(nb, side)
            # For side -1, this is still ordering from that side's perspective.
            s = -comps * 10000 + largest * 1000 - avgd * 120 - maxd * 50 + capture * 500
            # Prefer moves toward own centroid.
            ps = positions(board, side)
            if ps:
                cr = sum(p[0] for p in ps) / len(ps)
                cc = sum(p[1] for p in ps) / len(ps)
                oldd = max(abs(r1 - cr), abs(c1 - cc))
                newd = max(abs(r2 - cr), abs(c2 - cc))
                s += (oldd - newd) * 80
        scored.append((s, mv))

    scored.sort(reverse=True, key=lambda x: x[0])
    return [mv for _, mv in scored]
