
import numpy as np
from itertools import product
from collections import defaultdict, deque
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    A Battleship targeting policy that combines:
    - Ship placement probability inference (enemy likely locations)
    - Weighted grid scoring based on hits/misses
    - Pattern-based targeting when hits are detected
    - Randomized selection with priority to high-probability cells
    """
    
    n = len(board)
    grid = np.array(board, dtype=int)
    
    # Ship sizes
    ship_sizes = [5, 4, 3, 3, 2]
    
    # Track hit clusters (connected hit cells)
    def get_clusters():
        visited = np.zeros((n, n), dtype=bool)
        clusters = []
        
        def dfs(r, c, cluster):
            visited[r, c] = True
            cluster.append((r, c))
            
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < n and 0 <= nc < n and not visited[nr, nc] and grid[nr, nc] == 1:
                    dfs(nr, nc, cluster)
        
        for i in range(n):
            for j in range(n):
                if grid[i, j] == 1 and not visited[i, j]:
                    cluster = []
                    dfs(i, j, cluster)
                    clusters.append(cluster)
        
        return clusters
    
    # Calculate probability map based on remaining ship placements
    def calculate_probabilities():
        prob = np.zeros((n, n), dtype=float)
        remaining_ships = ship_sizes[:]  # copy
        
        # Remove ships we've already sunk
        clusters = get_clusters()
        for cluster in clusters:
            if len(cluster) >= 2:
                # Estimate which ship this might be
                # For now, don't remove from remaining_ships
                pass
        
        for ship_len in remaining_ships:
            # Horizontal placements
            for r in range(n):
                for c in range(n - ship_len + 1):
                    valid = True
                    for k in range(ship_len):
                        if grid[r, c + k] == -1:  # miss
                            valid = False
                            break
                    if valid:
                        for k in range(ship_len):
                            prob[r, c + k] += 1.0
            
            # Vertical placements
            for r in range(n - ship_len + 1):
                for c in range(n):
                    valid = True
                    for k in range(ship_len):
                        if grid[r + k, c] == -1:  # miss
                            valid = False
                            break
                    if valid:
                        for k in range(ship_len):
                            prob[r + k, c] += 1.0
        
        return prob
    
    # Find best adjacent cells to a hit cluster
    def get_adjacent_targets(clusters):
        candidates = []
        for cluster in clusters:
            adjacent = set()
            for r, c in cluster:
                for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < n and 0 <= nc < n and grid[nr, nc] == 0:
                        adjacent.add((nr, nc))
            
            # Prioritize adjacent cells that align with the cluster direction
            if len(cluster) > 1:
                # Determine cluster orientation
                cluster_set = set(cluster)
                for r, c in adjacent:
                    # Check if this cell continues a line
                    score = 0
                    # Horizontal line check
                    for dr, dc in [(0, 1), (0, -1)]:
                        nr, nc = r + dr, c + dc
                        while (nr, nc) in cluster_set and 0 <= nr < n and 0 <= nc < n:
                            score += 1
                            nr += dr
                            nc += dc
                    
                    # Vertical line check
                    for dr, dc in [(1, 0), (-1, 0)]:
                        nr, nc = r + dr, c + dc
                        while (nr, nc) in cluster_set and 0 <= nr < n and 0 <= nc < n:
                            score += 1
                            nr += dr
                            nc += dc
                    
                    candidates.append(((r, c), score + 10))  # bonus for alignment
            
            else:
                # Single hit - all adjacent cells are candidates
                for cell in adjacent:
                    candidates.append((cell, 5))
        
        return candidates
    
    # Main logic
    clusters = get_clusters()
    
    # If we have hits, prioritize adjacent cells
    if clusters:
        adjacent_targets = get_adjacent_targets(clusters)
        if adjacent_targets:
            # Sort by score, then randomize within top candidates
            adjacent_targets.sort(key=lambda x: x[1], reverse=True)
            top_score = adjacent_targets[0][1]
            top_candidates = [c for c, s in adjacent_targets if s >= top_score - 1]
            
            if top_candidates:
                # Randomly select from top candidates
                return random.choice(top_candidates)
    
    # If no hits or no adjacent targets, use probability-based selection
    prob = calculate_probabilities()
    
    # Mask out already fired cells
    mask = (grid != 0)
    prob[mask] = -1  # Don't shoot here
    
    # Find cells with highest probability
    max_prob = prob.max()
    if max_prob > 0:
        candidates = np.argwhere(prob == max_prob)
        if len(candidates) > 0:
            # Randomly select from tied highest-probability cells
            chosen = random.choice(candidates)
            return tuple(chosen)
    
    # Fallback: random selection among unknown cells
    unknown_cells = np.argwhere(grid == 0)
    if len(unknown_cells) > 0:
        chosen = random.choice(unknown_cells)
        return tuple(chosen)
    
    # Ultimate fallback (should not happen)
    return (0, 0)
