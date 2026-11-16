
from collections import deque
import math
import random

N = 19

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    me_set = set(me)
    op_set = set(opponent)
    occ = me_set | op_set

    def inb(r, c):
        return 1 <= r <= N and 1 <= c <= N

    def neigh(p):
        r, c = p
        if r > 1: yield (r-1, c)
        if r < N: yield (r+1, c)
        if c > 1: yield (r, c-1)
        if c < N: yield (r, c+1)

    def group_and_libs(start, stones):
        q = [start]
        seen = {start}
        libs = set()
        while q:
            p = q.pop()
            for nb in neigh(p):
                if nb in stones and nb not in seen:
                    seen.add(nb)
                    q.append(nb)
                elif nb not in occ:
                    libs.add(nb)
        return seen, libs

    # Build groups.
    my_groups = []
    seen = set()
    for s in me_set:
        if s not in seen:
            g, libs = group_and_libs(s, me_set)
            seen |= g
            my_groups.append((g, libs))

    op_groups = []
    seen = set()
    for s in op_set:
        if s not in seen:
            g, libs = group_and_libs(s, op_set)
            seen |= g
            op_groups.append((g, libs))

    def legal(move):
        if move == (0, 0):
            return True
        if move in occ:
            return False
        r, c = move
        if not inb(r, c):
            return False

        # Legal if it has an empty neighbor.
        for nb in neigh(move):
            if nb not in occ:
                return True

        # Legal if it connects to own group with another liberty.
        for nb in neigh(move):
            if nb in me_set:
                _, libs = group_and_libs(nb, me_set)
                if len(libs - {move}) > 0:
                    return True

        # Legal if it captures adjacent opponent group.
        for nb in neigh(move):
            if nb in op_set:
                _, libs = group_and_libs(nb, op_set)
                if libs == {move}:
                    return True
        return False

    def dist_center_score(r, c):
        # Favor balanced central influence while not overvaluing exact center.
        return -0.12 * (abs(r - 10) + abs(c - 10))

    def star_score(r, c):
        stars = [(4,4),(4,10),(4,16),(10,4),(10,10),(10,16),(16,4),(16,10),(16,16)]
        return max(0.0, 8.0 - min(abs(r-a)+abs(c-b) for a,b in stars))

    def edge_penalty(r, c):
        d = min(r, c, N+1-r, N+1-c)
        if d == 1:
            return -8.0
        if d == 2:
            return -2.0
        return 0.0

    def candidate_moves():
        cand = set()

        # Tactical liberties around all stones.
        for p in occ:
            for nb in neigh(p):
                if nb not in occ:
                    cand.add(nb)
                for nb in neigh(p):
                    for nb2 in neigh(nb):
                        if nb2 not in occ:
                            cand.add(nb2)

        # Opening points if board is sparse.
        if len(occ) < 80:
            for p in [(4,4),(4,16),(16,4),(16,16),(10,10),
                      (4,10),(10,4),(10,16),(16,10),
                      (3,4),(4,3),(3,16),(4,17),(16,3),(17,4),(16,17),(17,16),
                      (10,10),(10,4),(4,10),(16,10),(10,16)]:
                if p not in occ:
                    cand.add(p)

        if not cand:
            for r in range(1, N+1):
                for c in range(1, N+1):
                    if (r, c) not in occ:
                        cand.add((r, c))
        return cand

    # Immediate tactical priorities.
    best_capture = None
    best_capture_val = -1
    for g, libs in op_groups:
        if len(libs) == 1:
            m = next(iter(libs))
            if legal(m):
                val = len(g) * 100 + sum(1 for nb in neigh(m) if nb in me_set)
                if val > best_capture_val:
                    best_capture = m
                    best_capture_val = val
    if best_capture is not None:
        return best_capture

    # Save largest own group in atari, preferring capture escapes and high-liberty extensions.
    best_save = None
    best_save_val = -1
    for g, libs in my_groups:
        if len(libs) == 1:
            m = next(iter(libs))
            if legal(m):
                val = len(g) * 80
                for nb in neigh(m):
                    if nb in op_set:
                        og, ol = group_and_libs(nb, op_set)
                        if ol == {m}:
                            val += 200 + 80 * len(og)
                # count new adjacent empties
                val += 10 * sum(1 for nb in neigh(m) if nb not in occ)
                if val > best_save_val:
                    best_save = m
                    best_save_val = val
    if best_save is not None:
        return best_save

    # Attack groups with exactly two liberties.
    attack_moves = {}
    for g, libs in op_groups:
        if len(libs) == 2:
            for m in libs:
                if legal(m):
                    attack_moves[m] = attack_moves.get(m, 0) + 35 + 12 * len(g)

    # Extend own weak groups with two liberties.
    defend_moves = {}
    for g, libs in my_groups:
        if len(libs) == 2:
            for m in libs:
                if legal(m):
                    defend_moves[m] = defend_moves.get(m, 0) + 28 + 9 * len(g)

    def evaluate(m):
        r, c = m
        score = 0.0

        score += attack_moves.get(m, 0)
        score += defend_moves.get(m, 0)

        # Capturing potential / atari setup.
        adj_my = 0
        adj_op = 0
        adj_empty = 0
        merged_libs = set()
        for nb in neigh(m):
            if nb in me_set:
                adj_my += 1
                _, libs = group_and_libs(nb, me_set)
                merged_libs |= libs
            elif nb in op_set:
                adj_op += 1
                og, ol = group_and_libs(nb, op_set)
                if m in ol:
                    after = len(ol) - 1
                    score += max(0, 18 - 5 * after) + 2.5 * len(og)
                    if after == 1:
                        score += 30 + 8 * len(og)
            else:
                adj_empty += 1
                merged_libs.add(nb)

        score += 4.0 * adj_my + 2.0 * adj_op + 3.0 * adj_empty
        score += min(18, 2.2 * len(merged_libs))

        # Prefer moves near opponent and own stones, but not pointless contact too early.
        for s in opponent:
            d = abs(r - s[0]) + abs(c - s[1])
            if d == 1:
                score += 5
            elif d == 2:
                score += 4
            elif d == 3:
                score += 2
        for s in me:
            d = abs(r - s[0]) + abs(c - s[1])
            if d == 1:
                score += 2.5
            elif d == 2:
                score += 2.0
            elif d == 3:
                score += 1.0

        # Shape: avoid filling own eyes / completely surrounded points unless capturing.
        my_neighbors = sum(1 for nb in neigh(m) if nb in me_set)
        op_neighbors = sum(1 for nb in neigh(m) if nb in op_set)
        empty_neighbors = sum(1 for nb in neigh(m) if nb not in occ)
        if empty_neighbors == 0 and op_neighbors == 0:
            score -= 60
        if my_neighbors >= 3 and op_neighbors == 0:
            score -= 12

        # Opening / positional priorities.
        move_no = len(occ)
        if move_no < 60:
            score += 2.2 * star_score(r, c)
            # Corners before sides before center.
            corner_dist = min(abs(r-a)+abs(c-b) for a,b in [(4,4),(4,16),(16,4),(16,16)])
            score += max(0, 10 - corner_dist)
        elif move_no < 180:
            score += 1.2 * star_score(r, c)
            score += dist_center_score(r, c)
        else:
            score += 0.5 * dist_center_score(r, c)

        score += edge_penalty(r, c)

        # Mild deterministic noise for tie-breaking.
        score += ((r * 37 + c * 17 + len(occ) * 13) % 11) * 0.01
        return score

    best = None
    best_score = -10**18
    for m in candidate_moves():
        if legal(m):
            sc = evaluate(m)
            if sc > best_score:
                best_score = sc
                best = m

    if best is not None:
        return best

    # Guaranteed fallback: first legal empty point, otherwise pass.
    for r in range(1, N+1):
        for c in range(1, N+1):
            m = (r, c)
            if m not in occ and legal(m):
                return m
    return (0, 0)
