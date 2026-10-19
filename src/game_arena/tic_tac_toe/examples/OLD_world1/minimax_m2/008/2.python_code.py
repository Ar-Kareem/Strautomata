
INF = 10**9

def check_winner(board):
    for i in range(3):
        if board[i][0] == board[i][1] == board[i][2] != 0:
            return board[i][0]
    for j in range(3):
        if board[0][j] == board[1][j] == board[2][j] != 0:
            return board[0][j]
    if board[0][0] == board[1][1] == board[2][2] != 0:
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] != 0:
        return board[0][2]
    if all(board[i][j] != 0 for i in range(3) for j in range(3)):
        return 0
    return None

def minimax(board, depth, is_maximizing_player):
    winner = check_winner(board)
    if winner is not None:
        if winner == 1:
            return 10 - depth
        elif winner == -1:
            return depth - 10
        elif winner == 0:
            return 0
    
    if is_maximizing_player:
        best = -INF
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    board[i][j] = 1
                    score = minimax(board, depth + 1, False)
                    board[i][j] = 0
                    best = max(best, score)
        return best
    else:
        best = INF
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    board[i][j] = -1
                    score = minimax(board, depth + 1, True)
                    board[i][j] = 0
                    best = min(best, score)
        return best

def policy(board):
    best_move = None
    best_score = -INF
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = 1
                score = minimax(board, 1, False)
                board[i][j] = 0
                if score > best_score:
                    best_score = score
                    best_move = (i, j)
    return best_move
