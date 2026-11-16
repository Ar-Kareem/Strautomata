
import random
import numpy as np

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # Convert to numpy array for easier manipulation
    board_array = np.array(board)

    # Get all empty cells
    empty_cells = []
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board_array[i, j, k] == 0:
                    empty_cells.append((i, j, k))

    # If no empty cells, return None (though game should be over)
    if not empty_cells:
        return (0, 0, 0)

    # Check for winning moves
    for cell in empty_cells:
        i, j, k = cell
        # Temporarily place AI's mark
        board_array[i, j, k] = 1
        if check_win(board_array, 1):
            return cell
        # Undo the move
        board_array[i, j, k] = 0

    # Check for blocking moves (opponent's winning moves)
    for cell in empty_cells:
        i, j, k = cell
        # Temporarily place opponent's mark
        board_array[i, j, k] = -1
        if check_win(board_array, -1):
            return cell
        # Undo the move
        board_array[i, j, k] = 0

    # Prioritize center (1,1,1)
    center = (1, 1, 1)
    if center in empty_cells:
        return center

    # Prioritize corners (all combinations where each coordinate is 0 or 2)
    corners = [(i, j, k) for i in [0, 2] for j in [0, 2] for k in [0, 2]]
    for corner in corners:
        if corner in empty_cells:
            return corner

    # If no strategic move, return a random empty cell
    return random.choice(empty_cells)

def check_win(board_array: np.ndarray, player: int) -> bool:
    # Check all possible winning lines in 3D Tic Tac Toe

    # Check layers (z-axis)
    for layer in range(3):
        # Check rows in layer
        for row in range(3):
            if all(board_array[layer, row, col] == player for col in range(3)):
                return True
        # Check columns in layer
        for col in range(3):
            if all(board_array[layer, row, col] == player for row in range(3)):
                return True
        # Check diagonals in layer
        if board_array[layer, 0, 0] == board_array[layer, 1, 1] == board_array[layer, 2, 2] == player:
            return True
        if board_array[layer, 0, 2] == board_array[layer, 1, 1] == board_array[layer, 2, 0] == player:
            return True

    # Check rows across layers (x-axis)
    for row in range(3):
        for col in range(3):
            if all(board_array[layer, row, col] == player for layer in range(3)):
                return True

    # Check columns across layers (y-axis)
    for row in range(3):
        for col in range(3):
            if all(board_array[layer, row, col] == player for layer in range(3)):
                return True

    # Check space diagonals (3D diagonals)
    # Main space diagonal
    if board_array[0, 0, 0] == board_array[1, 1, 1] == board_array[2, 2, 2] == player:
        return True
    # Other space diagonals
    if board_array[0, 0, 2] == board_array[1, 1, 1] == board_array[2, 2, 0] == player:
        return True
    if board_array[0, 2, 0] == board_array[1, 1, 1] == board_array[2, 0, 2] == player:
        return True
    if board_array[0, 2, 2] == board_array[1, 1, 1] == board_array[2, 0, 0] == player:
        return True

    return False
