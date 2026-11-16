
from typing import List, Tuple
import random
import math

N = 19

def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]]) -> Tuple[int, int]:
    random.seed(len(me) * 1009 + len(opponent) * 9173)

    me_set = set(me)
    op_set = set(opponent)
    occupied = me_set | op_set

    def inb(r, c):
        return 1 <= r <= N and 1 <= c <= N

    def neigh(p):
        r, c = p
        if r > 1: yield (r-1, c)
        if r < N: yield (r+1, c)
        if c > 1: yield (r, c-1)
        if c < N: yield (r, c+1)

    def group_and_libs(start, stones, enemy):
        stack = [start]
        seen = {start}
        libs = set()
        while stack:
            p = stack.pop()
            for q in neigh(p):
                if q in stones and q not in seen:
                    seen.add(q)
                    stack.append(q)
                elif q not in enemy and q not in stones:
                    libs.add(q)
        return seen, libs

    def all_groups(stones, enemy):
        unseen = set(stones)
        out = []
        while unseen:
            s = next(iter(unseen))
            g, l = group_and_libs(s, stones, enemy)
            out.append((g, l))
            unseen -= g
        return out

    my_groups = all_groups(me_set, op_set)
    op_groups = all_groups(op_set, me_set)

    def legal(move):
        if move == (0, 0):
            return True
        if move in occupied or not inb(*move):
            return False

        # Immediate liberty means legal.
        for q in neigh(move):
            if q not in occupied:
                return True

        # Capturing adjacent opponent group makes it legal.
        for q in neigh(move):
            if q in op_set:
                g, l = group_and_libs(q, op_set, me_set | {move})
                if len(l) == 0:
                    return True

        # Connecting to friendly group with outside liberties.
        for q in neigh(move):
            if q in me_set:
                g, l = group_and_libs(q, me_set | {move}, op_set)
                if len(l) > 0:
                    return True

        return False

    legal_cache = {}
    def is_legal(m):
        if m not in legal_cache:
            legal_cache[m] = legal(m)
        return legal_cache[m]

    # Tactical priority 1: capture opponent groups in atari.
    capture_moves = []
    for g, libs in op_groups:
        if len(libs) == 1:
            m = next(iter(libs))
            if is_legal(m):
                capture_moves.append((len(g), m))
    if capture_moves:
        capture_moves.sort(reverse=True)
        return capture_moves[0][1]

    # Tactical priority 2: save own groups in atari, preferring capture/connection/space.
    save_moves = []
    for g, libs in my_groups:
        if len(libs) == 1:
            m = next(iter(libs))
            if is_legal(m):
                score = 10 * len(g)
                for q in neigh(m):
                    if q in me_set:
                        score += 5
                    elif q in op_set:
                        og, ol = group_and_libs(q, op_set, me_set | {m})
                        if len(ol) <= 1:
                            score += 40 + len(og)
                    else:
                        score += 2
                save_moves.append((score, m))
    if save_moves:
        save_moves.sort(reverse=True)
        return save_moves[0][1]

    def dist_to_edge(r, c):
        return min(r, c, N+1-r, N+1-c)

    def simulate_liberties(move):
        new_me = me_set | {move}
        libs = set()
        group = {move}
        stack = [move]
        while stack:
            p = stack.pop()
            for q in neigh(p):
                if q in new_me and q not in group:
                    group.add(q)
                    stack.append(q)
                elif q not in op_set and q not in new_me:
                    libs.add(q)
        return len(group), len(libs)

    def nearest_distance(move, stones, maxd=6):
        if not stones:
            return maxd + 1
        r, c = move
        best = maxd + 1
        for a, b in stones:
            d = abs(r-a) + abs(c-b)
            if d < best:
                best = d
                if best <= 1:
                    break
        return best

    # Candidate generation: empty points near stones plus important openings.
    candidates = set()
    if not occupied:
        return (4, 4)

    star_points = [(4,4),(4,10),(4,16),(10,4),(10,10),(10,16),(16,4),(16,10),(16,16),
                   (3,3),(3,16),(16,3),(16,16),(4,3),(3,4),(4,16),(16,4)]
    for p in star_points:
        if p not in occupied:
            candidates.add(p)

    for s in occupied:
        r, c = s
        for dr in range(-3, 4):
            for dc in range(-3, 4):
                if abs(dr) + abs(dc) <= 4:
                    p = (r+dr, c+dc)
                    if inb(*p) and p not in occupied:
                        candidates.add(p)

    # If candidate set accidentally empty, scan all.
    if not candidates:
        for r in range(1, N+1):
            for c in range(1, N+1):
                if (r, c) not in occupied:
                    candidates.add((r, c))

    # Precompute weak opponent liberties for pressure.
    op_lib_pressure = {}
    for g, libs in op_groups:
        if len(libs) <= 4:
            for l in libs:
                op_lib_pressure[l] = op_lib_pressure.get(l, 0) + (18 - 3 * len(libs) + min(len(g), 8))

    my_lib_safety = {}
    for g, libs in my_groups:
        if len(libs) <= 4:
            for l in libs:
                my_lib_safety[l] = my_lib_safety.get(l, 0) + (14 - 2 * len(libs) + min(len(g), 8))

    move_count = len(occupied)

    def score_move(m):
        if not is_legal(m):
            return -10**9
        r, c = m
        score = 0.0

        edge = dist_to_edge(r, c)
        # Favor 3rd/4th lines, avoid first line unless tactical.
        if edge == 1:
            score -= 18 if move_count < 180 else 5
        elif edge == 2:
            score += 2
        elif edge == 3:
            score += 8
        elif edge == 4:
            score += 10
        elif edge == 5:
            score += 5
        else:
            score += 1

        # Opening and whole-board development.
        corners = [(4,4), (4,16), (16,4), (16,16), (3,3), (3,17), (17,3), (17,17),
                   (3,4), (4,3), (3,16), (4,17), (16,3), (17,4), (16,17), (17,16)]
        for cr, cc in corners:
            d = abs(r-cr) + abs(c-cc)
            if d <= 3:
                score += 12 - 3*d

        # Friendly extension: not too close, not too far.
        df = nearest_distance(m, me_set, 8)
        de = nearest_distance(m, op_set, 8)
        if me_set:
            if df == 1:
                score += 4
            elif df == 2:
                score += 10
            elif df == 3:
                score += 9
            elif df == 4:
                score += 6
            elif df > 6:
                score -= 3

        # Contact/fighting when enemy is close.
        if de == 1:
            score += 3
        elif de == 2:
            score += 8
        elif de == 3:
            score += 5

        # Local adjacency shape.
        adj_my = adj_op = adj_empty = 0
        diag_my = diag_op = 0
        for q in neigh(m):
            if q in me_set:
                adj_my += 1
            elif q in op_set:
                adj_op += 1
            else:
                adj_empty += 1
        for dr in (-1, 1):
            for dc in (-1, 1):
                q = (r+dr, c+dc)
                if inb(*q):
                    if q in me_set:
                        diag_my += 1
                    elif q in op_set:
                        diag_op += 1

        score += adj_my * 5 + adj_op * 3 + adj_empty * 1.5
        score += diag_my * 2.5 + diag_op * 1.5

        # Pressure and defense.
        score += op_lib_pressure.get(m, 0) * 2.2
        score += my_lib_safety.get(m, 0) * 1.8

        # Liberties/self-atari evaluation.
        gsize, libs = simulate_liberties(m)
        score += min(libs, 8) * 4 + min(gsize, 6) * 1.5
        if libs <= 1:
            # Legal one-lib moves are usually bad unless capture pressure already values them.
            score -= 35
        elif libs == 2:
            score -= 8

        # Avoid filling own true eyes-ish points.
        if adj_my >= 3 and adj_op == 0 and adj_empty <= 1:
            score -= 25

        # Penalize overcrowding in already friendly-heavy local area.
        local_my = local_op = 0
        for a, b in me_set:
            if abs(r-a) <= 2 and abs(c-b) <= 2:
                local_my += 1
        for a, b in op_set:
            if abs(r-a) <= 2 and abs(c-b) <= 2:
                local_op += 1
        if local_my >= 5 and local_op == 0:
            score -= 12
        score += min(local_op, 5) * 2

        # Tiny deterministic noise for tie-breaking.
        score += random.random() * 0.01
        return score

    best = None
    best_score = -10**18
    for m in candidates:
        s = score_move(m)
        if s > best_score:
            best_score = s
            best = m

    if best is not None and best_score > -10**8:
        return best

    # Guaranteed legal fallback: full-board scan.
    for r in range(1, N+1):
        for c in range(1, N+1):
            m = (r, c)
            if m not in occupied and is_legal(m):
                return m

    return (0, 0)
