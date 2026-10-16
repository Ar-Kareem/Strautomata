
import math

def get_winner(board):
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
    return 0

def is_draw(board):
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                return False
    return True

def minimax(board, depth, is_maximizing, alpha, beta):
    winner = get_winner(board)
    if winner == 1:
        return 10 - depth
    elif winner == -1:
        return depth - 10
    elif is_draw(board):
        return 0

    if is_maximizing:
        max_eval = -math.inf
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    board[i][j] = 1
                    eval_score = minimax(board, depth+1, False, alpha, beta)
                    board[i][j] = 0
                    if eval_score > max_eval:
                        max_eval = eval_score
                    if eval_score > alpha:
                        alpha = eval_score
                    if beta <= alpha:
                        break
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = math.inf
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    board[i][j] = -1
                    eval_score = minimax(board, depth+1, True, alpha, beta)
                    board[i][j] = 0
                    if eval_score < min_eval:
                        min_eval = eval_score
                    if eval_score < beta:
                        beta = eval_score
                    if beta <= alpha:
                        break
            if beta <= alpha:
                break
        return min_eval

def policy(board: list[list[int]]) -> tuple[int, int]:
    best_score = -math.inf
    best_move = None

    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = 1
                score = minimax(board, 1, False, -math.inf, math.inf)
                board[i][j] = 0
                if score > best_score:
                    best_score = score
                    best_move = (i, j)

    return best_move
