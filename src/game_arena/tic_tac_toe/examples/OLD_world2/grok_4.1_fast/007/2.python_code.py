
def is_winner(board, player):
    # Check rows
    for i in range(4):
        if all(board[i][j] == player for j in range(4)):
            return True
    # Check columns
    for j in range(4):
        if all(board[i][j] == player for i in range(4)):
            return True
    # Check main diagonal
    if all(board[i][i] == player for i in range(4)):
        return True
    # Check anti-diagonal
    if all(board[i][3 - i] == player for i in range(4)):
        return True
    return False

def is_full(board):
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                return False
    return True

def minimax(board, alpha, beta, maximizing):
    if is_winner(board, 1):
        return 1
    if is_winner(board, -1):
        return -1
    if is_full(board):
        return 0

    moves = sorted(((i, j) for i in range(4) for j in range(4) if board[i][j] == 0),
                   key=lambda p: abs(p[0] - 1.5) + abs(p[1] - 1.5))

    if maximizing:
        max_eval = -2
        for i, j in moves:
            board[i][j] = 1
            eval_score = minimax(board, alpha, beta, False)
            board[i][j] = 0
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, max_eval)
            if alpha >= beta:
                break
        return max_eval
    else:
        min_eval = 2
        for i, j in moves:
            board[i][j] = -1
            eval_score = minimax(board, alpha, beta, True)
            board[i][j] = 0
            min_eval = min(min_eval, eval_score)
            beta = min(beta, min_eval)
            if alpha >= beta:
                break
        return min_eval

def policy(board: list[list[int]]) -> tuple[int, int]:
    best_score = -2
    best_move = (-1, -1)
    for i in range(4):
        for j in range(4):
            if board[i][j] != 0:
                continue
            board[i][j] = 1
            score = minimax(board, -2, 2, False)
            board[i][j] = 0
            if score > best_score:
                best_score = score
                best_move = (i, j)
            if best_score == 1:
                return best_move
    return best_move
