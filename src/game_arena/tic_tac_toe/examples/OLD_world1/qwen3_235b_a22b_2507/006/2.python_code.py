
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Minimax-based policy for Tic Tac Toe.
    Returns the best move (row, col) for player 1 (maximizing player).
    """
    board = np.array(board)
    
    def check_winner(board):
        # Check rows, columns, and diagonals
        for i in range(3):
            if abs(np.sum(board[i, :])) == 3:
                return np.sign(np.sum(board[i, :]))
            if abs(np.sum(board[:, i])) == 3:
                return np.sign(np.sum(board[:, i]))
        if abs(np.sum(np.diag(board))) == 3:
            return np.sign(np.sum(np.diag(board)))
        if abs(np.sum(np.diag(np.fliplr(board)))) == 3:
            return np.sign(np.sum(np.diag(np.fliplr(board))))
        return 0
    
    def is_terminal(board):
        winner = check_winner(board)
        if winner != 0:
            return True, winner
        if not np.any(board == 0):
            return True, 0
        return False, 0
    
    def minimax(board, depth, alpha, beta, is_maximizing):
        is_terminal_state, winner = is_terminal(board)
        if is_terminal_state:
            if winner == 1:
                return 10 - depth
            elif winner == -1:
                return depth - 10
            else:
                return 0
        
        if is_maximizing:
            max_eval = -float('inf')
            for i in range(3):
                for j in range(3):
                    if board[i][j] == 0:
                        board[i][j] = 1
                        eval_score = minimax(board, depth + 1, alpha, beta, False)
                        board[i][j] = 0
                        max_eval = max(max_eval, eval_score)
                        alpha = max(alpha, eval_score)
                        if beta <= alpha:
                            break
            return max_eval
        else:
            min_eval = float('inf')
            for i in range(3):
                for j in range(3):
                    if board[i][j] == 0:
                        board[i][j] = -1
                        eval_score = minimax(board, depth + 1, alpha, beta, True)
                        board[i][j] = 0
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
            if board[i][j] == 0:
                board[i][j] = 1
                move_value = minimax(board, 0, -float('inf'), float('inf'), False)
                board[i][j] = 0
                if move_value > best_value:
                    best_value = move_value
                    best_move = (i, j)
    
    return best_move
