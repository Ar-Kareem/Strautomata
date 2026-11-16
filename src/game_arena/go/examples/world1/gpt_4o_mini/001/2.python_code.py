
import numpy as np

def liberty_count(board, row, col):
    """Count the number of liberties for a potential move."""
    adjacent_positions = [
        (row - 1, col), (row + 1, col),
        (row, col - 1), (row, col + 1)
    ]
    liberties = 0
    for r, c in adjacent_positions:
        if 1 <= r <= 19 and 1 <= c <= 19:  # Check bounds
            if board[r, c] == 0:  # Empty
                liberties += 1
    return liberties

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    board = np.zeros((20, 20), dtype=int)  # Create a 19x19 board
    for r, c in me:
        board[r, c] = 1  # My stones
    for r, c in opponent:
        board[r, c] = -1  # Opponent's stones

    best_move = None
    best_liberty = -1

    # Evaluate all possible moves
    for row in range(1, 20):
        for col in range(1, 20):
            if board[row, col] == 0:  # Only consider empty positions
                current_liberty = liberty_count(board, row, col)
                if current_liberty > best_liberty:
                    best_liberty = current_liberty
                    best_move = (row, col)
    
    # If we haven't found any move, we will pass
    if best_move is None:
        return (0, 0)

    return best_move
