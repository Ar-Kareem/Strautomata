
import random

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    Chooses the next move for a 3x3x3 Tic Tac Toe game.

    Args:
        board: A 3x3x3 list of lists containing 0 (empty), 1 (you), and -1 (opponent).

    Returns:
        A tuple of three integers (0-2) indicating the empty cell you choose.
    """

    def check_win(board, player):
        """Checks for winning moves for the given player."""
        for i in range(3):
            for j in range(3):
                # Check rows in each layer
                if board[i][j][0] == player and board[i][j][1] == player and board[i][j][2] == 0:
                    return (i, j, 2)
                if board[i][j][0] == player and board[i][j][2] == player and board[i][j][1] == 0:
                    return (i, j, 1)
                if board[i][j][1] == player and board[i][j][2] == player and board[i][j][0] == 0:
                    return (i, j, 0)

                # Check columns in each layer
                if board[i][0][j] == player and board[i][1][j] == player and board[i][2][j] == 0:
                    return (i, 2, j)
                if board[i][0][j] == player and board[i][2][j] == player and board[i][1][j] == 0:
                    return (i, 1, j)
                if board[i][1][j] == player and board[i][2][j] == player and board[i][0][j] == 0:
                    return (i, 0, j)

                # Check depth columns in each layer
                if board[0][i][j] == player and board[1][i][j] == player and board[2][i][j] == 0:
                    return (2, i, j)
                if board[0][i][j] == player and board[2][i][j] == player and board[1][i][j] == 0:
                    return (1, i, j)
                if board[1][i][j] == player and board[2][i][j] == player and board[0][i][j] == 0:
                    return (0, i, j)

        # Check diagonals
        for i in range(3):
            # Diagonal along i = constant
            if board[i][0][0] == player and board[i][1][1] == player and board[i][2][2] == 0:
                return (i, 2, 2)
            if board[i][0][0] == player and board[i][2][2] == player and board[i][1][1] == 0:
                return (i, 1, 1)
            if board[i][1][1] == player and board[i][2][2] == player and board[i][0][0] == 0:
                return (i, 0, 0)
            if board[i][0][2] == player and board[i][1][1] == player and board[i][2][0] == 0:
                return (i, 2, 0)
            if board[i][0][2] == player and board[i][2][0] == player and board[i][1][1] == 0:
                return (i, 1, 1)
            if board[i][1][1] == player and board[i][2][0] == player and board[i][0][2] == 0:
                return (i, 0, 2)

        for j in range(3):
            # Diagonal along j = constant
            if board[0][j][0] == player and board[1][j][1] == player and board[2][j][2] == 0:
                return (2, j, 2)
            if board[0][j][0] == player and board[2][j][2] == player and board[1][j][1] == 0:
                return (1, j, 1)
            if board[1][j][1] == player and board[2][j][2] == player and board[0][j][0] == 0:
                return (0, j, 0)

            if board[0][j][2] == player and board[1][j][1] == player and board[2][j][0] == 0:
                return (2, j, 0)
            if board[0][j][2] == player and board[2][j][0] == player and board[1][j][1] == 0:
                return (1, j, 1)
            if board[1][j][1] == player and board[2][j][0] == player and board[0][j][2] == 0:
                return (0, j, 2)

        for k in range(3):
            # Diagonal along k = constant
             if board[0][0][k] == player and board[1][1][k] == player and board[2][2][k] == 0:
                 return (2, 2, k)
             if board[0][0][k] == player and board[2][2][k] == player and board[1][1][k] == 0:
                 return (1, 1, k)
             if board[1][1][k] == player and board[2][2][k] == player and board[0][0][k] == 0:
                 return (0, 0, k)
             if board[0][2][k] == player and board[1][1][k] == player and board[2][0][k] == 0:
                 return (2, 0, k)
             if board[0][2][k] == player and board[2][0][k] == player and board[1][1][k] == 0:
                 return (1, 1, k)
             if board[1][1][k] == player and board[2][0][k] == player and board[0][2][k] == 0:
                 return (0, 2, k)

        # All 4 diagonals across the cube
        if board[0][0][0] == player and board[1][1][1] == player and board[2][2][2] == 0:
             return (2, 2, 2)
        if board[0][0][0] == player and board[2][2][2] == player and board[1][1][1] == 0:
             return (1, 1, 1)
        if board[2][2][2] == player and board[1][1][1] == player and board[0][0][0] == 0:
             return (0, 0, 0)

        if board[0][0][2] == player and board[1][1][1] == player and board[2][2][0] == 0:
            return (2, 2, 0)
        if board[0][0][2] == player and board[2][2][0] == player and board[1][1][1] == 0:
            return (1, 1, 1)
        if board[2][2][0] == player and board[1][1][1] == player and board[0][0][2] == 0:
            return (0, 0, 2)

        if board[0][2][0] == player and board[1][1][1] == player and board[2][0][2] == 0:
            return (2, 0, 2)
        if board[0][2][0] == player and board[2][0][2] == player and board[1][1][1] == 0:
            return (1, 1, 1)
        if board[2][0][2] == player and board[1][1][1] == player and board[0][2][0] == 0:
            return (0, 2, 0)

        if board[0][2][2] == player and board[1][1][1] == player and board[2][0][0] == 0:
            return (2, 0, 0)
        if board[0][2][2] == player and board[2][0][0] == player and board[1][1][1] == 0:
            return (1, 1, 1)
        if board[2][0][0] == player and board[1][1][1] == player and board[0][2][2] == 0:
            return (0, 2, 2)
        return None
    # Check for winning moves
    winning_move = check_win(board, 1)
    if winning_move:
        return winning_move

    # Check for blocking moves
    blocking_move = check_win(board, -1)
    if blocking_move:
        return blocking_move

    # Pick a random empty space
    empty_cells = []
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    empty_cells.append((i, j, k))

    if empty_cells:
        return random.choice(empty_cells)
    else:
        return (0, 0, 0)  # Should not happen in a valid game
