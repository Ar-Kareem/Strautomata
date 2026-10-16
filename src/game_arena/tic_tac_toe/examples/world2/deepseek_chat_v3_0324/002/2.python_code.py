
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    board_array = np.array(board)
    
    # Check for immediate winning move
    for i in range(4):
        for j in range(4):
            if board_array[i, j] == 0:
                board_array[i, j] = 1
                if check_win(board_array, 1):
                    return (i, j)
                board_array[i, j] = 0
    
    # Check for opponent's immediate threat
    for i in range(4):
        for j in range(4):
            if board_array[i, j] == 0:
                board_array[i, j] = -1
                if check_win(board_array, -1):
                    board_array[i, j] = 0
                    return (i, j)
                board_array[i, j] = 0
    
    # Priority order: center (2x2), corners, then edges
    priority_squares = [
        (1, 1), (1, 2), (2, 1), (2, 2),  # Center 2x2
        (0, 0), (0, 3), (3, 0), (3, 3),  # Corners
        (0, 1), (0, 2), (1, 0), (1, 3),  # Edges
        (2, 0), (2, 3), (3, 1), (3, 2)   # Edges
    ]
    
    for i, j in priority_squares:
        if board_array[i, j] == 0:
            return (i, j)
    
    # Fallback (shouldn't reach here if board isn't full)
    for i in range(4):
        for j in range(4):
            if board_array[i, j] == 0:
                return (i, j)
    return (0, 0)

def check_win(board: np.ndarray, player: int) -> bool:
    # Check rows
    for i in range(4):
        if np.sum(board[i, :] == player) >= 3:
            return True
    
    # Check columns
    for j in range(4):
        if np.sum(board[:, j] == player) >= 3:
            return True
    
    # Check diagonals
    if np.sum(np.diag(board) == player) >= 3:
        return True
    if np.sum(np.diag(np.fliplr(board)) == player) >= 3:
        return True
    
    return False
