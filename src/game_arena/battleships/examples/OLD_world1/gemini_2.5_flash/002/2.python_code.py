
import numpy as np
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    board = np.array(board)
    rows, cols = board.shape

    # 1. Hunt Mode: If no ship is currently being targeted, search for a new ship.
    #    Prioritize checkerboard pattern to find ships efficiently.
    #    If a ship is hit, transition to Target Mode.

    # 2. Target Mode: Once a ship segment is hit, try to sink the rest of the ship.
    #    Expand outwards from the hit cell in cardinal directions.
    #    If the ship is sunk or no more valid moves are found in a direction,
    #    revert to Hunt Mode or continue to another hit segment.

    # Find all hit cells
    hit_cells = list(zip(*np.where(board == 1)))

    if hit_cells:
        # Target Mode: Try to sink the ship
        for r, c in hit_cells:
            # Check adjacent cells
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and board[nr, nc] == 0:
                    return (nr, nc)

        # If we have multiple hits, try to extend a line
        # This part handles cases where we hit multiple segments of the same ship
        # or different ships, and the simple adj search didn't cover all
        # possibilities yet.
        # Find potential lines from hits
        for i in range(len(hit_cells)):
            for j in range(i + 1, len(hit_cells)):
                r1, c1 = hit_cells[i]
                r2, c2 = hit_cells[j]

                # Check for horizontal line
                if r1 == r2:
                    if abs(c1 - c2) == 1:  # Adjacent hits
                        # Try to extend left
                        if c1 > 0 and board[r1, c1 - 1] == 0:
                            return (r1, c1 - 1)
                        # Try to extend right
                        if c2 < cols - 1 and board[r1, c2 + 1] == 0:
                            return (r1, c2 + 1)
                    elif c1 + 2 == c2: # gap of one (e.g. H_H)
                        if board[r1, c1 + 1] == 0:
                            return (r1, c1 + 1)
                    elif c2 + 2 == c1:
                        if board[r1, c2 + 1] == 0:
                            return (r1, c2 + 1)
                # Check for vertical line
                elif c1 == c2:
                    if abs(r1 - r2) == 1:  # Adjacent hits
                        # Try to extend up
                        if r1 > 0 and board[r1 - 1, c1] == 0:
                            return (r1 - 1, c1)
                        # Try to extend down
                        if r2 < rows - 1 and board[r2 + 1, c1] == 0:
                            return (r2 + 1, c1)
                    elif r1 + 2 == r2: # gap of one (e.g. H_H)
                        if board[r1 + 1, c1] == 0:
                            return (r1 + 1, c1)
                    elif r2 + 2 == r1:
                        if board[r2 + 1, c1] == 0:
                            return (r2 + 1, c1)
        
        # If still in target mode but no obvious adjacent unshot cell, a ship might have been sunk or
        # we have multiple scattered hits. Fallback to hunting or a more advanced disambiguation.
        # For now, if we have hits but no clear extension, we'll revert to hunting but prioritize cells
        # near existing hits that haven't been shot yet.
        
        # Collect all adjacent unshot cells to existing hits
        potential_targets = []
        for r, c in hit_cells:
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and board[nr, nc] == 0:
                    potential_targets.append((nr, nc))
        if potential_targets:
            return random.choice(potential_targets)

    # Hunt Mode: No current hits or unable to extend a hit.
    # Prioritize 'checkerboard' pattern to efficiently find new ships.
    # The optimal checkerboard pattern changes based on the remaining ship lengths.
    # For a simpler approach, we'll stick to a fixed pattern.
    
    # Try a simple checkerboard pattern (every other cell like r+c is even)
    # This is a basic checkerboard, trying to cover as much ground as possible.
    unshot_cells_checkerboard = []
    for r in range(rows):
        for c in range(cols):
            if board[r, c] == 0 and (r + c) % 2 == 0:
                unshot_cells_checkerboard.append((r, c))

    if unshot_cells_checkerboard:
        # Prioritize cells in the center of the board
        center_sort_key = lambda cell: abs(cell[0] - rows/2 + 0.5) + abs(cell[1] - cols/2 + 0.5)
        unshot_cells_checkerboard.sort(key=center_sort_key)
        return random.choice(unshot_cells_checkerboard[:len(unshot_cells_checkerboard)//4 + 1]) # Take a random from top 25% of central cells
    
    # If initial checkerboard cells are exhausted, try the other checkerboard pattern (r+c is odd)
    unshot_cells_other_checkerboard = []
    for r in range(rows):
        for c in range(cols):
            if board[r, c] == 0 and (r + c) % 2 == 1:
                unshot_cells_other_checkerboard.append((r, c))
    
    if unshot_cells_other_checkerboard:
        center_sort_key = lambda cell: abs(cell[0] - rows/2 + 0.5) + abs(cell[1] - cols/2 + 0.5)
        unshot_cells_other_checkerboard.sort(key=center_sort_key)
        return random.choice(unshot_cells_other_checkerboard[:len(unshot_cells_other_checkerboard)//4 + 1])


    # Fallback: If for some reason checkerboard patterns are exhausted
    # or no valid shot found by the above logic, just pick any unshot cell.
    unshot_cells = list(zip(*np.where(board == 0)))
    if unshot_cells:
        return random.choice(unshot_cells)

    # Should not happen in a correctly functioning game loop if there are still unshot cells
    # and the policy is called correctly. If it does, it implies no valid moves left.
    return (0, 0) # Default if no valid moves (shouldn't occur)
