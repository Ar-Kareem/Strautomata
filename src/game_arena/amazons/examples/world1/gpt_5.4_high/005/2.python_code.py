
import time
from collections import deque

SIZE = 6
N = SIZE * SIZE
DIRS = [(-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)]

WIN = 1000000
INF = 10**9

# Precomputed geometry
RAYS = []
NEIGH = []
CENTER = []

for idx in range(N):
    r, c = divmod(idx, SIZE)
    rays = []
    nbrs = []
    for dr, dc in DIRS:
        rr, cc = r + dr, c + dc
        if 0 <= rr < SIZE and 0 <= cc < SIZE:
            nbrs.append(rr * SIZE + cc)
        ray = []
        while 0 <= rr < SIZE and 0 <= cc < SIZE:
            ray.append(rr * SIZE + cc)
            rr += dr
            cc += dc
        rays.append(tuple(ray))
    RAYS.append(tuple(rays))
    NEIGH.append(tuple(nbrs))
    CENTER.append(6 - abs(2 * r - 5) - abs(2 * c - 5))

# Small persistent cache across calls
EVAL_CACHE = {}


class Timeout(Exception):
    pass


def idx_to_rc(i):
    return divmod(i, SIZE)


def move_to_str(move):
    fr, to, ar = move
    r1, c1 = idx_to_rc(fr)
    r2, c2 = idx_to_rc(to)
    r3, c3 = idx_to_rc(ar)
    return f"{r1},{c1}:{r2},{c2}:{r3},{c3}"


def apply_swapped(board_flat, move):
    fr, to, ar = move
    nb = board_flat[:]
    nb[fr] = 0
    nb[to] = 1
    nb[ar] = -1
    for i, v in enumerate(nb):
        if v == 1:
            nb[i] = 2
        elif v == 2:
            nb[i] = 1
    return nb


def has_any_move(board_flat):
    # Any destination square implies at least one legal full move,
    # because the amazon can always shoot back to its vacated square.
    for i, v in enumerate(board_flat):
        if v != 1:
            continue
        for ray in RAYS[i]:
            for j in ray:
                if board_flat[j] != 0:
                    break
                return True
    return False


def destination_count(board_flat, piece):
    count = 0
    for i, v in enumerate(board_flat):
        if v != piece:
            continue
        for ray in RAYS[i]:
            for j in ray:
                if board_flat[j] != 0:
                    break
                count += 1
    return count


def generate_moves(board_flat):
    moves = []
    for fr, v in enumerate(board_flat):
        if v != 1:
            continue
        board_flat[fr] = 0
        for ray in RAYS[fr]:
            for to in ray:
                if board_flat[to] != 0:
                    break
                board_flat[to] = 1
                for aray in RAYS[to]:
                    for ar in aray:
                        if board_flat[ar] != 0:
                            break
                        moves.append((fr, to, ar))
                board_flat[to] = 0
        board_flat[fr] = 1
    return moves


def local_liberties(board_flat, piece):
    score = 0
    for i, v in enumerate(board_flat):
        if v == piece:
            for n in NEIGH[i]:
                if board_flat[n] == 0:
                    score += 1
    return score


def queen_distances(board_flat, piece):
    dist = [INF] * N
    q = deque()

    for i, v in enumerate(board_flat):
        if v == piece:
            dist[i] = 0
            q.append(i)

    while q:
        x = q.popleft()
        nd = dist[x] + 1
        for ray in RAYS[x]:
            for y in ray:
                if board_flat[y] != 0:
                    break
                if dist[y] > nd:
                    dist[y] = nd
                    q.append(y)
    return dist


def territory_eval(board_flat):
    d1 = queen_distances(board_flat, 1)
    d2 = queen_distances(board_flat, 2)
    score = 0

    for i, v in enumerate(board_flat):
        if v != 0:
            continue
        a = d1[i]
        b = d2[i]
        if a < b:
            if b >= INF:
                score += 3
            elif b - a >= 2:
                score += 2
            else:
                score += 1
        elif b < a:
            if a >= INF:
                score -= 3
            elif a - b >= 2:
                score -= 2
            else:
                score -= 1
    return score


def static_eval(board_flat, mob1=None):
    key = tuple(board_flat)
    cached = EVAL_CACHE.get(key)
    if cached is not None:
        return cached

    if mob1 is None:
        mob1 = destination_count(board_flat, 1)

    if mob1 == 0:
        val = -WIN // 2
    else:
        mob2 = destination_count(board_flat, 2)
        terr = territory_eval(board_flat)
        libs = local_liberties(board_flat, 1) - local_liberties(board_flat, 2)
        center = 0
        for i, v in enumerate(board_flat):
            if v == 1:
                center += CENTER[i]
            elif v == 2:
                center -= CENTER[i]

        # Territory is primary; mobility/liberties matter a lot on 6x6.
        val = 5 * terr + 3 * (mob1 - mob2) + 2 * libs + center

    if len(EVAL_CACHE) > 60000:
        EVAL_CACHE.clear()
    EVAL_CACHE[key] = val
    return val


def leaf_value(board_flat):
    mob1 = destination_count(board_flat, 1)
    if mob1 == 0:
        return -WIN
    return static_eval(board_flat, mob1)


def cheap_ordered_successors(board_flat, moves):
    opps = [i for i, v in enumerate(board_flat) if v == 2]
    owns = [i for i, v in enumerate(board_flat) if v == 1]
    scored = []

    for mv in moves:
        fr, to, ar = mv
        s = 2 * CENTER[to] - CENTER[ar]

        for o in opps:
            if ar in NEIGH[o]:
                s += 3
            if to in NEIGH[o]:
                s += 1

        for o in owns:
            if o != fr and ar in NEIGH[o]:
                s -= 1

        scored.append((s, mv, None))

    scored.sort(reverse=True, key=lambda x: x[0])
    return scored


def ordered_successors(board_flat, moves, deadline):
    scored = []
    for mv in moves:
        if time.perf_counter() > deadline:
            raise Timeout
        nb = apply_swapped(board_flat, mv)
        s = -leaf_value(nb)
        scored.append((s, mv, nb))
    scored.sort(reverse=True, key=lambda x: x[0])
    return scored


def negamax(board_flat, depth, alpha, beta, deadline):
    if time.perf_counter() > deadline:
        raise Timeout

    if depth == 0:
        return leaf_value(board_flat)

    moves = generate_moves(board_flat)
    if not moves:
        return -WIN

    if len(moves) <= 24:
        succs = ordered_successors(board_flat, moves, deadline)
    else:
        succs = cheap_ordered_successors(board_flat, moves)

    best = -INF
    for _, mv, nb in succs:
        if time.perf_counter() > deadline:
            raise Timeout
        if nb is None:
            nb = apply_swapped(board_flat, mv)
        val = -negamax(nb, depth - 1, -beta, -alpha, deadline)
        if val > best:
            best = val
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break
    return best


def depth2_root_value(board_after_our_move, deadline, cutoff):
    # board_after_our_move is from opponent's perspective
    replies = generate_moves(board_after_our_move)
    if not replies:
        return WIN

    if len(replies) <= 24:
        ordered = ordered_successors(board_after_our_move, replies, deadline)
    else:
        ordered = cheap_ordered_successors(board_after_our_move, replies)

    worst = INF
    for _, mv, nb2 in ordered:
        if time.perf_counter() > deadline:
            raise Timeout
        if nb2 is None:
            nb2 = apply_swapped(board_after_our_move, mv)
        val = leaf_value(nb2)
        if val < worst:
            worst = val
        if worst <= cutoff:
            break
    return worst


def policy(board) -> str:
    try:
        board_flat = board.ravel().tolist()
    except Exception:
        board_flat = [int(x) for row in board for x in row]

    moves = generate_moves(board_flat)
    if not moves:
        # Robust fallback; environment should not call policy here.
        return "0,0:0,0:0,0"
    if len(moves) == 1:
        return move_to_str(moves[0])

    start = time.perf_counter()
    deadline = start + 0.93

    root_infos = []
    best_move = moves[0]
    best_heur = -INF

    # Heuristic pre-scan of all roots
    for mv in moves:
        if time.perf_counter() > deadline:
            break
        nb = apply_swapped(board_flat, mv)
        if not has_any_move(nb):
            return move_to_str(mv)  # immediate win
        s = -leaf_value(nb)
        root_infos.append([s, mv, nb])
        if s > best_heur:
            best_heur = s
            best_move = mv

    if not root_infos:
        return move_to_str(best_move)

    root_infos.sort(reverse=True, key=lambda x: x[0])

    empties = sum(1 for v in board_flat if v == 0)

    # Late-game / tactical exact search
    if empties <= 10 or len(root_infos) <= 16:
        ordered = root_infos[:]
        best_move = ordered[0][1]
        max_depth = 8 if (empties <= 8 or len(root_infos) <= 10) else 6
        depth = 2

        while depth <= max_depth and time.perf_counter() < deadline - 0.03:
            try:
                cur_best = -INF
                cur_move = best_move
                new_order = []
                alpha = -INF

                for _, mv, nb in ordered:
                    if time.perf_counter() > deadline:
                        raise Timeout
                    val = -negamax(nb, depth - 1, -INF, -alpha, deadline)
                    new_order.append((val, mv, nb))
                    if val > cur_best:
                        cur_best = val
                        cur_move = mv
                    if val > alpha:
                        alpha = val

                new_order.sort(reverse=True, key=lambda x: x[0])
                ordered = new_order
                best_move = cur_move
                depth += 1
            except Timeout:
                break

        return move_to_str(best_move)

    # Midgame: exact depth-2 minimax on strongest candidate roots
    if len(root_infos) <= 48:
        candidates = root_infos
    elif empties <= 16:
        candidates = root_infos[:36]
    elif len(root_infos) <= 100:
        candidates = root_infos[:30]
    else:
        candidates = root_infos[:24]

    best_score = -INF
    best_move = candidates[0][1]

    for _, mv, nb in candidates:
        try:
            val = depth2_root_value(nb, deadline, best_score)
        except Timeout:
            break
        if val > best_score:
            best_score = val
            best_move = mv

    return move_to_str(best_move)
