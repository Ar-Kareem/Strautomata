
def check_win(board, player):
    # Check horizontal lines
    for r in range(6):
        for c in range(4):
            if all(board[r][c+i] == player for i in range(4)):
                return True

    # Check vertical lines
    for r in range(3):
        for c in range(7):
            if all(board[r+i][c] == player for i in range(4)):
                return True

    # Check diagonal (down-right)
    for r in range(3):
        for c in range(4):
            if all(board[r+i][c+i] == player for i in range(4)):
                return True

    # Check diagonal (up-right)
    for r in range(3, 6):
        for c in range(4):
            if all(board[r-i][c+i] == player for i in range(4)):
                return True

    return False

def policy(board):
    # Identify playable columns (not full)
    valid_columns = [c for c in range(7) if board[0][c] == 0]

    # Check for immediate winning move
    for col in valid_columns:
        new_board = [row[:] for row in board]
        row_to_place = next(r for r in range(5, -1, -1) if new_board[r][col] == 0)
        new_board[row_to_place][col] = 1
        if check_win(new_board, 1):
            return col

    # Check if opponent can win next turn
    opponent_threats = []
    for col in valid_columns:
        new_board = [row[:] for row in board]
        row_to_place = next(r for r in range(5, -1, -1) if new_board[r][col] == 0)
        new_board[row_to_place][col] = -1
        if check_win(new_board, -1):
            opponent_threats.append(col)

    # Block opponent's winning move
    if opponent_threats:
        for col in [3, 2, 4, 1, 5, 0, 6]:
            if col in opponent_threats:
                return col

    # Default to center-preference heuristic
    for col in [3, 2, 4, 1, 5, 0, 6]:
        if col in valid_columns:
            return col
