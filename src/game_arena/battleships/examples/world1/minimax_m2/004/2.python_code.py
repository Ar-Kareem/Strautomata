
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Precompute the parity cells (cells where (row+col) is even) only once per call? 
    # But the grid is fixed, so we can precompute outside the function? However, the function is called multiple times.
    # We precompute here for the current call.
    parity_cells = set()
    for r in range(10):
        for c in range(10):
            if (r + c) % 2 == 0:
                parity_cells.add((r, c))

    # Step 1: Build set of shots taken (both hit and miss)
    shots_taken = set()
    for r in range(10):
        for c in range(10):
            if board[r][c] != 0:  # fired at
                shots_taken.add((r, c))

    # Step 2: Build target_set: cells adjacent to any hit that we haven't fired at
    target_set = set()
    for r in range(10):
        for c in range(10):
            if board[r][c] == 1:  # hit
                # Check the four neighbors
                for (nr, nc) in [(r-1, c), (r+1, c), (r, c-1), (r, c+1)]:
                    if 0 <= nr < 10 and 0 <= nc < 10 and (nr, nc) not in shots_taken:
                        target_set.add((nr, nc))

    # Step 3: Hunt set: parity cells not in shots_taken
    hunt_set = parity_cells - shots_taken

    # Step 4: If there are target cells, choose from target_set
    if target_set:
        choice = random.choice(list(target_set))
        return choice

    # Step 5: If no target cells but there are hunt cells, choose from hunt_set
    elif hunt_set:
        choice = random.choice(list(hunt_set))
        return choice

    # Step 6: If neither, choose from all unshot cells
    else:
        unshot = set()
        for r in range(10):
            for c in range(10):
                if board[r][c] == 0:
                    unshot.add((r, c))
        if unshot:
            choice = random.choice(list(unshot))
            return choice
        else:
            # This should not happen, but if all cells are shot, return (0,0) (though it will be invalid and not chosen again)
            return (0, 0)
