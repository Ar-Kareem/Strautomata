
import numpy as np

def policy(board):
    """Return the next shot (row, col) for a 10×10 Battleship board.

    board – list of lists: 0 = unknown, -1 = miss, 1 = hit.
    """
    # Convert to a numpy array for fast slice operations
    board = np.array(board, dtype=int)

    # Mask of cells we have not fired at yet
    unknown = (board == 0)

    # Score matrix: the more still‑possible placements cover a cell,
    # the higher its score.
    scores = np.zeros_like(board, dtype=int)

    # Ship lengths in the game (two ships of length 3)
    ship_lengths = [5, 4, 3, 3, 2]

    # -----------------------------------------------------------------
    # Count all placements that are still possible for each ship
    for length in ship_lengths:
        max_start_col = 10 - length
        max_start_row = 10 - length

        # ----- Horizontal placements -----
        for r in range(10):
            for c in range(max_start_col + 1):
                segment = board[r, c:c + length]
                # Placement is invalid if it touches a known miss
                if np.any(segment == -1):
                    continue
                # Increase the score of each cell in this segment
                scores[r, c:c + length] += 1

        # ----- Vertical placements -----
        for r in range(max_start_row + 1):
            for c in range(10):
                segment = board[r:r + length, c]
                if np.any(segment == -1):
                    continue
                scores[r:r + length, c] += 1

    # -----------------------------------------------------------------
    # Choose the unknown cell with the highest score
    best_score = -1
    best_move = None
    for r in range(10):
        for c in range(10):
            if unknown[r, c] and scores[r, c] > best_score:
                best_score = scores[r, c]
                best_move = (r, c)

    # In the extremely unlikely case that every cell has already been shot,
    # we return a dummy move – the game should already be over.
    if best_move is None:
        best_move = (0, 0)

    return best_move
