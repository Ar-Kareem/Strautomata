
def is_winner(board, player):
    # Check rows, columns, and diagonals for a win
    for i in range(3):
        if all(cell == player for cell in board[i]):
            return True
        if all(board[j][i] == player for j in range(3)):
            return True
    if all(board[i][i] == player for i in range(3)):
        return True
    if all(board[i][2 - i] == player for i in range(3)):
        return True
    return False

def is_draw(board):
    return all(cell != 0 for row in board for cell in row)

def is_terminal(board):
    return is_winner(board, 1) or is_winner(board, -1) or is_draw(board)

def evaluate(board):
    if is_winner(board, 1):
        return 1
    if is_winner(board, -1):
        return -1
    return 0

def minimax(board, is_maximizing, alpha, beta):
    if is_terminal(board):
        return evaluate(board)
    if is_maximizing:
        max_eval = float('-inf')
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    board[i][j] = 1
                    eval = minimax(board, False, alpha, beta)
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
                    eval = minimax(board, True, alpha, beta)
                    board[i][j] = 0
                    min_eval = min(min_eval, eval)
                    beta = min(beta, eval)
                    if beta <= alpha:
                        break
        return min_eval

def policy(board):
    best_move = None
    best_value = float('-inf')
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = 1
                move_value = minimax(board, False, float('-inf'), float('inf'))
                board[i][j] = 0
                if move_value > best_value:
                    best_value = move_value
                    best_move = (i, j)
    return best_move
