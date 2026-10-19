
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert to numpy for easier manipulation
    board = np.array(board)
    
    # Helper: check if someone has won
    def check_winner(b):
        # Check rows, cols, diagonals
        for i in range(3):
            if abs(b[i, :].sum()) == 3:
                return b[i, 0]
            if abs(b[:, i].sum()) == 3:
                return b[0, i]
        if abs(b[[0,1,2],[0,1,2]].sum()) == 3:
            return b[0,0]
        if abs(b[[0,1,2],[2,1,0]].sum()) == 3:
            return b[0,2]
        return 0
    
    # Check if board is full
    def is_full(b):
        return not (b == 0).any()
    
    # Minimax with alpha-beta pruning
    def minimax(b, depth, alpha, beta, is_maximizing):
        winner = check_winner(b)
        if winner == 1:
            return 10 - depth
        if winner == -1:
            return depth - 10
        if is_full(b):
            return 0
        
        if is_maximizing:
            max_eval = -float('inf')
            for i in range(3):
                for j in range(3):
                    if b[i, j] == 0:
                        b[i, j] = 1
                        eval_score = minimax(b, depth + 1, alpha, beta, False)
                        b[i, j] = 0
                        max_eval = max(max_eval, eval_score)
                        alpha = max(alpha, eval_score)
                        if beta <= alpha:
                            break
            return max_eval
        else:
            min_eval = float('inf')
            for i in range(3):
                for j in range(3):
                    if b[i, j] == 0:
                        b[i, j] = -1
                        eval_score = minimax(b, depth + 1, alpha, beta, True)
                        b[i, j] = 0
                        min_eval = min(min_eval, eval_score)
                        beta = min(beta, eval_score)
                        if beta <= alpha:
                            break
            return min_eval
    
    # Find the best move
    best_value = -float('inf')
    best_move = (0, 0)
    for i in range(3):
        for j in range(3):
            if board[i, j] == 0:
                board[i, j] = 1
                move_value = minimax(board, 0, -float('inf'), float('inf'), False)
                board[i, j] = 0
                if move_value > best_value:
                    best_value = move_value
                    best_move = (i, j)
    
    return best_move
