
import numpy as np
from typing import List, Tuple, Set, Dict, Optional
from collections import deque, defaultdict

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    A smart Battleship targeting policy that combines:
    - Probability-based targeting using ship placement likelihoods
    - Hit-following logic when a ship is hit
    - Pattern optimization to cover the board efficiently
    
    Args:
        board: 10x10 grid where:
            0 = unknown/unfired
            -1 = miss
            1 = hit
    
    Returns:
        (row, col) coordinates to fire next
    """
    grid = np.array(board)
    n = 10
    ships = [5, 4, 3, 3, 2]  # Ship lengths to find
    
    # Find all valid positions for a ship of given length
    def count_valid_placements(length: int, row: int, col: int) -> int:
        """Count how many ways a ship of given length can be placed covering (row,col)"""
        count = 0
        
        # Horizontal placements
        for c in range(col - length + 1, col + 1):
            if c >= 0 and c + length <= n:
                valid = True
                for i in range(length):
                    r, c_pos = row, c + i
                    if grid[r, c_pos] == -1:  # Miss
                        valid = False
                        break
                    if grid[r, c_pos] == 1 and not (c <= col <= c + length - 1):
                        valid = False
                        break
                if valid:
                    count += 1
        
        # Vertical placements
        for r in range(row - length + 1, row + 1):
            if r >= 0 and r + length <= n:
                valid = True
                for i in range(length):
                    r_pos, c = r + i, col
                    if grid[r_pos, c] == -1:  # Miss
                        valid = False
                        break
                    if grid[r_pos, c] == 1 and not (r <= row <= r + length - 1):
                        valid = False
                        break
                if valid:
                    count += 1
        
        return count
    
    # Check if a cell is part of a known hit chain
    def get_hit_neighbors(row: int, col: int) -> List[Tuple[int, int, int]]:
        """Get neighboring hit cells with direction information"""
        neighbors = []
        for dr, dc, direction in [(-1, 0, 'up'), (1, 0, 'down'), (0, -1, 'left'), (0, 1, 'right')]:
            r, c = row + dr, col + dc
            if 0 <= r < n and 0 <= c < n and grid[r, c] == 1:
                neighbors.append((r, c, direction))
        return neighbors
    
    # Find all connected hit components
    def find_hit_clusters() -> List[List[Tuple[int, int]]]:
        """Find groups of adjacent hit cells"""
        visited = set()
        clusters = []
        
        for i in range(n):
            for j in range(n):
                if grid[i, j] == 1 and (i, j) not in visited:
                    # BFS to find connected component
                    cluster = []
                    queue = deque([(i, j)])
                    visited.add((i, j))
                    
                    while queue:
                        r, c = queue.popleft()
                        cluster.append((r, c))
                        
                        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                            nr, nc = r + dr, c + dc
                            if (0 <= nr < n and 0 <= nc < n and 
                                grid[nr, nc] == 1 and (nr, nc) not in visited):
                                visited.add((nr, nc))
                                queue.append((nr, nc))
                    
                    clusters.append(cluster)
        
        return clusters
    
    # Get possible extensions of a hit cluster
    def get_cluster_extensions(cluster: List[Tuple[int, int]]) -> List[Tuple[int, int, int]]:
        """Find possible directions to extend a cluster and their likelihood"""
        if not cluster:
            return []
        
        # Find bounding box of cluster
        rows, cols = zip(*cluster)
        min_r, max_r = min(rows), max(rows)
        min_c, max_c = min(cols), max(cols)
        
        extensions = []
        
        # Try extending in possible directions
        if min_r == max_r:  # Horizontal alignment
            # Try left
            if min_c > 0 and grid[min_r, min_c - 1] == 0:
                extensions.append((min_r, min_c - 1, abs(max_c - min_c) + 2))
            # Try right
            if max_c < n - 1 and grid[min_r, max_c + 1] == 0:
                extensions.append((min_r, max_c + 1, abs(max_c - min_c) + 2))
        elif min_c == max_c:  # Vertical alignment
            # Try up
            if min_r > 0 and grid[min_r - 1, min_c] == 0:
                extensions.append((min_r - 1, min_c, abs(max_r - min_r) + 2))
            # Try down
            if max_r < n - 1 and grid[max_r + 1, min_c] == 0:
                extensions.append((max_r + 1, min_c, abs(max_r - min_r) + 2))
        
        return extensions
    
    # Check if a cell has been fired upon
    def is_unfired(row: int, col: int) -> bool:
        return grid[row, col] == 0
    
    # Main logic
    hit_clusters = find_hit_clusters()
    
    # Strategy 1: If we have hit clusters, try to extend them
    if hit_clusters:
        # Sort clusters by size (largest first)
        hit_clusters.sort(key=len, reverse=True)
        
        for cluster in hit_clusters:
            extensions = get_cluster_extensions(cluster)
            if extensions:
                # Prefer extending shorter ships first (they're easier to sink)
                extensions.sort(key=lambda x: x[2])  # Sort by required ship length
                for r, c, _ in extensions:
                    if is_unfired(r, c):
                        return (r, c)
    
    # Strategy 2: Use probability-based targeting
    prob_grid = np.zeros((n, n))
    
    for r in range(n):
        for c in range(n):
            if grid[r, c] == 0:  # Only consider unfired cells
                total_prob = 0
                for ship_len in ships:
                    placements = count_valid_placements(ship_len, r, c)
                    total_prob += placements
                prob_grid[r, c] = total_prob
    
    # Apply checkerboard pattern bias to unfired cells (avoid firing on cells 
    # that are all the same color in a checkerboard, since ships of length >= 2 
    # must span both colors)
    for r in range(n):
        for c in range(n):
            if grid[r, c] == 0:
                # Cells where (r+c) % 2 == 0 are one color in checkerboard
                # Prefer these initially, but don't ignore the others
                if (r + c) % 2 == 0:
                    prob_grid[r, c] *= 1.2
    
    # Find highest probability unfired cell
    unfired_mask = (grid == 0)
    if np.any(unfired_mask):
        candidate_probs = prob_grid * unfired_mask
        max_prob = np.max(candidate_probs)
        
        if max_prob > 0:
            # Find all cells with max probability
            max_cells = np.where(candidate_probs == max_prob)
            candidates = list(zip(max_cells[0], max_cells[1]))
            
            # If multiple cells have same probability, apply additional heuristics
            if len(candidates) > 1:
                # Prefer cells closer to center (higher probability of ship placement)
                center_score = lambda r, c: 1.0 / (1 + (r - 4.5)**2 + (c - 4.5)**2)
                scores = [(center_score(r, c), r, c) for r, c in candidates]
                scores.sort(reverse=True)
                return (scores[0][1], scores[0][2])
            else:
                return (candidates[0][0], candidates[0][1])
    
    # Fallback: Find any unfired cell (should not reach here in normal gameplay)
    for r in range(n):
        for c in range(n):
            if grid[r, c] == 0:
                return (r, c)
    
    # Last resort (should never happen)
    return (0, 0)
