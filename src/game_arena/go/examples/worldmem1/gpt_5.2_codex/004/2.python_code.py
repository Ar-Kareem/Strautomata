
from collections import deque
from typing import List, Tuple, Dict, Set

SIZE = 19
CENTER = (10, 10)

def neighbors(r: int, c: int):
    if r > 1: yield (r-1, c)
    if r < SIZE: yield (r+1, c)
    if c > 1: yield (r, c-1)
    if c < SIZE: yield (r, c+1)

def get_groups_and_liberties(stones: Set[Tuple[int,int]], other: Set[Tuple[int,int]]):
    visited = set()
    groups = []
    for s in stones:
        if s in visited:
            continue
        group = set()
        libs = set()
        q = deque([s])
        visited.add(s)
        while q:
            x = q.popleft()
            group.add(x)
            for nb in neighbors(*x):
                if nb in stones and nb not in visited:
                    visited.add(nb)
                    q.append(nb)
                elif nb not in stones and nb not in other:
                    libs.add(nb)
        groups.append((group, libs))
    return groups

def move_captures(move, me_set, opp_set):
    # if move is a liberty of any opponent group with exactly one liberty, it captures
    for group, libs in get_groups_and_liberties(opp_set, me_set):
        if len(libs) == 1 and move in libs:
            return True, len(group)
    return False, 0

def is_legal(move, me_set, opp_set):
    if move == (0,0):
        return True
    if move in me_set or move in opp_set:
        return False
    # capture check
    captures, _ = move_captures(move, me_set, opp_set)
    if captures:
        return True
    # check if the new group has any liberty
    new_me = set(me_set)
    new_me.add(move)
    # compute liberties of the new group containing move
    q = deque([move])
    visited = {move}
    libs = set()
    while q:
        x = q.popleft()
        for nb in neighbors(*x):
            if nb in new_me and nb not in visited:
                visited.add(nb)
                q.append(nb)
            elif nb not in new_me and nb not in opp_set:
                libs.add(nb)
    return len(libs) > 0

def policy(me: List[Tuple[int,int]], opponent: List[Tuple[int,int]], memory: Dict):
    me_set = set(me)
    opp_set = set(opponent)
    occupied = me_set | opp_set

    # 1. Immediate capture
    best_capture = None
    best_size = -1
    for group, libs in get_groups_and_liberties(opp_set, me_set):
        if len(libs) == 1:
            liberty = next(iter(libs))
            if is_legal(liberty, me_set, opp_set):
                if len(group) > best_size:
                    best_size = len(group)
                    best_capture = liberty
    if best_capture:
        return best_capture, memory

    # 2. Save own group in atari
    for group, libs in get_groups_and_liberties(me_set, opp_set):
        if len(libs) == 1:
            liberty = next(iter(libs))
            if is_legal(liberty, me_set, opp_set):
                return liberty, memory

    # 3. Strategic move: evaluate candidates
    candidates = set()
    for s in occupied:
        for nb in neighbors(*s):
            if nb not in occupied:
                candidates.add(nb)

    # If board empty, play center
    if not occupied:
        return CENTER, memory

    best_move = None
    best_score = -1e9
    for move in candidates:
        if not is_legal(move, me_set, opp_set):
            continue
        r, c = move
        score = 0.0
        # adjacency bonuses
        for nb in neighbors(r, c):
            if nb in me_set:
                score += 1.0
            elif nb in opp_set:
                score += 2.0
        # centrality bonus
        dist = abs(r - CENTER[0]) + abs(c - CENTER[1])
        score += (18 - dist) / 10.0
        # small bonus if creating atari
        temp_me = set(me_set)
        temp_me.add(move)
        for group, libs in get_groups_and_liberties(opp_set, temp_me):
            if len(libs) == 1:
                score += 3.0
        if score > best_score:
            best_score = score
            best_move = move

    if best_move:
        return best_move, memory

    # 4. Fallback: play any legal empty point
    for r in range(1, SIZE+1):
        for c in range(1, SIZE+1):
            if (r,c) not in occupied and is_legal((r,c), me_set, opp_set):
                return (r,c), memory

    # 5. If nothing legal, pass
    return (0,0), memory
