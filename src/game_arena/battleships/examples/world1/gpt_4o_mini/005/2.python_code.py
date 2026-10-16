
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    hits = []
    misses = []
    targets = []

    # Scan the board and identify seen hits and misses
    for r in range(10):
        for c in range(10):
            if board[r][c] == 1:
                hits.append((r, c))
            elif board[r][c] == -1:
                misses.append((r, c))

    # If we have hits, we attempt to target the nearby cells to find the ship orientation
    if hits:
        last_hit = hits[-1]
        row, col = last_hit
        
        # Try to hit adjacent cells
        potential_targets = [
            (row-1, col), (row+1, col),
            (row, col-1), (row, col+1)
        ]
        for target in potential_targets:
            if 0 <= target[0] < 10 and 0 <= target[1] < 10 and board[target[0]][target[1]] == 0:
                return target  # Return the first valid surrounding target

    # If no hits or surrounding targets are found, look for new potential targets based on a checkerboard pattern
    if not targets:
        for r in range(10):
            for c in range(10):
                if board[r][c] == 0:
                    targets.append((r, c))

        # Optimize the selection to choose cells in a checkerboard manner to cover more area
        target_choice = []
        for r in range(10):
            for c in range(10):
                if (r + c) % 2 == 0 and board[r][c] == 0:
                    target_choice.append((r, c))

        if target_choice:
            return target_choice[np.random.randint(len(target_choice))]  # Randomly choose one from the available targets

    # Return a fallback choice if something goes wrong
    while targets:
        return targets.pop()

    # Ideally, this should never be reached, but it ensures the function always returns a legal move
    return (0, 0)
