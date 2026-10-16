
import random

def policy(board: list[list[int]]) -> int:
    """
    A Connect 4 policy that prioritizes winning moves, blocking opponent's winning moves,
    and otherwise chooses a random valid move.

    Args:
        board: A 6x7 grid representing the Connect 4 board.

    Returns:
        The column index (0-6) to drop a disc in.
    """

    def is_valid_move(col: int) -> bool:
        """Checks if a column is a valid move."""
        return board[0][col] == 0

    def get_possible_moves() -> list[int]:
        """Returns a list of valid column indices."""
        return [col for col in range(7) if is_valid_move(col)]

    def check_win(board: list[list[int]], player: int) -> bool:
        """Checks if the given player has won the game."""
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

    def apply_move(board: list[list[int]], col: int, player: int) -> list[list[int]]:
      """Applies the move to a copy of the board."""
      new_board = [row[:] for row in board]
      for row in reversed(range(6)):
        if new_board[row][col] == 0:
          new_board[row][col] = player
          break
      return new_board
    
    # Check for winning move
    possible_moves = get_possible_moves()
    for col in possible_moves:
        temp_board = apply_move(board, col, 1)
        if check_win(temp_board, 1):
            return col

    # Check for blocking move
    for col in possible_moves:
        temp_board = apply_move(board, col, -1)
        if check_win(temp_board, -1):
            return col

    # Otherwise, choose a random valid move
    if possible_moves:
        return random.choice(possible_moves)
    else:
        return 0  # Should not happen in a valid game state, but handles the case of no moves.
