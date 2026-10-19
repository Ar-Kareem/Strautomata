
def check_win(board, player):
    # Check horizontal
    for r in range(6):
        for c in range(4):
            if all(board[r][c + i] == player for i in range(4)):
                return True
    # Check vertical
    for r in range(3):
        for c in range(7):
            if all(board[r + i][c] == player for i in range(4)):
                return True
    # Check diagonal \
    for r in range(3):
        for c in range(4):
            if all(board[r + i][c + i] == player for i in range(4)):
                return True
    # Check diagonal /
    for r in range(3):
        for c in range(3, 7):
            if all(board[r + i][c - i] == player for i in range(4)):
                return True
    return False

def policy(board):
    cols = [0, 1, 2, 3, 4, 5, 6]
    # First, check if I can win
    for col in cols:
        if board[0][col] != 0:
            continue
        r = 5
        while r >= 0 and board[r][col] != 0:
            r -= 1
        if r < 0:
            continue
        board[r][col] = 1
        if check_win(board, 1):
            board[r][col] = 0
            return col
        board[r][col] = 0
    # Then, check if I need to block opponent from winning
    for col in cols:
        if board[0][col] != 0:
            continue
        r = 5
        while r >= 0 and board[r][col] != 0:
            r -= 1
        if r < 0:
            continue
        board[r][col] = -1
        if check_win(board, -1):
            board[r][col] = 0
            return col
        board[r][col] = 0
    # Otherwise, pick the column with the deepest possible drop
    max_r = -1
    best_col = None
    for col in cols:
        if board[0][col] != 0:
            continue
        r = 5
        while r >= 0 and board[r][col] != 0:
            r -= 1
        if r >= 0 and r > max_r:
            max_r = r
            best_col = col
    return best_col
