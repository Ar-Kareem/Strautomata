
from typing import List, Tuple
import random

N = 19

DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))

STAR_POINTS = [
    (4, 4), (4, 10), (4, 16),
    (10, 4), (10, 10), (10, 16),
    (16, 4), (16, 10), (16, 16),
    (3, 3), (3, 17), (17, 3), (17, 17),
    (4, 3), (3, 4), (4, 17), (3, 16),
    (16, 3), (17, 4), (16, 17), (17, 16)
]

def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]]) -> Tuple[int, int]:
    """
    Return a legal move for 19x19 Go as (row, col), or (0,0) pass.
    Assumes no ko history is available, so only checks board legality/suicide.
    """
    my_set = set(me)
    op_set = set(opponent)

    # Clean any malformed coordinates defensively
    my_set = {(r, c) for (r, c) in my_set if 1 <= r <= N and 1 <= c <= N}
    op_set = {(r, c) for (r, c) in op_set if 1 <= r <= N and 1 <= c <= N and (r, c) not in my_set}
    occupied = my_set | op_set

    if len(occupied) >= N * N:
        return (0, 0)

    def neighbors(p):
        r, c = p
        for dr, dc in DIRS:
            q = (r + dr, c + dc)
            if 1 <= q[0] <= N and 1 <= q[1] <= N:
                yield q

    def get_group(start, stones):
        stack = [start]
        seen = {start}
        while stack:
            p = stack.pop()
            for q in neighbors(p):
                if q in stones and q not in seen:
                    seen.add(q)
                    stack.append(q)
        return seen

    def liberties(group, occ):
        libs = set()
        for p in group:
            for q in neighbors(p):
                if q not in occ:
                    libs.add(q)
        return libs

    # Precompute groups and liberties
    my_groups = []
    seen = set()
    for s in my_set:
        if s not in seen:
            g = get_group(s, my_set)
            seen |= g
            my_groups.append((g, liberties(g, occupied)))

    op_groups = []
    seen = set()
    for s in op_set:
        if s not in seen:
            g = get_group(s, op_set)
            seen |= g
            op_groups.append((g, liberties(g, occupied)))

    def move_result(move):
        """Returns (legal, captured_count, new_group_liberties)."""
        if move in occupied or not (1 <= move[0] <= N and 1 <= move[1] <= N):
            return (False, 0, 0)

        new_my = set(my_set)
        new_op = set(op_set)
        new_my.add(move)
        occ2 = new_my | new_op

        captured = 0
        # Capture adjacent opponent groups with no liberties after move
        checked = set()
        for q in neighbors(move):
            if q in new_op and q not in checked:
                g = get_group(q, new_op)
                checked |= g
                if len(liberties(g, occ2)) == 0:
                    for x in g:
                        new_op.remove(x)
                    captured += len(g)

        occ3 = new_my | new_op
        gnew = get_group(move, new_my)
        libs = len(liberties(gnew, occ3))

        # Suicide illegal unless captures produce liberties
        if libs == 0:
            return (False, captured, 0)
        return (True, captured, libs)

    # Candidate generation: all liberties around groups plus strategic points.
    candidates = set()

    for g, libs in op_groups:
        candidates |= libs
    for g, libs in my_groups:
        candidates |= libs

    # Add local empty neighbors around all stones and their second-order neighborhood
    for s in occupied:
        for q in neighbors(s):
            if q not in occupied:
                candidates.add(q)
            for qq in neighbors(q):
                if qq not in occupied:
                    candidates.add(qq)

    # Opening and fallback candidates
    for p in STAR_POINTS:
        if p not in occupied:
            candidates.add(p)

    # If board is very empty, strongly prefer big points
    if len(occupied) < 8:
        for p in STAR_POINTS:
            legal, _, _ = move_result(p)
            if legal:
                return p

    # Tactical: capture opponent groups in atari, largest first
    best_capture = None
    best_cap_size = -1
    for g, libs in op_groups:
        if len(libs) == 1:
            m = next(iter(libs))
            legal, cap, newlibs = move_result(m)
            if legal and cap > best_cap_size:
                best_capture = m
                best_cap_size = cap
    if best_capture is not None:
        return best_capture

    # Tactical: save own atari groups by playing their liberty, if useful
    best_save = None
    best_save_score = -10**9
    for g, libs in my_groups:
        if len(libs) == 1:
            m = next(iter(libs))
            legal, cap, newlibs = move_result(m)
            if legal:
                score = 100 * len(g) + 30 * cap + 5 * newlibs
                if score > best_save_score:
                    best_save_score = score
                    best_save = m
    if best_save is not None:
        return best_save

    def pos_value(p):
        r, c = p
        # Prefer 3rd/4th lines and star-point-like positions, avoid first line.
        edge_dist = min(r, c, N + 1 - r, N + 1 - c)
        if edge_dist == 1:
            base = -18
        elif edge_dist == 2:
            base = 2
        elif edge_dist in (3, 4):
            base = 12
        elif edge_dist == 5:
            base = 7
        else:
            base = 1

        # Corners/sides are valuable early/midgame.
        corner_dist = min(
            abs(r - 4) + abs(c - 4),
            abs(r - 4) + abs(c - 16),
            abs(r - 16) + abs(c - 4),
            abs(r - 16) + abs(c - 16),
        )
        base += max(0, 10 - 2 * corner_dist)

        # Center star modest bonus
        if p in STAR_POINTS:
            base += 8
        return base

    def score_move(m):
        legal, cap, newlibs = move_result(m)
        if not legal:
            return None

        score = 0
        score += 150 * cap
        score += 8 * min(newlibs, 8)
        score += pos_value(m)

        # Neighbor features
        adj_my = 0
        adj_op = 0
        empty_adj = 0
        for q in neighbors(m):
            if q in my_set:
                adj_my += 1
            elif q in op_set:
                adj_op += 1
            else:
                empty_adj += 1

        score += 10 * adj_my
        score += 6 * adj_op
        score += 3 * empty_adj

        # Attack opponent groups with few liberties
        for g, libs in op_groups:
            if m in libs:
                l = len(libs)
                if l == 2:
                    score += 70 + len(g) * 4
                elif l == 3:
                    score += 30 + len(g) * 2
                elif l <= 5:
                    score += 10

        # Defend own weak groups
        for g, libs in my_groups:
            if m in libs:
                l = len(libs)
                if l == 2:
                    score += 60 + len(g) * 4
                elif l == 3:
                    score += 25 + len(g) * 2
                elif l <= 5:
                    score += 8

        # Avoid filling own eyes / playing in surrounded spaces unless capture/urgent
        surrounded_my = 0
        surrounded_op = 0
        for q in neighbors(m):
            if q in my_set:
                surrounded_my += 1
            elif q in op_set:
                surrounded_op += 1
        if surrounded_my >= 3 and cap == 0 and adj_op == 0:
            score -= 45

        # Prefer contested area over isolated dame in late game
        nearest_op = 99
        nearest_my = 99
        for s in op_set:
            d = abs(m[0] - s[0]) + abs(m[1] - s[1])
            if d < nearest_op:
                nearest_op = d
                if nearest_op <= 2:
                    break
        for s in my_set:
            d = abs(m[0] - s[0]) + abs(m[1] - s[1])
            if d < nearest_my:
                nearest_my = d
                if nearest_my <= 2:
                    break

        if nearest_op <= 2:
            score += 12
        elif nearest_op <= 4:
            score += 6

        if nearest_my <= 2:
            score += 8
        elif nearest_my > 7 and len(occupied) > 30:
            score -= 8

        # Small deterministic noise to break ties without randomness dependency.
        score += ((m[0] * 37 + m[1] * 17 + len(occupied) * 13) % 11) / 10.0
        return score

    best = None
    best_score = None

    # Score generated candidates
    for m in candidates:
        if m in occupied:
            continue
        sc = score_move(m)
        if sc is not None and (best_score is None or sc > best_score):
            best_score = sc
            best = m

    if best is not None:
        return best

    # Full-board fallback: guarantee a legal move if one exists.
    fallback_best = None
    fallback_score = None
    for r in range(1, N + 1):
        for c in range(1, N + 1):
            m = (r, c)
            if m in occupied:
                continue
            sc = score_move(m)
            if sc is not None and (fallback_score is None or sc > fallback_score):
                fallback_score = sc
                fallback_best = m

    if fallback_best is not None:
        return fallback_best

    return (0, 0)
