
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
        """Checks if the given player has a winning move."""
        # Check rows, columns, and depth
        for i in range(3):
            for j in range(3):
                if all(board[i][j][k] == player for k in range(3)):
                    return True
                if all(board[i][k][j] == player for k in range(3)):
                    return True
                if all(board[k][i][j] == player for k in range(3)):
                    return True

        # Check diagonals in each plane
        for i in range(3):
            if all(board[i][k][k] == player for k in range(3)):
                return True
            if all(board[i][k][2-k] == player for k in range(3)):
                return True
            if all(board[k][i][k] == player for k in range(3)):
                return True
            if all(board[k][i][2-k] == player for k in range(3)):
                return True
            if all(board[k][k][i] == player for k in range(3)):
                return True
            if all(board[k][2-k][i] == player for k in range(3)):
                return True
        
        # Check diagonals across the cube
        if all(board[k][k][k] == player for k in range(3)):
            return True
        if all(board[k][k][2-k] == player for k in range(3)):
            return True
        if all(board[k][2-k][k] == player for k in range(3)):
            return True
        if all(board[k][2-k][2-k] == player for k in range(3)):
            return True
        return False

    def get_winning_move(board, player):
        """Returns the winning move for the given player, or None if no winning move exists."""
        for i in range(3):
            for j in range(3):
                for k in range(3):
                    if board[i][j][k] == 0:
                        board[i][j][k] = player
                        if check_win(board, player):
                            board[i][j][k] = 0
                            return (i, j, k)
                        board[i][j][k] = 0
        return None

    def get_blocking_move(board, player):
        """Returns the blocking move for the given player, or None if no blocking move exists."""
        opponent = -player
        return get_winning_move(board, opponent)

    # 1. Check for a winning move
    winning_move = get_winning_move(board, 1)
    if winning_move:
        return winning_move

    # 2. Check for a blocking move
    blocking_move = get_blocking_move(board, 1)
    if blocking_move:
        return blocking_move

    # 3. Choose a random empty cell
    empty_cells = []
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    empty_cells.append((i, j, k))

    if empty_cells:
        return random.choice(empty_cells)
    else:
        # Should not happen in a valid game state, but return (0,0,0) as a default.
        return (0, 0, 0)
