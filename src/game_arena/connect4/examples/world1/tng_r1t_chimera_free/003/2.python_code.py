
def policy(board: list[list[int]]) -> int:
    def is_win(b, player, row, col):
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for dx, dy in directions:
            count = 1
            x, y = row + dx, col + dy
            while 0 <= x < 6 and 0 <= y < 7:
                if (x == row and y == col) or b[x][y] == player:
                    count += 1
                else:
                    break
                x += dx
                y += dy
            x, y = row - dx, col - dy
            while 0 <= x < 6 and 0 <= y < 7:
                if (x == row and y == col) or b[x][y] == player:
                    count += 1
                else:
                    break
                x -= dx
                y -= dy
            if count >= 4:
                return True
        return False

    valid_columns = [col for col in range(7) if board[0][col] == 0]
    center_order = [3, 2, 4, 1, 5, 0, 6]

    # Check for immediate win
    for col in center_order:
        if col not in valid_columns:
            continue
        row = 5
        while row >= 0 and board[row][col] != 0:
            row -= 1
        if row < 0:
            continue
        if is_win(board, 1, row, col):
            return col

    # Check opponent's win
    for col in center_order:
        if col not in valid_columns:
            continue
        row = 5
        while row >= 0 and board[row][col] != 0:
            row -= 1
        if row < 0:
            continue
        if is_win(board, -1, row, col):
            return col

    # Choose best remaining column
    for col in center_order:
        if col in valid_columns:
            return col

    # Fallback (shouldn't reach here as valid_columns is non-empty)
    return valid_columns[0]
