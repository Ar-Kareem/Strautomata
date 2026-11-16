
def is_winner(board, player):
    # Check rows
    for i in range(3):
        if board[i][0] == player and board[i][1] == player and board[i][2] == player:
            return True
    # Check columns
    for j in range(3):
        if board[0][j] == player and board[1][j] == player and board[2][j] == player:
            return True
    # Check diagonals
    if board[0][0] == player and board[1][1] == player and board[2][2] == player:
        return True
    if board[0][2] == player and board[1][1] == player and board[2][0] == player:
        return True
    return False

def is_full(board):
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                return False
    return True

def get_legal_moves(board):
    moves = []
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                moves.append((i, j))
    return moves

def minimax(board, depth, is_maximizing, alpha=-float('inf'), beta=float('inf')):
    if is_winner(board, 1):
        return 10 - depth
    if is_winner(board, -1):
        return depth - 10
    if is_full(board):
        return 0

    if is_maximizing:
        max_eval = -float('inf')
        for i, j in get_legal_moves(board):
            board[i][j] = 1
            eval_score = minimax(board, depth + 1, False, alpha, beta)
            board[i][j] = 0
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for i, j in get_legal_moves(board):
            board[i][j] = -1
            eval_score = minimax(board, depth + 1, True, alpha, beta)
            board[i][j] = 0
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval

def policy(board: list[list[int]]) -> int:
    best_score = -float('inf')
    best_move = -1
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = 1
                score = minimax(board, 0, False, -float('inf'), float('inf'))
                board[i][j] = 0
                if score > best_score:
                    best_score = score
                    best_move = i * 3 + j + 1
    return best_move
