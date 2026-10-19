
import random
import numpy as np

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    n = len(board)
    current_board = np.array(board)
    
    # Define check_win function to determine if a player has won
    def check_win(board_state, player):
        # Check all possible winning lines: rows, columns, depths, and diagonals
        
        # Check rows, columns, and depths
        for i in range(n):
            for j in range(n):
                if np.all(board_state[i, j, :] == player) or \
                   np.all(board_state[i, :, j] == player) or \
                   np.all(board_state[:, i, j] == player):
                    return True
        
        # Check main diagonals of each 2D slice
        for i in range(n):
            if np.all(np.diag(board_state[i, :, :]) == player) or \
               np.all(np.diag(np.fliplr(board_state[i, :, :])) == player) or \
               np.all(np.diag(board_state[:, i, :]) == player) or \
               np.all(np.diag(np.fliplr(board_state[:, i, :])) == player) or \
               np.all(np.diag(board_state[:, :, i]) == player) or \
               np.all(np.diag(np.fliplr(board_state[:, :, i])) == player):
                return True
        
        # Check 3D main diagonals
        if np.all(np.array([board_state[i, i, i] for i in range(n)]) == player) or \
           np.all(np.array([board_state[i, i, n - 1 - i] for i in range(n)]) == player) or \
           np.all(np.array([board_state[i, n - 1 - i, i] for i in range(n)]) == player) or \
           np.all(np.array([board_state[n - 1 - i, i, i] for i in range(n)]) == player):
            return True
        
        return False

    # Get all empty cells
    empty_cells = []
    for x in range(n):
        for y in range(n):
            for z in range(n):
                if current_board[x, y, z] == 0:
                    empty_cells.append((x, y, z))

    # If no empty cells, return (this should not happen in a valid game state for a policy move)
    if not empty_cells:
        # Fallback for an unlikely edge case where policy is called on a full board
        # This will likely lead to an error in the arena if it's not handled by the game engine
        # For submission, we must return a tuple, so returning a default one that would be invalid is the best we can do.
        return (0, 0, 0) 

    # 1. Win if possible
    for (x, y, z) in empty_cells:
        temp_board = np.copy(current_board)
        temp_board[x, y, z] = 1  # Try placing our piece
        if check_win(temp_board, 1):
            return (x, y, z)

    # 2. Block immediate opponent win
    for (x, y, z) in empty_cells:
        temp_board = np.copy(current_board)
        temp_board[x, y, z] = -1  # Try placing opponent's piece
        if check_win(temp_board, -1):
            return (x, y, z)

    # 3. Prioritize center cells (if n is odd and applicable)
    if n % 2 == 1:
        center = n // 2
        center_cell = (center, center, center)
        if center_cell in empty_cells:
            return center_cell

    # 4. Take a corner cell
    corners = []
    for x in [0, n - 1]:
        for y in [0, n - 1]:
            for z in [0, n - 1]:
                if (x, y, z) in empty_cells:
                    corners.append((x, y, z))
    if corners:
        return random.choice(corners)

    # 5. Take any available random empty cell
    return random.choice(empty_cells)

