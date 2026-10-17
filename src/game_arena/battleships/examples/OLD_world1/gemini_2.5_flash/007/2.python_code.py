
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    n = len(board)
    board_np = np.array(board)

    # 1. Hunt Mode: If no active hits, search for ships
    # Prioritize cells that haven't been shot yet
    untried_cells = np.argwhere(board_np == 0)

    # If there are active hits, switch to Target Mode
    hit_cells = np.argwhere(board_np == 1)

    if len(hit_cells) > 0:
        # Target Mode: Try to sink the ship
        # Find isolated hits (single '1's) and connected hits
        
        # Try to extend existing hits
        for r, c in hit_cells:
            # Check neighbors
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < n and 0 <= nc < n and board_np[nr, nc] == 0:
                    # If neighbor is '0', fire there
                    return int(nr), int(nc)

        # If no immediate extension works, look for patterns (e.g., two hits in a line)
        # This is a basic pattern matching for two in a row or column
        for r1, c1 in hit_cells:
            for r2, c2 in hit_cells:
                if (r1, c1) == (r2, c2):
                    continue
                
                # Horizontal line
                if r1 == r2:
                    if abs(c1 - c2) == 1: # Adjacent hits
                        # Try to extend left
                        if c1 > 0 and board_np[r1, c1 - 1] == 0:
                            return int(r1), int(c1 - 1)
                        # Try to extend right
                        if c1 < n - 1 and board_np[r1, c1 + 1] == 0:
                            return int(r1), int(c1 + 1)
                        if c2 > 0 and board_np[r2, c2 - 1] == 0:
                            return int(r2), int(c2 - 1)
                        if c2 < n - 1 and board_np[r2, c2 + 1] == 0:
                            return int(r2), int(c2 + 1)
                # Vertical line
                elif c1 == c2:
                    if abs(r1 - r2) == 1: # Adjacent hits
                        # Try to extend up
                        if r1 > 0 and board_np[r1 - 1, c1] == 0:
                            return int(r1 - 1), int(c1)
                        # Try to extend down
                        if r1 < n - 1 and board_np[r1 + 1, c1] == 0:
                            return int(r1 + 1), int(c1)
                        if r2 > 0 and board_np[r2 - 1, c2] == 0:
                            return int(r2 - 1), int(c2)
                        if r2 < n - 1 and board_np[r2 + 1, c2] == 0:
                            return int(r2 + 1), int(c2)
        
        # If no obvious targeting based on adjacent hits or simple patterns,
        # fallback to a more general search around hit cells but still try to
        # maintain some "hunting" strategy
        for r, c in hit_cells:
            # Check diagonal neighbors the next turn if direct neighbors are shot
            # This is a less effective way but better than random if directly adjacent are misses
            for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < n and 0 <= nc < n and board_np[nr, nc] == 0:
                     # Prioritize cells that are part of a checkerboard pattern for new hits
                    if (nr + nc) % 2 == 0 : 
                         return int(nr), int(nc)
            
        # If failed to find a sensible target from hits, default to a hunter strategy.

    # 2. Hunt Mode (default or fallback):
    # Prioritize checkerboard pattern for new shots, which helps cover more ground
    # and hit ships of various lengths more efficiently.
    
    # Try even-sum cells first (r+c is even)
    for r in range(n):
        for c in range(n):
            if board_np[r, c] == 0 and (r + c) % 2 == 0:
                return int(r), int(c)

    # If all even-sum cells are shot, try odd-sum cells
    for r in range(n):
        for c in range(n):
            if board_np[r, c] == 0 and (r + c) % 2 != 0:
                return int(r), int(c)

    # Fallback: Should not happen in a 10x10 grid unless the grid is full
    # (But if it does, choose any unshot cell)
    if len(untried_cells) > 0:
        r, c = untried_cells[0]
        return int(r), int(c)
    
    # If all cells are tried, return an invalid coordinate to indicate an error or game over
    return -1, -1
