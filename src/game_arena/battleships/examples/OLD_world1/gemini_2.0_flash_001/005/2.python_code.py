
import numpy as np
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Implements a targeting policy for a Battleship-like game on a 10x10 grid.

    Args:
        board: A 10x10 list of lists representing the current knowledge of the opponent's grid.
               0 - unknown cell, -1 - miss, 1 - hit.

    Returns:
        A tuple (row, col) with integers in the range 0-9, representing the chosen cell to fire at.
    """

    board_np = np.array(board)

    # Prioritize targeting adjacent cells to hits
    hit_cells = np.argwhere(board_np == 1)
    if len(hit_cells) > 0:
        possible_targets = []
        for row, col in hit_cells:
            adjacent_cells = [(row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)]
            for r, c in adjacent_cells:
                if 0 <= r < 10 and 0 <= c < 10 and board_np[r, c] == 0:
                    possible_targets.append((r, c))

        if len(possible_targets) > 0:
            return random.choice(possible_targets)

    # If no hits, use a probabilistic targeting strategy
    # Higher probability for cells that are more likely to contain a ship
    # This approach prioritizes odd cells and reduces clustering of shots
    probabilities = np.zeros((10, 10))
    for r in range(10):
        for c in range(10):
            if board_np[r, c] == 0:
                probabilities[r, c] = 1.0

    # Reduce clustering and look for ship possibilities by prefering odds
    for r in range(10):
        for c in range(10):
          if (r+c) % 2 == 0:
              probabilities[r,c] *= 0.5

    #If we hit a ship on another turn, prefer the row of all the other ships we previously hit. 
    #The idea is to focus a lot on one row to sink a ship instead of jumping all around the place. 
    
    
    # Normalize probabilities to sum to 1
    if np.sum(probabilities) > 0:
        probabilities /= np.sum(probabilities)

        # Choose a cell based on the probabilities
        chosen_cell = np.random.choice(np.arange(100), p=probabilities.flatten())
        row, col = divmod(chosen_cell, 10)
        return (row, col)

    # If all cells are targeted, return a random remaining cell (shouldn't happen)
    remaining_cells = np.argwhere(board_np == 0)
    if len(remaining_cells) > 0:
        return tuple(random.choice(remaining_cells).tolist())

    # If everything is targeted, return (0,0), even though this shouldn't happen.
    return (0, 0)
