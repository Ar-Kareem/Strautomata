
import random

def policy(board: list[list[int]]) -> int:
    """
    A Connect 4 policy function that returns a valid column index to play.

    This policy prioritizes winning moves, then blocking opponent wins,
    and otherwise chooses a random valid column.
    """

    def check_win(board, player):
        # Check horizontal
        for row in range(6):
            for col in range(4):
                if (board[row][col] == player and
                    board[row][col+1] == player and
                    board[row][col+2] == player and
                    board[row][col+3] == player):
                    return True

        # Check vertical
        for row in range(3):
            for col in range(7):
                if (board[row][col] == player and
                    board[row+1][col] == player and
                    board[row+2][col] == player and
                    board[row+3][col] == player):
                    return True

        # Check positive diagonal
        for row in range(3):
            for col in range(4):
                if (board[row][col] == player and
                    board[row+1][col+1] == player and
                    board[row+2][col+2] == player and
                    board[row+3][col+3] == player):
                    return True

        # Check negative diagonal
        for row in range(3):
            for col in range(3, 7):
                if (board[row][col] == player and
                    board[row+1][col-1] == player and
                    board[row+2][col-2] == player and
                    board[row+3][col-3] == player):
                    return True

        return False

    def get_valid_moves(board):
        """Returns a list of valid column indices."""
        valid_moves = []
        for col in range(7):
            if board[0][col] == 0:
                valid_moves.append(col)
        return valid_moves

    def make_move(board, col, player):
        """Makes a move on a copy of the board and returns it."""
        temp_board = [row[:] for row in board]
        for row in range(5, -1, -1):
            if temp_board[row][col] == 0:
                temp_board[row][col] = player
                return temp_board
        return None  # Should not happen if the move is valid

    # 1. Check for winning moves
    for col in get_valid_moves(board):
        temp_board = make_move(board, col, 1)
        if temp_board and check_win(temp_board, 1):
            return col

    # 2. Check for opponent's winning moves and block them
    for col in get_valid_moves(board):
        temp_board = make_move(board, col, -1)
        if temp_board and check_win(temp_board, -1):
            return col

    # 3. If no winning or blocking moves, choose a random valid move
    valid_moves = get_valid_moves(board)
    if valid_moves:
        return random.choice(valid_moves)
    else:
        # Should not happen in a normal game, but return a default if it does
        return 0
