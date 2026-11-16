
import random

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    Chooses the next move for a 3x3x3 Tic Tac Toe game.

    Args:
        board: A 3x3x3 list of lists containing 0 (empty), 1 (you), and -1 (opponent).

    Returns:
        A tuple of three integers (0-2) indicating the empty cell you choose.
    """

    # Check for winning or blocking moves
    def check_win_block(player):
        for i in range(3):
            for j in range(3):
                for k in range(3):
                    # Check rows
                    if board[i][j][0] == player and board[i][j][1] == player and board[i][j][2] == 0:
                        return (i, j, 2)
                    if board[i][j][0] == player and board[i][j][1] == 0 and board[i][j][2] == player:
                        return (i, j, 1)
                    if board[i][j][0] == 0 and board[i][j][1] == player and board[i][j][2] == player:
                        return (i, j, 0)

                    # Check columns
                    if board[i][0][k] == player and board[i][1][k] == player and board[i][2][k] == 0:
                        return (i, 2, k)
                    if board[i][0][k] == player and board[i][1][k] == 0 and board[i][2][k] == player:
                        return (i, 1, k)
                    if board[i][0][k] == 0 and board[i][1][k] == player and board[i][2][k] == player:
                        return (i, 0, k)

                    # Check depth
                    if board[0][j][k] == player and board[1][j][k] == player and board[2][j][k] == 0:
                        return (2, j, k)
                    if board[0][j][k] == player and board[1][j][k] == 0 and board[2][j][k] == player:
                        return (1, j, k)
                    if board[0][j][k] == 0 and board[1][j][k] == player and board[2][j][k] == player:
                        return (0, j, k)

        # Check diagonals (in each 2D plane)
        for i in range(3):  # Iterate through 2D planes (i constant)
            if board[i][0][0] == player and board[i][1][1] == player and board[i][2][2] == 0:
                return (i, 2, 2)
            if board[i][0][0] == player and board[i][1][1] == 0 and board[i][2][2] == player:
                return (i, 1, 1)
            if board[i][0][0] == 0 and board[i][1][1] == player and board[i][2][2] == player:
                return (i, 0, 0)

            if board[i][0][2] == player and board[i][1][1] == player and board[i][2][0] == 0:
                return (i, 2, 0)
            if board[i][0][2] == player and board[i][1][1] == 0 and board[i][2][0] == player:
                return (i, 1, 1)
            if board[i][0][2] == 0 and board[i][1][1] == player and board[i][2][0] == player:
                return (i, 0, 2)

        for j in range(3):  # Iterate through 2D planes (j constant)
            if board[0][j][0] == player and board[1][j][1] == player and board[2][j][2] == 0:
                return (2, j, 2)
            if board[0][j][0] == player and board[1][j][1] == 0 and board[2][j][2] == player:
                return (1, j, 1)
            if board[0][j][0] == 0 and board[1][j][1] == player and board[2][j][2] == player:
                return (0, j, 0)

            if board[0][j][2] == player and board[1][j][1] == player and board[2][j][0] == 0:
                return (2, j, 0)
            if board[0][j][2] == player and board[1][j][1] == 0 and board[2][j][0] == player:
                return (1, j, 1)
            if board[0][j][2] == 0 and board[1][j][1] == player and board[2][j][0] == player:
                return (0, j, 2)

        for k in range(3):  # Iterate through 2D planes (k constant)
            if board[0][0][k] == player and board[1][1][k] == player and board[2][2][k] == 0:
                return (2, 2, k)
            if board[0][0][k] == player and board[1][1][k] == 0 and board[2][2][k] == player:
                return (1, 1, k)
            if board[0][0][k] == 0 and board[1][1][k] == player and board[2][2][k] == player:
                return (0, 0, k)

            if board[0][2][k] == player and board[1][1][k] == player and board[2][0][k] == 0:
                return (2, 0, k)
            if board[0][2][k] == player and board[1][1][k] == 0 and board[2][0][k] == player:
                return (1, 1, k)
            if board[0][2][k] == 0 and board[1][1][k] == player and board[2][0][k] == player:
                return (0, 2, k)
                
        # Check 3D diagonals
        if board[0][0][0] == player and board[1][1][1] == player and board[2][2][2] == 0:
            return (2, 2, 2)
        if board[0][0][0] == player and board[1][1][1] == 0 and board[2][2][2] == player:
            return (1, 1, 1)
        if board[0][0][0] == 0 and board[1][1][1] == player and board[2][2][2] == player:
            return (0, 0, 0)

        if board[0][0][2] == player and board[1][1][1] == player and board[2][2][0] == 0:
            return (2, 2, 0)
        if board[0][0][2] == player and board[1][1][1] == 0 and board[2][2][0] == player:
            return (1, 1, 1)
        if board[0][0][2] == 0 and board[1][1][1] == player and board[2][2][0] == player:
            return (0, 0, 2)

        if board[0][2][0] == player and board[1][1][1] == player and board[2][0][2] == 0:
            return (2, 0, 2)
        if board[0][2][0] == player and board[1][1][1] == 0 and board[2][0][2] == player:
            return (1, 1, 1)
        if board[0][2][0] == 0 and board[1][1][1] == player and board[2][0][2] == player:
            return (0, 2, 0)

        if board[0][2][2] == player and board[1][1][1] == player and board[2][0][0] == 0:
            return (2, 0, 0)
        if board[0][2][2] == player and board[1][1][1] == 0 and board[2][0][0] == player:
            return (1, 1, 1)
        if board[0][2][2] == 0 and board[1][1][1] == player and board[2][0][0] == player:
            return (0, 2, 2)

        return None  # No winning/blocking move found

    # Check if we can win
    winning_move = check_win_block(1)
    if winning_move:
        return winning_move

    # Check if we need to block
    blocking_move = check_win_block(-1)
    if blocking_move:
        return blocking_move

    # Take the center if available
    if board[1][1][1] == 0:
        return (1, 1, 1)

    # Take a corner if available
    corners = [(0, 0, 0), (0, 0, 2), (0, 2, 0), (0, 2, 2),
               (2, 0, 0), (2, 0, 2), (2, 2, 0), (2, 2, 2)]
    available_corners = [corner for corner in corners if board[corner[0]][corner[1]][corner[2]] == 0]
    if available_corners:
        return random.choice(available_corners)

    # Choose a random empty cell
    empty_cells = []
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    empty_cells.append((i, j, k))

    if empty_cells:
        return random.choice(empty_cells)
    else:
        return (0, 0, 0)  # Should not happen in a valid game, but return a default.
