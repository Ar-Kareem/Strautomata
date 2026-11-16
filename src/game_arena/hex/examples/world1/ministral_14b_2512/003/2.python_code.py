
import numpy as np
from collections import defaultdict

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    # Convert to sets for faster lookups
    my_stones = set(me)
    opp_stones = set(opp)

    # Determine the target sides for me and opponent
    if color == 'b':
        my_target = [(0, j) for j in range(11)]  # Top row
        opp_target = [(10, j) for j in range(11)]  # Bottom row
    else:  # 'w'
        my_target = [(i, 0) for i in range(11)]  # Left column
        opp_target = [(i, 10) for i in range(11)]  # Right column

    # Check if opponent has a winning move (block immediately)
    if has_winning_move(opp_stones, opp_target):
        return block_opponent_win(my_stones, opp_stones, opp_target)

    # Check if I have a winning move (play it)
    if has_winning_move(my_stones, my_target):
        return find_winning_move(my_stones, my_target)

    # If no immediate threats, play a smart move
    return smart_move(my_stones, opp_stones, color)

def has_winning_move(stones: set, target: list) -> bool:
    """Check if the given stones already connect the target sides."""
    # Build adjacency graph
    graph = defaultdict(set)
    for (i, j) in stones:
        neighbors = get_neighbors(i, j)
        for ni, nj in neighbors:
            if (ni, nj) in stones:
                graph[(i, j)].add((ni, nj))
                graph[(ni, nj)].add((i, j))

    # Check if any target is connected to another target via BFS
    visited = set()
    queue = []
    # Start from all targets
    for target_pos in target:
        if target_pos in stones and target_pos not in visited:
            queue.append(target_pos)
            visited.add(target_pos)
            while queue:
                (i, j) = queue.pop(0)
                for (ni, nj) in graph[(i, j)]:
                    if (ni, nj) not in visited:
                        visited.add((ni, nj))
                        queue.append((ni, nj))
                        # Check if this connects to another target
                        if (ni, nj) in target and (ni, nj) != target_pos:
                            return True
    return False

def find_winning_move(stones: set, target: list) -> tuple[int, int]:
    """Find a move that completes a winning path."""
    # Try all empty cells and check if placing there completes a win
    for i in range(11):
        for j in range(11):
            if (i, j) not in stones:
                temp_stones = stones.copy()
                temp_stones.add((i, j))
                if has_winning_move(temp_stones, target):
                    return (i, j)
    return (5, 5)  # Fallback (should not reach here if has_winning_move is correct)

def block_opponent_win(my_stones: set, opp_stones: set, opp_target: list) -> tuple[int, int]:
    """Find the move that blocks the opponent's winning path."""
    # Try all empty cells and check if placing there prevents the opponent's win
    for i in range(11):
        for j in range(11):
            if (i, j) not in my_stones and (i, j) not in opp_stones:
                temp_opp = opp_stones.copy()
                temp_opp.add((i, j))
                if not has_winning_move(temp_opp, opp_target):
                    return (i, j)
    return (5, 5)  # Fallback (should not reach here if opponent has a win)

def smart_move(my_stones: set, opp_stones: set, color: str) -> tuple[int, int]:
    """Play a smart move if no immediate threats exist."""
    # Prioritize moves that create double threats or disrupt opponent
    for i in range(11):
        for j in range(11):
            if (i, j) not in my_stones and (i, j) not in opp_stones:
                # Check if this move creates a double threat
                if creates_double_threat(my_stones, opp_stones, (i, j), color):
                    return (i, j)

    # If no double threats, prioritize center control
    if color == 'b':
        # Black prioritizes top and bottom
        return prioritize_move(my_stones, opp_stones, [(0, j) for j in range(11)], [(10, j) for j in range(11)])
    else:
        # White prioritizes left and right
        return prioritize_move(my_stones, opp_stones, [(i, 0) for i in range(11)], [(i, 10) for i in range(11)])

def creates_double_threat(my_stones: set, opp_stones: set, move: tuple[int, int], color: str) -> bool:
    """Check if placing a stone at 'move' creates two potential winning paths."""
    temp_my = my_stones.copy()
    temp_my.add(move)
    if color == 'b':
        my_target = [(0, j) for j in range(11)]
    else:
        my_target = [(i, 0) for i in range(11)]

    # Check if this move creates two separate paths to the target
    # (Simplified: if removing any neighbor breaks the path, it's a double threat)
    neighbors = get_neighbors(*move)
    for neighbor in neighbors:
        if neighbor in temp_my:
            temp_my.remove(neighbor)
            if not has_winning_move(temp_my, my_target):
                temp_my.add(neighbor)
                return True
            temp_my.add(neighbor)
    return False

def prioritize_move(my_stones: set, opp_stones: set, my_target: list, opp_target: list) -> tuple[int, int]:
    """Prioritize moves based on distance to targets and opponent's stones."""
    # Score each empty cell based on:
    # 1. Distance to my target (closer is better)
    # 2. Distance to opponent's target (farther is better)
    # 3. Avoiding opponent's stones
    scores = []
    for i in range(11):
        for j in range(11):
            if (i, j) not in my_stones and (i, j) not in opp_stones:
                # Distance to my target (min distance to any target)
                my_dist = min(manhattan_distance((i, j), target) for target in my_target)
                # Distance to opponent's target (max distance to any target)
                opp_dist = max(manhattan_distance((i, j), target) for target in opp_target)
                # Avoid opponent's stones (penalize if adjacent)
                opp_adj = sum(1 for neighbor in get_neighbors(i, j) if neighbor in opp_stones)
                # Score = (10 - my_dist) + opp_dist - opp_adj
                score = (10 - my_dist) + opp_dist - opp_adj
                scores.append((score, (i, j)))

    # Sort by score (descending) and pick the best
    scores.sort(reverse=True, key=lambda x: x[0])
    return scores[0][1]

def get_neighbors(i: int, j: int) -> list[tuple[int, int]]:
    """Get all 6 neighbors of a hexagonal cell (i, j)."""
    neighbors = []
    # Same row
    if j > 0:
        neighbors.append((i, j - 1))
    if j < 10:
        neighbors.append((i, j + 1))
    # Top row (odd columns)
    if i > 0:
        if j % 2 == 0:
            neighbors.append((i - 1, j))
            neighbors.append((i - 1, j + 1))
        else:
            neighbors.append((i - 1, j - 1))
            neighbors.append((i - 1, j))
    # Bottom row (even columns)
    if i < 10:
        if j % 2 == 0:
            neighbors.append((i + 1, j - 1))
            neighbors.append((i + 1, j))
        else:
            neighbors.append((i + 1, j))
            neighbors.append((i + 1, j + 1))
    return neighbors

def manhattan_distance(a: tuple[int, int], b: tuple[int, int]) -> int:
    """Hexagonal distance (simplified for this problem)."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])
