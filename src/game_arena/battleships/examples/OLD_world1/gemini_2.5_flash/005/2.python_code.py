
import random
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Implements a targeting policy for a Battleship-like game.

    The policy prioritizes sinking damaged ships, then searches in a checkerboard pattern,
    and finally targets random unknown cells.

    Args:
        board: A 10x10 list of lists representing the current knowledge of the opponent grid.
               0: unknown, -1: miss, 1: hit.

    Returns:
        A tuple (row, col) representing the next cell to fire at.
    """

    n = len(board)
    board_np = np.array(board)

    # 1. Prioritize sinking damaged ships
    hits = np.argwhere(board_np == 1)
    if len(hits) > 0:
        # Check for adjacent unknown cells around any hit
        for r, c in hits:
            # Check horizontal
            potential_targets_h = []
            if c > 0 and board_np[r, c-1] == 1: # Left is hit, try right
                if c < n - 1 and board_np[r, c+1] == 0:
                    potential_targets_h.append((r, c+1))
            if c < n - 1 and board_np[r, c+1] == 1: # Right is hit, try left
                if c > 0 and board_np[r, c-1] == 0:
                    potential_targets_h.append((r, c-1))
            
            # If we have hits on both sides, and there's an unknown in between, target it.
            if c > 0 and board_np[r,c-1] == 1 and c < n-1 and board_np[r,c+1] == 1:
                # If there's an unknown between them, target it
                for col_between in range(c-1, c+2):
                    if board_np[r, col_between] == 0:
                        return r, col_between
                        
            # Check vertical
            potential_targets_v = []
            if r > 0 and board_np[r-1, c] == 1: # Up is hit, try down
                if r < n - 1 and board_np[r+1, c] == 0:
                    potential_targets_v.append((r+1, c))
            if r < n - 1 and board_np[r+1, c] == 1: # Down is hit, try up
                if r > 0 and board_np[r-1, c] == 0:
                    potential_targets_v.append((r-1, c))

            # If we have hits on both sides, and there's an unknown in between, target it.
            if r > 0 and board_np[r-1,c] == 1 and r < n-1 and board_np[r+1,c] == 1:
                # If there's an unknown between them, target it
                for row_between in range(r-1, r+2):
                    if board_np[row_between, c] == 0:
                        return row_between, c


            # Combine potential targets and pick one if available
            adjacent_unknowns = []
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < n and 0 <= nc < n and board_np[nr, nc] == 0:
                    adjacent_unknowns.append((nr, nc))

            if potential_targets_h:
                return random.choice(potential_targets_h)
            if potential_targets_v:
                return random.choice(potential_targets_v)
            if adjacent_unknowns:
                return random.choice(adjacent_unknowns)

    # 2. Checkerboard pattern for initial search (strikes diagonal ships better)
    # Prefer cells that are part of a checkerboard pattern
    unknown_cells = []
    for r in range(n):
        for c in range(n):
            if board_np[r, c] == 0:
                unknown_cells.append((r, c))

    checkerboard_cells = [(r, c) for r, c in unknown_cells if (r + c) % 2 == 0]
    if checkerboard_cells:
        # Check if there are still a lot of ships left, if so, prioritize checkerboard
        # This is a heuristic, assuming the game is still early if few hits
        if len(hits) < 5: # Arbitrary threshold, can be tuned
            return random.choice(checkerboard_cells)
    
    # If checkerboard cells are depleted or we've hit many ships (prioritize sinking them instead)
    # Fallback to remaining unknown cells (the other half of the checkerboard, or any remaining)
    if unknown_cells:
        return random.choice(unknown_cells)

    # If somehow all cells are played (should not happen in a normal game)
    # This is a fallback and indicates an issue or game end.
    return 0, 0
