
import numpy as np

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    n = len(board)
    board_arr = np.array(board)

    # Convert 0s to 0, 1s to 1, and -1s to -1 (already done by np.array)
    # The board already uses 1 for 'me' and -1 for 'opponent'

    # Check for immediate winning moves
    for r in range(n):
        for c in range(n):
            for d in range(n):
                if board_arr[r, c, d] == 0:
                    # Try placing 'me' here
                    board_arr[r, c, d] = 1
                    if check_win(board_arr, 1):
                        return r, c, d
                    board_arr[r, c, d] = 0  # Undo the move

    # Check for immediate blocking moves
    for r in range(n):
        for c in range(n):
            for d in range(n):
                if board_arr[r, c, d] == 0:
                    # Try placing 'opponent' here to see if they win
                    board_arr[r, c, d] = -1
                    if check_win(board_arr, -1):
                        return r, c, d
                    board_arr[r, c, d] = 0  # Undo the move

    # If no immediate win or block, try to play center if available
    if n % 2 == 1:
        center = n // 2
        if board_arr[center, center, center] == 0:
            return center, center, center

    # Otherwise, pick the first available empty cell
    for r in range(n):
        for c in range(n):
            for d in range(n):
                if board_arr[r, c, d] == 0:
                    return r, c, d

    # Should not happen in a valid game state (there should always be an empty cell if the game isn't over)
    return -1, -1, -1

def check_win(board_arr: np.ndarray, player: int) -> bool:
    n = len(board_arr)

    # Check all rows, columns, and depths
    for i in range(n):
        for j in range(n):
            # Rows in a plane (fixed depth)
            if np.all(board_arr[i, j, :] == player): return True
            # Columns in a plane (fixed depth)
            if np.all(board_arr[i, :, j] == player): return True
            # Depths (fixed row, col)
            if np.all(board_arr[:, i, j] == player): return True

    # Check major diagonals within each 2D plane
    for i in range(n):
        # XY-plane diagonals (fixed z)
        if np.all(np.diag(board_arr[:, :, i]) == player): return True
        if np.all(np.diag(np.fliplr(board_arr[:, :, i])) == player): return True
        # XZ-plane diagonals (fixed y)
        if np.all(np.diag(board_arr[:, i, :]) == player): return True
        if np.all(np.diag(np.fliplr(board_arr[:, i, :])) == player): return True
        # YZ-plane diagonals (fixed x)
        if np.all(np.diag(board_arr[i, :, :]) == player): return True
        if np.all(np.diag(np.fliplr(board_arr[i, :, :])) == player): return True

    # Check 3D space diagonals
    if np.all(np.array([board_arr[i, i, i] for i in range(n)]) == player): return True
    if np.all(np.array([board_arr[i, i, n - 1 - i] for i in range(n)]) == player): return True
    if np.all(np.array([board_arr[i, n - 1 - i, i] for i in range(n)]) == player): return True
    if np.all(np.array([board_arr[n - 1 - i, i, i] for i in range(n)]) == player): return True

    # Secondary 3D diagonals
    if np.all(np.array([board_arr[i, n - 1 - i, n - 1 - i] for i in range(n)]) == player): return True
    if np.all(np.array([board_arr[n - 1 - i, i, n - 1 - i] for i in range(n)]) == player): return True
    if np.all(np.array([board_arr[n - 1 - i, n - 1 - i, i] for i in range(n)]) == player): return True
    if np.all(np.array([board_arr[n - 1 - i, n - 1 - i, n - 1 - i] for i in range(n)]) == player): return True

    return False

