
import time
from collections import deque
import numpy as np


DIRS = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
]

N = 6
WIN = 1_000_000.0


def policy(board) -> str:
    board = np.asarray(board, dtype=np.int8)

    move_cache = {}
    eval_cache = {}

    class Timeout(Exception):
        pass

    start = time.perf_counter()
    deadline = start + 0.92
    node_counter = 0

    def time_check():
        nonlocal node_counter
        node_counter += 1
        if (node_counter & 127) == 0 and time.perf_counter() > deadline:
            raise Timeout

    def fmt(mv):
        fr, fc, tr, tc, ar, ac = mv
        return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"

    def iter_reachable(b, r, c, free=None):
        fr = fc = -1
        if free is not None:
            fr, fc = free
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            while 0 <= nr < N and 0 <= nc < N:
                if nr == fr and nc == fc:
                    cell = 0
                else:
                    cell = b[nr, nc]
                if cell != 0:
                    break
                yield nr, nc
                nr += dr
                nc += dc

    def generate_moves(b):
        key = b.tobytes()
        cached = move_cache.get(key)
        if cached is not None:
            return cached

        moves = []
        my_positions = np.argwhere(b == 1)
        for fr, fc in my_positions:
            for tr, tc in iter_reachable(b, fr, fc):
                for ar, ac in iter_reachable(b, tr, tc, free=(fr, fc)):
                    moves.append((int(fr), int(fc), int(tr), int(tc), int(ar), int(ac)))

        move_cache[key] = moves
        return moves

    def mobility_squares(b, who):
        total = 0
        for r, c in np.argwhere(b == who):
            for _ in iter_reachable(b, int(r), int(c)):
                total += 1
        return total

    def local_liberties(b, who):
        total = 0
        for r, c in np.argwhere(b == who):
            r = int(r)
            c = int(c)
            for dr, dc in DIRS:
                nr, nc = r + dr, c + dc
                if 0 <= nr < N and 0 <= nc < N and b[nr, nc] == 0:
                    total += 1
        return total

    def queen_distance_map(b, who):
        inf = 99
        dist = np.full((N, N), inf, dtype=np.int16)
        q = deque()

        for r, c in np.argwhere(b == who):
            r = int(r)
            c = int(c)
            for nr, nc in iter_reachable(b, r, c):
                if dist[nr, nc] == inf:
                    dist[nr, nc] = 1
                    q.append((nr, nc))

        while q:
            r, c = q.popleft()
            nd = dist[r, c] + 1
            for nr, nc in iter_reachable(b, r, c):
                if dist[nr, nc] == inf:
                    dist[nr, nc] = nd
                    q.append((nr, nc))
        return dist

    def territory_score(b):
        d1 = queen_distance_map(b, 1)
        d2 = queen_distance_map(b, 2)
        score = 0.0
        inf = 99
        for r in range(N):
            for c in range(N):
                if b[r, c] != 0:
                    continue
                a = d1[r, c]
                o = d2[r, c]
                if a < o:
                    score += 1.0
                elif o < a:
                    score -= 1.0
                elif a < inf:
                    score += 0.15
        return score

    def center_score(b, who):
        s = 0.0
        for r, c in np.argwhere(b == who):
            dr = float(r) - 2.5
            dc = float(c) - 2.5
            s += -(dr * dr + dc * dc)
        return s

    def evaluate(b):
        key = b.tobytes()
        cached = eval_cache.get(key)
        if cached is not None:
            return cached

        mob1 = mobility_squares(b, 1)
        mob2 = mobility_squares(b, 2)

        if mob1 == 0:
            val = -WIN / 2
            eval_cache[key] = val
            return val
        if mob2 == 0:
            val = WIN / 2
            eval_cache[key] = val
            return val

        libs1 = local_liberties(b, 1)
        libs2 = local_liberties(b, 2)
        terr = territory_score(b)
        cent = center_score(b, 1) - center_score(b, 2)
        empties = int(np.count_nonzero(b == 0))

        if empties > 18:
            val = (
                2.4 * (mob1 - mob2)
                + 3.6 * terr
                + 0.5 * (libs1 - libs2)
                + 0.18 * cent
            )
        else:
            val = (
                1.8 * (mob1 - mob2)
                + 5.2 * terr
                + 0.7 * (libs1 - libs2)
                + 0.08 * cent
            )

        eval_cache[key] = val
        return val

    def apply_move_and_swap(b, mv):
        fr, fc, tr, tc, ar, ac = mv
        nb = b.copy()
        nb[fr, fc] = 0
        nb[tr, tc] = 1
        nb[ar, ac] = -1

        mask1 = (nb == 1)
        mask2 = (nb == 2)
        nb[mask1] = 2
        nb[mask2] = 1
        return nb

    def quick_move_score(b, mv, own_pos, opp_pos):
        fr, fc, tr, tc, ar, ac = mv

        landing = 0
        for _ in iter_reachable(b, tr, tc, free=(fr, fc)):
            landing += 1

        center = 5.0 - ((tr - 2.5) ** 2 + (tc - 2.5) ** 2)

        pressure = 0.0
        for orow, ocol in opp_pos:
            d_arrow = max(abs(ar - orow), abs(ac - ocol))
            if d_arrow < 3:
                pressure += (3 - d_arrow)

            d_to = max(abs(tr - orow), abs(tc - ocol))
            if d_to < 3:
                pressure += 0.5 * (3 - d_to)

        self_penalty = 0.0
        for myr, myc in own_pos:
            if myr == fr and myc == fc:
                continue
            d_self = max(abs(ar - myr), abs(ac - myc))
            if d_self <= 1:
                self_penalty += 1.0

        return 2.0 * landing + 0.8 * center + 0.9 * pressure - self_penalty

    def order_moves(b, moves, depth_remaining):
        if len(moves) <= 1:
            return moves

        own_pos = [tuple(map(int, x)) for x in np.argwhere(b == 1)]
        opp_pos = [tuple(map(int, x)) for x in np.argwhere(b == 2)]

        scored = []
        for mv in moves:
            scored.append((quick_move_score(b, mv, own_pos, opp_pos), mv))
        scored.sort(key=lambda x: x[0], reverse=True)

        ordered = [mv for _, mv in scored]

        if depth_remaining >= 3 and len(ordered) > 20:
            return ordered[:20]
        if depth_remaining >= 2 and len(ordered) > 28:
            return ordered[:28]
        return ordered

    def negamax(b, depth, alpha, beta):
        time_check()

        if depth == 0:
            return evaluate(b)

        moves = generate_moves(b)
        if not moves:
            return -WIN + depth

        moves = order_moves(b, moves, depth)

        best = -WIN
        for mv in moves:
            child = apply_move_and_swap(b, mv)
            score = -negamax(child, depth - 1, -beta, -alpha)
            if score > best:
                best = score
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
        return best

    try:
        legal_moves = generate_moves(board)
        if not legal_moves:
            return "0,0:0,0:0,0"

        fallback = legal_moves[0]

        own_pos = [tuple(map(int, x)) for x in np.argwhere(board == 1)]
        opp_pos = [tuple(map(int, x)) for x in np.argwhere(board == 2)]
        root_order = sorted(
            legal_moves,
            key=lambda mv: quick_move_score(board, mv, own_pos, opp_pos),
            reverse=True,
        )

        best_move = root_order[0]
        prev_scores = {}

        empties = int(np.count_nonzero(board == 0))
        depths = [1, 2]
        if len(root_order) <= 36 or empties <= 16:
            depths.append(3)
        if len(root_order) <= 10 and empties <= 8:
            depths.append(4)

        for depth in depths:
            if time.perf_counter() > deadline:
                break

            if prev_scores:
                root_order = sorted(
                    root_order,
                    key=lambda mv: prev_scores.get(mv, -1e18),
                    reverse=True,
                )

            iter_best_move = best_move
            iter_best_score = -WIN
            iter_scores = {}
            alpha = -WIN
            beta = WIN

            for mv in root_order:
                if time.perf_counter() > deadline:
                    raise Timeout

                child = apply_move_and_swap(board, mv)
                score = -negamax(child, depth - 1, -beta, -alpha)
                iter_scores[mv] = score

                if score > iter_best_score:
                    iter_best_score = score
                    iter_best_move = mv

                if score > alpha:
                    alpha = score

            best_move = iter_best_move
            prev_scores = iter_scores

        return fmt(best_move)

    except Exception:
        # Safety fallback: always prefer a legal move over risking disqualification.
        try:
            legal_moves = generate_moves(board)
            if legal_moves:
                return fmt(legal_moves[0])
        except Exception:
            pass
        return "0,0:0,0:0,0"
