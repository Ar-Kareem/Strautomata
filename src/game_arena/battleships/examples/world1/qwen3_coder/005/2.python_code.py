
import random
from collections import deque

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert board to more convenient format
    hits = []  # List of (row, col) where we hit a ship
    misses = []  # List of (row, col) where we missed
    unknown = []  # List of (row, col) we haven't fired at
    
    for r in range(10):
        for c in range(10):
            if board[r][c] == 1:
                hits.append((r, c))
            elif board[r][c] == -1:
                misses.append((r, c))
            else:  # board[r][c] == 0
                unknown.append((r, c))
    
    # If no hits, we're in hunt mode
    if not hits:
        # Use checkerboard pattern for efficient hunting
        # Check even rows and cols first
        checkerboard = [(r, c) for r, c in unknown if (r + c) % 2 == 0]
        if checkerboard:
            return random.choice(checkerboard)
        else:
            return random.choice(unknown)
    
    # We have hits, so we're in target mode
    # Find adjacent cells to hits that are still unknown
    adjacent_to_hits = []
    
    for r, c in hits:
        # Check four directions
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                adjacent_to_hits.append((nr, nc))
    
    # If we have adjacent cells to hit, prioritize those
    if adjacent_to_hits:
        # Prefer continuing in a line if we have multiple hits
        line_continuations = []
        
        for r, c in hits:
            # Check if this hit has a neighbor that's also a hit
            # Look for horizontal or vertical lines
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 1:
                    # We found two hits in a line - continue in that direction
                    # Direction vector is (dr, dc)
                    # Continue in that direction from both ends
                    continuation1 = (r - dr, c - dc)
                    continuation2 = (nr + dr, nc + dc)
                    
                    for cont_r, cont_c in [continuation1, continuation2]:
                        if (0 <= cont_r < 10 and 0 <= cont_c < 10 and 
                            board[cont_r][cont_c] == 0):
                            line_continuations.append((cont_r, cont_c))
        
        # If we found line continuations, prioritize them
        if line_continuations:
            # Filter to only those that are in adjacent_to_hits
            valid_continuations = [pos for pos in line_continuations if pos in adjacent_to_hits]
            if valid_continuations:
                return random.choice(valid_continuations)
        
        # Otherwise, just pick a random adjacent cell
        return random.choice(adjacent_to_hits)
    
    # If no adjacent unknown cells, go back to hunt mode
    checkerboard = [(r, c) for r, c in unknown if (r + c) % 2 == 0]
    if checkerboard:
        return random.choice(checkerboard)
    else:
        return random.choice(unknown)
