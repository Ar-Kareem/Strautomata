
import numpy as np
from collections import deque

# Hexagonal directions (6 neighbors)
HEX_DIRECTIONS = [
    (-1, 0), (0, -1), (0, 1), (1, 0), (-1, 1), (1, -1)
]

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    board_size = len(valid_mask)
    me_set = set(me)
    opp_set = set(opp)
    empty_cells = [(r, c) for r in range(board_size) for c in range(board_size)
                  if valid_mask[r][c] and (r, c) not in me_set and (r, c) not in opp_set]

    # Check for immediate winning moves
    for move in empty_cells:
        if is_winning_move(move, me_set, opp_set, board_size):
            return move

    # Check for opponent winning moves to block
    for move in empty_cells:
        if is_winning_move(move, opp_set, me_set, board_size):
            return move

    # Evaluate all possible moves with scoring
    best_move = None
    best_score = -float('inf')

    for move in empty_cells:
        score = evaluate_move(move, me_set, opp_set, board_size)
        if score > best_score:
            best_score = score
            best_move = move

    return best_move

def is_winning_move(move, player_stones, opponent_stones, board_size):
    """Check if placing a stone at move creates a winning condition."""
    new_stones = player_stones | {move}

    # Check for ring
    if has_ring(new_stones, board_size):
        return True

    # Check for bridge
    if has_bridge(new_stones, board_size):
        return True

    # Check for fork
    if has_fork(new_stones, board_size):
        return True

    return False

def has_ring(stones, board_size):
    """Check if stones form a ring (loop)."""
    if len(stones) < 6:  # Minimum stones needed for a ring
        return False

    # Use BFS to find cycles
    visited = set()
    for stone in stones:
        if stone not in visited:
            parent = {stone: None}
            queue = deque([stone])
            visited.add(stone)

            while queue:
                current = queue.popleft()
                for dr, dc in HEX_DIRECTIONS:
                    neighbor = (current[0] + dr, current[1] + dc)
                    if neighbor in stones and neighbor not in visited:
                        visited.add(neighbor)
                        parent[neighbor] = current
                        queue.append(neighbor)
                    elif neighbor in stones and neighbor != parent.get(current, None):
                        # Found a cycle
                        return True
    return False

def has_bridge(stones, board_size):
    """Check if stones connect two corners."""
    corners = [(0, 0), (0, board_size-1), (board_size-1, 0), (board_size-1, board_size-1)]
    corner_pairs = [
        (corners[0], corners[1]),
        (corners[0], corners[2]),
        (corners[0], corners[3]),
        (corners[1], corners[2]),
        (corners[1], corners[3]),
        (corners[2], corners[3])
    ]

    for corner1, corner2 in corner_pairs:
        if is_connected(corner1, corner2, stones):
            return True
    return False

def has_fork(stones, board_size):
    """Check if stones connect three edges."""
    # Define edge groups (each edge is a set of cells)
    top_edge = [(0, c) for c in range(1, board_size-1)]
    bottom_edge = [(board_size-1, c) for c in range(1, board_size-1)]
    left_edge = [(r, 0) for r in range(1, board_size-1)]
    right_edge = [(r, board_size-1) for r in range(1, board_size-1)]
    top_left_edge = [(r, board_size-1 - r) for r in range(1, board_size-1)]
    bottom_right_edge = [(r, r) for r in range(1, board_size-1)]

    edge_groups = [
        top_edge, bottom_edge, left_edge,
        right_edge, top_left_edge, bottom_right_edge
    ]

    # Check all combinations of 3 edges
    from itertools import combinations
    for edges in combinations(edge_groups, 3):
        connected = True
        for i in range(3):
            for j in range(i+1, 3):
                if not any(is_connected(e1, e2, stones) for e1 in edges[i] for e2 in edges[j]):
                    connected = False
                    break
            if not connected:
                break
        if connected:
            return True
    return False

def is_connected(start, end, stones):
    """Check if there's a path between start and end through stones."""
    if start not in stones or end not in stones:
        return False

    visited = set()
    queue = deque([start])
    visited.add(start)

    while queue:
        current = queue.popleft()
        if current == end:
            return True

        for dr, dc in HEX_DIRECTIONS:
            neighbor = (current[0] + dr, current[1] + dc)
            if neighbor in stones and neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)

    return False

def evaluate_move(move, me_stones, opp_stones, board_size):
    """Evaluate a potential move with various strategic considerations."""
    score = 0
    r, c = move

    # 1. Proximity to corners (good for bridges)
    corners = [(0, 0), (0, board_size-1), (board_size-1, 0), (board_size-1, board_size-1)]
    min_corner_dist = min(abs(r - cr) + abs(c - cc) for cr, cc in corners)
    score += (board_size - min_corner_dist) * 0.5

    # 2. Proximity to edges (good for forks)
    edge_dist = min(r, c, board_size-1 - r, board_size-1 - c)
    score += (board_size - edge_dist) * 0.3

    # 3. Central control (good for rings)
    center_dist = abs(r - board_size/2) + abs(c - board_size/2)
    score += (board_size - center_dist) * 0.2

    # 4. Connectivity to existing stones
    connected_to_me = 0
    connected_to_opp = 0
    for dr, dc in HEX_DIRECTIONS:
        neighbor = (r + dr, c + dc)
        if neighbor in me_stones:
            connected_to_me += 1
        elif neighbor in opp_stones:
            connected_to_opp += 1

    score += connected_to_me * 2
    score -= connected_to_opp * 1.5

    # 5. Potential to create multiple connections
    # Count how many of my stones are reachable from this move
    temp_stones = me_stones | {move}
    reachable = set()
    queue = deque([move])
    reachable.add(move)

    while queue:
        current = queue.popleft()
        for dr, dc in HEX_DIRECTIONS:
            neighbor = (current[0] + dr, current[1] + dc)
            if neighbor in temp_stones and neighbor not in reachable:
                reachable.add(neighbor)
                queue.append(neighbor)

    score += len(reachable) * 0.1

    # 6. Blocking opponent's potential connections
    temp_opp = opp_stones | {move}
    opp_reachable = set()
    for opp_stone in opp_stones:
        if opp_stone not in opp_reachable:
            queue = deque([opp_stone])
            opp_reachable.add(opp_stone)
            while queue:
                current = queue.popleft()
                for dr, dc in HEX_DIRECTIONS:
                    neighbor = (current[0] + dr, current[1] + dc)
                    if neighbor in temp_opp and neighbor not in opp_reachable:
                        opp_reachable.add(neighbor)
                        queue.append(neighbor)

    # Penalize moves that help opponent connect more stones
    score -= len(opp_reachable) * 0.05

    return score
