
def check_winner(board):
    # Check rows
    for row in board:
        if row[0] != 0 and row[0] == row[1] == row[2]:
            return row[0]
    # Check columns
    for col in range(3):
        if board[0][col] != 0 and board[0][col] == board[1][col] == board[2][col]:
            return board[0][col]
    # Check diagonals
    if board[0][0] != 0 and board[0][0] == board[1][1] == board[2][2]:
        return board[0][0]
    if board[0][2] != 0 and board[0][2] == board[1][1] == board[2][0]:
        return board[0][2]
    return 0

def is_full(board):
    return all(cell != 0 for row in board for cell in row)

def minimax(board, is_max_turn, alpha, beta):
    winner = check_winner(board)
    if winner == 1:
        return 10  # AI wins
    elif winner == -1:
        return -10  # Opponent wins
    if is_full(board):
        return 0  # Draw

    if is_max_turn:
        max_val = -float('inf')
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    board[i][j] = 1
                    score = minimax(board, False, alpha, beta)
                    board[i][j] = 0
                    max_val = max(max_val, score)
                    alpha = max(alpha, score)
                    if beta <= alpha:
                        return max_val
        return max_val
    else:
        min_val = float('inf')
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    board[i][j] = -1
                    score = minimax(board, True, alpha, beta)
                    board[i][j] = 0
                    min_val = min(min_val, score)
                    beta = min(beta, score)
                    if beta <= alpha:
                        return min_val
        return min_val

def policy(board: list[list[int]]) -> tuple[int, int]:
    empty = [(i, j) for i in range(3) for j in range(3) if board[i][j] == 0]
    if not empty:
        return (0, 0)
    best_score = -float('inf')
    best_move = (0, 0)
    for i, j in empty:
        board[i][j] = 1
        score = minimax(board, False, -float('inf'), float('inf'))
        board[i][j] = 0
        if score > best_score:
            best_score = score
            best_move = (i, j)
    return best_move
