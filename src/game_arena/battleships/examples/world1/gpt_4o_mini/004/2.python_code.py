
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert the board to a numpy array for easier manipulation
    grid = np.array(board)
    
    # Possible moves are the cells we haven't fired at yet (grid value 0)
    possible_moves = np.argwhere(grid == 0)
    
    # Check hits to prioritize the search around them
    hits = np.argwhere(grid == 1)
    if hits.size > 0:
        # If we have hits, we look for the adjacent cells
        potential_targets = set()
        for hit in hits:
            row, col = hit
            for d_row in [-1, 0, 1]:
                for d_col in [-1, 0, 1]:
                    if abs(d_row) != abs(d_col):  # Ensure we only check straight lines
                        new_row, new_col = row + d_row, col + d_col
                        if 0 <= new_row < 10 and 0 <= new_col < 10:
                            if grid[new_row][new_col] == 0:
                                potential_targets.add((new_row, new_col))
        
        if potential_targets:
            return potential_targets.pop()  # Return the first found potential target

    # If no hits, fall back to a systematic strategy or random choice
    if possible_moves.size > 0:
        return tuple(possible_moves[np.random.choice(possible_moves.shape[0])])

    # This should not happen, but if it does, choose the first possible move
    return (0, 0)

