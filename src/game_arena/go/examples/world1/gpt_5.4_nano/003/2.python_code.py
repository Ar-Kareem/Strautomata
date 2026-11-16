
from __future__ import annotations

from typing import List, Tuple, Set, Dict
import random
import numpy as np

BoardSize = 19
PASS_MOVE = (0, 0)

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    me_set: Set[Tuple[int, int]] = set(me)
    op_set: Set[Tuple[int, int]] = set(opponent)
    all_stones: Set[Tuple[int, int]] = me_set | op_set

    # Helpers
    def inside(r: int, c: int) -> bool:
        return 1 <= r <= BoardSize and 1 <= c <= BoardSize

    def neighbors(r: int, c: int):
        if r > 1: yield (r - 1, c)
        if r < BoardSize: yield (r + 1, c)
        if c > 1: yield (r, c - 1)
        if c < BoardSize: yield (r, c + 1)

    def get_empty_points_near(stones: Set[Tuple[int, int]], radius: int = 2) -> Set[Tuple[int, int]]:
        # Not too expensive: examine bounding box +/- radius around stones (approx)
        res = set()
        if not stones:
            # Center-ish start
            center = (10, 10)
            for r in range(max(1, center[0]-radius), min(BoardSize, center[0]+radius)+1):
                for c in range(max(1, center[1]-radius), min(BoardSize, center[1]+radius)+1):
                    if (r, c) not in all_stones:
                        res.add((r, c))
            return res

        rows = [r for r, _ in stones]
        cols = [c for _, c in stones]
        rmin = max(1, min(rows) - radius)
        rmax = min(BoardSize, max(rows) + radius)
        cmin = max(1, min(cols) - radius)
        cmax = min(BoardSize, max(cols) + radius)

        for r in range(rmin, rmax + 1):
            for c in range(cmin, cmax + 1):
                if (r, c) not in all_stones:
                    # quick distance filter
                    # (use manhattan to reduce candidates)
                    close = False
                    for rr in range(max(1, r-radius), min(BoardSize, r+radius)+1):
                        # small optimization: still fine due to small radius
                        for cc in range(max(1, c-radius), min(BoardSize, c+radius)+1):
                            if (rr, cc) in stones and abs(rr-r)+abs(cc-c) <= radius:
                                close = True
                                break
                        if close:
                            break
                    if close or (rmin==1 and rmax==BoardSize and cmin==1 and cmax==BoardSize):
                        res.add((r, c))
        return res

    def compute_group_and_liberties(start: Tuple[int, int], board_me: Set[Tuple[int, int]], board_op: Set[Tuple[int, int]]):
        # Returns (group_set, liberties_set)
        r0, c0 = start
        if start in board_me:
            my_color = 1
        else:
            my_color = 2
        visited = set()
        stack = [start]
        group = set()
        liberties = set()
        while stack:
            r, c = stack.pop()
            if (r, c) in visited:
                continue
            visited.add((r, c))
            group.add((r, c))
            for nr, nc in neighbors(r, c):
                if my_color == 1:
                    if (nr, nc) in board_me and (nr, nc) not in visited:
                        stack.append((nr, nc))
                    elif (nr, nc) not in board_me and (nr, nc) not in board_op:
                        liberties.add((nr, nc))
                else:
                    if (nr, nc) in board_op and (nr, nc) not in visited:
                        stack.append((nr, nc))
                    elif (nr, nc) not in board_me and (nr, nc) not in board_op:
                        liberties.add((nr, nc))
        return group, liberties

    def would_capture(op_board_me: Set[Tuple[int, int]], op_board_op: Set[Tuple[int, int]], move: Tuple[int, int]) -> bool:
        # after placing our stone at move, check if any adjacent opponent group loses its last liberty
        r, c = move
        test_me = set(op_board_me)
        test_op = set(op_board_op)
        if move in test_me or move in test_op:
            return False
        test_me.add(move)
        # opponent groups adjacent to move
        for nr, nc in neighbors(r, c):
            if (nr, nc) in test_op:
                grp, libs = compute_group_and_liberties((nr, nc), test_me, test_op)
                # If after placement the liberties set size is 0, group would be captured; but usually libs already computed
                # Actually compute_group_and_liberties with test_me already removes our placement, so last-liberty capture => libs==set()
                if len(libs) == 0:
                    return True
        return False

    def is_legal_simple(move: Tuple[int, int]) -> bool:
        # We don't enforce full superko; instead ensure basic legality: not occupied, not suicide (no liberties)
        r, c = move
        if not inside(r, c) or move in all_stones:
            return False
        test_me = set(me_set)
        test_op = set(op_set)
        test_me.add(move)
        # If any adjacent opponent group is captured, suicide is avoided
        captured_any = False
        to_remove = set()
        for nr, nc in neighbors(r, c):
            if (nr, nc) in test_op:
                grp, libs = compute_group_and_liberties((nr, nc), test_me, test_op)
                if len(libs) == 0:
                    captured_any = True
                    to_remove |= grp
        if captured_any:
            test_op -= to_remove
            # after capture, our placed stone group should have liberties (at least) automatically
            return True

        # No capture: check our group liberties
        grp, libs = compute_group_and_liberties((r, c), test_me, test_op)
        return len(libs) > 0

    # Candidate moves: near stones
    candidate_set = set()
    candidate_set |= get_empty_points_near(me_set, radius=2)
    candidate_set |= get_empty_points_near(op_set, radius=2)
    if not candidate_set:
        # early game fallback
        for r in range(7, 13):
            for c in range(7, 13):
                if (r, c) not in all_stones:
                    candidate_set.add((r, c))

    # Also consider exact atari responses: any empty adjacent to opponent stones
    for r, c in op_set:
        for nr, nc in neighbors(r, c):
            if (nr, nc) not in all_stones and inside(nr, nc):
                candidate_set.add((nr, nc))
    # Limit candidates for speed
    if len(candidate_set) > 140:
        # choose those closest to center among candidates
        cand = list(candidate_set)
        cand.sort(key=lambda p: abs(p[0]-10)+abs(p[1]-10))
        candidate_set = set(cand[:140])

    legal_moves = [m for m in candidate_set if is_legal_simple(m)]
    if not legal_moves:
        return PASS_MOVE if (0, 0) else PASS_MOVE

    # Heuristic scoring
    def local_attack_value(move: Tuple[int, int]) -> int:
        # capture immediate
        if would_capture(me_set, op_set, move):
            return 10000
        # block opponent atari: if move makes any adjacent opponent group have no liberties -> actually that means capturing? No,
        # but we can estimate by checking if adjacent opponent group currently has 1 liberty and the move is that liberty.
        r, c = move
        # if any adjacent opponent group has exactly 1 liberty and it's this move => urgent block
        for nr, nc in neighbors(r, c):
            if (nr, nc) in op_set:
                grp, libs = compute_group_and_liberties((nr, nc), me_set, op_set)
                if len(libs) == 1 and (r, c) in libs:
                    return 8000
        return 0

    def self_atari_penalty(move: Tuple[int, int]) -> int:
        # Penalize if move results in our group having exactly 1 liberty (likely atari)
        r, c = move
        test_me = set(me_set)
        test_op = set(op_set)
        test_me.add(move)

        # If capturing, don't penalize heavily
        captured_any = False
        to_remove = set()
        for nr, nc in neighbors(r, c):
            if (nr, nc) in test_op:
                grp, libs = compute_group_and_liberties((nr, nc), test_me, test_op)
                if len(libs) == 0:
                    captured_any = True
                    to_remove |= grp
        if captured_any:
            test_op -= to_remove
        grp, libs = compute_group_and_liberties((r, c), test_me, test_op)
        if len(libs) == 1:
            return 120
        if len(libs) == 0:
            return 100000
        return 0

    def expansion_score(move: Tuple[int, int]) -> float:
        # Prefer moves that touch our and empty areas and away from being too isolated.
        r, c = move
        center_dist = abs(r-10) + abs(c-10)
        score = -0.8 * center_dist

        # adjacency
        adj_me = 0
        adj_op = 0
        for nr, nc in neighbors(r, c):
            if (nr, nc) in me_set:
                adj_me += 1
            elif (nr, nc) in op_set:
                adj_op += 1
        score += 2.5 * adj_me
        score += 1.0 * adj_op

        # local liberty potential if we play here: count empty neighbors
        empty_adj = 0
        for nr, nc in neighbors(r, c):
            if (nr, nc) not in all_stones:
                empty_adj += 1
        score += 1.6 * empty_adj

        # small preference for moves that would create more liberties for our group
        # approximate: our group's liberties after move (with captures applied)
        test_me = set(me_set)
        test_op = set(op_set)
        test_me.add(move)
        captured_any = False
        to_remove = set()
        for nr, nc in neighbors(r, c):
            if (nr, nc) in test_op:
                grp, libs = compute_group_and_liberties((nr, nc), test_me, test_op)
                if len(libs) == 0:
                    captured_any = True
                    to_remove |= grp
        if captured_any:
            test_op -= to_remove
        grp, libs = compute_group_and_liberties((r, c), test_me, test_op)
        score += 0.25 * len(libs)

        return score

    scored = []
    for m in legal_moves:
        attack = local_attack_value(m)
        penalty = self_atari_penalty(m)
        if penalty >= 100000:
            continue
        sc = attack + (-penalty) + expansion_score(m)
        # tiny random tie-break to avoid deterministic loops
        sc += random.random() * 0.01
        scored.append((sc, m))

    scored.sort(reverse=True, key=lambda x: x[0])
    best = scored[0][1]
    return best
