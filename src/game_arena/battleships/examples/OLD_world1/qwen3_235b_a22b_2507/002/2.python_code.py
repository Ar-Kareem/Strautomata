
import numpy as np
from typing import List, Tuple, Set, Dict
from collections import deque, defaultdict

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Advanced Battleship targeting policy using probability-based search
    and pattern recognition for optimal shot selection.
    """
    board = np.array(board)
    n = 10
    
    # Track hit clusters for potential ship continuation
    hit_positions = []
    for i in range(n):
        for j in range(n):
            if board[i, j] == 1:
                hit_positions.append((i, j))
    
    # If we have hits but no ongoing ship pattern, try to extend
    if hit_positions:
        # Group nearby hits
        clusters = group_hits(hit_positions)
        
        # Try to extend existing clusters
        for cluster in clusters:
            if len(cluster) > 0:
                # Sort cluster to get most recent or strategic hits first
                sorted_cluster = sorted(cluster, key=lambda x: count_adjacent_hits(x, board), reverse=True)
                for hit_pos in sorted_cluster:
                    # Look for continuation in the four directions
                    for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                        if can_extend_ship(hit_pos, dr, dc, board):
                            return hit_pos[0] + dr, hit_pos[1] + dc
    
    # Use probability map for next shot when no obvious extension
    prob_map = compute_probability_map(board)
    
    # Exclude already fired positions
    for i in range(n):
        for j in range(n):
            if board[i, j] != 0:
                prob_map[i, j] = -1
    
    # Find highest probability cell
    max_prob = np.max(prob_map)
    candidates = np.where(prob_map == max_prob)
    
    # Break ties with a pattern (e.g. diagonal preference)
    if len(candidates[0]) > 1:
        # Prefer cells that are on a checkerboard pattern (odd+odd or even+even indices)
        parity_candidates = []
        for r, c in zip(candidates[0], candidates[1]):
            if (r + c) % 2 == 0:  # Prefer even-sum coordinates
                parity_candidates.append((r, c))
        
        if parity_candidates:
            r, c = parity_candidates[0]
            return int(r), int(c)
    
    # Otherwise just pick the first highest-probability cell
    r, c = candidates[0][0], candidates[1][0]
    return int(r), int(c)

def group_hits(hit_positions: List[Tuple[int, int]]) -> List[List[Tuple[int, int]]]:
    """Group nearby hits into clusters."""
    if not hit_positions:
        return []
    
    clusters = []
    visited = set()
    
    for pos in hit_positions:
        if pos in visited:
            continue
            
        # Start new cluster with BFS
        cluster = []
        queue = deque([pos])
        visited.add(pos)
        
        while queue:
            curr = queue.popleft()
            cluster.append(curr)
            
            # Check 4-directional neighbors
            for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nr, nc = curr[0] + dr, curr[1] + dc
                if (nr, nc) in hit_positions and (nr, nc) not in visited:
                    queue.append((nr, nc))
                    visited.add((nr, nc))
        
        clusters.append(cluster)
    
    return clusters

def count_adjacent_hits(pos: Tuple[int, int], board: np.ndarray) -> int:
    """Count how many adjacent cells have been hits."""
    count = 0
    r, c = pos
    for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 10 and 0 <= nc < 10 and board[nr, nc] == 1:
            count += 1
    return count

def can_extend_ship(pos: Tuple[int, int], dr: int, dc: int, board: np.ndarray) -> bool:
    """Check if we can extend a ship in a given direction."""
    r, c = pos
    nr, nc = r + dr, c + dc
    
    # Check bounds
    if not (0 <= nr < 10 and 0 <= nc < 10):
        return False
    
    # Must be unexplored
    if board[nr, nc] != 0:
        return False
    
    # Check if this extension could reasonably form a ship
    # Look for continuity - don't create isolated hits
    for dr2, dc2 in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
        if abs(dr2 - dr) > 1 or abs(dc2 - dc) > 1:  # Not the same direction
            nr2, nc2 = nr + dr2, nc + dc2
            if (0 <= nr2 < 10 and 0 <= nc2 < 10 and 
                board[nr2, nc2] == 1 and (nr2, nc2) != (r, c)):
                # Another hit in a conflicting direction suggests this might not be valid
                return False
    
    return True

def compute_probability_map(board: np.ndarray) -> np.ndarray:
    """Compute a probability map of where ships might be."""
    n = 10
    prob_map = np.zeros((n, n))
    
    # Ship lengths in the game
    ships = [5, 4, 3, 3, 2]
    
    # For each cell, count how many ways each ship can be placed covering that cell
    for i in range(n):
        for j in range(n):
            if board[i, j] != 0:  # Already fired here
                continue
                
            total_ways = 0
            
            for ship_len in ships:
                # Count horizontal placements
                for offset in range(ship_len):
                    start_j = j - offset
                    if start_j >= 0 and start_j + ship_len <= n:
                        valid = True
                        for k in range(ship_len):
                            if board[i, start_j + k] == -1:  # Miss
                                valid = False
                                break
                        if valid:
                            total_ways += 1
                
                # Count vertical placements
                for offset in range(ship_len):
                    start_i = i - offset
                    if start_i >= 0 and start_i + ship_len <= n:
                        valid = True
                        for k in range(ship_len):
                            if board[start_i + k, j] == -1:  # Miss
                                valid = False
                                break
                        if valid:
                            total_ways += 1
            
            prob_map[i, j] = total_ways
    
    return prob_map
