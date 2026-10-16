
import random
from copy import deepcopy
from typing import List, Tuple, Dict

# Constants for board coordinates
BOARD_SIZE = 19
DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]

def _get_groups(coord_set: set) -> List[set]:
    """Return all connected groups (4‑connected) as a list of sets."""
    groups: List[set] = []
    visited = set()
    stack: List[Tuple[int, int]] = []
    for pt in coord_set:
        if pt in visited:
            continue
        group = set()
        stack.append(pt)
        while stack:
            cur = stack.pop()
            if cur in visited:
                continue
            visited.add(cur)
            group.add(cur)
            for dr, dc in DIRS:
                nb = (cur[0] + dr, cur[1] + dc)
                if 1 <= nb[0] <= BOARD_SIZE and 1 <= nb[1] <= BOARD_SIZE and nb in coord_set:
                    stack.append(nb)
        groups.append(group)
    return groups


def _liberties(group: set, board_set: set) -> int:
    """Number of orthogonal empty points adjacent to every point in the group."""
    libs = set()
    for pt in group:
        for dr, dc in DIRS:
            nb = (pt[0] + dr, pt[1] + dc)
            if 1 <= nb[0] <= BOARD_SIZE and 1 <= nb[1] <= BOARD_SIZE:
                if nb not in board_set:
                    libs.add(nb)
    return len(libs)


def _simulate_move(move: Tuple[int, int],
                   my_stones: set,
                   opp_stones: set,
                   memory: Dict) -> Tuple[set, set] | None:
    """
    Return new sets of stones (my, opp) after applying `move` if legal,
    otherwise return None.
    The function implements capture, suicide check and simple super‑ko.
    """
    # place our own stone
    new_my = my_stones | {move}
    # copy opponent stones for simulation
    new_opp = opp_stones.copy()

    # ----- opponent capture -----
    opp_groups = _get_groups(new_opp)
    to_remove = []
    for g in opp_groups:
        libs = _liberties(g, new_my | new_opp)
        if libs == 0:               # this group would be captured
            to_remove.append(g)

    # apply capture
    new_opp = {pt for pt in new_opp if pt not in to_remove}
    # ----- suicide check for us -----
    our_groups = _get_groups(new_my)
    suicide = False
    for g in our_groups:
        libs = _liberties(g, new_my | new_opp)
        if libs == 0:
            suicide = True
            break
    if suicide:
        return None

    # ----- super‑ko detection (optional, but safe) -----
    final_board = frozenset(new_my | new_opp)
    if final_board == memory.get('last_board', final_board):
        # would recreate the exact previous board → illegal
        return None

    return new_my, new_opp


def policy(me: List[Tuple[int, int]],
           opponent: List[Tuple[int, int]],
           memory: Dict) -> Tuple[Tuple[int, int], Dict]:
    """
    Select a legal move on a 19×19 Go board.
    Returns a tuple (move, memory) where move is (row, col) or (0,0) for pass.
    """
    # Initialise persistent memory structures
    if 'last_board' not in memory:
        memory['last_board'] = frozenset(set(me) | set(opponent))
    if 'ko_point' not in memory:
        memory['ko_point'] = None

    my_set = set(me)
    opp_set = set(opponent)

    # List all empty points
    empty_points = [(r, c) for r in range(1, BOARD_SIZE + 1)
                           for c in range(1, BOARD_SIZE + 1)
                           if (r, c) not in my_set and (r, c) not in opp_set]

    # Helper to store candidate moves
    candidates: List[Tuple[int, int, int]] = []  # (capture_sum, liberties, move)

    random.seed(42)                     # deterministic randomness

    for move in empty_points:
        new_my, new_opp = _simulate_move(move, my_set, opp_set, memory)
        if new_my is None:               # move illegal (suicide, ko repeat, etc.)
            continue

        # Capture sum (number of opponent stones taken)
        orig_opp_groups = _get_groups(opp_set)
        capture_sum = sum(len(g) for g in orig_opp_groups) - sum(len(g) for g in new_opp)
        capture_sum = max(capture_sum, 0)

        # Liberties count of the player's group that contains the new stone
        our_groups = _get_groups(new_my)
        move_group = next(g for g in our_groups if move in g)
        lib_count = _liberties(move_group, new_my | new_opp)

        candidates.append((capture_sum, lib_count, move))

    # Choose the best move according to heuristic
    if candidates:
        # First, maximize capture; tie‑break with larger liberties
        candidates.sort(key=lambda x: (x[0], -x[1]), reverse=True)
        best = candidates[0]
        action = best[2]                # move (row, col)

        # Update memory for the next turn
        memory['ko_point'] = memory.get('ko_point') or action
        memory['last_board'] = memory['last_board']  # board before our move
        # If we captured, remember that point as ko
        memory['ko_point'] = action
        return action, memory
    else:
        # No legal move found → pass
        action = (0, 0)
        memory['ko_point'] = None
        memory['last_board'] = memory['last_board']
        return action, memory
