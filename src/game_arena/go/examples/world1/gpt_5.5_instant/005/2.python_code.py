
from collections import deque
import math
import random

N = 19

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
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

    def group(start, stones):
        q = [start]
        seen = {start}
        libs = set()
        for p in q:
            for nb in neigh(p):
                if nb in stones and nb not in seen:
                    seen.add(nb)
                    q.append(nb)
                elif nb not in occupied:
                    libs.add(nb)
        return seen, libs

    # Build groups.
    my_groups = []
    seen = set()
    for s in me_set:
        if s not in seen:
            g, libs = group(s, me_set)
            seen |= g
            my_groups.append((g, libs))

    op_groups = []
    seen = set()
    for s in op_set:
        if s not in seen:
            g, libs = group(s, op_set)
            seen |= g
            op_groups.append((g, libs))

    def legal(move):
        if move == (0, 0):
            return True
        if move in occupied or not inb(*move):
            return False

        # Legal if adjacent to an empty liberty.
        for nb in neigh(move):
            if nb not in occupied:
                return True

        # Legal if connects to friendly group with >1 liberties.
        for g, libs in my_groups:
            if any(nb in g for nb in neigh(move)):
                if len(libs - {move}) > 0:
                    return True

        # Legal if captures adjacent enemy group with exactly one liberty.
        for g, libs in op_groups:
            if move in libs and len(libs) == 1:
                return True

        return False

    legal_moves_cache = None
    def legal_moves():
        nonlocal legal_moves_cache
        if legal_moves_cache is None:
            legal_moves_cache = [(r, c) for r in range(1, N+1) for c in range(1, N+1) if legal((r, c))]
        return legal_moves_cache

    # 1. Capture opponent groups in atari, preferring larger captures.
    captures = []
    for g, libs in op_groups:
        if len(libs) == 1:
            m = next(iter(libs))
            if legal(m):
                captures.append((len(g), m))
    if captures:
        captures.sort(reverse=True)
        return captures[0][1]

    # 2. Save own groups in atari, preferring larger groups.
    saves = []
    for g, libs in my_groups:
        if len(libs) == 1:
            m = next(iter(libs))
            if legal(m):
                saves.append((len(g), m))
    if saves:
        saves.sort(reverse=True)
        return saves[0][1]

    # Helpers for heuristic scoring.
    op_lib_count = {}
    my_lib_count = {}
    for g, libs in op_groups:
        for s in g:
            op_lib_count[s] = len(libs)
    for g, libs in my_groups:
        for s in g:
            my_lib_count[s] = len(libs)

    def is_true_eyeish(m):
        # Avoid playing inside our own simple eye unless tactically needed.
        r, c = m
        ns = list(neigh(m))
        if not ns:
            return False
        if all(nb in me_set for nb in ns):
            diag_enemy = 0
            diag_off = 0
            for dr, dc in ((-1,-1), (-1,1), (1,-1), (1,1)):
                d = (r+dr, c+dc)
                if not inb(*d):
                    diag_off += 1
                elif d in op_set:
                    diag_enemy += 1
            return diag_enemy + diag_off <= 1
        return False

    def point_empty_neighbors(m):
        return sum(1 for nb in neigh(m) if nb not in occupied)

    def distance_to_nearest(stones, m):
        if not stones:
            return 99
        r, c = m
        best = 99
        # sample all; max 361 is fine
        for a, b in stones:
            d = abs(r-a) + abs(c-b)
            if d < best:
                best = d
        return best

    # Opening preferences: star points, corners, extensions.
    star_points = {
        (4,4), (4,10), (4,16),
        (10,4), (10,10), (10,16),
        (16,4), (16,10), (16,16)
    }
    corner_points = {(4,4), (4,16), (16,4), (16,16), (3,3), (3,17), (17,3), (17,17)}

    move_count = len(occupied)

    def score(m):
        if is_true_eyeish(m):
            return -10000.0

        r, c = m
        s = 0.0

        # Prefer tactically active/legal shape.
        empty_n = point_empty_neighbors(m)
        s += empty_n * 2.0

        adj_my = 0
        adj_op = 0
        weakest_adj_op = 10
        weakest_adj_my = 10

        for nb in neigh(m):
            if nb in me_set:
                adj_my += 1
                weakest_adj_my = min(weakest_adj_my, my_lib_count.get(nb, 10))
            elif nb in op_set:
                adj_op += 1
                weakest_adj_op = min(weakest_adj_op, op_lib_count.get(nb, 10))

        s += adj_my * 5.0
        s += adj_op * 4.0

        # Attack enemy groups close to atari and strengthen weak friendly groups.
        if adj_op:
            s += max(0, 7 - weakest_adj_op) * 5.5
        if adj_my:
            s += max(0, 6 - weakest_adj_my) * 3.5

        # Bonus for reducing liberties of opponent groups to atari.
        for g, libs in op_groups:
            if m in libs:
                new_libs = len(libs) - 1
                if new_libs == 1:
                    s += 35 + len(g) * 3
                else:
                    s += max(0, 5 - new_libs) * (2 + min(len(g), 6))

        # Bonus for increasing liberties/connecting friendly groups.
        touching_groups = 0
        for g, libs in my_groups:
            if any(nb in g for nb in neigh(m)):
                touching_groups += 1
                s += min(len(g), 8) * 0.8
                s += max(0, 4 - len(libs)) * 2.5
        if touching_groups >= 2:
            s += 10.0 * (touching_groups - 1)

        # Opening/whole-board positional play.
        if move_count < 40:
            if m in star_points:
                s += 28.0
            if m in corner_points:
                s += 22.0
            # Prefer 3rd/4th lines over first/second early.
            edge_dist = min(r, c, N+1-r, N+1-c)
            if edge_dist in (3, 4):
                s += 10.0
            elif edge_dist == 2:
                s += 2.0
            elif edge_dist == 1:
                s -= 12.0
            # Spread from own stones but not too far from activity.
            dmy = distance_to_nearest(me_set, m)
            dop = distance_to_nearest(op_set, m)
            if me_set:
                s += -abs(dmy - 5) * 1.2
            if op_set:
                s += max(0, 7 - dop) * 1.0
        else:
            # Midgame: stay near stones and contested areas.
            d_all = distance_to_nearest(occupied, m)
            s += max(0, 6 - d_all) * 3.0
            edge_dist = min(r, c, N+1-r, N+1-c)
            if edge_dist == 1:
                s -= 6.0
            elif edge_dist in (2, 3, 4):
                s += 2.0

        # Influence: value intersections surrounded by friendly presence, contest enemy presence.
        for a, b in me_set:
            d = abs(r-a) + abs(c-b)
            if d <= 4:
                s += (5 - d) * 0.55
        for a, b in op_set:
            d = abs(r-a) + abs(c-b)
            if d <= 4:
                s += (5 - d) * 0.45

        # Slight central/corner balance.
        center_dist = abs(r-10) + abs(c-10)
        if move_count < 12:
            s -= center_dist * 0.05
        else:
            s += max(0, 10 - center_dist) * 0.10

        # Deterministic tiny tie-breaker favoring stable points.
        s += ((r * 37 + c * 17) % 100) / 10000.0
        return s

    candidates = set()

    # Candidate generation around stones and strategic points.
    for p in occupied:
        pr, pc = p
        for dr in range(-3, 4):
            for dc in range(-3, 4):
                if abs(dr) + abs(dc) <= 4:
                    q = (pr + dr, pc + dc)
                    if inb(*q) and q not in occupied:
                        candidates.add(q)

    candidates |= star_points
    candidates |= corner_points

    # If very empty, use strong opening points directly.
    if move_count == 0:
        return (4, 4)
    if move_count == 1:
        for m in [(16,16), (4,16), (16,4), (4,4), (10,10)]:
            if legal(m):
                return m

    # Ensure some candidates exist.
    candidates = [m for m in candidates if m not in occupied and legal(m)]
    if not candidates:
        candidates = legal_moves()

    if candidates:
        best = max(candidates, key=score)
        if legal(best):
            return best

    # Final guaranteed fallback.
    lm = legal_moves()
    if lm:
        return lm[0]
    return (0, 0)
