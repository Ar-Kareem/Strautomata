
def policy(board: list[list[int]]) -> int:
    def get_row(col: int) -> int:
        for r in range(5, -1, -1):
            if board[r][col] == 0:
                return r
        return -1

    def is_win(player: int, row: int, col: int) -> bool:
        directions = [(0, 1), (1, 0), (1, 1), (-1, 1)]
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

    # Check for immediate win
    for col in range(7):
        row = get_row(col)
        if row == -1:
            continue
        original = board[row][col]
        board[row][col] = 1
        if is_win(1, row, col):
            board[row][col] = original
            return col
        board[row][col] = original

    # Block opponent's win
    for col in range(7):
        row = get_row(col)
        if row == -1:
            continue
        original = board[row][col]
        board[row][col] = -1
        if is_win(-1, row, col):
            board[row][col] = original
            return col
        board[row][col] = original

    # Prefer center columns
    for col in [3, 2, 4, 1, 5, 0, 6]:
        if board[0][col] == 0:
            return col

    # Fallback (should not reach here)
    for col in range(7):
        if board[0][col] == 0:
            return col
    return 0  # default return, though unreachable
