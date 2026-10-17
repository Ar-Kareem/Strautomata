
import numpy as np
from typing import List, Tuple, Set

def policy(board: List[List[int]]) -> Tuple[int, int]:
    # Convert to numpy for easier manipulation
    grid = np.array(board)
    
    # Ship lengths
    ship_lengths = [5, 4, 3, 3, 2]
    
    # Find all hit positions and missed positions
    hits = set((r, c) for r in range(10) for c in range(10) if grid[r, c] == 1)
    misses = set((r, c) for r in range(10) for c in range(10) if grid[r, c] == -1)
    known = hits.union(misses)
    
    # If we have hits that aren't part of sunk ships, target around them
    if hits:
        # Find potential targets around hits
        targets = set()
        for r, c in hits:
            # Check adjacent cells
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 10 and 0 <= nc < 10 and (nr, nc) not in known:
                    targets.add((nr, nc))
        
        if targets:
            # Among adjacent cells, pick one that could be part of a ship placement
            best_target = None
            best_score = -1
            
            for r, c in targets:
                score = 0
                # Count how many possible ship placements would go through this cell
                for length in ship_lengths:
                    # Horizontal placements
                    for dr in range(max(0, r - length + 1), min(r + 1, 11 - length)):
                        if all(0 <= c + dc < 10 and (dr, c + dc) not in misses for dc in range(length)):
                            score += 1
                    
                    # Vertical placements
                    for dc in range(max(0, c - length + 1), min(c + 1, 11 - length)):
                        if all(0 <= r + dr < 10 and (r + dr, dc) not in misses for dr in range(length)):
                            score += 1
                
                if score > best_score:
                    best_score = score
                    best_target = (r, c)
            
            if best_target:
                return best_target
    
    # Hunt mode - create probability map
    prob_map = np.zeros((10, 10))
    
    # For each ship length, count possible placements
    for length in ship_lengths:
        # Horizontal placements
        for r in range(10):
            for c in range(11 - length):
                # Check if this placement is possible (no misses)
                valid = True
                hit_count = 0
                for dc in range(length):
                    if (r, c + dc) in misses:
                        valid = False
                        break
                    if (r, c + dc) in hits:
                        hit_count += 1
                
                if valid:
                    # Add probability to each cell in this placement
                    for dc in range(length):
                        if (r, c + dc) not in known:  # Only add to unknown cells
                            prob_map[r, c + dc] += 1 + hit_count  # Boost for hits
        
        # Vertical placements
        for c in range(10):
            for r in range(11 - length):
                # Check if this placement is possible (no misses)
                valid = True
                hit_count = 0
                for dr in range(length):
                    if (r + dr, c) in misses:
                        valid = False
                        break
                    if (r + dr, c) in hits:
                        hit_count += 1
                
                if valid:
                    # Add probability to each cell in this placement
                    for dr in range(length):
                        if (r + dr, c) not in known:  # Only add to unknown cells
                            prob_map[r + dr, c] += 1 + hit_count  # Boost for hits
    
    # Find the cell with maximum probability
    max_prob = -1
    best_cell = None
    
    for r in range(10):
        for c in range(10):
            if (r, c) not in known and prob_map[r, c] > max_prob:
                max_prob = prob_map[r, c]
                best_cell = (r, c)
    
    # If we found a good cell, return it
    if best_cell:
        return best_cell
    
    # Fallback: return first available cell
    for r in range(10):
        for c in range(10):
            if (r, c) not in known:
                return (r, c)
    
    # Should never happen
    return (0, 0)
