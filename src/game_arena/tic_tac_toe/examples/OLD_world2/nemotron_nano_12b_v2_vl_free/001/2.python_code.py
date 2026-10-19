
def policy(board: list[list[int]]) -> tuple[int, int]:
    def is_win(p, i, j):
        # Check row
        if all(board[i][c] == p for c in range(4)):
            return True
        # Check column
        if all(board[r][j] == p for r in range(4)):
            return True
        # Check main diagonal
        if i == j and all(board[x][x] == p for x in range(4)):
            return True
        # Check anti-diagonal
        if i + j == 3 and all(board[x][3 - x] == p for x in range(4)):
            return True
        return False

    # Priority order: center, corners, edges
    priority = [
        (1, 1), (1, 2), (2, 1), (2, 2),
        (0, 0), (0, 3), (3, 0), (3, 3),
        (0, 1), (0, 2), (1, 0), (1, 3),
        (2, 0), (2, 3), (3, 1), (3, 2)
    ]

    # Step 1: Check for immediate win
    for move in priority:
        i, j = move
        if board[i][j] == 0:
            if is_win(1, i, j):
                return (i, j)

    # Step 2: Check to block opponent's win
    for move in priority:
        i, j = move
        if board[i][j] == 0:
            if is_win(-1, i, j):
                return (i, j)

    # Step 3: Take highest priority available cell
    for move in priority:
        i, j = move
        if board[i][j] == 0:
            return (i, j)

    # Fallback (should not be reached as there's always a move available)
    return (0, 0)
