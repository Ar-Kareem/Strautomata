
def policy(board):
    # Helper function to check if a column is full
    def is_full(board, column):
        return all(board[row][column] != 0 for row in range(6))

    # Helper function to find the lowest empty row in a column
    def find_empty_row(board, column):
        for row in reversed(range(6)):
            if board[row][column] == 0:
                return row
        return 6  # Indicates column is full

    # Helper function to check win condition for a given position and player
    def check_win(b, r, c, p):
        # Horizontal check
        cnt = 1
        j = c - 1
        while j >= 0 and b[r][j] == p:
            cnt += 1
            j -= 1
        j = c + 1
        while j < 7 and b[r][j] == p:
            cnt += 1
            j += 1
        if cnt >= 4:
            return True

        # Vertical check
        cnt = 1
        i = r - 1
        while i >= 0 and b[i][c] == p:
            cnt += 1
            i -= 1
        i = r + 1
        while i < 6 and b[i][c] == p:
            cnt += 1
            i += 1
        if cnt >= 4:
            return True

        # Diagonal (down-right)
        cnt = 1
        i, j = r - 1, c - 1
        while i >= 0 and j >= 0 and b[i][j] == p:
            cnt += 1
            i -= 1
            j -= 1
        i, j = r + 1, c + 1
        while i < 6 and j < 7 and b[i][j] == p:
            cnt += 1
            i += 1
            j += 1
        if cnt >= 4:
            return True

        # Diagonal (down-left)
        cnt = 1
        i, j = r - 1, c + 1
        while i >= 0 and j < 7 and b[i][j] == p:
            cnt += 1
            i -= 1
            j += 1
        i, j = r + 1, c - 1
        while i < 6 and j >= 0 and b[i][j] == p:
            cnt += 1
            i += 1
            j -= 1
        if cnt >= 4:
            return True

        return False

    # Step 1: Check for immediate winning move
    for col in range(7):
        if is_full(board, col):
            continue
        row = find_empty_row(board, col)
        new_board = [row.copy() for row in board]
        new_board[row][col] = 1
        if check_win(new_board, row, col, 1):
            return col

    # Step 2: Block opponent's immediate win
    for col in range(7):
        if is_full(board, col):
            continue
        row = find_empty_row(board, col)
        new_board = [row.copy() for row in board]
        new_board[row][col] = -1
        if check_win(new_board, row, col, -1):
            return col

    # Step 3: Heuristic to prioritize central columns
    order = [3, 4, 2, 5, 1, 6, 0]
    for candidate in order:
        if not is_full(board, candidate):
            return candidate

    # Fallback to first available column
    for col in range(7):
        if not is_full(board, col):
            return col

    return 0
