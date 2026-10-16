
import functools

def check_winner(board):
    # Check rows, columns, and diagonals for a winner
    for i in range(3):
        if board[i][0] == board[i][1] == board[i][2] != 0:
            return board[i][0]
        if board[0][i] == board[1][i] == board[2][i] != 0:
            return board[0][i]
    if board[0][0] == board[1][1] == board[2][2] != 0:
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] != 0:
        return board[0][2]
    return None

def is_full(board):
    return all(cell != 0 for row in board for cell in row)

@functools.lru_cache(maxsize=None)
def minimax(board_tuple, is_maximizing):
    board = [list(board_tuple[i:i+3]) for i in range(0, 9, 3)]
    winner = check_winner(board)
    if winner == 1:
        return 1
    elif winner == -1:
        return -1
    if is_full(board):
        return 0
    
    if is_maximizing:
        max_eval = -float('inf')
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    board[i][j] = 1
                    eval = minimax(tuple(sum(board, [])), False)
                    board[i][j] = 0
                    max_eval = max(max_eval, eval)
        return max_eval
    else:
        min_eval = float('inf')
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    board[i][j] = -1
                    eval = minimax(tuple(sum(board, [])), True)
                    board[i][j] = 0
                    min_eval = min(min_eval, eval)
        return min_eval

def policy(board):
    best_score = -float('inf')
    best_move = None
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = 1
                score = minimax(tuple(sum(board, [])), False)
                board[i][j] = 0
                if score > best_score:
                    best_score = score
                    best_move = (i, j)
    return best_move
