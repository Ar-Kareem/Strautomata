
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    board = np.array(board)
    
    def check_winner(board):
        # Check rows, columns, and diagonals
        for i in range(3):
            if abs(sum(board[i, :])) == 3:
                return board[i, 0]
            if abs(sum(board[:, i])) == 3:
                return board[0, i]
        if abs(sum([board[i, i] for i in range(3)])) == 3:
            return board[0, 0]
        if abs(sum([board[i, 2-i] for i in range(3)])) == 3:
            return board[0, 2]
        return 0
    
    def is_terminal(board):
        winner = check_winner(board)
        if winner != 0:
            return True, winner
        if not (board == 0).any():
            return True, 0
        return False, 0
    
    def minimax(board, depth, alpha, beta, maximizing):
        is_term, result = is_terminal(board)
        if is_term:
            return result
        
        if maximizing:
            max_eval = float('-inf')
            for i in range(3):
                for j in range(3):
                    if board[i, j] == 0:
                        board[i, j] = 1  # My move
                        eval_score = minimax(board, depth + 1, alpha, beta, False)
                        board[i, j] = 0  # Undo move
                        max_eval = max(max_eval, eval_score)
                        alpha = max(alpha, eval_score)
                        if beta <= alpha:
                            break
            return max_eval
        else:
            min_eval = float('inf')
            for i in range(3):
                for j in range(3):
                    if board[i, j] == 0:
                        board[i, j] = -1  # Opponent's move
                        eval_score = minimax(board, depth + 1, alpha, beta, True)
                        board[i, j] = 0  # Undo move
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
            if board[i, j] == 0:
                board[i, j] = 1  # Try my move
                score = minimax(board, 0, float('-inf'), float('inf'), False)
                board[i, j] = 0  # Undo move
                
                if score > best_score:
                    best_score = score
                    best_move = (i, j)
    
    return best_move
