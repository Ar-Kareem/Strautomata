
import numpy as np

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    Chooses the next move for a 3x3x3 Tic Tac Toe game.

    Args:
        board: A 3x3x3 list of lists containing 0 (empty), 1 (you), and -1 (opponent).

    Returns:
        A tuple of three integers (0-2) indicating the empty cell you choose.
    """

    board_np = np.array(board)

    def check_win_or_block(player):
        # Check rows
        for i in range(3):
            for j in range(3):
                if np.sum(board_np[i][j] == player) == 2 and 0 in board_np[i][j]:
                    k = np.where(board_np[i][j] == 0)[0][0]
                    return (i, j, k)
        # Check columns
        for i in range(3):
            for k in range(3):
                if np.sum(board_np[i, :, k] == player) == 2 and 0 in board_np[i, :, k]:
                    j = np.where(board_np[i, :, k] == 0)[0][0]
                    return (i, j, k)
        # Check depth
        for j in range(3):
            for k in range(3):
                if np.sum(board_np[:, j, k] == player) == 2 and 0 in board_np[:, j, k]:
                    i = np.where(board_np[:, j, k] == 0)[0][0]
                    return (i, j, k)
        # Check diagonals in each layer
        for i in range(3):
            if np.sum(np.diag(board_np[i]) == player) == 2 and 0 in np.diag(board_np[i]):
                j = np.where(np.diag(board_np[i]) == 0)[0][0]
                return (i, j, j)
            if np.sum(np.diag(np.fliplr(board_np[i])) == player) == 2 and 0 in np.diag(np.fliplr(board_np[i])):
                j = np.where(np.diag(np.fliplr(board_np[i])) == 0)[0][0]
                return (i, j, 2 - j)

        #check diagonals on each face for 3d cube
        for j in range(3):
            if np.sum( [board_np[0][j][0],board_np[1][j][1],board_np[2][j][2]] == player) == 2 and 0 in [board_np[0][j][0],board_np[1][j][1],board_np[2][j][2]]:
                indexes = [0,1,2]
                vals = [board_np[0][j][0],board_np[1][j][1],board_np[2][j][2]]
                i = indexes[vals.index(0)]
                return (i,j,i)
            if np.sum( [board_np[0][j][2],board_np[1][j][1],board_np[2][j][0]] == player) == 2 and 0 in [board_np[0][j][2],board_np[1][j][1],board_np[2][j][0]]:
                indexes = [0,1,2]
                vals = [board_np[0][j][2],board_np[1][j][1],board_np[2][j][0]]
                i = indexes[vals.index(0)]
                return (i,j,2-i)
        for i in range(3):
            if np.sum( [board_np[i][0][0],board_np[i][1][1],board_np[i][2][2]] == player) == 2 and 0 in [board_np[i][0][0],board_np[i][1][1],board_np[i][2][2]]:
                indexes = [0,1,2]
                vals = [board_np[i][0][0],board_np[i][1][1],board_np[i][2][2]]
                j = indexes[vals.index(0)]
                return (i,j,j)
            if np.sum( [board_np[i][0][2],board_np[i][1][1],board_np[i][2][0]] == player) == 2 and 0 in [board_np[i][0][2],board_np[i][1][1],board_np[i][2][0]]:
                indexes = [0,1,2]
                vals = [board_np[i][0][2],board_np[i][1][1],board_np[i][2][0]]
                j = indexes[vals.index(0)]
                return (i,j,2-j)
        for k in range(3):
            if np.sum( [board_np[0][0][k],board_np[1][1][k],board_np[2][2][k]] == player) == 2 and 0 in [board_np[0][0][k],board_np[1][1][k],board_np[2][2][k]]:
                indexes = [0,1,2]
                vals = [board_np[0][0][k],board_np[1][1][k],board_np[2][2][k]]
                i = indexes[vals.index(0)]
                return (i,i,k)
            if np.sum( [board_np[0][2][k],board_np[1][1][k],board_np[2][0][k]] == player) == 2 and 0 in [board_np[0][2][k],board_np[1][1][k],board_np[2][0][k]]:
                indexes = [0,1,2]
                vals = [board_np[0][2][k],board_np[1][1][k],board_np[2][0][k]]
                i = indexes[vals.index(0)]
                return (i,2-i,k)

        # check main diag
        if np.sum( [board_np[0][0][0],board_np[1][1][1],board_np[2][2][2]] == player) == 2 and 0 in [board_np[0][0][0],board_np[1][1][1],board_np[2][2][2]]:
            indexes = [0,1,2]
            vals = [board_np[0][0][0],board_np[1][1][1],board_np[2][2][2]]
            i = indexes[vals.index(0)]
            return (i,i,i)
        # check other diagonals
        if np.sum( [board_np[0][0][2],board_np[1][1][1],board_np[2][2][0]] == player) == 2 and 0 in [board_np[0][0][2],board_np[1][1][1],board_np[2][2][0]]:
            indexes = [0,1,2]
            vals = [board_np[0][0][2],board_np[1][1][1],board_np[2][2][0]]
            i = indexes[vals.index(0)]
            return (i,i,2-i)
        if np.sum( [board_np[0][2][0],board_np[1][1][1],board_np[2][0][2]] == player) == 2 and 0 in [board_np[0][2][0],board_np[1][1][1],board_np[2][0][2]]:
            indexes = [0,1,2]
            vals = [board_np[0][2][0],board_np[1][1][1],board_np[2][0][2]]
            i = indexes[vals.index(0)]
            return (i,2-i,i)
        if np.sum( [board_np[0][2][2],board_np[1][1][1],board_np[2][0][0]] == player) == 2 and 0 in  [board_np[0][2][2],board_np[1][1][1],board_np[2][0][0]]:
            indexes = [0,1,2]
            vals = [board_np[0][2][2],board_np[1][1][1],board_np[2][0][0]]
            i = indexes[vals.index(0)]
            return (i,2-i,2-i)
        return None

    # Check for winning move
    winning_move = check_win_or_block(1)
    if winning_move:
        return winning_move

    # Check for blocking move
    blocking_move = check_win_or_block(-1)
    if blocking_move:
        return blocking_move

    # Try to take the center
    if board[1][1][1] == 0:
        return (1, 1, 1)

    # Try to take a corner
    corners = [(0, 0, 0), (0, 0, 2), (0, 2, 0), (0, 2, 2),
               (2, 0, 0), (2, 0, 2), (2, 2, 0), (2, 2, 2)]
    for corner in corners:
        if board[corner[0]][corner[1]][corner[2]] == 0:
            return corner

    # Play any empty cell
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    return (i, j, k)

    return (0, 0, 0)  # Should not happen, but return a default value to avoid errors
