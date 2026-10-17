
import numpy as np
from collections import deque
from time import perf_counter

SIZE = 6
N = SIZE * SIZE
DIRS = [(-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)]

# Precompute rays for queen-like movement.
RAYS = [[None] * 8 for _ in range(N)]
for idx in range(N):
    r, c = divmod(idx, SIZE)
    for d, (dr, dc) in enumerate(DIRS):
        rr, cc = r + dr, c + dc
        ray = []
        while 0 <= rr < SIZE and 0 <= cc < SIZE:
            ray.append(rr * SIZE + cc)
            rr += dr
            cc += dc
        RAYS[idx][d] = ray

# Mild centrality preference for move ordering.
CENTER = []
for idx in range(N):
    r, c = divmod(idx, SIZE)
    CENTER.append(-((r - 2.5) ** 2 + (c - 2.5) ** 2))

# Chebyshev distances for quick "arrow near enemy" bonuses.
CHEB = [[0] * N for _ in range(N)]
for i in range(N):
    r1, c1 = divmod(i, SIZE)
    for j in range(N):
        r2, c2 = divmod(j, SIZE)
        CHEB[i][j] = max(abs(r1 - r2), abs(c1 - c2))


class _Timeout(Exception):
    pass


def _format_move(move):
    if move is None:
        return "0,0:0,0:0,0"
    f, t, a = move
    fr, fc = divmod(f, SIZE)
    tr, tc = divmod(t, SIZE)
    ar, ac = divmod(a, SIZE)
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"


def _first_legal_move(flat_board):
    b = list(flat_board)
    for f, v in enumerate(b):
        if v != 1:
            continue
        b[f] = 0
        for ray in RAYS[f]:
            for t in ray:
                if b[t] != 0:
                    break
                b[t] = 1
                for aray in RAYS[t]:
                    for a in aray:
                        if b[a] != 0:
                            break
                        b[t] = 0
                        b[f] = 1
                        return (f, t, a)
                b[t] = 0
        b[f] = 1
    return None


def policy(board) -> str:
    flat = np.asarray(board, dtype=int).reshape(-1).tolist()
    fallback = _first_legal_move(flat)
    if fallback is None:
        # Environment should not call policy with no legal move, but stay robust.
        return "0,0:0,0:0,0"

    try:
        deadline = perf_counter() + 0.90
        eval_cache = {}
        tt_move = {}
        node_counter = 0

        WIN = 10_000_000
        INF = 1_000_000_000

        def check_time():
            nonlocal node_counter
            node_counter += 1
            if (node_counter & 127) == 0 and perf_counter() > deadline:
                raise _Timeout

        def queen_mobility_from(b, pos):
            cnt = 0
            for ray in RAYS[pos]:
                for x in ray:
                    if b[x] != 0:
                        break
                    cnt += 1
            return cnt

        def queen_distances(b, sources):
            dist = [99] * N
            dq = deque()
            for s in sources:
                dist[s] = 0
                dq.append(s)
            while dq:
                x = dq.popleft()
                nd = dist[x] + 1
                for ray in RAYS[x]:
                    for y in ray:
                        if b[y] != 0:
                            break
                        if dist[y] > nd:
                            dist[y] = nd
                            dq.append(y)
            return dist

        def evaluate(b, empties):
            key = tuple(b)
            if key in eval_cache:
                return eval_cache[key]

            our_pos = []
            opp_pos = []
            for i, v in enumerate(b):
                if v == 1:
                    our_pos.append(i)
                elif v == 2:
                    opp_pos.append(i)

            our_mob = 0
            opp_mob = 0
            our_min = 999
            opp_min = 999

            for p in our_pos:
                m = queen_mobility_from(b, p)
                our_mob += m
                if m < our_min:
                    our_min = m

            for p in opp_pos:
                m = queen_mobility_from(b, p)
                opp_mob += m
                if m < opp_min:
                    opp_min = m

            if our_min == 999:
                our_min = 0
            if opp_min == 999:
                opp_min = 0

            d1 = queen_distances(b, our_pos)
            d2 = queen_distances(b, opp_pos)

            territory = 0
            our_reach = 0
            opp_reach = 0
            contested = 0

            for i, v in enumerate(b):
                if v != 0:
                    continue
                a = d1[i]
                c = d2[i]
                if a < 99:
                    our_reach += 1
                if c < 99:
                    opp_reach += 1
                if a < c:
                    territory += 1
                elif c < a:
                    territory -= 1
                elif a < 99 and c < 99:
                    contested += 1

            if contested == 0:
                score = (
                    120 * territory
                    + 4 * (our_mob - opp_mob)
                    + 3 * (our_min - opp_min)
                )
            elif empties > 18:
                score = (
                    8 * territory
                    + 3 * (our_mob - opp_mob)
                    + (our_reach - opp_reach)
                    + 2 * (our_min - opp_min)
                )
            elif empties > 10:
                score = (
                    10 * territory
                    + 2 * (our_mob - opp_mob)
                    + (our_reach - opp_reach)
                    + 3 * (our_min - opp_min)
                )
            else:
                score = (
                    14 * territory
                    + 2 * (our_mob - opp_mob)
                    + (our_reach - opp_reach)
                    + 4 * (our_min - opp_min)
                )

            eval_cache[key] = score
            return score

        def generate_moves_scored(b, player, preferred=None, timed=True):
            opp = 2 if player == 1 else 1
            opp_positions = [i for i, v in enumerate(b) if v == opp]

            moves = []
            append = moves.append
            made = 0

            for f, v in enumerate(b):
                if v != player:
                    continue
                if timed and perf_counter() > deadline:
                    raise _Timeout

                b[f] = 0
                for ray in RAYS[f]:
                    for t in ray:
                        if b[t] != 0:
                            break

                        b[t] = player

                        local_mob = 0
                        for ray2 in RAYS[t]:
                            for x in ray2:
                                if b[x] != 0:
                                    break
                                local_mob += 1

                        base = 4.0 * local_mob + 1.5 * CENTER[t]

                        for aray in RAYS[t]:
                            for a in aray:
                                if b[a] != 0:
                                    break

                                bonus = 0.0
                                if opp_positions:
                                    dmin = 10
                                    for o in opp_positions:
                                        d = CHEB[a][o]
                                        if d < dmin:
                                            dmin = d
                                            if dmin <= 1:
                                                break
                                    if dmin <= 1:
                                        bonus = 3.0
                                    elif dmin == 2:
                                        bonus = 1.0

                                s = base + CENTER[a] + bonus
                                if preferred is not None and (f, t, a) == preferred:
                                    s += 1e9

                                append((s, (f, t, a)))
                                made += 1
                                if timed and (made & 127) == 0 and perf_counter() > deadline:
                                    raise _Timeout

                        b[t] = 0
                b[f] = player

            moves.sort(key=lambda x: x[0], reverse=True)
            return [m for _, m in moves]

        def branch_cap(num_moves, depth, empties):
            if num_moves <= 12:
                return num_moves
            if depth <= 1:
                return num_moves

            if empties > 18:
                table = {2: 18, 3: 12, 4: 8, 5: 6, 6: 5}
            elif empties > 10:
                table = {2: 22, 3: 14, 4: 10, 5: 8, 6: 6}
            else:
                table = {2: 28, 3: 18, 4: 12, 5: 10, 6: 8}

            return min(num_moves, table.get(depth, 8))

        def root_cap(num_moves, depth, empties):
            if num_moves <= 24:
                return num_moves
            if depth <= 1:
                return num_moves

            if empties > 18:
                table = {2: 32, 3: 20, 4: 14, 5: 10, 6: 8}
            elif empties > 10:
                table = {2: 40, 3: 24, 4: 16, 5: 12, 6: 10}
            else:
                table = {2: 64, 3: 36, 4: 22, 5: 14, 6: 10}

            return min(num_moves, table.get(depth, 10))

        def negamax(b, turn, depth, alpha, beta, ply, empties):
            check_time()

            if depth == 0:
                val = evaluate(b, empties)
                return val if turn == 1 else -val

            key = (turn, tuple(b))
            preferred = tt_move.get(key)

            moves = generate_moves_scored(b, turn, preferred=preferred, timed=True)
            if not moves:
                return -WIN + ply

            cap = branch_cap(len(moves), depth, empties)
            if cap < len(moves):
                moves = moves[:cap]

            best_val = -INF
            best_move = moves[0]
            nxt = 2 if turn == 1 else 1

            for f, t, a in moves:
                b[f] = 0
                b[t] = turn
                b[a] = -1

                val = -negamax(b, nxt, depth - 1, -beta, -alpha, ply + 1, empties - 1)

                b[a] = 0
                b[t] = 0
                b[f] = turn

                if val > best_val:
                    best_val = val
                    best_move = (f, t, a)

                if val > alpha:
                    alpha = val
                if alpha >= beta:
                    break

            tt_move[key] = best_move
            return best_val

        def search_root(b, ordered_root, depth, empties):
            alpha = -INF
            beta = INF

            cap = root_cap(len(ordered_root), depth, empties)
            candidates = ordered_root if cap >= len(ordered_root) else ordered_root[:cap]

            best_score = -INF
            best_move = candidates[0]
            scored = []

            for f, t, a in candidates:
                check_time()

                b[f] = 0
                b[t] = 1
                b[a] = -1

                val = -negamax(b, 2, depth - 1, -beta, -alpha, 1, empties - 1)

                b[a] = 0
                b[t] = 0
                b[f] = 1

                scored.append((val, (f, t, a)))
                if val > best_score:
                    best_score = val
                    best_move = (f, t, a)
                if val > alpha:
                    alpha = val

            scored.sort(key=lambda x: x[0], reverse=True)

            if cap >= len(ordered_root):
                new_order = [m for _, m in scored]
            else:
                seen = {m for _, m in scored}
                new_order = [m for _, m in scored] + [m for m in ordered_root if m not in seen]

            return best_score, best_move, new_order

        root_moves = generate_moves_scored(flat, 1, preferred=None, timed=False)
        if not root_moves:
            return _format_move(fallback)

        best_move = root_moves[0]
        if len(root_moves) == 1:
            return _format_move(best_move)

        empties0 = flat.count(0)
        nroot = len(root_moves)

        if nroot > 140:
            max_depth = 2
        elif nroot > 80:
            max_depth = 3
        elif nroot > 40:
            max_depth = 4
        else:
            max_depth = 5
        if empties0 <= 10 and nroot <= 20:
            max_depth = 6

        ordered_root = root_moves

        for depth in range(1, max_depth + 1):
            if depth > 1 and perf_counter() > deadline - 0.05:
                break
            try:
                score, move, ordered_root = search_root(flat, ordered_root, depth, empties0)
                best_move = move
                if abs(score) >= WIN - 1000:
                    break
            except _Timeout:
                break

        return _format_move(best_move)

    except Exception:
        return _format_move(fallback)
