
def policy(board: list[list[int]]) -> tuple[int, int]:
    def is_winner(b, player):
        # Check rows
        for row in b:
            if all(cell == player for cell in row):
                return True
        # Check columns
        for col in range(4):
            if all(b[row][col] == player for row in range(4)):
                return True
        # Check main diagonal
        if all(b[i][i] == player for i in range(4)):
            return True
        # Check anti-diagonal
        if all(b[i][3 - i] == player for i in range(4)):
            return True
        return False

    empty_cells = []
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                empty_cells.append((i, j))

    # Check for immediate winning move
    for i, j in empty_cells:
        temp = [row.copy() for row in board]
        temp[i][j] = 1
        if is_winner(temp, 1):
            return (i, j)

    # Check for opponent's winning move to block
    for i, j in empty_cells:
        temp = [row.copy() for row in board]
        temp[i][j] = -1
        if is_winner(temp, -1):
            return (i, j)

    # Priority grid (higher values are better)
    priority = [
        [0, 1, 1, 0],
        [1, 2, 2, 1],
        [1, 2, 2, 1],
        [0, 1, 1, 0],
    ]

    # Sort cells by priority descending, then by position
    ordered = sorted(empty_cells, key=lambda x: (-priority[x[0]][x[1]], x))
    return ordered[0]
