
import time
import math

BOARD_N = 8
DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
BIG = 10**9


def policy(board) -> str:
    start = time.time()
    limit = 0.88

    try:
        b = [list(row) for row in board]
        moves = legal_moves(b, 1)
        if not moves:
            return "0,0:0,0"  # Should not occur in valid LOA positions.

        # Immediate winning move.
        for mv in moves:
            nb = apply_move(b, mv, 1)
            if connected(nb, 1):
                return fmt(mv)

        best = moves[0]
        ordered = order_moves(b, moves, 1)

        # Iterative deepening. Depth 3 is usually safe; depth 4 when positions are quiet/small.
        max_depth = 3
        if len(moves) <= 12:
            max_depth = 4

        for depth in range(1, max_depth + 1):
            if time.time() - start > limit:
                break
            alpha, beta = -BIG, BIG
            local_best = best
            local_score = -BIG
            for mv in ordered:
                if time.time() - start > limit:
                    raise TimeoutError
                nb = apply_move(b, mv, 1)
                sc = -negamax(nb, depth - 1, -1, -beta, -alpha, start, limit)
                if sc > local_score:
                    local_score = sc
                    local_best = mv
                if sc > alpha:
                    alpha = sc
                if alpha >= beta:
                    break
            best = local_best
            # Put current best first for next iteration.
            ordered = [best] + [m for m in ordered if m != best]

        return fmt(best)

    except Exception:
        # Absolute safety fallback: recompute and return first legal move.
        try:
            b = [list(row) for row in board]
            ms = legal_moves(b, 1)
            if ms:
                return fmt(ms[0])
        except Exception:
            pass
        return "0,0:0,0"


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
                # May not jump over enemy pieces.
                ok = True
                rr, cc = r + dr, c + dc
                while (rr, cc) != (tr, tc):
                    if b[rr][cc] == -side:
                        ok = False
                        break
                    rr += dr
                    cc += dc
                if ok:
                    res.append((r, c, tr, tc))
    return res


def line_count(b, r, c, dr, dc):
    # Count all pieces on the full row/col/diagonal containing (r,c) in direction (dr,dc).
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


def count_pieces(b, side):
    n = 0
    for r in range(BOARD_N):
        for c in range(BOARD_N):
            if b[r][c] == side:
                n += 1
    return n


def components_info(b, side):
    seen = [[False] * BOARD_N for _ in range(BOARD_N)]
    comps = []
    for r in range(BOARD_N):
        for c in range(BOARD_N):
            if b[r][c] == side and not seen[r][c]:
                stack = [(r, c)]
                seen[r][c] = True
                size = 0
                sr = sc = 0
                while stack:
                    x, y = stack.pop()
                    size += 1
                    sr += x
                    sc += y
                    for dr, dc in DIRS:
                        nx, ny = x + dr, y + dc
                        if inb(nx, ny) and not seen[nx][ny] and b[nx][ny] == side:
                            seen[nx][ny] = True
                            stack.append((nx, ny))
                comps.append((size, sr / size, sc / size))
    if not comps:
        return 0, 0, []
    return len(comps), max(x[0] for x in comps), comps


def connected(b, side):
    total = count_pieces(b, side)
    if total <= 1:
        return True
    groups, largest, _ = components_info(b, side)
    return groups == 1 and largest == total


def centroid_compactness(b, side):
    pts = []
    for r in range(BOARD_N):
        for c in range(BOARD_N):
            if b[r][c] == side:
                pts.append((r, c))
    if not pts:
        return -10000
    cr = sum(p[0] for p in pts) / len(pts)
    cc = sum(p[1] for p in pts) / len(pts)
    dist = 0.0
    center = 0.0
    for r, c in pts:
        dist += abs(r - cr) + abs(c - cc)
        center += abs(r - 3.5) + abs(c - 3.5)
    return -dist * 12 - center * 2


def mobility_score(b, side):
    # Capped to keep move generation cost useful but bounded.
    return min(40, len(legal_moves(b, side)))


def eval_side(b, side):
    if connected(b, side):
        return 500000
    if connected(b, -side):
        return -500000

    my_count = count_pieces(b, side)
    op_count = count_pieces(b, -side)
    my_groups, my_largest, my_comps = components_info(b, side)
    op_groups, op_largest, op_comps = components_info(b, -side)

    if my_count == 0:
        return -500000
    if op_count == 0:
        return 500000

    score = 0
    # Primary LOA objective: fewer groups and larger largest component.
    score += (op_groups - my_groups) * 850
    score += (my_largest / float(my_count) - op_largest / float(op_count)) * 1200

    # Captures help, but not at the expense of connection.
    score += (my_count - op_count) * 90

    score += centroid_compactness(b, side)
    score -= centroid_compactness(b, -side)

    # Encourage moving component centroids closer together.
    score += component_closeness(my_comps) * 30
    score -= component_closeness(op_comps) * 30

    score += (mobility_score(b, side) - mobility_score(b, -side)) * 8
    return int(score)


def component_closeness(comps):
    if len(comps) <= 1:
        return 80
    s = 0.0
    pairs = 0
    for i in range(len(comps)):
        for j in range(i + 1, len(comps)):
            _, r1, c1 = comps[i]
            _, r2, c2 = comps[j]
            s -= max(abs(r1 - r2), abs(c1 - c2))
            pairs += 1
    return s / max(1, pairs)


def order_moves(b, moves, side):
    scored = []
    for mv in moves:
        r1, c1, r2, c2 = mv
        cap = 1 if b[r2][c2] == -side else 0
        nb = apply_move(b, mv, side)
        groups, largest, _ = components_info(nb, side)
        total = count_pieces(nb, side)
        central = -(abs(r2 - 3.5) + abs(c2 - 3.5))
        sc = cap * 500 + largest * 80 - groups * 120 + central * 5
        if connected(nb, side):
            sc += 100000
        scored.append((sc, mv))
    scored.sort(reverse=True, key=lambda x: x[0])
    return [m for _, m in scored]


def negamax(b, depth, side, alpha, beta, start, limit):
    if time.time() - start > limit:
        raise TimeoutError

    if connected(b, side):
        return 500000 + depth
    if connected(b, -side):
        return -500000 - depth
    if depth <= 0:
        return eval_side(b, side)

    moves = legal_moves(b, side)
    if not moves:
        return eval_side(b, side)

    moves = order_moves(b, moves, side)
    best = -BIG
    for mv in moves:
        nb = apply_move(b, mv, side)
        val = -negamax(nb, depth - 1, -side, -beta, -alpha, start, limit)
        if val > best:
            best = val
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break
    return best
