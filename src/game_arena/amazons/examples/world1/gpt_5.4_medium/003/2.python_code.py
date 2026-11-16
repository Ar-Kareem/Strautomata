
import time
from collections import deque
import numpy as np


DIRS = (
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
)


def policy(board) -> str:
    board = np.asarray(board, dtype=np.int8)
    N = 6
    INF = 10**9
    DIST_INF = 99
    deadline = time.perf_counter() + 0.92

    pos_cache = {}
    moves_cache = {}
    dest_cache = {}
    quick_cache = {}
    eval_cache = {}
    terr_cache = {}

    def board_key(b):
        return b.tobytes()

    def in_bounds(r, c):
        return 0 <= r < N and 0 <= c < N

    def positions(b, player):
        key = (board_key(b), player)
        if key in pos_cache:
            return pos_cache[key]
        arr = np.argwhere(b == player)
        res = [(int(x[0]), int(x[1])) for x in arr]
        pos_cache[key] = res
        return res

    def ray_targets(b, r, c, vacate=None):
        vr = vc = -1
        if vacate is not None:
            vr, vc = vacate
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            while 0 <= nr < N and 0 <= nc < N:
                if nr == vr and nc == vc:
                    yield (nr, nc)
                    nr += dr
                    nc += dc
                    continue
                if b[nr, nc] != 0:
                    break
                yield (nr, nc)
                nr += dr
                nc += dc

    def generate_moves(b, player):
        key = (board_key(b), player)
        if key in moves_cache:
            return moves_cache[key]

        res = []
        for fr, fc in positions(b, player):
            for tr, tc in ray_targets(b, fr, fc):
                for ar, ac in ray_targets(b, tr, tc, vacate=(fr, fc)):
                    res.append((fr, fc, tr, tc, ar, ac))

        moves_cache[key] = res
        return res

    def apply_move(b, move, player):
        fr, fc, tr, tc, ar, ac = move
        nb = b.copy()
        nb[fr, fc] = 0
        nb[tr, tc] = player
        nb[ar, ac] = -1
        return nb

    def count_destinations(b, player):
        key = (board_key(b), player)
        if key in dest_cache:
            return dest_cache[key]
        total = 0
        for r, c in positions(b, player):
            for _ in ray_targets(b, r, c):
                total += 1
        dest_cache[key] = total
        return total

    def adjacent_liberties(b, player):
        total = 0
        for r, c in positions(b, player):
            for dr, dc in DIRS:
                nr, nc = r + dr, c + dc
                if 0 <= nr < N and 0 <= nc < N and b[nr, nc] == 0:
                    total += 1
        return total

    def center_score(b):
        s = 0
        for r, c in positions(b, 1):
            s += 6 - abs(2 * r - 5) - abs(2 * c - 5)
        for r, c in positions(b, 2):
            s -= 6 - abs(2 * r - 5) - abs(2 * c - 5)
        return s

    def queen_distances(b, starts):
        dist = np.full((N, N), DIST_INF, dtype=np.int16)
        q = deque()
        for r, c in starts:
            dist[r, c] = 0
            q.append((r, c))

        while q:
            r, c = q.popleft()
            nd = dist[r, c] + 1
            for dr, dc in DIRS:
                nr, nc = r + dr, c + dc
                while 0 <= nr < N and 0 <= nc < N:
                    if b[nr, nc] != 0:
                        break
                    if nd < dist[nr, nc]:
                        dist[nr, nc] = nd
                        q.append((nr, nc))
                    nr += dr
                    nc += dc
        return dist

    def territory_score(b):
        key = board_key(b)
        if key in terr_cache:
            return terr_cache[key]

        p1 = positions(b, 1)
        p2 = positions(b, 2)
        d1 = queen_distances(b, p1)
        d2 = queen_distances(b, p2)

        terr = 0
        prox = 0
        for r in range(N):
            for c in range(N):
                if b[r, c] != 0:
                    continue
                a = int(d1[r, c])
                o = int(d2[r, c])

                if a < o:
                    terr += 1
                elif o < a:
                    terr -= 1

                if a < DIST_INF and o == DIST_INF:
                    terr += 2
                    prox += 3
                elif o < DIST_INF and a == DIST_INF:
                    terr -= 2
                    prox -= 3
                elif a < DIST_INF and o < DIST_INF:
                    diff = o - a
                    if diff > 3:
                        diff = 3
                    elif diff < -3:
                        diff = -3
                    prox += diff

        terr_cache[key] = (terr, prox)
        return terr_cache[key]

    def quick_evaluate(b):
        key = board_key(b)
        if key in quick_cache:
            return quick_cache[key]

        myd = count_destinations(b, 1)
        opd = count_destinations(b, 2)

        if opd == 0:
            val = 100000 + myd
            quick_cache[key] = val
            return val
        if myd == 0:
            val = -100000 - opd
            quick_cache[key] = val
            return val

        local = adjacent_liberties(b, 1) - adjacent_liberties(b, 2)
        val = 10 * (myd - opd) + 2 * local + center_score(b)
        quick_cache[key] = val
        return val

    def evaluate(b):
        key = board_key(b)
        if key in eval_cache:
            return eval_cache[key]

        myd = count_destinations(b, 1)
        opd = count_destinations(b, 2)

        if opd == 0:
            val = 100000 + 50 * myd
            eval_cache[key] = val
            return val
        if myd == 0:
            val = -100000 - 50 * opd
            eval_cache[key] = val
            return val

        terr, prox = territory_score(b)
        local = adjacent_liberties(b, 1) - adjacent_liberties(b, 2)
        cen = center_score(b)

        val = 28 * terr + 8 * prox + 7 * (myd - opd) + 2 * local + cen
        eval_cache[key] = val
        return val

    def search(b, depth, player, alpha, beta, beam):
        if time.perf_counter() > deadline:
            return evaluate(b)

        moves = generate_moves(b, player)
        if not moves:
            return -100000 if player == 1 else 100000
        if depth == 0:
            return evaluate(b)

        maximizing = (player == 1)
        children = []

        for m in moves:
            nb = apply_move(b, m, player)
            children.append((quick_evaluate(nb), nb))
            if time.perf_counter() > deadline and children:
                break

        children.sort(key=lambda x: x[0], reverse=maximizing)
        if beam is not None and len(children) > beam:
            children = children[:beam]

        next_beam = None if beam is None else max(5, beam - 2)

        if maximizing:
            value = -INF
            for _, nb in children:
                v = search(nb, depth - 1, 2, alpha, beta, next_beam)
                if v > value:
                    value = v
                if value > alpha:
                    alpha = value
                if alpha >= beta or time.perf_counter() > deadline:
                    break
            return value
        else:
            value = INF
            for _, nb in children:
                v = search(nb, depth - 1, 1, alpha, beta, next_beam)
                if v < value:
                    value = v
                if value < beta:
                    beta = value
                if alpha >= beta or time.perf_counter() > deadline:
                    break
            return value

    def fmt(move):
        return f"{move[0]},{move[1]}:{move[2]},{move[3]}:{move[4]},{move[5]}"

    root_moves = generate_moves(board, 1)
    if not root_moves:
        return "0,0:0,0:0,0"

    if len(root_moves) == 1:
        return fmt(root_moves[0])

    root_children = []
    for m in root_moves:
        nb = apply_move(board, m, 1)
        s = quick_evaluate(nb)
        root_children.append((s, m, nb))

    root_children.sort(key=lambda x: x[0], reverse=True)

    if root_children[0][0] >= 100000:
        return fmt(root_children[0][1])

    n = len(root_children)
    if n <= 12:
        depth = 3
        root_beam = n
        beam = 10
    elif n <= 30:
        depth = 3
        root_beam = min(n, 12)
        beam = 9
    elif n <= 80:
        depth = 2
        root_beam = min(n, 16)
        beam = 12
    else:
        depth = 2
        root_beam = min(n, 12)
        beam = 8

    candidates = root_children[:root_beam]

    best_move = candidates[0][1]
    best_quick = candidates[0][0]
    best_value = -INF
    alpha = -INF
    beta = INF

    for quick_score, move, nb in candidates:
        if time.perf_counter() > deadline:
            break
        value = search(nb, depth - 1, 2, alpha, beta, beam)
        if value > best_value or (value == best_value and quick_score > best_quick):
            best_value = value
            best_quick = quick_score
            best_move = move
        if value > alpha:
            alpha = value
        if value >= 100000:
            break

    return fmt(best_move)
