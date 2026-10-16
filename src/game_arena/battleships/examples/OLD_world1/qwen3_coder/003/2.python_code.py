
import random
from typing import List, Tuple, Optional, Set

def policy(board: List[List[int]]) -> Tuple[int, int]:
    # Constants
    SIZE = 10
    SHIP_LENGTHS = [5, 4, 3, 3, 2]
    
    # Find all hits (1) that haven't been fully processed
    hits = []
    hit_neighbors = []  # Hits that have at least one neighbor that is unknown
    
    for r in range(SIZE):
        for c in range(SIZE):
            if board[r][c] == 1:  # Hit
                hits.append((r, c))
                # Check for unknown neighbors
                for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < SIZE and 0 <= nc < SIZE and board[nr][nc] == 0:
                        hit_neighbors.append((r, c))
                        break
    
    # If we have a hit with unknown neighbors, try to continue in that direction
    if hit_neighbors:
        # Try to find a line of hits to determine direction
        for r, c in hit_neighbors:
            # Check each direction
            for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                # Check if there's a line of hits in this direction
                line_length = 1
                nr, nc = r + dr, c + dc
                while (0 <= nr < SIZE and 0 <= nc < SIZE and 
                       board[nr][nc] == 1):
                    line_length += 1
                    nr += dr
                    nc += dc
                
                # Check if next cell in line is unknown
                if (0 <= nr < SIZE and 0 <= nc < SIZE and 
                    board[nr][nc] == 0):
                    return (nr, nc)
                
                # Check the other end of the line
                nr, nc = r - dr, c - dc
                if (0 <= nr < SIZE and 0 <= nc < SIZE and 
                    board[nr][nc] == 0):
                    return (nr, nc)
        
        # If we can't determine direction, pick a random neighbor of a hit
        for r, c in hit_neighbors:
            candidates = []
            for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < SIZE and 0 <= nc < SIZE and board[nr][nc] == 0:
                    candidates.append((nr, nc))
            if candidates:
                return random.choice(candidates)
    
    # If we have any hits at all, target neighbors of any hit
    if hits:
        candidates = []
        for r, c in hits:
            for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < SIZE and 0 <= nc < SIZE and board[nr][nc] == 0:
                    candidates.append((nr, nc))
        if candidates:
            return random.choice(candidates)
    
    # No hits yet - use a checkerboard pattern for initial search
    # This maximizes information gain since ships are at least 2 cells long
    checkerboard = []
    for r in range(SIZE):
        for c in range(SIZE):
            if (r + c) % 2 == 0 and board[r][c] == 0:
                checkerboard.append((r, c))
    
    if checkerboard:
        return random.choice(checkerboard)
    
    # Fallback - choose any remaining unknown cell
    candidates = []
    for r in range(SIZE):
        for c in range(SIZE):
            if board[r][c] == 0:
                candidates.append((r, c))
    
    if candidates:
        return random.choice(candidates)
    
    # Should never happen if the game is ongoing
    return (0, 0)
