
def policy(board):
    rows = len(board)
    cols = len(board[0]) if rows else 0

    def is_win(b, player):
        # Check horizontal
        for r in range(rows):
            for c in range(cols - 3):
                if all(b[r][c + i] == player for i in range(4)):
                    return True
        # Check vertical
        for c in range(cols):
            for r in range(rows - 3):
                if all(b[r + i][c] == player for i in range(4)):
                    return True
        # Check diagonal down-right
        for r in range(rows - 3):
            for c in range(cols - 3):
                if all(b[r + i][c + i] == player for i in range(4)):
                    return True
        # Check diagonal up-right
        for r in range(3, rows):
            for c in range(cols - 3):
                if all(b[r - i][c + i] == player for i in range(4)):
                    return True
        return False

    # Check for immediate win
    for col in range(cols):
        if board[0][col] != 0:
            continue
        new_board = [row[:] for row in board]
        row = next((r for r in range(rows - 1, -1, -1) if new_board[r][col] == 0), -1)
        if row == -1:
            continue
        new_board[row][col] = 1
        if is_win(new_board, 1):
            return col

    # Block opponent's potential win
    for col in range(cols):
        if board[0][col] != 0:
            continue
        new_board = [row[:] for row in board]
        row = next((r for r in range(rows - 1, -1, -1) if new_board[r][col] == 0), -1)
        if row == -1:
            continue
        new_board[row][col] = -1
        if is_win(new_board, -1):
            return col

    # Heuristic: prefer center columns
    center = cols // 2
    best_score = -1
    best_col = None
    for col in range(cols):
        if board[0][col] == 0:
            score = (cols - 1 - abs(col - center))
            if score > best_score:
                best_score = score
                best_col = col
    return best_col if best_col is not None else 0
