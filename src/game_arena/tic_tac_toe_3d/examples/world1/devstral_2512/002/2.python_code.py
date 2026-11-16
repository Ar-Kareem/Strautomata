
import numpy as np

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # Convert to numpy array for easier manipulation
    board_array = np.array(board)

    # Get all empty positions
    empty_positions = []
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board_array[i, j, k] == 0:
                    empty_positions.append((i, j, k))

    # If no empty positions, return None (though game should be over)
    if not empty_positions:
        return None

    # Check for immediate winning move
    for pos in empty_positions:
        i, j, k = pos
        # Temporarily place our mark
        board_array[i, j, k] = 1
        if check_win(board_array, 1):
            return pos
        # Undo the temporary placement
        board_array[i, j, k] = 0

    # Check for immediate blocking move
    for pos in empty_positions:
        i, j, k = pos
        # Temporarily place opponent's mark
        board_array[i, j, k] = -1
        if check_win(board_array, -1):
            return pos
        # Undo the temporary placement
        board_array[i, j, k] = 0

    # If no immediate win/block, use strategic positioning
    # Priority: center, then corners, then edges

    # Check if center is available
    center = (1, 1, 1)
    if center in empty_positions:
        return center

    # Check corners (all coordinates are 0 or 2)
    corners = [(0,0,0), (0,0,2), (0,2,0), (0,2,2),
               (2,0,0), (2,0,2), (2,2,0), (2,2,2)]
    for corner in corners:
        if corner in empty_positions:
            return corner

    # Check edges (two coordinates are 0/2, one is 1)
    edges = []
    for i in [0, 2]:
        for j in [0, 2]:
            edges.append((i, j, 1))  # z-edge
            edges.append((i, 1, j))  # y-edge
            edges.append((1, i, j))  # x-edge

    for edge in edges:
        if edge in empty_positions:
            return edge

    # If all else fails, return the first available position
    return empty_positions[0]

def check_win(board: np.ndarray, player: int) -> bool:
    """Check if the given player has won on the board."""
    # Check all rows in each layer
    for i in range(3):
        for j in range(3):
            if all(board[i, j, :] == player):
                return True

    # Check all columns in each layer
    for i in range(3):
        for k in range(3):
            if all(board[i, :, k] == player):
                return True

    # Check all depth lines (pillars)
    for j in range(3):
        for k in range(3):
            if all(board[:, j, k] == player):
                return True

    # Check face diagonals
    # Front and back faces (z=0 and z=2)
    for i in [0, 2]:
        if board[i, 0, 0] == player and board[i, 1, 1] == player and board[i, 2, 2] == player:
            return True
        if board[i, 0, 2] == player and board[i, 1, 1] == player and board[i, 2, 0] == player:
            return True

    # Left and right faces (x=0 and x=2)
    for k in [0, 2]:
        if board[0, 0, k] == player and board[1, 1, k] == player and board[2, 2, k] == player:
            return True
        if board[0, 2, k] == player and board[1, 1, k] == player and board[2, 0, k] == player:
            return True

    # Top and bottom faces (y=0 and y=2)
    for j in [0, 2]:
        if board[0, j, 0] == player and board[1, j, 1] == player and board[2, j, 2] == player:
            return True
        if board[0, j, 2] == player and board[1, j, 1] == player and board[2, j, 0] == player:
            return True

    # Check space diagonals
    if board[0, 0, 0] == player and board[1, 1, 1] == player and board[2, 2, 2] == player:
        return True
    if board[0, 0, 2] == player and board[1, 1, 1] == player and board[2, 2, 0] == player:
        return True
    if board[0, 2, 0] == player and board[1, 1, 1] == player and board[2, 0, 2] == player:
        return True
    if board[0, 2, 2] == player and board[1, 1, 1] == player and board[2, 0, 0] == player:
        return True

    return False
