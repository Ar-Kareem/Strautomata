
import numpy as np
from typing import List, Tuple, Set, Optional
from collections import deque

def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str) -> Tuple[int, int]:
    # Convert to sets for O(1) lookup
    my_stones = set(me)
    opp_stones = set(opp)
    all_stones = my_stones | opp_stones

    # All board positions
    board_size = 11
    all_positions = [(i, j) for i in range(board_size) for j in range(board_size)]
    empty_cells = [pos for pos in all_positions if pos not in all_stones]

    # If no moves made yet, take center for advantage
    if len(my_stones) == 0 and len(opp_stones) == 0:
        return (5, 5)

    # Precompute neighbor function
    def get_neighbors(pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        i, j = pos
        # All 6 hex neighbors
        directions = [
            (0, -1), (0, 1),           # left, right
            (-1, 0), (-1, 1),          # up-left, up-right
            (1, -1), (1, 0)            # down-left, down-right
        ]
        neighbors = []
        for di, dj in directions:
            ni, nj = i + di, j + dj
            if 0 <= ni < board_size and 0 <= nj < board_size:
                neighbors.append((ni, nj))
        return neighbors

    # BFS to check if there is a path from any cell in start_set to any cell in target_set
    def is_connected(start_set: Set[Tuple[int, int]], target_set: Set[Tuple[int, int]], player_stones: Set[Tuple[int, int]]) -> bool:
        visited = set()
        queue = deque(start_set)
        visited.update(start_set)

        while queue:
            pos = queue.popleft()
            for neighbor in get_neighbors(pos):
                if neighbor in visited or neighbor not in player_stones:
                    continue
                if neighbor in target_set:
                    return True
                visited.add(neighbor)
                queue.append(neighbor)
        return False

    # Get my goal edges
    if color == 'b':  # black: connect top (row 0) to bottom (row 10)
        my_start = {(0, j) for j in range(board_size)} & my_stones
        my_target = {(10, j) for j in range(board_size)} & my_stones
        my_progressive_axis = 0  # row is the key axis
    else:  # white: connect left (col 0) to right (col 10)
        my_start = {(i, 0) for i in range(board_size)} & my_stones
        my_target = {(i, 10) for i in range(board_size)} & my_stones
        my_progressive_axis = 1  # col is the key axis

    # Check if I've already won — though not needed since it's our move
    # But more importantly: check if opponent is one move away from winning
    opp_color = 'w' if color == 'b' else 'b'
    if opp_color == 'b':
        opp_start = {(0, j) for j in range(board_size)} & opp_stones
        opp_target = {(10, j) for j in range(board_size)} & opp_stones
    else:
        opp_start = {(i, 0) for i in range(board_size)} & opp_stones
        opp_target = {(i, 10) for i in range(board_size)} & opp_stones

    # Helper: evaluate how close a player is to connecting
    def evaluate_progress(player_stones: Set[Tuple[int, int]], start_set: Set[Tuple[int, int]], target_set: Set[Tuple[int, int]]) -> int:
        if not start_set or not target_set:
            return 0
        visited = set()
        queue = deque((pos, 0) for pos in start_set)
        visited.update(start_set)
        min_distance = float('inf')

        while queue:
            pos, dist = queue.popleft()
            for neighbor in get_neighbors(pos):
                if neighbor in visited or neighbor not in player_stones:
                    continue
                new_dist = dist + 1
                if neighbor in target_set:
                    min_distance = min(min_distance, new_dist)
                visited.add(neighbor)
                queue.append((neighbor, new_dist))

        return -min_distance if min_distance != float('inf') else 0

    # Score a move by simulating it
    def score_move(move: Tuple[int, int]) -> float:
        score = 0.0

        # Feature 1: Distance to center (favor center early)
        i, j = move
        center_distance = abs(i - 5) + abs(j - 5)
        score -= center_distance * 0.01  # slight penalty for being far

        # Feature 2: Number of my adjacent stones (connectivity)
        my_adj = 0
        opp_adj = 0
        for nb in get_neighbors(move):
            if nb in my_stones:
                my_adj += 1
            elif nb in opp_stones:
                opp_adj += 1
        score += my_adj * 2.0
        score -= opp_adj * 1.5  # penalty for being surrounded by opponent

        # Feature 3: Simulate move and check progress toward goal
        temp_my_stones = my_stones | {move}
        if color == 'b':
            new_start = my_start | ({move} if move[0] == 0 else set())
            new_target = my_target | ({move} if move[0] == 10 else set())
        else:
            new_start = my_start | ({move} if move[1] == 0 else set())
            new_target = my_target | ({move} if move[1] == 10 else set())

        progress = evaluate_progress(temp_my_stones, new_start, new_target)
        if progress < 0:
            score -= progress  # higher progress = lower distance = better

        # Feature 4: Block opponent
        temp_opp_stones = opp_stones | {move}
        opp_progress = evaluate_progress(temp_opp_stones, opp_start, opp_target)
        if opp_progress < 0:
            # If placing here prevents opponent progress, reward it
            score -= opp_progress * 1.2  # block more aggressively

        # Feature 5: Create bridges or forking positions
        # Reward moves that have potential to connect multiple paths
        # Look for "diamond" or "bridge" patterns
        for nb in get_neighbors(move):
            if nb in my_stones:
                # Check for extended connection opportunities
                for nb2 in get_neighbors(nb):
                    if nb2 != move and nb2 in my_stones:
                        # move can potentially connect two of my groups
                        score += 1.0

        return score

    # Critical: First, check if opponent is one move away from winning
    best_urgency_move = None
    highest_blocking_score = -float('inf')
    for cell in empty_cells:
        temp_opp_stones = opp_stones | {cell}
        if is_connected(opp_start, opp_target, temp_opp_stones):
            # This move wins for opponent — must block!
            return cell

    # Also, check if we can win now
    for cell in empty_cells:
        temp_my_stones = my_stones | {cell}
        temp_start = my_start | ({cell} if (color == 'b' and cell[0] == 0) or (color == 'w' and cell[1] == 0) else set())
        temp_target = my_target | ({cell} if (color == 'b' and cell[0] == 10) or (color == 'w' and cell[1] == 10) else set())
        if is_connected(temp_start, temp_target, temp_my_stones):
            return cell

    # Otherwise, score all legal moves and pick best
    move_scores = []
    for cell in empty_cells:
        score = score_move(cell)
        move_scores.append((score, cell))

    move_scores.sort(reverse=True)
    best_move = move_scores[0][1]

    # Final fallback
    if best_move is None or best_move in all_stones:
        best_move = empty_cells[0]

    return best_move
