
from typing import List, Tuple
import random

BOARD_SIZE = 19

def neighbors(pos: Tuple[int, int]) -> List[Tuple[int, int]]:
    """Return the four orthogonal neighbours of a point (clipped to the board)."""
    r, c = pos
    dirs = [(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)]
    return [(nr, nc) for nr, nc in dirs
            if 1 <= nr <= BOARD_SIZE and 1 <= nc <= BOARD_SIZE]

def find_groups(stones: set, player: int) -> List[dict]:
    """
    Find all connected groups for `player` among `stones`.
    Returns a list of dicts each containing:
        - 'stones': set of positions in the group
        - 'libs':   set of liberty positions (empty or opponent stones)
    """
    groups = []
    visited = set()
    for stone in stones:
        if stone in visited:
            continue
        queue = [stone]
        visited.add(stone)
        group_stones = {stone}
        libs = set()
        while queue:
            cur = queue.pop()
            for nb in neighbors(cur):
                if nb in stones and nb not in visited:
                    visited.add(nb)
                    queue.append(nb)
                    group_stones.add(nb)
                elif nb not in stones or stones_nb_to_player[nb] != player:
                    # liberty: empty or opponent stone
                    libs.add(nb)
        groups.append({'stones': group_stones, 'libs': libs})
    return groups

def is_legal(p: Tuple[int, int]) -> bool:
    """
    Return True iff playing on empty point `p` does not commit suicide.
    We compute the merged my‑stone group that would result and count its
    liberties after the move.
    """
    # Combine all my stones that touch p (directly or indirectly)
    reachable = set()
    for nb in neighbors(p):
        if nb in me_positions:
            reachable.add(nb)

    # BFS across my stones to gather the whole component
    visited = set(reachable)
    queue = list(reachable)
    while queue:
        cur = queue.pop()
        for nb in neighbors(cur):
            if nb in me_positions and nb not in visited:
                visited.add(nb)
                queue.append(nb)

    combined = visited | {p}
    # Count liberties after p would be placed
    libs = set()
    for stone in combined:
        for nb in neighbors(stone):
            if nb not in board:  # empty → liberty
                libs.add(nb)
    return len(libs) > 0

def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]]) -> Tuple[int, int]:
    """
    Return the next move as a tuple (row, col). Use (0, 0) for pass.
    """
    global me_positions, opp_positions, board, stones_nb_to_player

    # Convert input to sets for fast membership tests
    me_positions = set(me)
    opp_positions = set(opponent)

    # Build a board dictionary mapping occupied points to player id
    #   1 = me, -1 = opponent, points not in dict are empty
    board = {}
    for pt in me_positions:
        board[pt] = 1
    for pt in opp_positions:
        board[pt] = -1

    # All points on a 19×19 board
    all_pts = [(r, c) for r in range(1, BOARD_SIZE + 1)
              for c in range(1, BOARD_SIZE + 1)]

    # Empty points (legal candidates unless suicide)
    empty_positions = [pt for pt in all_pts if pt not in board]

    # If the board is full we have to pass
    if not empty_positions:
        return (0, 0)

    # -------------------------------------------------
    # 1. Find opponent groups and urgent defence map
    # -------------------------------------------------
    opp_groups = find_groups(opp_positions, -1)

    urgent_score: dict[Tuple[int, int], int] = {}
    for grp in opp_groups:
        libs = grp['libs']
        if len(libs) == 1:  # immediate threat
            liberty = next(iter(libs))
            urgent_score[liberty] = urgent_score.get(liberty, 0) + len(grp['stones'])

    # Capture candidates: opponent groups with a single liberty
    capture_candidates = []
    for grp in opp_groups:
        libs = grp['libs']
        if len(libs) == 1:
            liberty = next(iter(libs))
            if liberty not in board:  # it must be empty
                capture_candidates.append((liberty, len(grp['stones'])))

    # -------------------------------------------------
    # 2. Immediate capture phase
    # -------------------------------------------------
    for pt, grp_size in capture_candidates:
        if is_legal(pt):
            # Give a modest extra weight to captures of large groups,
            # but capture is already high priority.
            return pt

    # -------------------------------------------------
    # 3. Heuristic scoring phase
    # -------------------------------------------------
    best_score = -float('inf')
    best_moves: List[Tuple[int, int]] = []

    def edge_weight(pt: Tuple[int, int]) -> int:
        """Weight based on distance to the nearest board edge."""
        r, c = pt
        dist = min(r - 1, BOARD_SIZE - r, c - 1, BOARD_SIZE - c)
        if dist == 0:                     # border squares
            if (r, c) in {(1, 1), (1, BOARD_SIZE), (BOARD_SIZE, 1), (BOARD_SIZE, BOARD_SIZE)}:
                return 3   # corners
            else:
                return 2   # edges but not corners
        elif dist == 1:
            return 2
        else:
            return 1

    for pt in empty_positions:
        # Skip illegal suicide moves
        if not is_legal(pt):
            continue

        # Neighbour counts
        opp_adj = sum(1 for nb in neighbors(pt) if nb in opp_positions)
        my_adj = sum(1 for nb in neighbors(pt) if nb in me_positions)
        empty_neighbours = sum(1 for nb in neighbors(pt) if nb not in board)

        urgency = urgent_score.get(pt, 0)

        # Score components (tuned to give strong preference to urgent defence)
        score = (edge_weight(pt)
                 + opp_adj * 5
                 - my_adj * 2
                 + empty_neighbours * 2
                 + urgency * 10)

        if score > best_score:
            best_score = score
            best_moves = [pt]
        elif score == best_score:
            best_moves.append(pt)

    # If no legal moves survived the suicide filter, pass
    if not best_moves:
        return (0, 0)

    # Random tie‑break makes the policy less predictable while still deterministic in most cases
    return random.choice(best_moves)
