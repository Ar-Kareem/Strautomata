
import random
from collections import deque

def policy(board: list[list[int]]) -> tuple[int, int]:
    n = 10
    # Convert board to numpy array for easier handling
    import numpy as np
    board_array = np.array(board)
    
    # Find all hit positions
    hits = np.where(board_array == 1)
    hit_positions = list(zip(hits[0], hits[1]))
    
    # Find all miss positions
    misses = np.where(board_array == -1)
    miss_positions = set(zip(misses[0], misses[1]))
    
    # If we have hits, try to sink the ships first
    if hit_positions:
        # For each hit, check if we can determine the direction of the ship
        for hit_r, hit_c in hit_positions:
            # Check if we have adjacent hits to determine ship direction
            adjacent_hits = []
            for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nr, nc = hit_r + dr, hit_c + dc
                if 0 <= nr < n and 0 <= nc < n and board_array[nr, nc] == 1:
                    adjacent_hits.append((nr, nc))
            
            # If we have adjacent hits, we know the direction
            if adjacent_hits:
                # Determine direction
                if len(adjacent_hits) == 1:
                    adj_r, adj_c = adjacent_hits[0]
                    dr, dc = hit_r - adj_r, hit_c - adj_c
                    # Extend in both directions
                    targets = []
                    # One direction
                    nr, nc = hit_r + dr, hit_c + dc
                    while 0 <= nr < n and 0 <= nc < n:
                        if board_array[nr, nc] == -1:  # Miss, stop in this direction
                            break
                        if board_array[nr, nc] == 0:  # Unknown, potential target
                            targets.append((nr, nc))
                            break
                        nr, nc = nr + dr, nc + dc
                    # Other direction
                    nr, nc = adj_r - dr, adj_c - dc
                    while 0 <= nr < n and 0 <= nc < n:
                        if board_array[nr, nc] == -1:  # Miss, stop in this direction
                            break
                        if board_array[nr, nc] == 0:  # Unknown, potential target
                            targets.append((nr, nc))
                            break
                        nr, nc = nr - dr, nc - dc
                    if targets:
                        return targets[0]
            
            # If no adjacent hits, try all four directions
            else:
                for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                    nr, nc = hit_r + dr, hit_c + dc
                    if 0 <= nr < n and 0 <= nc < n and board_array[nr, nc] == 0:
                        return (nr, nc)
    
    # If no hits or no valid moves from hits, use checkerboard pattern for searching
    # This is optimal for finding ships of length 2 or more
    checkerboard = []
    for r in range(n):
        for c in range(n):
            if (r + c) % 2 == 0 and board_array[r, c] == 0:
                checkerboard.append((r, c))
    
    if checkerboard:
        # Prioritize center positions
        center = [(r, c) for r, c in checkerboard if 3 <= r <= 6 and 3 <= c <= 6]
        if center:
            return random.choice(center)
        return random.choice(checkerboard)
    
    # If no checkerboard positions, pick any remaining unknown
    unknowns = np.where(board_array == 0)
    if len(unknowns[0]) > 0:
        idx = random.randint(0, len(unknowns[0]) - 1)
        return (unknowns[0][idx], unknowns[1][idx])
    
    # Fallback (should not happen in a valid game)
    for r in range(n):
        for c in range(n):
            if board_array[r, c] == 0:
                return (r, c)
    
    # This should never happen
    return (0, 0)
