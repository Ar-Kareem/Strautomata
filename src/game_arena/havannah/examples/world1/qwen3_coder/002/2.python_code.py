
import numpy as np
from collections import deque

# Board size
BOARD_SIZE = 15

# Hexagonal neighbors (in row,col format)
NEIGHBOR_DELTAS = [
    (-1, 0), (-1, 1), (0, -1), 
    (0, 1), (1, -1), (1, 0)
]

# Corner positions (0-indexed)
CORNERS = [(0, 0), (0, 14), (14, 0), (14, 14), (7, 0), (7, 14)]

# Edge positions (excluding corners)
EDGES = []
for i in range(1, BOARD_SIZE-1):
    EDGES.append((i, 0))
    EDGES.append((i, BOARD_SIZE-1))
    if i != 7:  # Skip corners
        EDGES.append((0, i))
        EDGES.append((BOARD_SIZE-1, i))

def get_neighbors(r, c):
    """Get valid neighbors of a hex cell."""
    neighbors = []
    for dr, dc in NEIGHBOR_DELTAS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
            neighbors.append((nr, nc))
    return neighbors

def bfs_connected_group(start_r, start_c, stones):
    """BFS to find all stones in the connected group."""
    visited = set()
    queue = deque([(start_r, start_c)])
    group = []
    
    while queue:
        r, c = queue.popleft()
        if (r, c) in visited:
            continue
        visited.add((r, c))
        group.append((r, c))
        
        for nr, nc in get_neighbors(r, c):
            if (nr, nc) in stones and (nr, nc) not in visited:
                queue.append((nr, nc))
    
    return group

def check_ring(stones, move):
    """Check if placing a stone at move creates a ring."""
    # Create a temporary set with the new move
    temp_stones = set(stones)
    temp_stones.add(move)
    
    # Find connected group containing the new move
    group = bfs_connected_group(move[0], move[1], temp_stones)
    
    # Check if any stone in the group has two non-adjacent neighbors in the same group
    for r, c in group:
        neighbors = get_neighbors(r, c)
        connected_neighbors = [n for n in neighbors if n in temp_stones]
        
        # A ring exists if there are at least 2 connected neighbors and they form a cycle
        if len(connected_neighbors) >= 2:
            # For a ring, there should be a path from one neighbor to another that doesn't go through (r,c)
            # Simplified check: see if removing the stone still keeps the neighbors connected
            temp_stones.remove((r, c))
            for i in range(len(connected_neighbors)):
                for j in range(i+1, len(connected_neighbors)):
                    # Check if these two neighbors are connected without going through (r,c)
                    if connected_without_intermediate(connected_neighbors[i], connected_neighbors[j], temp_stones, set()):
                        temp_stones.add((r, c))
                        return True
            temp_stones.add((r, c))
    
    return False

def connected_without_intermediate(start, end, stones, visited):
    """Check if start and end are connected without going through a specific intermediate point."""
    if start == end:
        return True
    if start in visited:
        return False
    visited.add(start)
    
    neighbors = get_neighbors(start[0], start[1])
    connected_neighbors = [n for n in neighbors if n in stones]
    
    for n in connected_neighbors:
        if connected_without_intermediate(n, end, stones, visited):
            return True
    return False

def check_bridge(stones, move):
    """Check if placing a stone at move creates a bridge (connects two corners)."""
    # Create a temporary set with the new move
    temp_stones = set(stones)
    temp_stones.add(move)
    
    # Find all connected groups
    visited = set()
    corner_groups = {}
    
    for corner in CORNERS:
        if corner in temp_stones and corner not in visited:
            group = bfs_connected_group(corner[0], corner[1], temp_stones)
            for pos in group:
                visited.add(pos)
                if pos in CORNERS:
                    if id(tuple(group)) not in corner_groups:
                        corner_groups[id(tuple(group))] = []
                    corner_groups[id(tuple(group))].append(pos)
    
    # Check if any group connects at least two corners
    for group_id, corners_in_group in corner_groups.items():
        if len(corners_in_group) >= 2:
            return True
    
    return False

def check_fork(stones, move):
    """Check if placing a stone at move creates a fork (connects three edges)."""
    # Create a temporary set with the new move
    temp_stones = set(stones)
    temp_stones.add(move)
    
    # Find all connected groups
    visited = set()
    edge_groups = {}
    
    for edge in EDGES:
        if edge in temp_stones and edge not in visited:
            group = bfs_connected_group(edge[0], edge[1], temp_stones)
            for pos in group:
                visited.add(pos)
                if pos in EDGES:
                    if id(tuple(group)) not in edge_groups:
                        edge_groups[id(tuple(group))] = set()
                    edge_groups[id(tuple(group))].add(pos)
    
    # Check if any group connects at least three edges
    for group_id, edges_in_group in edge_groups.items():
        if len(edges_in_group) >= 3:
            return True
    
    return False

def evaluate_move(move, me, opp, valid_mask):
    """Evaluate a move based on strategic importance."""
    score = 0
    r, c = move
    
    # Check for immediate win conditions
    if check_ring(me, move) or check_bridge(me, move) or check_fork(me, move):
        return 10000
    
    # Check for blocking opponent win
    if check_ring(opp, move) or check_bridge(opp, move) or check_fork(opp, move):
        score += 5000
    
    # Proximity to our existing stones
    for mr, mc in me:
        dist = abs(r - mr) + abs(c - mc)  # Manhattan distance
        if dist == 1:
            score += 100
        elif dist == 2:
            score += 50
    
    # Distance to corners (for bridge potential)
    min_corner_dist = min(abs(r - cr) + abs(c - cc) for cr, cc in CORNERS)
    score += (15 - min_corner_dist) * 2
    
    # Distance to edges (for fork potential)
    min_edge_dist = min(min(abs(r - er), abs(c - ec)) for er, ec in EDGES)
    score += (7 - min_edge_dist) * 3
    
    # Central positioning bonus
    center_r, center_c = BOARD_SIZE // 2, BOARD_SIZE // 2
    dist_to_center = abs(r - center_r) + abs(c - center_c)
    score += (15 - dist_to_center)
    
    return score

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    """Main policy function."""
    # Convert lists to sets for faster lookup
    me_set = set(me)
    opp_set = set(opp)
    
    # Get all valid moves
    valid_moves = [(r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE) if valid_mask[r][c]]
    
    # If no valid moves, return first valid position (should not happen per rules)
    if not valid_moves:
        return (0, 0)
    
    # Evaluate all valid moves
    best_move = valid_moves[0]
    best_score = -float('inf')
    
    for move in valid_moves:
        score = evaluate_move(move, me_set, opp_set, valid_mask)
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move
