
def policy(board: list[list[int]]) -> tuple[int, int]:
    def check_win(b, player):
        # Check rows for a win
        for row in b:
            if row[0] == row[1] == row[2] == player:
                return True
        # Check columns for a win
        for col in range(3):
            if b[0][col] == b[1][col] == b[2][col] == player:
                return True
        # Check diagonals for a win
        if (b[0][0] == b[1][1] == b[2][2] == player) or (b[0][2] == b[1][1] == b[2][0] == player):
            return True
        return False

    # Collect all empty cells
    empty = [(i, j) for i in range(3) for j in range(3) if board[i][j] == 0]

    # Check for a winning move
    for i, j in empty:
        new_board = [row.copy() for row in board]
        new_board[i][j] = 1
        if check_win(new_board, 1):
            return (i, j)

    # Check for opponent's winning move to block
    for i, j in empty:
        new_board = [row.copy() for row in board]
        new_board[i][j] = -1
        if check_win(new_board, -1):
            return (i, j)

    # Select the best available position based on priority
    priority_cells = [
        (1, 1),  # Center
        (0, 0), (0, 2), (2, 0), (2, 2),  # Corners
        (0, 1), (1, 0), (1, 2), (2, 1)   # Edges
    ]
    for cell in priority_cells:
        if cell in empty:
            return cell

    # Fallback (should never be reached as all cells are checked)
    return empty[0]
