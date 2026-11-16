
import time
import math
from collections import deque

N = 8
DIRS = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]

def policy(board) -> str:
    start = time.time()
    try:
        b = [list(row) for row in board]
        moves = legal_moves(b, 1)
        if not moves:
            return "0,0:0,0"  # Should not occur in valid LOA positions.

        # Immediate win.
        for m in moves:
            nb = make_move(b, m, 1)
            if connected(nb, 1):
                return fmt(m)

        # If opponent has immediate wins, prefer moves that stop all/most of them.
        opp_now = legal_moves(b, -1)
        opp_wins = []
        for om in opp_now:
            ob = make_move(b, om, -1)
            if connected(ob, -1):
                opp_wins.append(om)

        if opp_wins:
            safe = []
            for m in moves:
                nb = make_move(b, m, 1)
                bad = False
                for om in legal_moves(nb, -1):
                    if connected(make_move(nb, om, -1), -1):
                        bad = True
                        break
                if not bad:
                    safe.append(m)
            if safe:
                moves = safe

        # Order candidate moves for better alpha-beta.
        moves = sorted(moves, key=lambda m: move_order_score(b, m, 1), reverse=True)

        best = moves[0]
        best_score = -10**18

        # Adaptive depth: normally 3 plies, deeper in small positions.
        pieces = count_pieces(b, 1) + count_pieces(b, -1)
        depth = 3 if pieces > 12 else 4

        alpha = -10**18
        beta = 10**18

        for m in moves:
            if time.time() - start > 0.88:
                break
            nb = make_move(b, m, 1)
            sc = alphabeta(nb, depth - 1, alpha, beta, -1, start)
            if sc > best_score:
                best_score = sc
                best = m
            alpha = max(alpha, best_score)

        return fmt(best)
    except Exception:
        # Absolute safety fallback.
        try:
            b = [list(row) for row in board]
            ms = legal_moves(b, 1)
            if ms:
                return fmt(ms[0])
        except Exception:
            pass
        return "0,0:0,0"


def fmt(m):
    return f"{m[0]},{m[1]}:{m[2]},{m[3]}"


def inb(r, c):
    return 0 <= r < N and 0 <= c < N


def count_pieces(b, side):
    s = 0
    for r in range(N):
        for c in range(N):
            if b[r][c] == side:
                s += 1
    return s


def line_count(b, r, c, dr, dc):
    # Count all pieces on the full line through (r,c) in direction dr,dc.
    total = 0
    rr, cc = r, c
    while inb(rr - dr, cc - dc):
        rr -= dr
        cc -= dc
    while inb(rr, cc):
        if b[rr][cc] != 0:
            total += 1
        rr += dr
        cc += dc
    return total


def legal_moves(b, side):
    ms = []
    for r in range(N):
        for c in range(N):
            if b[r][c] != side:
                continue
            for dr, dc in DIRS:
                dist = line_count(b, r, c, dr, dc)
                tr, tc = r + dr * dist, c + dc * dist
                if not inb(tr, tc):
                    continue
                if b[tr][tc] == side:
                    continue

                # May jump own pieces, but not enemy pieces before destination.
                ok = True
                rr, cc = r + dr, c + dc
                while (rr, cc) != (tr, tc):
                    if b[rr][cc] == -side:
                        ok = False
                        break
                    rr += dr
                    cc += dc
                if ok:
                    ms.append((r, c, tr, tc))
    return ms


def make_move(b, m, side):
    r, c, tr, tc = m
    nb = [row[:] for row in b]
    nb[r][c] = 0
    nb[tr][tc] = side
    return nb


def components_and_largest(b, side):
    seen = [[False] * N for _ in range(N)]
    comps = 0
    largest = 0
    total = 0
    for r in range(N):
        for c in range(N):
            if b[r][c] == side:
                total += 1
                if not seen[r][c]:
                    comps += 1
                    q = [(r, c)]
                    seen[r][c] = True
                    sz = 0
                    for x, y in q:
                        sz += 1
                        for dr, dc in DIRS:
                            nx, ny = x + dr, y + dc
                            if inb(nx, ny) and not seen[nx][ny] and b[nx][ny] == side:
                                seen[nx][ny] = True
                                q.append((nx, ny))
                    largest = max(largest, sz)
    return comps, largest, total


def connected(b, side):
    comps, largest, total = components_and_largest(b, side)
    return total > 0 and comps == 1


def centroid_stats(b, side):
    pts = []
    for r in range(N):
        for c in range(N):
            if b[r][c] == side:
                pts.append((r, c))
    if not pts:
        return 999.0, 999.0, 0.0

    ar = sum(p[0] for p in pts) / len(pts)
    ac = sum(p[1] for p in pts) / len(pts)
    avg = sum(max(abs(r - ar), abs(c - ac)) for r, c in pts) / len(pts)
    center = sum((3.5 - abs(r - 3.5)) + (3.5 - abs(c - 3.5)) for r, c in pts) / len(pts)
    return avg, abs(ar - 3.5) + abs(ac - 3.5), center


def adjacency_score(b, side):
    s = 0
    for r in range(N):
        for c in range(N):
            if b[r][c] == side:
                for dr, dc in DIRS:
                    nr, nc = r + dr, c + dc
                    if inb(nr, nc) and b[nr][nc] == side:
                        s += 1
    return s / 2


def side_eval(b, side):
    comps, largest, total = components_and_largest(b, side)
    if total == 0:
        return -100000
    if comps == 1:
        return 100000 + 500 * total

    avgdist, centdist, center = centroid_stats(b, side)
    mob = len(legal_moves(b, side))
    adj = adjacency_score(b, side)

    # LOA is mostly about connectivity: components/largest component dominate.
    val = 0
    val -= 1400 * comps
    val += 260 * largest
    val += 35 * adj
    val -= 90 * avgdist
    val -= 12 * centdist
    val += 8 * center
    val += 5 * mob
    # Having slightly fewer pieces can help connectivity, but too few is dangerous;
    # use only a small material term.
    val += 18 * total
    return val


def evaluate(b):
    if connected(b, 1):
        return 10000000
    if connected(b, -1):
        return -10000000
    return side_eval(b, 1) - side_eval(b, -1)


def move_order_score(b, m, side):
    r, c, tr, tc = m
    score = 0
    if b[tr][tc] == -side:
        score += 500
    nb = make_move(b, m, side)
    if connected(nb, side):
        score += 100000
    comps, largest, total = components_and_largest(nb, side)
    score += 200 * largest - 900 * comps
    score += adjacency_score(nb, side) * 20
    score += (7 - (abs(tr - 3.5) + abs(tc - 3.5))) * 5
    return score


def alphabeta(b, depth, alpha, beta, side, start):
    if time.time() - start > 0.94:
        return evaluate(b)

    if connected(b, 1):
        return 10000000 + depth
    if connected(b, -1):
        return -10000000 - depth
    if depth <= 0:
        return evaluate(b)

    ms = legal_moves(b, side)
    if not ms:
        return evaluate(b)

    ms = sorted(ms, key=lambda m: move_order_score(b, m, side), reverse=True)

    if side == 1:
        v = -10**18
        for m in ms:
            nb = make_move(b, m, side)
            v = max(v, alphabeta(nb, depth - 1, alpha, beta, -side, start))
            alpha = max(alpha, v)
            if alpha >= beta or time.time() - start > 0.94:
                break
        return v
    else:
        v = 10**18
        for m in ms:
            nb = make_move(b, m, side)
            v = min(v, alphabeta(nb, depth - 1, alpha, beta, -side, start))
            beta = min(beta, v)
            if alpha >= beta or time.time() - start > 0.94:
                break
        return v
