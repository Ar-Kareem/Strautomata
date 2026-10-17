
import numpy as np
from typing import List, Tuple, Set

def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]]) -> Tuple[int, int]:
    # Convert input to sets for faster lookup
    my_stones = set(me)
    opp_stones = set(opponent)
    all_stones = my_stones | opp_stones

    # Board size
    N = 19

    # Helper: check if a position is on the board
    def is_on_board(r: int, c: int) -> bool:
        return 1 <= r <= N and 1 <= c <= N

    # Helper: get neighbors (up, down, left, right)
    def neighbors(r: int, c: int) -> List[Tuple[int, int]]:
        return [(r-1, c), (r+1, c), (r, c-1), (r, c+1)]

    # Helper: find connected group and their liberties
    def find_group_and_liberties(start_r: int, start_c: int, color_set: Set[Tuple[int, int]]) -> Tuple[Set[Tuple[int, int]], Set[Tuple[int, int]]]:
        stack = [(start_r, start_c)]
        group = set()
        visited = set()
        liberties = set()
        while stack:
            r, c = stack.pop()
            if (r, c) in visited:
                continue
            visited.add((r, c))
            if (r, c) in color_set:
                group.add((r, c))
                for nr, nc in neighbors(r, c):
                    if is_on_board(nr, nc):
                        if (nr, nc) in color_set:
                            if (nr, nc) not in visited:
                                stack.append((nr, nc))
                        elif (nr, nc) not in all_stones:
                            liberties.add((nr, nc))
        return group, liberties

    # Helper: check if placing a stone leads to a capture
    def would_capture(r: int, c: int) -> List[Tuple[int, int]]:
        captures = []
        for nr, nc in neighbors(r, c):
            if (nr, nc) in opp_stones:
                # Check if opponent group now has 0 liberties
                opp_group, opp_liberties = find_group_and_liberties(nr, nc, opp_stones)
                # Temporarily remove captured liberties
                temp_liberties = set(opp_liberties)
                if (r, c) in temp_liberties:
                    temp_liberties.remove((r, c))
                # Also remove if any own stones are captured
                all_occupied = all_stones | {(r, c)}
                for gr, gc in opp_group:
                    for gnr, gnc in neighbors(gr, gc):
                        if is_on_board(gnr, gnc) and (gnr, gnc) not in all_occupied:
                            temp_liberties.add((gnr, gnc))
                if len(temp_liberties) == 0:
                    captures.extend(opp_group)
        return list(set(captures))  # deduplicate

    # Helper: check if a move is suicidal
    def is_suicidal(r: int, c: int) -> bool:
        if (r, c) in all_stones:
            return True
        my_new_stones = my_stones | {(r, c)}
        _, my_liberties = find_group_and_liberties(r, c, my_new_stones)
        if len(my_liberties) == 0:
            return True
        return False

    # Check for any immediate capture moves
    candidates = []
    for r in range(1, N+1):
        for c in range(1, N+1):
            if (r, c) in all_stones:
                continue
            captures = would_capture(r, c)
            if captures:
                # This move captures at least one stone
                # Prefer more captures or critical captures
                candidates.append((len(captures), 0, r, c))  # (capture count, priority, r, c)

    if candidates:
        # Sort by capture size descending
        candidates.sort(reverse=True)
        return candidates[0][2], candidates[0][3]

    # Check for moves that prevent opponent capture (defend)
    # Look for own groups in atari (1 liberty) and try to save them
    defense_moves = []
    for stone in my_stones:
        group, liberties = find_group_and_liberties(stone[0], stone[1], my_stones)
        if len(liberties) == 1:
            # Group is in atari, try to add liberty
            lib_r, lib_c = next(iter(liberties))
            if not is_suicidal(lib_r, lib_c):
                defense_moves.append((lib_r, lib_c))

    if defense_moves:
        # Return the first defense move
        # Could prioritize but returning first for speed
        return defense_moves[0]

    # Look for good shape and territory moves
    # Prefer corners (3-4, 4-4), then sides, then center
    # Use a heuristic score map
    score_map = np.zeros((N+1, N+1))  # 1-indexed

    # Base position values: corners and sides favored early
    for r in range(1, N+1):
        for c in range(1, N+1):
            if (r, c) in all_stones:
                continue
            # Distance to center
            dist_to_center = abs(r - 10) + abs(c - 10)
            # Prefer 3-4, 4-4 points
            if (r in [4, 16] and c in [4, 16]) or (r in [4, 16] and c in [3, 17]) or (r in [3, 17] and c in [4, 16]):
                score_map[r][c] += 5
            # Edges
            if r in [4, 16] or c in [4, 16] or r in [3, 17] or c in [3, 17]:
                score_map[r][c] += 2
            # Center
            if 7 <= r <= 13 and 7 <= c <= 13:
                score_map[r][c] += 1

    # Bonus for creating eyes or connections
    for r in range(1, N+1):
        for c in range(1, N+1):
            if (r, c) in all_stones or is_suicidal(r, c):
                continue
            # Count adjacent own stones
            adj_own = 0
            adj_opp = 0
            for nr, nc in neighbors(r, c):
                if (nr, nc) in my_stones:
                    adj_own += 1
                if (nr, nc) in opp_stones:
                    adj_opp += 1
            # Connect to self
            if adj_own >= 1:
                score_map[r][c] += 3
            # Avoid crowding opponent unless for capture (but captures already handled)
            if adj_opp >= 3:
                score_map[r][c] -= 2  # danger zone
            # Add liberty to own group
            for nr, nc in neighbors(r, c):
                if (nr, nc) in my_stones:
                    _, libs = find_group_and_liberties(nr, nc, my_stones)
                    if len(libs) <= 2 and (r, c) in libs:
                        score_map[r][c] += 4  # urgent extension

    # Avoid self-atari
    for r in range(1, N+1):
        for c in range(1, N+1):
            if (r, c) in all_stones:
                continue
            if is_suicidal(r, c):
                score_map[r][c] = -1000

    # Avoid immediate loss of liberty
    flat_scores = []
    for r in range(1, N+1):
        for c in range(1, N+1):
            if (r, c) in all_stones:
                continue
            if score_map[r][c] > -1000:
                flat_scores.append((score_map[r][c], r, c))

    if flat_scores:
        flat_scores.sort(reverse=True)
        return flat_scores[0][1], flat_scores[0][2]

    # If no good move, pass
    return (0, 0)
