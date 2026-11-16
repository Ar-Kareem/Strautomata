
import random
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Battleship policy using Hunt (Parity) and Target (Adjacency/Line) modes.
    """
    rows, cols = 10, 10
    
    # Helper to check if a move is legal (cell is unknown)
    def is_valid(r: int, c: int) -> bool:
        return 0 <= r < rows and 0 <= c < cols and board[r][c] == 0

    # Identify all hits on the board
    hits = [(r, c) for r in range(rows) for c in range(cols) if board[r][c] == 1]
    
    # Directions for neighbors: Up, Down, Left, Right
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    # --- TARGET MODE ---
    # If we have hits, try to sink the ship
    if hits:
        potential_moves = []

        # Priority 1: Extend existing lines of hits
        # We iterate through all hits. If a hit has a neighbor that is also a hit,
        # we attempt to extend the line in that direction.
        for r, c in hits:
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                # Check if neighbor is a hit
                if 0 <= nr < rows and 0 <= nc < cols and board[nr][nc] == 1:
                    # We found a line. Try to extend "backward" from current cell
                    br, bc = r - dr, c - dc
                    if is_valid(br, bc):
                        potential_moves.append((br, bc))
                    
                    # Try to extend "forward" from the neighbor hit
                    fr, fc = nr + dr, nc + dc
                    if is_valid(fr, fc):
                        potential_moves.append((fr, fc))
        
        if potential_moves:
            # Remove duplicates and return a random choice
            return random.choice(list(set(potential_moves)))

        # Priority 2: Attack neighbors of isolated hits
        # If no lines were found, target any unknown cell adjacent to a hit
        adjacent_moves = []
        for r, c in hits:
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if is_valid(nr, nc):
                    adjacent_moves.append((nr, nc))
        
        if adjacent_moves:
            return random.choice(list(set(adjacent_moves)))

    # --- HUNT MODE ---
    # No active targets. Use checkerboard parity to find ships efficiently.
    # Checkerboard: (row + col) % 2 == 0 guarantees a hit on any ship of length >= 2.
    valid_moves = [(r, c) for r in range(rows) for c in range(cols) if board[r][c] == 0]
    
    # Filter for even parity cells
    parity_moves = [m for m in valid_moves if (m[0] + m[1]) % 2 == 0]
    
    if parity_moves:
        return random.choice(parity_moves)
    
    # Fallback: If parity cells are exhausted (rare), pick any valid move
    return random.choice(valid_moves)
