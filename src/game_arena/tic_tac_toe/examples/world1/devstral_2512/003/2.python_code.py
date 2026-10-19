
def policy(board: list[list[int]]) -> tuple[int, int]:
    def is_winning_move(board, player, row, col):
        # Check row
        if all(cell == player for cell in board[row]):
            return True
        # Check column
        if all(board[i][col] == player for i in range(3)):
            return True
        # Check diagonals
        if row == col and all(board[i][i] == player for i in range(3)):
            return True
        if row + col == 2 and all(board[i][2-i] == player for i in range(3)):
            return True
        return False

    def get_empty_positions(board):
        return [(i, j) for i in range(3) for j in range(3) if board[i][j] == 0]

    empty_positions = get_empty_positions(board)

    # Check for winning moves
    for (i, j) in empty_positions:
        board[i][j] = 1  # Try the move
        if is_winning_move(board, 1, i, j):
            board[i][j] = 0  # Undo the move
            return (i, j)
        board[i][j] = 0  # Undo the move

    # Check for blocking moves (opponent would win)
    for (i, j) in empty_positions:
        board[i][j] = -1  # Try opponent's move
        if is_winning_move(board, -1, i, j):
            board[i][j] = 0  # Undo the move
            return (i, j)
        board[i][j] = 0  # Undo the move

    # Take center if available
    if board[1][1] == 0:
        return (1, 1)

    # Take a corner if available
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    for (i, j) in corners:
        if board[i][j] == 0:
            return (i, j)

    # Take any remaining edge
    edges = [(0, 1), (1, 0), (1, 2), (2, 1)]
    for (i, j) in edges:
        if board[i][j] == 0:
            return (i, j)

    # If all else fails (shouldn't happen as we checked empty positions)
    return empty_positions[0]
