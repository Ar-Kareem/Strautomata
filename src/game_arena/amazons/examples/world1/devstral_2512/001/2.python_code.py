
import numpy as np

def is_path_clear(board, start, end):
    """Check if the path from start to end is clear (queen-like move)."""
    start_row, start_col = start
    end_row, end_col = end

    # Check if the move is straight or diagonal
    if start_row != end_row and start_col != end_col and abs(start_row - end_row) != abs(start_col - end_col):
        return False

    # Determine the direction of the move
    row_step = 0 if start_row == end_row else (1 if end_row > start_row else -1)
    col_step = 0 if start_col == end_col else (1 if end_col > start_col else -1)

    # Check each square along the path
    row, col = start_row + row_step, start_col + col_step
    while (row, col) != end:
        if board[row, col] != 0:
            return False
        row += row_step
        col += col_step

    return True

def get_legal_moves(board):
    """Generate all legal moves for the current player."""
    legal_moves = []
    rows, cols = board.shape

    # Find all positions of the player's amazons
    amazon_positions = np.argwhere(board == 1)

    for from_row, from_col in amazon_positions:
        # Check all possible queen-like moves
        for to_row in range(rows):
            for to_col in range(cols):
                if (to_row, to_col) == (from_row, from_col):
                    continue
                if board[to_row, to_col] != 0:
                    continue
                if not is_path_clear(board, (from_row, from_col), (to_row, to_col)):
                    continue

                # Simulate the move to check arrow shots
                temp_board = board.copy()
                temp_board[from_row, from_col] = 0
                temp_board[to_row, to_col] = 1

                # Check all possible arrow shots from the new position
                for arrow_row in range(rows):
                    for arrow_col in range(cols):
                        if (arrow_row, arrow_col) == (to_row, to_col):
                            continue
                        if temp_board[arrow_row, arrow_col] != 0:
                            continue
                        if not is_path_clear(temp_board, (to_row, to_col), (arrow_row, arrow_col)):
                            continue

                        # Valid move found
                        move_str = f"{from_row},{from_col}:{to_row},{to_col}:{arrow_row},{arrow_col}"
                        legal_moves.append(move_str)

    return legal_moves

def policy(board) -> str:
    """Return a legal move string for the current board state."""
    legal_moves = get_legal_moves(board)
    if not legal_moves:
        # This should not happen as per the problem statement, but return a dummy move if no legal moves are found
        return "0,0:0,0:0,0"
    return legal_moves[0]
