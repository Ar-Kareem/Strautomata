
import random
from typing import List, Tuple, Set, Dict, Optional
import numpy as np

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Smart Battleship targeting policy using hit propagation and probability.
    
    Strategy:
    1. If we have hits but no ongoing ship (no adjacent hit), look around isolated hits
    2. If we have hits that are aligned, continue in that direction
    3. Otherwise, use probability-based weighting considering ship placements
    """
    
    board = np.array(board)
    n = 10
    ship_lengths = [5, 4, 3, 3, 2]
    
    # Get all unknown cells
    unknown_cells = [(i, j) for i in range(n) for j in range(n) if board[i, j] == 0]
    
    # If no hits yet, use probabilistic approach with pattern skipping
    hits = [(i, j) for i in range(n) for j in range(n) if board[i, j] == 1]
    
    if not hits:
        # Use checkerboard pattern to maximize coverage efficiency
        # Only target every other cell in checkerboard fashion
        candidates = [cell for cell in unknown_cells 
                    if (cell[0] + cell[1]) % 2 == 0]
        if candidates:
            return random.choice(candidates)
        else:
            return random.choice(unknown_cells)
    
    # Look for potential ship continuations
    for hit in hits:
        row, col = hit
        
        # Check for adjacent hits to determine orientation
        adjacent_hits = []
        for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nr, nc = row + dr, col + dc
            if 0 <= nr < n and 0 <= nc < n and board[nr, nc] == 1:
                adjacent_hits.append((dr, dc))
        
        # If we have adjacent hits, we know the orientation
        if len(adjacent_hits) > 0:
            # Find the line of hits
            line_direction = adjacent_hits[0]
            if len(adjacent_hits) > 1:
                # Make sure they're colinear
                if adjacent_hits[0][0] + adjacent_hits[1][0] != 0 and adjacent_hits[0][1] + adjacent_hits[1][1] != 0:
                    line_direction = adjacent_hits[0]  # They agree on direction
                else:
                    # Opposite directions - we're in the middle of a ship
                    pass
            
            # Try to extend in both directions along the line
            for direction_multiplier in [1, -1]:
                if len(adjacent_hits) == 1:
                    # Use the direction from the adjacent hit
                    dr, dc = adjacent_hits[0]
                else:
                    # No clear direction, try all cardinal directions
                    dr, dc = line_direction[0], line_direction[1]
                    
                dr *= direction_multiplier
                dc *= direction_multiplier
                
                # Look for empty cell in this direction
                for length in range(1, 6):  # Check up to 5 cells away
                    nr, nc = row + dr * length, col + dc * length
                    if 0 <= nr < n and 0 <= nc < n:
                        if board[nr, nc] == 0:
                            return (nr, nc)
                        elif board[nr, nc] == -1:  # Hit water, stop in this direction
                            break
                    else:  # Out of bounds, stop in this direction
                        break
    
    # If we have hits but couldn't extend, prioritize adjacent to hits
    for hit in hits:
        row, col = hit
        # Check all adjacent cells
        for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nr, nc = row + dr, col + dc
            if 0 <= nr < n and 0 <= nc < n and board[nr, nc] == 0:
                # Prioritize these cells
                return (nr, nc)
    
    # If we get here, use probability map based on possible ship placements
    prob = np.zeros((n, n))
    
    for length in ship_lengths:
        # Count valid positions for this ship
        for row in range(n):
            for col in range(n):
                # Horizontal placement
                if col + length <= n:
                    valid = True
                    for k in range(length):
                        if board[row, col + k] == -1:  # Would overlap with miss
                            valid = False
                            break
                    if valid:
                        for k in range(length):
                            if board[row, col + k] == 0:  # Only count unknown cells
                                prob[row, col + k] += 1
                
                # Vertical placement
                if row + length <= n:
                    valid = True
                    for k in range(length):
                        if board[row + k, col] == -1:  # Would overlap with miss
                            valid = False
                            break
                    if valid:
                        for k in range(length):
                            if board[row + k, col] == 0:  # Only count unknown cells
                                prob[row + k, col] += 1
    
    # Find unknown cells with highest probability
    max_prob = -1
    best_candidates = []
    
    for i in range(n):
        for j in range(n):
            if board[i, j] == 0 and prob[i, j] > max_prob:
                max_prob = prob[i, j]
                best_candidates = [(i, j)]
            elif board[i, j] == 0 and prob[i, j] == max_prob:
                best_candidates.append((i, j))
    
    if best_candidates:
        return random.choice(best_candidates)
    
    # Fallback - should not reach here
    return random.choice(unknown_cells)
