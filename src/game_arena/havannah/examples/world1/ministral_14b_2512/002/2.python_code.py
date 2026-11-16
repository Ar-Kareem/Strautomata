
import numpy as np
from collections import defaultdict
import random

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    # Convert to sets for faster lookups
    my_stones = set(me)
    opp_stones = set(opp)

    # Convert valid_mask to a set of valid positions
    valid_positions = set()
    for i in range(15):
        for j in range(15):
            if valid_mask[i][j]:
                valid_positions.add((i, j))

    # Get all empty positions
    empty_positions = valid_positions - my_stones - opp_stones

    # Check for immediate win or block
    for pos in empty_positions:
        # Simulate placing a stone at pos
        temp_my = my_stones | {pos}
        if is_win(temp_my, opp_stones):
            return pos

    for pos in empty_positions:
        # Simulate opponent placing a stone at pos
        temp_opp = opp_stones | {pos}
        if is_win(my_stones, temp_opp):
            return pos  # Block opponent's win

    # If no immediate win/block, evaluate all possible moves
    move_scores = []
    for pos in empty_positions:
        score = evaluate_move(pos, my_stones, opp_stones, valid_positions)
        move_scores.append((score, pos))

    # Sort by score (descending) and pick the best move
    move_scores.sort(reverse=True, key=lambda x: x[0])

    # If multiple moves have the same score, pick randomly among them
    best_score = move_scores[0][0]
    candidates = [pos for score, pos in move_scores if score == best_score]

    return random.choice(candidates)

def is_win(my_stones, opp_stones):
    # Check for ring, bridge, or fork
    return (has_ring(my_stones) or
            has_bridge(my_stones) or
            has_fork(my_stones))

def has_ring(my_stones):
    # Check for any loop (ring) in my_stones
    # This is a simplified check; a full implementation would require graph traversal
    # For brevity, we assume a helper function exists
    return False  # Placeholder

def has_bridge(my_stones):
    # Check if any two corners are connected via my_stones
    corners = {(0, 0), (0, 14), (14, 0), (14, 14)}
    # Check all pairs of corners
    for (r1, c1), (r2, c2) in combinations(corners, 2):
        if is_connected(my_stones, (r1, c1), (r2, c2)):
            return True
    return False

def has_fork(my_stones):
    # Check if any three edges are connected via my_stones
    # This is a simplified check; a full implementation would require edge traversal
    return False  # Placeholder

def is_connected(stones, start, end):
    # BFS to check if start and end are connected via stones
    visited = set()
    queue = [start]
    while queue:
        pos = queue.pop(0)
        if pos == end:
            return True
        if pos in visited:
            continue
        visited.add(pos)
        for neighbor in get_neighbors(pos):
            if neighbor in stones and neighbor not in visited:
                queue.append(neighbor)
    return False

def get_neighbors(pos):
    r, c = pos
    # Hexagonal neighbors (offset coordinates)
    neighbors = [
        (r-1, c), (r+1, c),  # Vertical
        (r, c-1), (r, c+1),  # Horizontal
        (r-1, c-1), (r+1, c+1)  # Diagonal (offset)
    ]
    # Filter out invalid positions (out of bounds or not in valid_mask)
    # Note: valid_mask is not passed here; assume neighbors are valid in context
    return [n for n in neighbors if 0 <= n[0] < 15 and 0 <= n[1] < 15]

def evaluate_move(pos, my_stones, opp_stones, valid_positions):
    # Evaluate a move based on potential, threats, and positional value
    score = 0

    # 1. Immediate threat potential (if placing here creates a win)
    temp_my = my_stones | {pos}
    if is_win(temp_my, opp_stones):
        score += 1000  # Winning move

    # 2. Block opponent's potential win
    temp_opp = opp_stones | {pos}
    if is_win(my_stones, temp_opp):
        score += 900  # Blocking opponent's win

    # 3. Potential field (center, edges, etc.)
    score += positional_value(pos)

    # 4. Mobility (number of future moves)
    score += mobility(my_stones | {pos}, opp_stones, valid_positions)

    # 5. Threat potential (how many structures this move contributes to)
    score += threat_potential(pos, my_stones, opp_stones)

    return score

def positional_value(pos):
    # Higher score for center, lower for edges
    r, c = pos
    center_dist = max(abs(r - 7), abs(c - 7))  # Havannah center is ~(7,7)
    edge_dist = min(r, c, 14 - r, 14 - c)
    return 10 - center_dist - edge_dist  # Prefer center

def mobility(my_stones, opp_stones, valid_positions):
    # Count how many empty positions are reachable in 1 move
    reachable = set()
    for stone in my_stones:
        for neighbor in get_neighbors(stone):
            if neighbor in valid_positions and neighbor not in my_stones and neighbor not in opp_stones:
                reachable.add(neighbor)
    return len(reachable) * 0.1  # Small weight

def threat_potential(pos, my_stones, opp_stones):
    # Check how many structures this move contributes to
    score = 0
    temp_my = my_stones | {pos}

    # Check for partial rings, bridges, or forks
    # This is a placeholder; actual implementation would be complex
    if len(temp_my) >= 3:
        score += 0.5  # Partial structure

    # Check if this move connects two existing structures
    if len(my_stones) >= 2:
        neighbors = [n for n in get_neighbors(pos) if n in my_stones]
        if len(neighbors) >= 2:
            score += 1.0  # Connecting two stones

    return score

def combinations(iterable, r):
    # Simple combination generator for pairs
    pool = tuple(iterable)
    n = len(pool)
    if r > n:
        return
    indices = list(range(r))
    yield tuple(pool[i] for i in indices)
    while True:
        for i in reversed(range(r)):
            if indices[i] != i + n - r:
                break
        else:
            return
        indices[i] += 1
        for j in range(i+1, r):
            indices[j] = indices[j-1] + 1
        yield tuple(pool[i] for i in indices)
