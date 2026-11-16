
import numpy as np

def policy(board) -> str:
    """
    Selects a legal move for Amazons on a 6x6 board.

    Args:
        board: A 6x6 numpy array representing the board state.

    Returns:
        A string representing a legal move in the format
        "from_row,from_col:to_row,to_col:arrow_row,arrow_col".
    """

    def is_valid(r, c):
        return 0 <= r < 6 and 0 <= c < 6

    def get_possible_moves(board, from_row, from_col):
        possible_moves = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                for dist in range(1, 6):
                    to_row = from_row + dr * dist
                    to_col = from_col + dc * dist
                    if not is_valid(to_row, to_col):
                        break
                    if board[to_row, to_col] != 0:
                        break
                    possible_moves.append((to_row, to_col))
        return possible_moves

    # Find all amazons
    amazons = np.where(board == 1)
    amazon_rows = amazons[0]
    amazon_cols = amazons[1]

    # Iterate through amazons and their possible moves
    for i in range(len(amazon_rows)):
        from_row = amazon_rows[i]
        from_col = amazon_cols[i]
        possible_moves = get_possible_moves(board, from_row, from_col)

        # Iterate through possible moves and arrow shots
        for to_row, to_col in possible_moves:
            temp_board = np.copy(board)
            temp_board[from_row, from_col] = 0
            temp_board[to_row, to_col] = 1

            possible_arrows = get_possible_moves(temp_board, to_row, to_col)
            for arrow_row, arrow_col in possible_arrows:
                move_str = f"{from_row},{from_col}:{to_row},{to_col}:{arrow_row},{arrow_col}"
                return move_str
    return "0,0:0,1:0,2" # should not happen


