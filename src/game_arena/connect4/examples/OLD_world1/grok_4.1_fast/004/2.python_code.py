
ROWS = 6
COLS = 7
DEPTH = 8

PIECE_WEIGHTS = [
    [3, 4, 5, 2, 5, 4, 3],
    [4, 5, 6, 3, 6, 5, 4],
    [5, 6, 7, 8, 7, 6, 5],
    [4, 6, 8, 10, 8, 6, 4],
    [3, 5, 7, 8, 7, 5, 3],
    [2, 4, 6, 7, 6, 4, 2]
]

def drop(board, col, player):
    for r in range(ROWS - 1, -1, -1):
        if board[r][col] == 0:
            board[r][col] = player
            return r
    return -1

def undo(board, col, row):
    board[row][col] = 0

def has_winner(board):
    # horizontal
    for row in board:
        for i in range(COLS - 3):
            p = row[i]
            if p != 0 and row[i] == row[i + 1] == row[i + 2] == row[i + 3]:
                return p
    # vertical
    for c in range(COLS):
        for i in range(ROWS - 3):
            p = board[i][c]
            if p != 0 and board[i][c] == board[i + 1][c] == board[i + 2][c] == board[i + 3][c]:
                return p
    # diagonal /
    for i in range(ROWS - 3):
        for j in range(COLS - 3):
            p = board[i][j]
            if p != 0 and board[i][j] == board[i + 1][j + 1] == board[i + 2][j + 2] == board[i + 3][j + 3]:
                return p
    # diagonal \
    for i in range(ROWS - 3):
        for j in range(3, COLS):
            p = board[i][j]
            if p != 0 and board[i][j] == board[i + 1][j - 1] == board[i + 2][j - 2] == board[i + 3][j - 3]:
                return p
    return 0

def is_board_full(board):
    return all(board[0][c] != 0 for c in range(COLS))

def evaluate_position(board):
    score = 0
    for r in range(ROWS):
        for c in range(COLS):
            if board[r][c] == 1:
                score += PIECE_WEIGHTS[r][c]
            elif board[r][c] == -1:
                score -= PIECE_WEIGHTS[r][c]
    return score

def get_ordered_moves(board):
    col_order = [3, 2, 4, 1, 5, 0, 6]
    return [c for c in col_order if board[0][c] == 0]

def minimax(board, depth, alpha, beta, maximizing):
    winner = has_winner(board)
    if winner != 0:
        return winner * (100000 + depth * 100)
    if is_board_full(board):
        return 0
    if depth == 0:
        return evaluate_position(board)

    moves = get_ordered_moves(board)
    if maximizing:
        max_eval = -1e9
        for col in moves:
            row = drop(board, col, 1)
            eval_score = minimax(board, depth - 1, alpha, beta, False)
            undo(board, col, row)
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = 1e9
        for col in moves:
            row = drop(board, col, -1)
            eval_score = minimax(board, depth - 1, alpha, beta, True)
            undo(board, col, row)
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval

def policy(board: list[list[int]]) -> int:
    # Check for immediate win
    for col in range(COLS):
        if board[0][col] == 0:
            row = drop(board, col, 1)
            if has_winner(board) == 1:
                undo(board, col, row)
                return col
            undo(board, col, row)
    # Check for immediate block
    for col in range(COLS):
        if board[0][col] == 0:
            row = drop(board, col, -1)
            if has_winner(board) == -1:
                undo(board, col, row)
                return col
            undo(board, col, row)
    # Minimax search
    best_score = -float('inf')
    best_col = 3  # default center
    ordered_moves = get_ordered_moves(board)
    for col in ordered_moves:
        row = drop(board, col, 1)
        score = minimax(board, DEPTH, -float('inf'), float('inf'), False)
        undo(board, col, row)
        if score > best_score:
            best_score = score
            best_col = col
    return best_col
