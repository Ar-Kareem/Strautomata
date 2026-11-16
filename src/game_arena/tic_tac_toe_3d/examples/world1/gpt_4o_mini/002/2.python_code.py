
import numpy as np

def check_winner(board: np.ndarray, player: int) -> bool:
    # Check rows, columns, and depths
    for i in range(3):
        if np.all(board[i, :, :] == player) or np.all(board[:, i, :] == player) or np.all(board[:, :, i] == player):
            return True

    # Check diagonals in each layer
    for i in range(3):
        if np.all(np.diag(board[i, :, :]) == player) or np.all(np.diag(np.fliplr(board[i, :, :])) == player):
            return True
        if np.all(np.diag(board[:, i, :]) == player) or np.all(np.diag(np.fliplr(board[:, i, :])) == player):
            return True

    # Check diagonals across layers
    if np.all(np.diag(board) == player) or np.all(np.diag(np.fliplr(board)) == player):
        return True
    
    # Check the remaining layer diagonals
    if np.all(np.diag(board[:, :, 0]) == player) or np.all(np.diag(np.fliplr(board[:, :, 0])) == player):
        return True
    if np.all(np.diag(board[:, :, 2]) == player) or np.all(np.diag(np.fliplr(board[:, :, 2])) == player):
        return True

    return False

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    board_np = np.array(board)
    empty_positions = [(i, j, k) for i in range(3) for j in range(3) for k in range(3) if board_np[i, j, k] == 0]
    
    # Check for winning move for 'you' (1)
    for position in empty_positions:
        board_np[position] = 1  # Try your move
        if check_winner(board_np, 1):
            return position
        board_np[position] = 0  # Reset
    
    # Check for blocking move for opponent (-1)
    for position in empty_positions:
        board_np[position] = -1  # Try opponent's move
        if check_winner(board_np, -1):
            board_np[position] = 0  # Reset
            return position
        board_np[position] = 0  # Reset

    # If no immediate win or block, return the first available move
    return empty_positions[0] if empty_positions else (-1, -1, -1)  # Should not reach here under normal conditions
