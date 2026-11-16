
import random
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Battleship policy that hunts for ships using a checkerboard pattern
    and targets them using alignment heuristics.
    """
    rows, cols = 10, 10
    hits = []
    
    # Collect all current hits
    for r in range(rows):
        for c in range(cols):
            if board[r][c] == 1:
                hits.append((r, c))

    # --- Target Mode ---
    # If we have hits, try to sink the ship
    candidates = {}  # Map (r, c) -> score
    
    for r, c in hits:
        # Check 4 orthogonal neighbors
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            
            # Check bounds and if cell is unknown
            if 0 <= nr < rows and 0 <= nc < cols and board[nr][nc] == 0:
                
                score = 0
                
                # Check if this move bridges a gap between two hits (e.g., 1 ? 1)
                # Look one step further in the same direction
                bridge_r, bridge_c = r + 2 * dr, c + 2 * dc
                is_bridge = False
                if 0 <= bridge_r < rows and 0 <= bridge_c < cols and board[bridge_r][bridge_c] == 1:
                    score = 100  # Highest priority: guaranteed hit/sink
                    is_bridge = True
                
                if not is_bridge:
                    # Score based on extending a line of hits
                    # Base score for being adjacent to a hit
                    score = 1
                    
                    # Look behind the hit (r, c) to see how many hits are in this line
                    look_r, look_c = r - dr, c - dc
                    consecutive_hits = 0
                    while 0 <= look_r < rows and 0 <= look_c < cols and board[look_r][look_c] == 1:
                        consecutive_hits += 1
                        look_r -= dr
                        look_c -= dc
                    
                    # Add bonus for longer lines (prioritize sinking damaged ships)
                    score += consecutive_hits

                # Keep the highest score for this cell
                if (nr, nc) not in candidates or score > candidates[(nr, nc)]:
                    candidates[(nr, nc)] = score

    if candidates:
        # Return the move with the highest score
        # If multiple moves have the same top score, pick one randomly
        max_score = max(candidates.values())
        best_moves = [pos for pos, s in candidates.items() if s == max_score]
        return random.choice(best_moves)

    # --- Hunt Mode ---
    # If no active targets, fire on checkerboard pattern to find a ship
    # Parity: (row + col) % 2 == 0 covers all even squares
    valid_moves = []
    for r in range(rows):
        for c in range(cols):
            if board[r][c] == 0:
                if (r + c) % 2 == 0:
                    valid_moves.append((r, c))
    
    # If checkerboard is exhausted (unlikely but possible in late game), fill in odd squares
    if not valid_moves:
        for r in range(rows):
            for c in range(cols):
                if board[r][c] == 0:
                    valid_moves.append((r, c))
                    
    # Pick a random valid move
    return random.choice(valid_moves)
