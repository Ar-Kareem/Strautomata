
import numpy as np
import random

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # Convert board to numpy array
    board_array = np.array(board)
    
    # Check all possible lines for a winning move or block
    lines = []
    
    # Add all rows, columns, and depths
    for i in range(3):
        for j in range(3):
            lines.append(board_array[i, j, :])  # depth lines
            lines.append(board_array[i, :, j])  # column lines
            lines.append(board_array[:, i, j])  # row lines
    
    # Add all 4 space diagonals
    lines.append(np.array([board_array[i, i, i] for i in range(3)]))  # main diagonal
    lines.append(np.array([board_array[i, i, 2-i] for i in range(3)]))  # anti-diagonal in depth
    lines.append(np.array([board_array[i, 2-i, i] for i in range(3)]))  # other diagonal
    lines.append(np.array([board_array[2-i, i, i] for i in range(3)]))  # other diagonal
    
    # Check for winning move (two 1s and one 0)
    for line in lines:
        if np.sum(line == 1) == 2 and np.sum(line == 0) == 1:
            empty_pos = np.where(line == 0)[0][0]
            # Find the 3D coordinates of this empty position
            # This requires checking which line type we're looking at
            # For simplicity, we'll search the whole board for matching pattern
            pass
    
    # Search for empty positions that would complete three 1s
    empty_positions = np.argwhere(board_array == 0)
    for pos in empty_positions:
        x, y, z = pos
        # Temporarily place our mark
        board_array[x, y, z] = 1
        # Check if this creates a win
        if check_win(board_array, 1):
            return tuple(pos)
        # Undo the move
        board_array[x, y, z] = 0
    
    # Check for opponent's winning move (two -1s and one 0)
    for pos in empty_positions:
        x, y, z = pos
        # Temporarily place opponent's mark
        board_array[x, y, z] = -1
        # Check if this creates a win for them
        if check_win(board_array, -1):
            board_array[x, y, z] = 0  # undo
            return tuple(pos)
        # Undo the move
        board_array[x, y, z] = 0
    
    # Try to take the center if available
    if board_array[1, 1, 1] == 0:
        return (1, 1, 1)
    
    # Try to take a corner if available
    corners = [(0, 0, 0), (0, 0, 2), (0, 2, 0), (0, 2, 2),
               (2, 0, 0), (2, 0, 2), (2, 2, 0), (2, 2, 2)]
    random.shuffle(corners)  # randomize corner selection
    for corner in corners:
        if board_array[corner] == 0:
            return corner
    
    # If all else fails, choose randomly from remaining empty positions
    if len(empty_positions) > 0:
        return tuple(random.choice(empty_positions))
    
    # Fallback (shouldn't reach here if board isn't full)
    return (0, 0, 0)

def check_win(board: np.ndarray, player: int) -> bool:
    """Check if the specified player has won."""
    # Check all rows, columns, and depths
    for i in range(3):
        for j in range(3):
            if np.all(board[i, j, :] == player):  # depth line
                return True
            if np.all(board[i, :, j] == player):  # column line
                return True
            if np.all(board[:, i, j] == player):  # row line
                return True
    
    # Check all 4 space diagonals
    if np.all(np.array([board[i, i, i] for i in range(3)]) == player):
        return True
    if np.all(np.array([board[i, i, 2-i] for i in range(3)]) == player):
        return True
    if np.all(np.array([board[i, 2-i, i] for i in range(3)]) == player):
        return True
    if np.all(np.array([board[2-i, i, i] for i in range(3)]) == player):
        return True
    
    return False
