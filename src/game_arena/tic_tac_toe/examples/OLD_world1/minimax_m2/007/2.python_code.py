
def policy(board: list[list[int]]) -> tuple[int, int]:
    best_score = -10
    best_move = (0, 0)
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = 1
                score = minimax(board, False, 1)
                board[i][j] = 0
                if score > best_score:
                    best_score = score
                    best_move = (i, j)
    return best_move

def minimax(board, is_maximizing, depth):
    winner = check_winner(board)
    if winner != 0:
        if winner == 1:
            return 10 - depth
        else:
            return depth - 10
    if is_full(board):
        return 0
    if is_maximizing:
        best = -10
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    board[i][j] = 1
                    score = minimax(board, False, depth + 1)
                    board[i][j] = 0
                    if score > best:
                        best = score
        return best
    else:
        best = 10
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    board[i][j] = -1
                    score = minimax(board, True, depth + 1)
                    board[i][j] = 0
                    if score < best:
                        best = score
        return best

def check_winner(board):
    for i in range(3):
        if board[i][0] == board[i][1] == board[i][2] and board[i][0] != 0:
            return board[i][0]
    for j in range(3):
        if board[0][j] == board[1][j] == board[2][j] and board[0][j] != 0:
            return board[0][j]
    if board[0][0] == board[1][1] == board[2][2] and board[0][0] != 0:
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] and board[0][2] != 0:
        return board[0][2]
    return 0

def is_full(board):
    for row in board:
        if 0 in row:
            return False
    return True
