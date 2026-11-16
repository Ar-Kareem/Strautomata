
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert to numpy array for easier manipulation
    board = np.array(board)
    
    # Get empty positions
    empty_positions = [(i, j) for i in range(3) for j in range(3) if board[i][j] == 0]
    
    # If no moves left, return something (shouldn't happen in valid game)
    if not empty_positions:
        return (0, 0)
    
    # 1. Check if we can win in one move
    for i, j in empty_positions:
        board[i][j] = 1  # Try placing our mark
        if check_win(board, 1):
            board[i][j] = 0  # Reset
            return (i, j)
        board[i][j] = 0  # Reset
    
    # 2. Block opponent from winning
    for i, j in empty_positions:
        board[i][j] = -1  # Try placing opponent's mark
        if check_win(board, -1):
            board[i][j] = 0  # Reset
            return (i, j)
        board[i][j] = 0  # Reset
    
    # 3. Take center if available
    if board[1][1] == 0:
        return (1, 1)
    
    # 4. Take a corner if available (prioritize corners)
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    for corner in corners:
        if board[corner[0]][corner[1]] == 0:
            return corner
    
    # 5. Take any remaining edge
    edges = [(0, 1), (1, 0), (1, 2), (2, 1)]
    for edge in edges:
        if board[edge[0]][edge[1]] == 0:
            return edge
    
    # Fallback (shouldn't reach here if board is valid)
    return empty_positions[0]

def check_win(board, player):
    # Check rows
    for i in range(3):
        if np.all(board[i] == player):
            return True
    
    # Check columns
    for j in range(3):
        if np.all(board[:, j] == player):
            return True
    
    # Check diagonals
    if board[0, 0] == player and board[1, 1] == player and board[2, 2] == player:
        return True
    if board[0, 2] == player and board[1, 1] == player and board[2, 0] == player:
        return True
    
    return False
