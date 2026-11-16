
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Determines the next move for a Tic-Tac-Toe game.

    Args:
        board: A 3x3 list of lists representing the Tic-Tac-Toe board.
               0: empty, 1: your move, -1: opponent's move.

    Returns:
        A tuple (row, col) indicating the chosen move.
    """

    # Helper function to check if placing a player_id at (r_move, c_move)
    # would result in a win for that player on the current_board.
    def check_win_after_move(current_board, r_move, c_move, player_id):
        # A line (row, col, diagonal) wins if all three cells are player_id.
        # This implies the sum of the cells in that line will be 3 * player_id.
        # If we are checking an empty spot (r_move, c_move), and placing player_id there,
        # then the sum of the *other two cells* in that line must be 2 * player_id
        # for a win to occur.

        # Check row
        row_sum_excluding_move = 0
        for c in range(3):
            if c != c_move:
                row_sum_excluding_move += current_board[r_move][c]
        if row_sum_excluding_move + player_id == 3 * player_id:
            return True

        # Check column
        col_sum_excluding_move = 0
        for r in range(3):
            if r != r_move:
                col_sum_excluding_move += current_board[r][c_move]
        if col_sum_excluding_move + player_id == 3 * player_id:
            return True

        # Check main diagonal (top-left to bottom-right)
        if r_move == c_move:
            diag_sum_excluding_move = 0
            for i in range(3):
                if i != r_move:
                    diag_sum_excluding_move += current_board[i][i]
            if diag_sum_excluding_move + player_id == 3 * player_id:
                return True

        # Check anti-diagonal (top-right to bottom-left)
        if r_move + c_move == 2:
            anti_diag_sum_excluding_move = 0
            for i in range(3):
                if i != r_move: # Check the corresponding cell on anti-diagonal
                    anti_diag_sum_excluding_move += current_board[i][2 - i]
            if anti_diag_sum_excluding_move + player_id == 3 * player_id:
                return True
        
        return False

    empty_cells = []
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                empty_cells.append((r, c))

    # If no empty cells, game should be over or draw. Return a dummy move (should not happen).
    if not empty_cells:
        return (0, 0)

    # 1. Check for an immediate win for self (player 1)
    for r, c in empty_cells:
        if check_win_after_move(board, r, c, 1):
            return (r, c)

    # 2. Check for an immediate win for opponent (player -1) and block it
    for r, c in empty_cells:
        if check_win_after_move(board, r, c, -1):
            return (r, c)

    # 3. Take the center if available
    if (1, 1) in empty_cells:
        return (1, 1)

    # 4. Take any available corner (randomized for variation if multiple are open)
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    # Shuffle to vary play slightly if multiple corners are equally good
    random.shuffle(corners) 
    for r, c in corners:
        if (r, c) in empty_cells:
            return (r, c)
            
    # 5. Take any available side (randomized for variation if multiple are open)
    sides = [(0, 1), (1, 0), (1, 2), (2, 1)]
    # Shuffle to vary play slightly if multiple sides are equally good
    random.shuffle(sides)
    for r, c in sides:
        if (r, c) in empty_cells:
            return (r, c)

    # Fallback: Return the first available empty cell. 
    # This should only be reached if the above rules didn't cover all empty cells,
    # which implies a very late game state or one where only non-strategic moves remain.
    return empty_cells[0]

