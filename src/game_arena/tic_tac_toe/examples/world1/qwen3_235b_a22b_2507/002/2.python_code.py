
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    def check_winner(b):
        # Check rows, columns, and diagonals
        arr = np.array(b)
        for i in range(3):
            if abs(arr[i, :].sum()) == 3:  # row
                return arr[i, 0]
            if abs(arr[:, i].sum()) == 3:  # column
                return arr[0, i]
        if abs(arr[[0,1,2],[0,1,2]].sum()) == 3:  # main diagonal
            return arr[0, 0]
        if abs(arr[[0,1,2],[2,1,0]].sum()) == 3:  # anti-diagonal
            return arr[0, 2]
        return 0
    
    def is_terminal(b):
        winner = check_winner(b)
        if winner != 0:
            return True
        # Check if board is full (draw)
        for i in range(3):
            for j in range(3):
                if b[i][j] == 0:
                    return False
        return True
    
    def minimax(b, depth, alpha, beta, is_maximizing):
        if is_terminal(b):
            winner = check_winner(b)
            if winner == 1:  # I win
                return 10 - depth
            elif winner == -1:  # opponent wins
                return depth - 10
            else:  # draw
                return 0
        
        if is_maximizing:
            max_eval = float('-inf')
            for i in range(3):
                for j in range(3):
                    if b[i][j] == 0:
                        b[i][j] = 1
                        eval_score = minimax(b, depth + 1, alpha, beta, False)
                        b[i][j] = 0
                        max_eval = max(max_eval, eval_score)
                        alpha = max(alpha, eval_score)
                        if beta <= alpha:
                            break
            return max_eval
        else:
            min_eval = float('inf')
            for i in range(3):
                for j in range(3):
                    if b[i][j] == 0:
                        b[i][j] = -1
                        eval_score = minimax(b, depth + 1, alpha, beta, True)
                        b[i][j] = 0
                        min_eval = min(min_eval, eval_score)
                        beta = min(beta, eval_score)
                        if beta <= alpha:
                            break
            return min_eval
    
    # Find the best move
    best_score = float('-inf')
    best_move = (0, 0)
    
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = 1
                score = minimax(board, 0, float('-inf'), float('inf'), False)
                board[i][j] = 0
                if score > best_score:
                    best_score = score
                    best_move = (i, j)
    
    return best_move
