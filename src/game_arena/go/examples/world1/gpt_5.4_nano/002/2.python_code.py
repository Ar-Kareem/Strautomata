
from __future__ import annotations

from typing import List, Tuple, Set
import random

N = 19

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    my_set: Set[Tuple[int, int]] = set(me)
    op_set: Set[Tuple[int, int]] = set(opponent)
    empty = {(r, c) for r in range(1, N+1) for c in range(1, N+1)} - my_set - op_set

    # Board helpers
    def inb(p: Tuple[int, int]) -> bool:
        r, c = p
        return 1 <= r <= N and 1 <= c <= N

    def neighbors(p: Tuple[int, int]):
        r, c = p
        for dr, dc in ((1,0), (-1,0), (0,1), (0,-1)):
            q = (r+dr, c+dc)
            if inb(q):
                yield q

    def group_and_liberties(start: Tuple[int, int], stones: Set[Tuple[int,int]]) -> tuple[Set[Tuple[int,int]], Set[Tuple[int,int]]]:
        # Returns (group stones, liberties empty points)
        if start not in stones:
            return set(), set()
        to_visit = [start]
        visited = {start}
        group = set()
        libs = set()
        while to_visit:
            p = to_visit.pop()
            group.add(p)
            for q in neighbors(p):
                if q in stones and q not in visited:
                    visited.add(q)
                    to_visit.append(q)
                elif q not in my_set and q not in op_set:
                    libs.add(q)
        return group, libs

    def would_capture(move: Tuple[int,int]) -> bool:
        # place our stone at move; check if any adjacent opponent group loses its last liberty
        for q in neighbors(move):
            if q in op_set:
                grp, libs = group_and_liberties(q, op_set)
                if len(libs) == 1 and move in libs:
                    return True
        return False

    def is_legal(move: Tuple[int,int]) -> bool:
        # Basic legality: must be empty; no suicide (unless captures)
        if move not in empty:
            return False
        # Determine if move captures anything
        capture = would_capture(move)
        # Compute our group liberties if we play there
        # Create temporary placement
        stones_tmp = my_set | {move}
        # Find our group from move
        grp, libs = group_and_liberties(move, stones_tmp)
        if libs:
            return True
        # no liberties: only legal if capturing
        return capture

    def candidate_moves() -> List[Tuple[int,int]]:
        # Focus on moves near stones
        cand = set()
        for p in my_set | op_set:
            for q in neighbors(p):
                if q in empty:
                    cand.add(q)
        # If board is empty early, pick center
        if not cand:
            center = (10, 10) if (10, 10) in empty else next(iter(empty))
            return [center]
        # Also include immediate liberties around my/op groups slightly more diversely
        return list(cand)

    # Heuristic scoring
    def score_move(move: Tuple[int,int]) -> float:
        # Higher is better
        if not is_legal(move):
            return -1e9

        # Capture bonus
        sc = 0.0
        if would_capture(move):
            sc += 1000.0

        # Evaluate adjacent groups
        # If move connects to our groups, increase their liberties; if it reduces opponent liberties, good.
        # Temporarily place move
        stones_tmp = my_set | {move}

        # Our group libs after play
        _, my_libs = group_and_liberties(move, stones_tmp)
        sc += 2.5 * len(my_libs)

        # Reduce opponent liberties for adjacent groups
        for q in neighbors(move):
            if q in op_set:
                grp, libs = group_and_liberties(q, op_set)
                # After playing at move, if move is a liberty of that group, libs reduce by 1
                if move in libs:
                    new_libs = len(libs) - 1
                    # Big reward for putting group into atari; bigger if capturing later
                    if new_libs == 0:
                        sc += 800.0
                    elif new_libs == 1:
                        sc += 120.0
                    else:
                        sc += 10.0 / (1 + new_libs)

        # Center preference
        r, c = move
        sc += 2.0 * (-(abs(r - 10) + abs(c - 10)) / 18.0)

        # Avoid making moves that leave our group in atari without capturing
        # (after play, if our group has 1 liberty and no immediate capture)
        if not would_capture(move):
            _, libs_after = group_and_liberties(move, stones_tmp)
            if len(libs_after) == 1:
                sc -= 60.0

        # Small random jitter to break ties deterministically-ish
        sc += random.uniform(-0.5, 0.5)
        return sc

    cand = candidate_moves()
    # Filter legal moves
    legal = [m for m in cand if is_legal(m)]
    if not legal:
        # If no legal adjacent moves, try any empty legal move (rare but possible)
        for m in list(empty):
            if is_legal(m):
                legal.append(m)
                break

    if not legal:
        return (0, 0)

    # Pick best by heuristic
    best = max(legal, key=score_move)
    return best
