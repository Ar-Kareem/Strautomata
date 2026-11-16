
import numpy as np

def policy(board):
    """
    Selects a legal move for the Amazons game on a 6x6 board.

    Args:
        board (np.ndarray): A 6x6 numpy array representing the game board.

    Returns:
        str: A legal move string in the format "from_row,from_col:to_row,to_col:arrow_row,arrow_col".
    """

    def is_valid_move(board, from_row, from_col, to_row, to_col):
        """Checks if a move from (from_row, from_col) to (to_row, to_col) is valid."""
        if from_row < 0 or from_row > 5 or from_col < 0 or from_col > 5 or to_row < 0 or to_row > 5 or to_col < 0 or to_col > 5:
            return False
        if board[from_row, from_col] != 1 or board[to_row, to_col] != 0:
            return False

        # Check for obstructions along the path
        row_dir = 0 if from_row == to_row else (1 if to_row > from_row else -1)
        col_dir = 0 if from_col == to_col else (1 if to_col > from_col else -1)

        curr_row, curr_col = from_row + row_dir, from_col + col_dir
        while curr_row != to_row or curr_col != to_col:
            if board[curr_row, curr_col] != 0:
                return False
            curr_row += row_dir
            curr_col += col_dir

        return True

    def is_valid_arrow_shot(board, to_row, to_col, arrow_row, arrow_col, from_row, from_col):
        """Checks if an arrow shot from (to_row, to_col) to (arrow_row, arrow_col) is valid."""
        if arrow_row < 0 or arrow_row > 5 or arrow_col < 0 or arrow_col > 5:
            return False
        if board[arrow_row, arrow_col] != 0:
            return False

        # Temporarily modify the board for obstruction check
        temp_board = np.copy(board)
        # temp_board[from_row, from_col] = 0  # Amazon has already moved.
        temp_board[to_row, to_col] = 1 #consider that amazon has moved

        # Check for obstructions along the path
        row_dir = 0 if to_row == arrow_row else (1 if arrow_row > to_row else -1)
        col_dir = 0 if to_col == arrow_col else (1 if arrow_col > to_col else -1)

        curr_row, curr_col = to_row + row_dir, to_col + col_dir
        while curr_row != arrow_row or curr_col != arrow_col:
            if temp_board[curr_row, curr_col] != 0:
                return False
            curr_row += row_dir
            curr_col += col_dir
        return True

    # Iterate through all possible moves
    for from_row in range(6):
        for from_col in range(6):
            if board[from_row, from_col] == 1:  # Found an Amazon
                for to_row in range(6):
                    for to_col in range(6):
                        if is_valid_move(board, from_row, from_col, to_row, to_col):  # Valid Amazon move
                            for arrow_row in range(6):
                                for arrow_col in range(6):
                                    if is_valid_arrow_shot(board, to_row, to_col, arrow_row, arrow_col, from_row, from_col):
                                        return f"{from_row},{from_col}:{to_row},{to_col}:{arrow_row},{arrow_col}"

    return "0,0:0,1:0,2"  # Should not reach here, but return a default move in case of error.
