
def policy(board):
    def is_win(b, p):
        rows = len(b)
        cols = len(b[0])
        for r in range(rows):
            for c in range(cols - 3):
                if b[r][c] == p and b[r][c+1] == p and b[r][c+2] == p and b[r][c+3] == p:
                    return True
        for c in range(cols):
            for r in range(rows - 3):
                if b[r][c] == p and b[r+1][c] == p and b[r+2][c] == p and b[r+3][c] == p:
                    return True
        for r in range(rows - 3):
            for c in range(cols - 3):
                if b[r][c] == p and b[r+1][c+1] == p and b[r+2][c+2] == p and b[r+3][c+3] == p:
                    return True
        for r in range(rows - 3):
            for c in range(3, cols):
                if b[r][c] == p and b[r+1][c-1] == p and b[r+2][c-2] == p and b[r+3][c-3] == p:
                    return True
        return False

    def is_playable(b, c):
        return any(b[r][c] == 0 for r in range(6))

    for col in range(7):
        if is_playable(board, col):
            new_row = None
            for r in reversed(range(6)):
                if board[r][col] == 0:
                    new_row = r
                    break
            new_board = [row.copy() for row in board]
            new_board[new_row][col] = 1
            if is_win(new_board, 1):
                return col

    for col in range(7):
        if is_playable(board, col):
            new_row = None
            for r in reversed(range(6)):
                if board[r][col] == 0:
                    new_row = r
                    break
            new_board = [row.copy() for row in board]
            new_board[new_row][col] = -1
            if is_win(new_board, -1):
                return col

    def evaluate_move(col):
        new_row = None
        for r in reversed(range(6)):
            if board[r][col] == 0:
                new_row = r
                break
        temp_board = [row.copy() for row in board]
        temp_board[new_row][col] = 1
        score = 0

        # Horizontal
        count = 1
        c = col - 1
        while c >= 0 and temp_board[new_row][c] == 1:
            count += 1
            c -= 1
        c = col + 1
        while c < 7 and temp_board[new_row][c] == 1:
            count += 1
            c += 1
        if count >= 3:
            score += count

        # Vertical
        count = 1
        r = new_row - 1
        while r >= 0 and temp_board[r][col] == 1:
            count += 1
            r -= 1
        if count >= 3:
            score += count

        # Diagonal \
        count = 1
        r, c = new_row - 1, col - 1
        while r >= 0 and c >= 0 and temp_board[r][c] == 1:
            count += 1
            r -= 1
            c -= 1
        r, c = new_row + 1, col + 1
        while r < 6 and c < 7 and temp_board[r][c] == 1:
            count += 1
            r += 1
            c += 1
        if count >= 3:
            score += count

        # Diagonal /
        count = 1
        r, c = new_row - 1, col + 1
        while r >= 0 and c < 7 and temp_board[r][c] == 1:
            count += 1
            r -= 1
            c += 1
        r, c = new_row + 1, col - 1
        while r < 6 and c >= 0 and temp_board[r][c] == 1:
            count += 1
            r += 1
            c -= 1
        if count >= 3:
            score += count

        center_bonus = 3 - abs(col - 3)
        score += center_bonus * 2
        return score

    playable = [c for c in range(7) if is_playable(board, c)]
    if not playable:
        return 0

    best_score = -float('inf')
    best_cols = []
    for c in playable:
        score = evaluate_move(c)
        if score > best_score:
            best_score = score
            best_cols = [c]
        elif score == best_score:
            best_cols.append(c)

    best_col = min(best_cols, key=lambda x: abs(x - 3))
    return best_col
