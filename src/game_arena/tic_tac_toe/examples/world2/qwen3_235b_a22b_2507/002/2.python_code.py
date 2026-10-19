
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    board = np.array(board)
    
    def check_winner(board):
        # Check rows, columns, and diagonals for a winner
        for i in range(4):
            if abs(sum(board[i, :])) == 4:
                return np.sign(sum(board[i, :]))
            if abs(sum(board[:, i])) == 4:
                return np.sign(sum(board[:, i]))
        
        # Diagonals
        if abs(sum(board[i, i] for i in range(4))) == 4:
            return np.sign(sum(board[i, i] for i in range(4)))
        if abs(sum(board[i, 3 - i] for i in range(4))) == 4:
            return np.sign(sum(board[i, 3 - i] for i in range(4)))
        
        return 0  # No winner

    def is_full(board):
        return not (board == 0).any()

    def minimax(board, depth, alpha, beta, maximizing):
        winner = check_winner(board)
        if winner != 0:
            return winner
        if is_full(board):
            return 0
        
        if maximizing:
            max_eval = -float('inf')
            for i in range(4):
                for j in range(4):
                    if board[i, j] == 0:
                        board[i, j] = 1
                        eval_score = minimax(board, depth + 1, alpha, beta, False)
                        board[i, j] = 0
                        max_eval = max(max_eval, eval_score)
                        alpha = max(alpha, eval_score)
                        if beta <= alpha:
                            break
            return max_eval
        else:
            min_eval = float('inf')
            for i in range(4):
                for j in range(4):
                    if board[i, j] == 0:
                        board[i, j] = -1
                        eval_score = minimax(board, depth + 1, alpha, beta, True)
                        board[i, j] = 0
                        min_eval = min(min_eval, eval_score)
                        beta = min(beta, eval_score)
                        if beta <= alpha:
                            break
            return min_eval

    best_move = None
    best_value = -float('inf')
    moves = []
    for i in range(4):
        for j in range(4):
            if board[i, j] == 0:
                board[i, j] = 1
                move_value = minimax(board, 0, -float('inf'), float('inf'), False)
                board[i, j] = 0
                moves.append(((i, j), move_value))
                if move_value > best_value:
                    best_value = move_value
                    best_move = (i, j)
                    
    # If all moves are equally bad (e.g., loss is unavoidable), pick first valid move
    if best_move is None:
        for i in range(4):
            for j in range(4):
                if board[i, j] == 0:
                    return (i, j)
                    
    return best_move
