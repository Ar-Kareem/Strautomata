
import random
from typing import List, Tuple, Set, Dict, Optional
import numpy as np

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Intelligent Battleship targeting policy using probability-based search
    and pattern exploitation.
    """
    board = np.array(board)
    n = 10
    
    # Track hits that haven't sunk a ship yet (potential ship extensions)
    hit_positions = []
    for i in range(n):
        for j in range(n):
            if board[i, j] == 1:
                hit_positions.append((i, j))
    
    # If we have isolated hits, try to extend them
    if hit_positions:
        # Group hits that might belong to the same ship
        hit_clusters = []
        unassigned = hit_positions.copy()
        
        while unassigned:
            cluster = [unassigned.pop()]
            # Find connected hits in same row or column
            changed = True
            while changed:
                changed = False
                for pos in unassigned[:]:
                    # Check if pos is in same row or column as any cluster member
                    for c_pos in cluster:
                        if (pos[0] == c_pos[0] and abs(pos[1] - c_pos[1]) == 1) or \
                           (pos[1] == c_pos[1] and abs(pos[0] - c_pos[0]) == 1):
                            cluster.append(pos)
                            unassigned.remove(pos)
                            changed = True
                            break
                        if changed:
                            break
            
            hit_clusters.append(cluster)
        
        # For clusters with hits, try to extend in possible directions
        for cluster in hit_clusters:
            if len(cluster) >= 1:
                # Sort cluster by position to get direction
                if len(cluster) == 1:
                    # Single hit - try all four directions
                    r, c = cluster[0]
                    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
                    random.shuffle(directions)
                    
                    for dr, dc in directions:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < n and 0 <= nc < n and board[nr, nc] == 0:
                            return (nr, nc)
                
                else:
                    # Multiple hits - determine direction and extend
                    cluster.sort()
                    # Check if horizontal (same row)
                    if cluster[0][0] == cluster[-1][0]:
                        # Horizontal - sort by column
                        cluster.sort(key=lambda x: x[1])
                        r = cluster[0][0]
                        left_c = cluster[0][1] - 1
                        right_c = cluster[-1][1] + 1
                        
                        if left_c >= 0 and board[r, left_c] == 0:
                            return (r, left_c)
                        if right_c < n and board[r, right_c] == 0:
                            return (r, right_c)
                    
                    else:
                        # Vertical - sort by row
                        cluster.sort()
                        c = cluster[0][1]
                        top_r = cluster[0][0] - 1
                        bottom_r = cluster[-1][0] + 1
                        
                        if top_r >= 0 and board[top_r, c] == 0:
                            return (top_r, c)
                        if bottom_r < n and board[bottom_r, c] == 0:
                            return (bottom_r, c)
    
    # If no good extension, use probability-based search with checkerboard pattern
    # Battleship ships need at least 2 spaces, so we can use checkerboard pattern
    # But avoid pure checkerboard since ships can be length 2
    
    # Create probability map
    prob = np.zeros((n, n))
    
    # Ship lengths in the game
    ship_lengths = [5, 4, 3, 3, 2]
    
    for length in ship_lengths:
        # Add probability for horizontal placements
        for r in range(n):
            for c in range(n - length + 1):
                valid = True
                for i in range(length):
                    if board[r, c + i] == -1:  # Miss
                        valid = False
                        break
                if valid:
                    for i in range(length):
                        if board[r, c + i] == 0:  # Unknown
                            prob[r, c + i] += 1
        
        # Add probability for vertical placements
        for r in range(n - length + 1):
            for c in range(n):
                valid = True
                for i in range(length):
                    if board[r + i, c] == -1:  # Miss
                        valid = False
                        break
                if valid:
                    for i in range(length):
                        if board[r + i, c] == 0:  # Unknown
                            prob[r + i, c] += 1
    
    # Set already fired positions to minimum probability
    for r in range(n):
        for c in range(n):
            if board[r, c] != 0:  # Already fired here
                prob[r, c] = -np.inf
    
    # Enhance probability of cells in checkerboard pattern (odd sum coordinates)
    # This helps cover the board efficiently
    for r in range(n):
        for c in range(n):
            if board[r, c] == 0:
                # Prefer cells where (r+c) is odd, but not exclusively
                if (r + c) % 2 == 1:
                    prob[r, c] *= 1.2
    
    # Find highest probability cells
    max_prob = np.max(prob)
    if max_prob > 0:
        candidates = []
        for r in range(n):
            for c in range(n):
                if prob[r, c] == max_prob:
                    candidates.append((r, c))
        
        # Break ties: prefer center, then random
        if candidates:
            # Sort by distance to center (prefer center shots)
            center = (4.5, 4.5)
            candidates.sort(key=lambda x: (x[0]-center[0])**2 + (x[1]-center[1])**2)
            # Choose among top candidates randomly to avoid predictability
            top_candidates = [c for c in candidates if ((c[0]-center[0])**2 + (c[1]-center[1])**2) <= 
                            ((candidates[0][0]-center[0])**2 + (candidates[0][1]-center[1])**2) + 1]
            return random.choice(top_candidates)
    
    # Fallback: find any unexplored cell
    unknown_cells = []
    for r in range(n):
        for c in range(n):
            if board[r, c] == 0:
                unknown_cells.append((r, c))
    
    if unknown_cells:
        # Apply simple checkerboard preference
        odd_cells = [cell for cell in unknown_cells if (cell[0] + cell[1]) % 2 == 1]
        if odd_cells:
            return random.choice(odd_cells)
        else:
            return random.choice(unknown_cells)
    
    # This should never happen
    return (0, 0)
