
import random
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    n = len(board)
    board_np = np.array(board)

    # 1. Hunt mode: If no ship is currently being hit, hunt for new ships
    # Prioritize cells adjacent to known single hits or in a checkerboard pattern
    
    # Check if we have any hits that are not yet part of a sunk ship
    hits = np.argwhere(board_np == 1)
    
    # If there are active hits, try to sink the ship
    if len(hits) > 0:
        # Try to expand existing hits
        for r, c in hits:
            # Check neighbors
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < n and 0 <= nc < n and board_np[nr, nc] == 0:
                    # Found a valid un-shot neighbor of a hit
                    # Before returning, check for potential ship orientation
                    
                    # If this hit is part of a 2-segment ship (e.g., [1, 1, 0] or [0, 1, 1])
                    # and the third cell is unshot, prioritize it
                    
                    # Check horizontal
                    if c + 1 < n and board_np[r, c+1] == 1: # [1, 1, ?]
                        if c + 2 < n and board_np[r, c+2] == 0:
                            return r, c + 2
                    if c - 1 >= 0 and board_np[r, c-1] == 1: # [?, 1, 1]
                        if c - 2 >= 0 and board_np[r, c-2] == 0:
                            return r, c - 2
                    
                    # Check vertical
                    if r + 1 < n and board_np[r+1, c] == 1: # [1, ?, 1]
                        if r + 2 < n and board_np[r+2, c] == 0:
                            return r + 2, c
                    if r - 1 >= 0 and board_np[r-1, c] == 1: # [1, ?, 1]
                        if r - 2 >= 0 and board_np[r-2, c] == 0:
                            return r - 2, c
                    
                    # Otherwise, just pick any unshot neighbor
                    return nr, nc
        
        # If all neighbors of active hits are either hit or miss,
        # it means we might have a gap in a ship or a single isolated hit.
        # Fallback to smart hunting
        
    # If no hits or after expanding a hit, resume hunting
    
    # Prioritize cells in a checkerboard pattern
    # Start with a checkerboard that covers the even sums of coordinates
    potential_targets = []
    for r in range(n):
        for c in range(n):
            if board_np[r, c] == 0 and (r + c) % 2 == 0:
                potential_targets.append((r, c))

    if potential_targets:
        # Sort potential targets based on proximity to known hits,
        # or just pick a random one if far from hits
        random.shuffle(potential_targets)
        for r, c in potential_targets:
            # Simple check, if a checkerboard cell is next to a miss, it's less likely to be a ship
            # But we need to explore
            return r, c

    # If the first checkerboard is exhausted, try the other one
    potential_targets_odd = []
    for r in range(n):
        for c in range(n):
            if board_np[r, c] == 0 and (r + c) % 2 != 0:
                potential_targets_odd.append((r, c))

    if potential_targets_odd:
        random.shuffle(potential_targets_odd)
        return potential_targets_odd[0]

    # Fallback: If no strategic cells are left, just pick any unshot cell
    unshot_cells = np.argwhere(board_np == 0)
    if unshot_cells.size > 0:
        r, c = random.choice(unshot_cells)
        return r, c
    
    # Should not happen in a normal game, all cells are shot
    return 0, 0
