
def policy(board: list[list[int]]) -> tuple[int, int]:
    def check_win(b, player):
        # Check rows
        for row in b:
            if all(cell == player for cell in row):
                return True
        # Check columns
        for col in range(3):
            if all(b[row][col] == player for row in range(3)):
                return True
        # Check diagonals
        if all(b[i][i] == player for i in range(3)):
            return True
        if all(b[i][2 - i] == player for i in range(3)):
            return True
        return False

    preferred_order = [
        (1, 1),
        (0, 0), (0, 2), (2, 0), (2, 2),
        (0, 1), (1, 0), (2, 1), (1, 2),
    ]

    for r, c in preferred_order:
        if board[r][c] == 0:
            new_board = [row[:] for row in board]
            new_board[r][c] = 1
            if check_win(new_board, 1):
                return (r, c)

    for r, c in preferred_order:
        if board[r][c] == 0:
            new_board = [row[:] for row in board]
            new_board[r][c] = -1
            if check_win(new_board, -1):
                return (r, c)

    for r, c in preferred_order:
        if board[r][c] == 0:
            return (r, c)

    # Fallback in case of any unexpected state
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                return (i, j)

    return (0, 0)
