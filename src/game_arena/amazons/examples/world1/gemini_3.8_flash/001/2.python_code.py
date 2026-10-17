
import time
import numpy as np

# 8 directional offsets (dr, dc)
DIRECTIONS = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1)
]

# Precompute ray paths for every cell on a 6x6 board
RAYS = []
for r in range(6):
    for c in range(6):
        cell_rays = []
        for dr, dc in DIRECTIONS:
            ray = []
            nr, nc = r + dr, c + dc
            while 0 <= nr < 6 and 0 <= nc < 6:
                ray.append(nr * 6 + nc)
                nr += dr
                nc += dc
            if ray:
                cell_rays.append(tuple(ray))
        RAYS.append(tuple(cell_rays))
RAYS = tuple(RAYS)

# Precomputed coordinate strings "r,c"
COORD_STR = [f"{r},{c}" for r in range(6) for c in range(6)]


def queen_bfs(amazons, board_flat):
    """Computes the shortest queen-distance from given amazons to all empty cells."""
    dist = [99] * 36
    queue = []
    for sq in amazons:
        dist[sq] = 0
        queue.append(sq)

    head = 0
    while head < len(queue):
        curr = queue[head]
        head += 1
        d = dist[curr] + 1
        for ray in RAYS[curr]:
            for nxt in ray:
                if board_flat[nxt] != 0:
                    break
                if dist[nxt] > d:
                    dist[nxt] = d
                    queue.append(nxt)
    return dist


def evaluate(board_flat, p1_amazons, p2_amazons):
    """Evaluates the board state from the perspective of Player 1."""
    # Player 2 mobility
    p2_mob = 0
    min_p2_mob = 99
    for sq in p2_amazons:
        m = 0
        for ray in RAYS[sq]:
            for nxt in ray:
                if board_flat[nxt] != 0:
                    break
                m += 1
        p2_mob += m
        if m < min_p2_mob:
            min_p2_mob = m

    if p2_mob == 0:
        return 100000.0  # Terminal win for Player 1

    # Player 1 mobility
    p1_mob = 0
    min_p1_mob = 99
    for sq in p1_amazons:
        m = 0
        for ray in RAYS[sq]:
            for nxt in ray:
                if board_flat[nxt] != 0:
                    break
                m += 1
        p1_mob += m
        if m < min_p1_mob:
            min_p1_mob = m

    if p1_mob == 0:
        return -100000.0  # Terminal loss for Player 1

    # Queen-distance territory BFS
    dist1 = queen_bfs(p1_amazons, board_flat)
    dist2 = queen_bfs(p2_amazons, board_flat)

    terr = 0.0
    for sq in range(36):
        if board_flat[sq] == 0:
            d1 = dist1[sq]
            d2 = dist2[sq]
            if d1 < d2:
                diff = min(d2 - d1, 4)
                terr += 1.0 + 0.1 * diff
            elif d2 < d1:
                diff = min(d1 - d2, 4)
                terr -= 1.0 + 0.1 * diff

    trap_bonus = (4 - min_p2_mob) * 1.5 if min_p2_mob < 4 else 0.0
    trap_penalty = (4 - min_p1_mob) * 1.5 if min_p1_mob < 4 else 0.0

    return terr * 3.0 + (p1_mob - 1.5 * p2_mob) + trap_bonus - trap_penalty


def policy(board) -> str:
    start_time = time.time()
    board_flat = np.array(board, dtype=int).ravel()

    p1_amazons = tuple(i for i in range(36) if board_flat[i] == 1)
    p2_amazons = tuple(i for i in range(36) if board_flat[i] == 2)

    if not p1_amazons:
        return ""

    # Generate all legal moves for Player 1
    moves = []
    for f in p1_amazons:
        for ray in RAYS[f]:
            for t in ray:
                if board_flat[t] != 0:
                    break
                for ray_ar in RAYS[t]:
                    for a in ray_ar:
                        if a == f:
                            moves.append((f, t, a))
                        elif board_flat[a] != 0:
                            break
                        else:
                            moves.append((f, t, a))

    if not moves:
        return ""

    # Depth 1 evaluation & move ordering
    candidates = []
    for f, t, a in moves:
        board_flat[f] = 0
        board_flat[t] = 1
        board_flat[a] = -1
        new_p1 = tuple(t if sq == f else sq for sq in p1_amazons)

        score = evaluate(board_flat, new_p1, p2_amazons)

        board_flat[a] = 0
        board_flat[t] = 0
        board_flat[f] = 1

        if score >= 90000.0:
            # Immediate win found
            return f"{COORD_STR[f]}:{COORD_STR[t]}:{COORD_STR[a]}"

        candidates.append(((f, t, a), score))

    candidates.sort(key=lambda x: x[1], reverse=True)
    best_move = candidates[0][0]

    # Depth 2 Minimax search with Alpha-Beta pruning on top candidates
    alpha = -1e9
    max_depth2_candidates = min(len(candidates), 35)

    for idx in range(max_depth2_candidates):
        if time.time() - start_time > 0.82:
            break

        (f, t, a), d1_score = candidates[idx]

        board_flat[f] = 0
        board_flat[t] = 1
        board_flat[a] = -1
        new_p1 = tuple(t if sq == f else sq for sq in p1_amazons)

        opp_min = 1e9
        has_opp_move = False
        cutoff = False

        for opp_f in p2_amazons:
            if cutoff:
                break
            for opp_ray in RAYS[opp_f]:
                if cutoff:
                    break
                for opp_t in opp_ray:
                    if cutoff:
                        break
                    if board_flat[opp_t] != 0:
                        break
                    for opp_ray_ar in RAYS[opp_t]:
                        if cutoff:
                            break
                        for opp_a in opp_ray_ar:
                            if opp_a == opp_f:
                                pass
                            elif board_flat[opp_a] != 0:
                                break

                            has_opp_move = True
                            board_flat[opp_f] = 0
                            board_flat[opp_t] = 2
                            board_flat[opp_a] = -1
                            new_p2 = tuple(opp_t if sq == opp_f else sq for sq in p2_amazons)

                            val = evaluate(board_flat, new_p1, new_p2)

                            board_flat[opp_a] = 0
                            board_flat[opp_t] = 0
                            board_flat[opp_f] = 2

                            if val < opp_min:
                                opp_min = val
                            if opp_min <= alpha:
                                cutoff = True
                                break

        board_flat[a] = 0
        board_flat[t] = 0
        board_flat[f] = 1

        if not has_opp_move:
            return f"{COORD_STR[f]}:{COORD_STR[t]}:{COORD_STR[a]}"

        if opp_min > alpha:
            alpha = opp_min
            best_move = (f, t, a)

    return f"{COORD_STR[best_move[0]]}:{COORD_STR[best_move[1]]}:{COORD_STR[best_move[2]]}"
