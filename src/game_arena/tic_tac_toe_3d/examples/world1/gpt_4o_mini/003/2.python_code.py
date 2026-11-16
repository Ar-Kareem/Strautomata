
import numpy as np

def check_win(board: np.ndarray, player: int) -> bool:
    """Check if a given player has a winning condition."""
    size = 3

    # Check rows, columns, and depths
    for i in range(size):
        for j in range(size):
            if all(board[i, j, :] == player) or all(board[i, :, j] == player) or all(board[:, i, j] == player):
                return True
    
    # Check 2D diagonals in each layer
    for k in range(size):
        if all(board[k, i, i] == player for i in range(size)) or all(board[k, i, size - 1 - i] == player for i in range(size)):
            return True

    # Check main diagonals through layers
    if all(board[i, i, i] == player for i in range(size)) or all(board[i, i, size - 1 - i] == player for i in range(size)):
        return True
    if all(board[i, size - 1 - i, i] == player for i in range(size)) or all(board[size - 1 - i, i, i] == player for i in range(size)):
        return True

    return False

def get_empty_positions(board: np.ndarray) -> list[tuple[int, int, int]]:
    """Get list of empty positions."""
    return list(zip(*np.where(board == 0)))

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    board_np = np.array(board)
    
    # Check for a winning move for myself
    empty_positions = get_empty_positions(board_np)
    for position in empty_positions:
        x, y, z = position
        board_np[x, y, z] = 1  # Try the move
        if check_win(board_np, 1):
            return (x, y, z)
        board_np[x, y, z] = 0  # Undo the move

    # Check for a blocking move against the opponent
    for position in empty_positions:
        x, y, z = position
        board_np[x, y, z] = -1  # Try the move
        if check_win(board_np, -1):
            return (x, y, z)
        board_np[x, y, z] = 0  # Undo the move

    # If no immediate win or block, choose a random empty position
    if empty_positions:
        return empty_positions[0]  # Just take the first available move

    # In case of no available moves (should not happen in a normal game)
    return (-1, -1, -1)  # Indicate no move possible
