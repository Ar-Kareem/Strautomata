
def try_drop(board, col, player):
    for row in range(5, -1, -1):
        if board[row][col] == 0:
            board[row][col] = player
            return row
    return -1

def undo(board, row, col):
    board[row][col] = 0

def get_winner(board):
    # horizontal
    for r in range(6):
        for c in range(4):
            if board[r][c] == board[r][c + 1] == board[r][c + 2] == board[r][c + 3] == 1:
                return 1
            if board[r][c] == board[r][c + 1] == board[r][c + 2] == board[r][c + 3] == -1:
                return -1
    # vertical
    for c in range(7):
        for r in range(3):
            if board[r][c] == board[r + 1][c] == board[r + 2][c] == board[r + 3][c] == 1:
                return 1
            if board[r][c] == board[r + 1][c] == board[r + 2][c] == board[r + 3][c] == -1:
                return -1
    # diagonal /
    for r in range(3):
        for c in range(4):
            if board[r][c] == board[r + 1][c + 1] == board[r + 2][c + 2] == board[r + 3][c + 3] == 1:
                return 1
            if board[r][c] == board[r + 1][c + 1] == board[r + 2][c + 2] == board[r + 3][c + 3] == -1:
                return -1
    # diagonal \
    for r in range(3):
        for c in range(3, 7):
            if board[r][c] == board[r + 1][c - 1] == board[r + 2][c - 2] == board[r + 3][c - 3] == 1:
                return 1
            if board[r][c] == board[r + 1][c - 1] == board[r + 2][c - 2] == board[r + 3][c - 3] == -1:
                return -1
    return None

def is_full(board):
    for c in range(7):
        if board[0][c] == 0:
            return False
    return True

def heuristic(board):
    col_weights = [3, 4, 5, 7, 5, 4, 3]
    score = 0
    for c in range(7):
        for r in range(6):
            if board[r][c] == 1:
                score += col_weights[c]
            elif board[r][c] == -1:
                score -= col_weights[c]
    return score

def minimax(board, depth, alpha, beta, maximizing):
    winner = get_winner(board)
    if winner == 1:
        return 10000000
    if winner == -1:
        return -10000000
    if depth == 0 or is_full(board):
        return heuristic(board)
    move_order = [3, 2, 4, 1, 5, 0, 6]
    if maximizing:
        max_eval = -float('inf')
        for col in move_order:
            if board[0][col] != 0:
                continue
            row = try_drop(board, col, 1)
            eval_score = minimax(board, depth - 1, alpha, beta, False)
            undo(board, row, col)
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, max_eval)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for col in move_order:
            if board[0][col] != 0:
                continue
            row = try_drop(board, col, -1)
            eval_score = minimax(board, depth - 1, alpha, beta, True)
            undo(board, row, col)
            min_eval = min(min_eval, eval_score)
            beta = min(beta, min_eval)
            if beta <= alpha:
                break
        return min_eval

def policy(board: list[list[int]]) -> int:
    # Check for immediate win
    for col in range(7):
        if board[0][col] != 0:
            continue
        row = try_drop(board, col, 1)
        if get_winner(board) == 1:
            undo(board, row, col)
            return col
        undo(board, row, col)
    # Check for block
    for col in range(7):
        if board[0][col] != 0:
            continue
        row = try_drop(board, col, -1)
        if get_winner(board) == -1:
            undo(board, row, col)
            return col
        undo(board, row, col)
    # Minimax search
    best_score = -float('inf')
    best_col = 3  # default center
    move_order = [3, 2, 4, 1, 5, 0, 6]
    for col in move_order:
        if board[0][col] != 0:
            continue
        row = try_drop(board, col, 1)
        score = minimax(board, 12, -float('inf'), float('inf'), False)
        undo(board, row, col)
        if score > best_score:
            best_score = score
            best_col = col
    return best_col
