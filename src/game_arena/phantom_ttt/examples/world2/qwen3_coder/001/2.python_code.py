
import numpy as np

def policy(board: list[list[int]]) -> int:
    # Convert to numpy array for easier handling
    board_np = np.array(board)
    
    # Get all available positions (where we haven't confirmed our mark)
    available_positions = []
    for i in range(3):
        for j in range(3):
            if board_np[i][j] != 1:  # Not already confirmed as ours
                available_positions.append((i, j))
    
    # Check for immediate win opportunities
    for pos in available_positions:
        # Simulate placing our mark
        test_board = board_np.copy()
        test_board[pos[0]][pos[1]] = 1
        
        # Check if this creates a win for us
        if check_win(test_board):
            return pos
    
    # Check for opponent win prevention
    # In phantom tic-tac-toe, we don't know opponent positions, 
    # but we can assume they might be about to win on any available cell
    
    # For now, let's use a strategic approach:
    # 1. Prefer center if available
    if (1, 1) in available_positions:
        return (1, 1)
    
    # 2. Prefer corners
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    available_corners = [pos for pos in corners if pos in available_positions]
    if available_corners:
        return available_corners[0]
    
    # 3. Take any remaining edge
    return available_positions[0]

def check_win(board):
    # Check rows
    for row in board:
        if np.sum(row) == 3:
            return True
    
    # Check columns
    for col in range(3):
        if np.sum(board[:, col]) == 3:
            return True
    
    # Check diagonals
    if board[0, 0] + board[1, 1] + board[2, 2] == 3:
        return True
    if board[0, 2] + board[1, 1] + board[2, 0] == 3:
        return True
    
    return False
