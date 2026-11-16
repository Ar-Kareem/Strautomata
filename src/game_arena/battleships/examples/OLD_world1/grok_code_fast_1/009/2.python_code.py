
import random
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    board_np = np.array(board)
    if board_np.shape != (10, 10):
        raise ValueError("Board must be 10x10")
    
    # Get all unknown cells (where we haven't shot yet)
    unknowns = np.where(board_np == 0)
    unknown_list = list(zip(unknowns[0], unknowns[1]))
    
    if not unknown_list:
        # Theoretically impossible, but fallback
        return (0, 0)
    
    # Get all hit cells
    hits = np.where(board_np == 1)
    hit_list = list(zip(hits[0], hits[1]))
    
    if not hit_list:
        # Search mode: use checkerboard pattern (target even parity of row+col)
        checkerboard_targets = [pos for pos in unknown_list if (pos[0] + pos[1]) % 2 == 0]
        if checkerboard_targets:
            target = random.choice(checkerboard_targets)
        else:
            # If no checkerboard targets (shouldn't happen in 10x10), randomly among unknowns
            target = random.choice(unknown_list)
    else:
        # Hunt mode: look for cells adjacent to hits that are unknown
        candidates = set()
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # up, down, left, right
        for row, col in hit_list:
            for dr, dc in directions:
                nr, nc = row + dr, col + dc
                if 0 <= nr < 10 and 0 <= nc < 10 and board_np[nr, nc] == 0:
                    candidates.add((nr, nc))
        
        if candidates:
            target = random.choice(list(candidates))
        else:
            # No candidates (e.g., all possible adjacents are misses or hits), fallback to random unknown
            target = random.choice(unknown_list)
    
    # Convert back to tuple of ints
    return target
