
import random

def policy(board: list[list[int]]) -> int:
    """
    A Connect 4 policy that prioritizes winning moves, blocks opponent's winning moves, and 
    otherwise chooses a random valid column.

    Args:
        board: A 6x7 grid representing the Connect 4 board.
               0 indicates an empty cell, 1 is the current player's disc, and -1 is the opponent's disc.

    Returns:
        An integer representing the column index (0-6) where the current player should drop their disc.
    """

    rows = len(board)
    cols = len(board[0])

    def is_valid_move(col: int) -> bool:
        """
        Checks if a column is a valid move (i.e., not full).
        """
        return board[0][col] == 0

    def check_win(board: list[list[int]], player: int) -> bool:
        """
        Checks if the given player has won the game on the current board.
        """
        # Check horizontal
        for row in range(rows):
            for col in range(cols - 3):
                if board[row][col] == player and \
                   board[row][col + 1] == player and \
                   board[row][col + 2] == player and \
                   board[row][col + 3] == player:
                    return True

        # Check vertical
        for row in range(rows - 3):
            for col in range(cols):
                if board[row][col] == player and \
                   board[row + 1][col] == player and \
                   board[row + 2][col] == player and \
                   board[row + 3][col] == player:
                    return True

        # Check positive diagonal
        for row in range(rows - 3):
            for col in range(cols - 3):
                if board[row][col] == player and \
                   board[row + 1][col + 1] == player and \
                   board[row + 2][col + 2] == player and \
                   board[row + 3][col + 3] == player:
                    return True

        # Check negative diagonal
        for row in range(3, rows):
            for col in range(cols - 3):
                if board[row][col] == player and \
                   board[row - 1][col + 1] == player and \
                   board[row - 2][col + 2] == player and \
                   board[row - 3][col + 3] == player:
                    return True

        return False

    def get_next_board(board: list[list[int]], col: int, player: int) -> list[list[int]]:
        """
        Simulates the next board state after dropping a disc in the given column.
        """
        new_board = [row[:] for row in board]  # Create a deep copy
        for row in range(rows - 1, -1, -1):
            if new_board[row][col] == 0:
                new_board[row][col] = player
                break
        return new_board

    # Check for winning move
    for col in range(cols):
        if is_valid_move(col):
            temp_board = get_next_board(board, col, 1)
            if check_win(temp_board, 1):
                return col

    # Check for blocking opponent's winning move
    for col in range(cols):
        if is_valid_move(col):
            temp_board = get_next_board(board, col, -1)
            if check_win(temp_board, -1):
                return col

    # Choose a random valid column
    valid_cols = [col for col in range(cols) if is_valid_move(col)]
    if valid_cols:
        return random.choice(valid_cols)
    else:
        # Should not happen in a proper game, but handle it to avoid errors.
        return 0
