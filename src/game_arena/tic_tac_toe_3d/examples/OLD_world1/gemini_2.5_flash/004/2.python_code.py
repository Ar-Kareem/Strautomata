
import random
import numpy as np

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    n = len(board)
    current_board = np.array(board)

    # Helper function to check if a player has won
    def check_win(current_board_state, player):
        # Check all possible winning lines for a given player
        # Lines: rows, columns, stacks, main diagonals, and space diagonals

        # 1. Check rows, columns, and stacks within each layer
        for i in range(n):
            for j in range(n):
                if np.all(current_board_state[i, j, :] == player) or \
                   np.all(current_board_state[i, :, j] == player) or \
                   np.all(current_board_state[:, i, j] == player):
                    return True

        # 2. Check main diagonals within each layer
        for i in range(n):
            if np.all(np.diag(current_board_state[i, :, :]) == player) or \
               np.all(np.diag(np.fliplr(current_board_state[i, :, :])) == player) or \
               np.all(np.diag(current_board_state[:, i, :]) == player) or \
               np.all(np.diag(np.fliplr(current_board_state[:, i, :])) == player) or \
               np.all(np.diag(current_board_state[:, :, i]) == player) or \
               np.all(np.diag(np.fliplr(current_board_state[:, :, i])) == player):
                return True

        # 3. Check space diagonals (4 of them)
        if np.all(np.array([current_board_state[i, i, i] for i in range(n)]) == player) or \
           np.all(np.array([current_board_state[i, i, n - 1 - i] for i in range(n)]) == player) or \
           np.all(np.array([current_board_state[i, n - 1 - i, i] for i in range(n)]) == player) or \
           np.all(np.array([current_board_state[n - 1 - i, i, i] for i in range(n)]) == player):
            return True
        
        return False

    empty_cells = []
    for x in range(n):
        for y in range(n):
            for z in range(n):
                if current_board[x, y, z] == 0:
                    empty_cells.append((x, y, z))

    # 1. Check for a winning move for self (player 1)
    for (x, y, z) in empty_cells:
        temp_board = np.copy(current_board)
        temp_board[x, y, z] = 1
        if check_win(temp_board, 1):
            return (x, y, z)

    # 2. Check for a blocking move for the opponent (player -1)
    for (x, y, z) in empty_cells:
        temp_board = np.copy(current_board)
        temp_board[x, y, z] = -1
        if check_win(temp_board, -1):
            return (x, y, z)

    # 3. Try to take the center if available (for 3x3x3)
    if n == 3:
        center = (1, 1, 1)
        if current_board[center] == 0:
            return center

    # 4. Take a corner if available (for 3x3x3) - extendable to other n
    corners = []
    if n == 3:
        corners = [(0,0,0), (0,0,2), (0,2,0), (0,2,2),
                   (2,0,0), (2,0,2), (2,2,0), (2,2,2)]
    
    for x,y,z in corners:
        if current_board[x,y,z] == 0:
            return (x,y,z)

    # 5. Otherwise, pick a random empty cell
    if empty_cells:
        return random.choice(empty_cells)

    # Should not happen in a valid game, but return an error or default if no empty cells
    # This implies the board is full, which likely means a draw or an error in game state.
    raise ValueError("No empty cells left on the board.")

