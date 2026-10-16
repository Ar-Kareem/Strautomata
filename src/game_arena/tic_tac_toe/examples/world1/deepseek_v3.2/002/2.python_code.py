
def check_winner(board):
    # rows
    for i in range(3):
        if board[i][0] == board[i][1] == board[i][2] != 0:
            return board[i][0]
    # columns
    for j in range(3):
        if board[0][j] == board[1][j] == board[2][j] != 0:
            return board[0][j]
    # diagonals
    if board[0][0] == board[1][1] == board[2][2] != 0:
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] != 0:
        return board[0][2]
    return 0

def is_board_full(board):
    for row in board:
        if 0 in row:
            return False
    return True

def minimax(board, depth, alpha, beta, maximizing):
    winner = check_winner(board)
    if winner != 0:
        # prefer faster wins/losses
        return winner * (10 - depth)
    if is_board_full(board):
        return 0

    if maximizing:
        max_eval = -float('inf')
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    board[i][j] = 1
                    eval = minimax(board, depth + 1, alpha, beta, False)
                    board[i][j] = 0
                    max_eval = max(max_eval, eval)
                    alpha = max(alpha, eval)
                    if beta <= alpha:
                        break
        return max_eval
    else:
        min_eval = float('inf')
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    board[i][j] = -1
                    eval = minimax(board, depth + 1, alpha, beta, True)
                    board[i][j] = 0
                    min_eval = min(min_eval, eval)
                    beta = min(beta, eval)
                    if beta <= alpha:
                        break
        return min_eval

def policy(board):
    best_score = -float('inf')
    best_move = None
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = 1
                score = minimax(board, 0, -float('inf'), float('inf'), False)
                board[i][j] = 0
                if score > best_score:
                    best_score = score
                    best_move = (i, j)
    # In the unlikely case that no move is found (board full), return a fallback.
    if best_move is None:
        # find any empty cell
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    return (i, j)
        return (0, 0)  # should never happen
    return best_move
