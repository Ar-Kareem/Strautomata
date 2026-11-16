
import random
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Determines the next move for a Battleship game.
    
    Strategy:
    1. Check for lines of hits to sink the ship (Sinking Mode).
    2. If no lines, check neighbors of isolated hits (Target Mode).
    3. If no hits, use parity search (Hunt Mode).
    """
    rows, cols = 10, 10
    
    def is_valid(r: int, c: int) -> bool:
        return 0 <= r < rows and 0 <= c < cols

    # Helper to get cell value, returning None if out of bounds
    def get_val(r: int, c: int):
        if not is_valid(r, c): return None
        return board[r][c]

    # Collect all hit coordinates
    hits = [(r, c) for r in range(rows) for c in range(cols) if board[r][c] == 1]
    
    # Directions: Up, Down, Left, Right
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    # --- MODE 1: SINKING (Extend lines of hits) ---
    # If we have at least two hits adjacent to each other, we have a line.
    # We try to extend that line.
    potential_moves = []
    
    for r, c in hits:
        for dr, dc in directions:
            # Look at the immediate neighbor
            nr, nc = r + dr, c + dc
            
            # If the immediate neighbor is also a hit, we have a direction.
            if is_valid(nr, nc) and board[nr][nc] == 1:
                # Try to shoot the cell *beyond* the neighbor in the same direction
                nnr, nnc = nr + dr, nc + dc
                if is_valid(nnr, nnc) and board[nnr][nnc] == 0:
                    potential_moves.append((nnr, nnc))
                    
    if potential_moves:
        # Return a random move from the high-priority extensions to be slightly unpredictable
        return random.choice(list(set(potential_moves)))

    # --- MODE 2: TARGETING (Neighbors of isolated hits) ---
    # If no lines found, check neighbors of all hits.
    # We filter out misses (-1) and hits (1) to find unknown (0) spots.
    target_moves = []
    for r, c in hits:
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if is_valid(nr, nc) and board[nr][nc] == 0:
                target_moves.append((nr, nc))
                
    if target_moves:
        return random.choice(list(set(target_moves)))

    # --- MODE 3: HUNTING (Global Parity Search) ---
    # If no hits, use a checkerboard pattern.
    # This guarantees finding ships of length 2 or greater.
    # We pick random valid cells from the checkerboard to ensure randomness.
    hunt_moves = []
    for r in range(rows):
        for c in range(cols):
            if board[r][c] == 0 and (r + c) % 2 == 0:
                hunt_moves.append((r, c))
                
    if hunt_moves:
        return random.choice(hunt_moves)
        
    # Fallback: If we somehow exhausted parity (unlikely given ship lengths), pick any valid cell.
    all_moves = [(r, c) for r in range(rows) for c in range(cols) if board[r][c] == 0]
    return random.choice(all_moves)
