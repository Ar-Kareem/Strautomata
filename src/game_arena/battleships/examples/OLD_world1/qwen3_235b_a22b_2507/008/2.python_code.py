
import random
from typing import List, Tuple, Set, Optional

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Targeting policy for Battleship game using a hybrid approach:
    - Hunt mode: search randomly with even coverage
    - Target mode: when a hit is found, prioritize adjacent cells
    - Use probability-based weighting to focus on high-probability locations
    """
    
    # Track hits that haven't been fully explored
    hits = []
    for r in range(10):
        for c in range(10):
            if board[r][c] == 1:
                hits.append((r, c))
    
    # Possible ship lengths (standard Battleship)
    ship_lengths = [5, 4, 3, 3, 2]
    
    # If we have hits but no obvious pattern to follow, try adjacent cells
    if hits:
        # Look for partially destroyed ships - check neighbors of each hit
        for hit_r, hit_c in hits:
            # Check 4 adjacent directions
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            possible_moves = []
            
            for dr, dc in directions:
                nr, nc = hit_r + dr, hit_c + dc
                if (0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0):
                    # Check if this could continue a pattern
                    # If we have another hit in the same line, prioritize that direction
                    possible_moves.append((nr, nc))
            
            if possible_moves:
                # If adjacent to a hit, prefer these cells
                return random.choice(possible_moves)
    
    # If no hits or no valid adjacent cells, use probability mapping
    # Create a probability grid based on where ships could fit
    prob = [[0 for _ in range(10)] for _ in range(10)]
    
    for length in ship_lengths:
        # Horizontal placements
        for r in range(10):
            for c in range(11 - length):
                # Check if ship can fit here
                valid = True
                for i in range(length):
                    if board[r][c+i] == -1:  # Miss
                        valid = False
                        break
                if valid:
                    for i in range(length):
                        if board[r][c+i] == 0:  # Only count unknown cells
                            prob[r][c+i] += 1
        
        # Vertical placements
        for r in range(11 - length):
            for c in range(10):
                valid = True
                for i in range(length):
                    if board[r+i][c] == -1:  # Miss
                        valid = False
                        break
                if valid:
                    for i in range(length):
                        if board[r+i][c] == 0:  # Only count unknown cells
                            prob[r+i][c] += 1
    
    # Exclude already-fired cells and find max probability
    candidates = []
    max_prob = 0
    
    for r in range(10):
        for c in range(10):
            if board[r][c] == 0:  # Only consider un-fired cells
                if prob[r][c] > max_prob:
                    max_prob = prob[r][c]
                    candidates = [(r, c)]
                elif prob[r][c] == max_prob:
                    candidates.append((r, c))
    
    # Add slight preference for center (better ship placement distribution)
    if candidates:
        # Sort by distance to center (5.5, 5.5) - prioritize center
        center_candidates = sorted(candidates, key=lambda x: (x[0]-4.5)**2 + (x[1]-4.5)**2)
        # Choose among the best few to maintain randomness
        choice_count = min(3, len(center_candidates))
        return random.choice(center_candidates[:choice_count])
    
    # Fallback: random selection (should not reach here)
    available = []
    for r in range(10):
        for c in range(10):
            if board[r][c] == 0:
                available.append((r, c))
    
    return random.choice(available) if available else (0, 0)
