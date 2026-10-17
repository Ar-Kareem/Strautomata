
import numpy as np
import random

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # Convert board to numpy array for easier manipulation
    board_np = np.array(board)
    
    # List all empty positions
    empty_positions = [(x, y, z) for x in range(3) for y in range(3) for z in range(3) if board[x][y][z] == 0]
    
    # Check for winning moves (place that would make 3 in a row for us)
    for pos in empty_positions:
        temp_board = board_np.copy()
        temp_board[pos] = 1
        if check_win(temp_board, 1):
            return pos
    
    # Check for blocking moves (opponent would win next turn)
    for pos in empty_positions:
        temp_board = board_np.copy()
        temp_board[pos] = -1
        if check_win(temp_board, -1):
            return pos
    
    # Prefer center position if available
    if (1, 1, 1) in empty_positions:
        return (1, 1, 1)
    
    # Then prefer corners
    corners = [(0, 0, 0), (0, 0, 2), (0, 2, 0), (0, 2, 2),
               (2, 0, 0), (2, 0, 2), (2, 2, 0), (2, 2, 2)]
    for corner in corners:
        if corner in empty_positions:
            return corner
    
    # If none of the above, choose randomly
    return random.choice(empty_positions)

def check_win(board: np.ndarray, player: int) -> bool:
    # Check all possible lines in 3D space
    # Rows in each dimension
    for dim in range(3):
        for i in range(3):
            for j in range(3):
                if np.all(board.take(i, axis=dim).take(j, axis=(dim+1)%3) == player):
                    return True
    
    # Diagonals in each plane
    for dim in range(3):
        if np.all(np.diagonal(board.take(0, axis=dim)) == player):
            return True
        if np.all(np.diagonal(np.flipud(board.take(0, axis=dim))) == player):
            return True
    
    # Space diagonals
    if board[0, 0, 0] == board[1, 1, 1] == board[2, 2, 2] == player:
        return True
    if board[0, 0, 2] == board[1, 1, 1] == board[2, 2, 0] == player:
        return True
    if board[0, 2, 0] == board[1, 1, 1] == board[2, 0, 2] == player:
        return True
    if board[0, 2, 2] == board[1, 1, 1] == board[2, 0, 0] == player:
        return True
    
    return False
