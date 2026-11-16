
def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Chooses the next move for a 4x4 Tic Tac Toe game.

    Args:
        board: A 4x4 list of lists containing 0 (empty), 1 (you), and -1 (opponent).

    Returns:
        A tuple of two integers (row, col) indicating the row and column you choose.
    """

    def check_win(board, player):
        """Checks if the given player has won the board."""
        # Check rows
        for row in range(4):
            if all(board[row][col] == player for col in range(4)):
                return True
        # Check columns
        for col in range(4):
            if all(board[row][col] == player for row in range(4)):
                return True
        # Check diagonals
        if all(board[i][i] == player for i in range(4)):
            return True
        if all(board[i][3 - i] == player for i in range(4)):
            return True
        return False

    def get_possible_moves(board):
        """Returns a list of possible moves (row, col)."""
        moves = []
        for row in range(4):
            for col in range(4):
                if board[row][col] == 0:
                    moves.append((row, col))
        return moves

    # Check for a winning move
    for row, col in get_possible_moves(board):
        board[row] = board[row][:col] + [1] + board[row][col+1:] # Place a temporary '1'
        if check_win(board, 1):
            board[row] = board[row][:col] + [0] + board[row][col+1:] # Reset the board
            return (row, col)
        board[row] = board[row][:col] + [0] + board[row][col+1:] # Reset the board

    # Check for a blocking move
    for row, col in get_possible_moves(board):
        board[row] = board[row][:col] + [-1] + board[row][col+1:] # Place a temporary '-1'
        if check_win(board, -1):
            board[row] = board[row][:col] + [0] + board[row][col+1:] # Reset the board
            return (row, col)
        board[row] = board[row][:col] + [0] + board[row][col+1:] # Reset the board

    # If no winning or blocking move, return the first available move
    for row in range(4):
        for col in range(4):
            if board[row][col] == 0:
                return (row, col)

    return None  # Should never happen in a valid game

