
def policy(board: list[list[int]]) -> int:
    def get_row_for_col(col: int) -> int:
        for row in range(5, -1, -1):
            if board[row][col] == 0:
                return row
        return -1  # Column is full

    def is_win_move(player: int, row: int, col: int) -> bool:
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]  # horizontal, vertical, diag1, diag2
        for dr, dc in directions:
            count = 1
            r, c = row + dr, col + dc
            while 0 <= r < 6 and 0 <= c < 7 and board[r][c] == player:
                count += 1
                r += dr
                c += dc
            r, c = row - dr, col - dc
            while 0 <= r < 6 and 0 <= c < 7 and board[r][c] == player:
                count += 1
                r -= dr
                c -= dc
            if count >= 4:
                return True
        return False

    # Column order prioritizes center columns for better strategic positions
    column_order = [3, 2, 4, 1, 5, 0, 6]

    # Check for immediate winning move
    for col in column_order:
        row = get_row_for_col(col)
        if row == -1:
            continue
        board[row][col] = 1  # Temporarily place the disc
        if is_win_move(1, row, col):
            board[row][col] = 0  # Undo temporary placement
            return col
        board[row][col] = 0  # Undo temporary placement

    # Check if opponent can win next move and block
    for col in column_order:
        row = get_row_for_col(col)
        if row == -1:
            continue
        board[row][col] = -1  # Temporarily place opponent's disc
        if is_win_move(-1, row, col):
            board[row][col] = 0  # Undo temporary placement
            return col
        board[row][col] = 0  # Undo temporary placement

    # Default to center-first heuristic if no immediate win/block
    for col in column_order:
        if board[0][col] == 0:  # If column is not full
            return col

    # As per problem statement, there's always a valid move, so this is a fallback
    return next(col for col in range(7) if board[0][col] == 0)
