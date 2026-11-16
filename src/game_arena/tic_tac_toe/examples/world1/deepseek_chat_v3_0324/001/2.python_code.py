
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert board to numpy array for easier manipulation
    board = np.array(board)
    
    # Check for immediate winning move
    for i in range(3):
        for j in range(3):
            if board[i, j] == 0:
                # Test if placing here wins
                board[i, j] = 1
                if check_win(board, 1):
                    return (i, j)
                board[i, j] = 0
    
    # Check for opponent's immediate winning move to block
    for i in range(3):
        for j in range(3):
            if board[i, j] == 0:
                # Test if opponent would win here
                board[i, j] = -1
                if check_win(board, -1):
                    board[i, j] = 0
                    return (i, j)
                board[i, j] = 0
    
    # Take center if available
    if board[1, 1] == 0:
        return (1, 1)
    
    # Take a corner if available
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    for i, j in corners:
        if board[i, j] == 0:
            return (i, j)
    
    # Take any available side
    sides = [(0, 1), (1, 0), (1, 2), (2, 1)]
    for i, j in sides:
        if board[i, j] == 0:
            return (i, j)
    
    # Fallback (shouldn't reach here if board isn't full)
    for i in range(3):
        for j in range(3):
            if board[i, j] == 0:
                return (i, j)
    return (0, 0)

def check_win(board: np.ndarray, player: int) -> bool:
    # Check rows and columns
    for i in range(3):
        if np.all(board[i, :] == player) or np.all(board[:, i] == player):
            return True
    # Check diagonals
    if np.all(np.diag(board) == player) or np.all(np.diag(np.fliplr(board)) == player):
        return True
    return False
