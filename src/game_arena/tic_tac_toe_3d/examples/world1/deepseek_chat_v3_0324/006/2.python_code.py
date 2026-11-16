
import numpy as np
import random

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # Convert board to numpy array for easier manipulation
    board_array = np.array(board)
    
    # Generate all possible lines in 3D space
    lines = []
    
    # Rows (x varies) in each y,z plane
    for y in range(3):
        for z in range(3):
            lines.append(board_array[:, y, z])
    
    # Columns (y varies) in each x,z plane
    for x in range(3):
        for z in range(3):
            lines.append(board_array[x, :, z])
    
    # Depths (z varies) in each x,y plane
    for x in range(3):
        for y in range(3):
            lines.append(board_array[x, y, :])
    
    # Diagonals within each plane
    for z in range(3):
        lines.append([board_array[i, i, z] for i in range(3)])  # Main diagonal in x,y plane
        lines.append([board_array[2-i, i, z] for i in range(3)])  # Anti-diagonal in x,y plane
    
    for y in range(3):
        lines.append([board_array[i, y, i] for i in range(3)])  # Main diagonal in x,z plane
        lines.append([board_array[2-i, y, i] for i in range(3)])  # Anti-diagonal in x,z plane
    
    for x in range(3):
        lines.append([board_array[x, i, i] for i in range(3)])  # Main diagonal in y,z plane
        lines.append([board_array[x, 2-i, i] for i in range(3)])  # Anti-diagonal in y,z plane
    
    # Space diagonals
    lines.append([board_array[i, i, i] for i in range(3)])
    lines.append([board_array[2-i, i, i] for i in range(3)])
    lines.append([board_array[i, 2-i, i] for i in range(3)])
    lines.append([board_array[i, i, 2-i] for i in range(3)])
    
    # Check for winning move (two 1s and one 0)
    for line in lines:
        if np.sum(line == 1) == 2 and np.sum(line == 0) == 1:
            empty_pos = np.where(line == 0)[0][0]
            # Need to find which coordinates this corresponds to in the original board
            # This is complex, so we'll use a different approach
            
    # Alternative approach: check all empty cells for winning moves
    empty_cells = [(x, y, z) for x in range(3) for y in range(3) for z in range(3) if board_array[x, y, z] == 0]
    
    # Check for immediate win
    for (x, y, z) in empty_cells:
        # Temporarily place our mark
        board_array[x, y, z] = 1
        # Check if this creates a win
        if check_win(board_array, 1):
            return (x, y, z)
        # Undo the temporary placement
        board_array[x, y, z] = 0
    
    # Check for opponent's immediate win
    for (x, y, z) in empty_cells:
        # Temporarily place opponent's mark
        board_array[x, y, z] = -1
        # Check if this creates a win for opponent
        if check_win(board_array, -1):
            # Block by taking this position
            board_array[x, y, z] = 0  # Undo temporary placement
            return (x, y, z)
        # Undo the temporary placement
        board_array[x, y, z] = 0
    
    # Try to take center if available
    if board_array[1, 1, 1] == 0:
        return (1, 1, 1)
    
    # If no strategic moves, choose random empty cell
    return random.choice(empty_cells)

def check_win(board: np.ndarray, player: int) -> bool:
    """Check if the specified player has a winning line."""
    # Check all rows, columns, depths, and diagonals
    # Rows (x varies)
    for y in range(3):
        for z in range(3):
            if np.all(board[:, y, z] == player):
                return True
    # Columns (y varies)
    for x in range(3):
        for z in range(3):
            if np.all(board[x, :, z] == player):
                return True
    # Depths (z varies)
    for x in range(3):
        for y in range(3):
            if np.all(board[x, y, :] == player):
                return True
    # Diagonals within each plane
    for z in range(3):
        if np.all([board[i, i, z] == player for i in range(3)]):
            return True
        if np.all([board[2-i, i, z] == player for i in range(3)]):
            return True
    for y in range(3):
        if np.all([board[i, y, i] == player for i in range(3)]):
            return True
        if np.all([board[2-i, y, i] == player for i in range(3)]):
            return True
    for x in range(3):
        if np.all([board[x, i, i] == player for i in range(3)]):
            return True
        if np.all([board[x, 2-i, i] == player for i in range(3)]):
            return True
    # Space diagonals
    if np.all([board[i, i, i] == player for i in range(3)]):
        return True
    if np.all([board[2-i, i, i] == player for i in range(3)]):
        return True
    if np.all([board[i, 2-i, i] == player for i in range(3)]):
        return True
    if np.all([board[i, i, 2-i] == player for i in range(3)]):
        return True
    return False
