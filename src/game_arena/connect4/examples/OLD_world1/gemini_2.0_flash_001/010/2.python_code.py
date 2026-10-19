
import random

def policy(board: list[list[int]]) -> int:
    """
    A Connect 4 policy that prioritizes winning moves, blocks opponent's winning moves,
    and otherwise makes a random valid move.
    """
    cols = len(board[0])

    def check_win(board, player):
        """Checks if the given player has won the game."""
        # Check horizontal
        for row in range(len(board)):
            for col in range(len(board[0]) - 3):
                if (board[row][col] == player and
                    board[row][col+1] == player and
                    board[row][col+2] == player and
                    board[row][col+3] == player):
                    return True

        # Check vertical
        for row in range(len(board) - 3):
            for col in range(len(board[0])):
                if (board[row][col] == player and
                    board[row+1][col] == player and
                    board[row+2][col] == player and
                    board[row+3][col] == player):
                    return True

        # Check positive diagonal
        for row in range(len(board) - 3):
            for col in range(len(board[0]) - 3):
                if (board[row][col] == player and
                    board[row+1][col+1] == player and
                    board[row+2][col+2] == player and
                    board[row+3][col+3] == player):
                    return True

        # Check negative diagonal
        for row in range(3, len(board)):
            for col in range(len(board[0]) - 3):
                if (board[row][col] == player and
                    board[row-1][col+1] == player and
                    board[row-2][col+2] == player and
                    board[row-3][col+3] == player):
                    return True

        return False


    def get_possible_moves(board):
        """Returns a list of valid column indices."""
        possible_moves = []
        for col in range(cols):
            if board[0][col] == 0:  # Column not full
                possible_moves.append(col)
        return possible_moves
    
    def make_move(board, col, player):
        """Makes a move on a copy of the board."""
        temp_board = [row[:] for row in board]  # Create a deep copy
        for row in range(len(temp_board) - 1, -1, -1):
            if temp_board[row][col] == 0:
                temp_board[row][col] = player
                return temp_board
        return None # Invalid move
    
    # 1. Check for winning moves for the current player
    possible_moves = get_possible_moves(board)
    for col in possible_moves:
        temp_board = make_move(board, col, 1) # 1 is the current player disc
        if temp_board and check_win(temp_board, 1):
            return col

    # 2. Check for blocking moves for the opponent
    for col in possible_moves:
        temp_board = make_move(board, col, -1) # -1 is the opponent disc
        if temp_board and check_win(temp_board, -1):
            return col

    # 3. If no winning or blocking move, make a random valid move
    if possible_moves:
        return random.choice(possible_moves)
    else:
        # Should not happen in a standard game, but handle it anyway
        return 0  # Return the first column if no moves are available
