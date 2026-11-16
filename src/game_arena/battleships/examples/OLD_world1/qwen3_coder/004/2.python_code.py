
import random
from collections import deque

def policy(board: list[list[int]]) -> tuple[int, int]:
    n = len(board)
    
    # Find all hits that are not yet sunk
    hits = []
    for i in range(n):
        for j in range(n):
            if board[i][j] == 1:
                hits.append((i, j))
    
    # If we have hits, try to extend the ship
    if hits:
        # For each hit, check if it's part of a known line
        for hit in hits:
            r, c = hit
            # Check horizontal and vertical directions
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            
            for dr, dc in directions:
                # Look in both directions from this hit
                count = 0
                next_r, next_c = r + dr, c + dc
                
                # Count how many consecutive hits we have in this direction
                while (0 <= next_r < n and 0 <= next_c < n and 
                       board[next_r][next_c] == 1):
                    count += 1
                    next_r += dr
                    next_c += dc
                
                # If we have a line, try to extend it
                if count > 0:
                    # Try extending in the same direction
                    extend_r, extend_c = r + (count + 1) * dr, c + (count + 1) * dc
                    if (0 <= extend_r < n and 0 <= extend_c < n and 
                        board[extend_r][extend_c] == 0):
                        return (extend_r, extend_c)
                    
                    # Try extending in the opposite direction
                    opposite_r, opposite_c = r - dr, c - dc
                    if (0 <= opposite_r < n and 0 <= opposite_c < n and 
                        board[opposite_r][opposite_c] == 0):
                        return (opposite_r, opposite_c)
                
                # If no line yet, just try adjacent cells
                elif count == 0:
                    adj_r, adj_c = r + dr, c + dc
                    if (0 <= adj_r < n and 0 <= adj_c < n and 
                        board[adj_r][adj_c] == 0):
                        return (adj_r, adj_c)
    
    # If we have isolated hits, target around them
    if hits:
        for r, c in hits:
            # Check adjacent cells
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if (0 <= nr < n and 0 <= nc < n and 
                    board[nr][nc] == 0):
                    return (nr, nc)
    
    # Parity strategy for searching: target every other cell
    # This is especially effective for larger ships
    possible_moves = []
    for i in range(n):
        for j in range(n):
            if board[i][j] == 0:  # Unknown cell
                # Check if it's a "good" parity (checkerboard pattern)
                if (i + j) % 2 == 0:
                    possible_moves.append((i, j))
    
    # If no good parity moves, take any unknown cell
    if not possible_moves:
        for i in range(n):
            for j in range(n):
                if board[i][j] == 0:
                    return (i, j)
    
    # Return a random choice from good moves
    return random.choice(possible_moves) if possible_moves else (0, 0)
