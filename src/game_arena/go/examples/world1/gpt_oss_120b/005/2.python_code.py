
import random
from collections import deque
from typing import List, Tuple, Set

# Directions: up, down, left, right
DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]

def _neighbors(pos: Tuple[int, int]) -> List[Tuple[int, int]]:
    r, c = pos
    return [(r + dr, c + dc) for dr, dc in DIRS
            if 1 <= r + dr <= 19 and 1 <= c + dc <= 19]

def _build_groups(stones: Set[Tuple[int, int]],
                  empty: Set[Tuple[int, int]]) -> List[Tuple[Set[Tuple[int, int]], Set[Tuple[int, int]]]]:
    """Return a list of (group, liberties) for the given set of stones."""
    groups = []
    visited = set()
    for s in stones:
        if s in visited:
            continue
        group = set()
        liberties = set()
        stack = [s]
        while stack:
            cur = stack.pop()
            if cur in visited:
                continue
            visited.add(cur)
            group.add(cur)
            for nb in _neighbors(cur):
                if nb in stones:
                    if nb not in visited:
                        stack.append(nb)
                elif nb not in stones:
                    # nb is empty (cannot be opponent stone because we only pass own stones)
                    liberties.add(nb)
        groups.append((group, liberties))
    return groups

def _group_map(groups: List[Tuple[Set[Tuple[int, int]], Set[Tuple[int, int]]]]) -> dict:
    """Map each stone to the index of its group."""
    mapping = {}
    for idx, (grp, _) in enumerate(groups):
        for stone in grp:
            mapping[stone] = idx
    return mapping

def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]]) -> Tuple[int, int]:
    """Return a single legal move for the current player."""
    me_set = set(me)
    opp_set = set(opponent)
    occupied = me_set | opp_set
    empty = {(r, c) for r in range(1, 20) for c in range(1, 20)} - occupied

    # No empty points → must pass
    if not empty:
        return (0, 0)

    # Build opponent groups with their liberties
    opp_groups = _build_groups(opp_set, empty)
    # Build own groups and a quick lookup table
    my_groups = _build_groups(me_set, empty)
    my_group_index = _group_map(my_groups)

    best_move = None
    best_score = -float('inf')

    for move in empty:
        r, c = move
        # Determine which opponent groups would be captured
        captured_stones = 0
        for grp, libs in opp_groups:
            if libs == {move}:
                captured_stones += len(grp)

        # Determine neighbours of own stones
        my_neighbor_groups = set()
        opp_neighbor_count = 0
        for nb in _neighbors(move):
            if nb in me_set:
                my_neighbor_groups.add(my_group_index[nb])
            elif nb in opp_set:
                opp_neighbor_count += 1

        # Legal move test
        legal = False
        if captured_stones > 0:
            legal = True
        else:
            # Adjacent empty point?
            if any(nb in empty for nb in _neighbors(move)):
                legal = True
            else:
                # Connecting to own group that still has another liberty?
                for gid in my_neighbor_groups:
                    _, libs = my_groups[gid]
                    # after playing at `move` one liberty disappears
                    if len(libs - {move}) > 0:
                        legal = True
                        break

        if not legal:
            continue

        # Scoring
        score = 0
        score += 100 * captured_stones                     # capture priority
        score += 10 * len(my_neighbor_groups)              # stay connected
        score += opp_neighbor_count                        # pressure opponent
        score += random.random() * 1e-6                    # tiny noise to break ties

        if score > best_score:
            best_score = score
            best_move = move

    # If for some reason we found no legal move (should not happen), pass.
    if best_move is None:
        return (0, 0)
    return best_move
