
import time
import numpy as np

# Precompute 8 queen directions for 6x6 board
DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]

RAYS = [[] for _ in range(36)]
for r in range(6):
    for c in range(6):
        sq = r * 6 + c
        rays_for_sq = []
        for dr, dc in DIRS:
            ray = []
            nr, nc = r + dr, c + dc
            while 0 <= nr < 6 and 0 <= nc < 6:
                ray.append(nr * 6 + nc)
                nr += dr
                nc += dc
            if ray:
                rays_for_sq.append(tuple(ray))
        RAYS[sq] = tuple(rays_for_sq)
RAYS = tuple(RAYS)


def generate_moves(amazons, occ):
    """Generate all legal (from_sq, to_sq, arrow_sq) moves for given amazons."""
    moves = []
    for f_sq in amazons:
        for ray in RAYS[f_sq]:
            for t_sq in ray:
                if (occ >> t_sq) & 1:
                    break
                # Vacate from_sq and occupy to_sq
                occ_after_move = (occ ^ (1 << f_sq)) | (1 << t_sq)
                for a_ray in RAYS[t_sq]:
                    for a_sq in a_ray:
                        if (occ_after_move >> a_sq) & 1:
                            break
                        moves.append((f_sq, t_sq, a_sq))
    return moves


def queen_bfs(amazons, occ):
    """Compute minimum queen moves from any amazon in `amazons` to all board squares."""
    dist = [-1] * 36
    queue = list(amazons)
    for a in amazons:
        dist[a] = 0
    d = 0
    while queue:
        next_queue = []
        d += 1
        for s in queue:
            for ray in RAYS[s]:
                for target in ray:
                    if (occ >> target) & 1:
                        break
                    if dist[target] == -1:
                        dist[target] = d
                        next_queue.append(target)
        queue = next_queue
    return dist


def evaluate(p1_amazons, p2_amazons, occ):
    """Heuristic evaluation from player 1's perspective."""
    # Player 1 mobility
    m1 = 0
    for a in p1_amazons:
        for ray in RAYS[a]:
            for t in ray:
                if (occ >> t) & 1:
                    break
                m1 += 1

    # Player 2 mobility
    m2 = 0
    for a in p2_amazons:
        for ray in RAYS[a]:
            for t in ray:
                if (occ >> t) & 1:
                    break
                m2 += 1

    if m2 == 0:
        return 1000000.0
    if m1 == 0:
        return -1000000.0

    d1 = queen_bfs(p1_amazons, occ)
    d2 = queen_bfs(p2_amazons, occ)

    territory = 0.0
    for sq in range(36):
        if not ((occ >> sq) & 1):
            dist1 = d1[sq]
            dist2 = d2[sq]
            if dist1 != -1 and dist2 == -1:
                territory += 2.0
            elif dist1 == -1 and dist2 != -1:
                territory -= 2.0
            elif dist1 != -1 and dist2 != -1:
                if dist1 < dist2:
                    territory += 1.0 + 0.1 * (dist2 - dist1)
                elif dist2 < dist1:
                    territory -= (1.0 + 0.1 * (dist1 - dist2))

    return (m1 - 2.0 * m2) + 1.5 * territory


def policy(board) -> str:
    start_time = time.time()

    p1_amazons = []
    p2_amazons = []
    occ = 0

    for r in range(6):
        for c in range(6):
            val = int(board[r, c])
            sq = r * 6 + c
            if val == 1:
                p1_amazons.append(sq)
                occ |= (1 << sq)
            elif val == 2:
                p2_amazons.append(sq)
                occ |= (1 << sq)
            elif val == -1:
                occ |= (1 << sq)

    p1_amazons = tuple(p1_amazons)
    p2_amazons = tuple(p2_amazons)

    moves = generate_moves(p1_amazons, occ)
    if not moves:
        return "0,0:0,0:0,0"
    if len(moves) == 1:
        f_sq, t_sq, a_sq = moves[0]
        return f"{f_sq // 6},{f_sq % 6}:{t_sq // 6},{t_sq % 6}:{a_sq // 6},{a_sq % 6}"

    # 1-ply evaluation and check for immediate wins
    scored_moves = []
    for f_sq, t_sq, a_sq in moves:
        new_occ = (occ ^ (1 << f_sq)) | (1 << t_sq) | (1 << a_sq)
        new_p1 = tuple(t_sq if a == f_sq else a for a in p1_amazons)

        # Quick check if opponent has any legal move
        has_p2_move = False
        for p2_a in p2_amazons:
            for ray in RAYS[p2_a]:
                for target in ray:
                    if not ((new_occ >> target) & 1):
                        has_p2_move = True
                        break
                if has_p2_move:
                    break
            if has_p2_move:
                break

        if not has_p2_move:
            # Immediate winning move found
            return f"{f_sq // 6},{f_sq % 6}:{t_sq // 6},{t_sq % 6}:{a_sq // 6},{a_sq % 6}"

        score = evaluate(new_p1, p2_amazons, new_occ)
        scored_moves.append((score, (f_sq, t_sq, a_sq), new_p1, new_occ))

    # Sort descending by 1-ply score
    scored_moves.sort(key=lambda x: x[0], reverse=True)

    best_move = scored_moves[0][1]
    best_score = -float('inf')

    # 2-ply Minimax search on top candidates
    candidate_pool = scored_moves[:20]

    for p1_score, move, new_p1, new_occ in candidate_pool:
        if time.time() - start_time > 0.82:
            break

        p2_replies = generate_moves(p2_amazons, new_occ)
        if not p2_replies:
            best_move = move
            break

        worst_score_for_p1 = float('inf')
        for p2_f, p2_t, p2_a in p2_replies:
            occ2 = (new_occ ^ (1 << p2_f)) | (1 << p2_t) | (1 << p2_a)
            new_p2 = tuple(p2_t if a == p2_f else a for a in p2_amazons)

            score = evaluate(new_p1, new_p2, occ2)
            if score < worst_score_for_p1:
                worst_score_for_p1 = score
                if worst_score_for_p1 <= best_score:
                    # Alpha-Beta cutoff: opponent refutes this candidate
                    break

        if worst_score_for_p1 > best_score:
            best_score = worst_score_for_p1
            best_move = move

    f_sq, t_sq, a_sq = best_move
    return f"{f_sq // 6},{f_sq % 6}:{t_sq // 6},{t_sq % 6}:{a_sq // 6},{a_sq % 6}"
