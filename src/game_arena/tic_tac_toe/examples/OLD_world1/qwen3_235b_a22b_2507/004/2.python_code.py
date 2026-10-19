
import numpy as np
from typing import Tuple

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Determines the optimal move for Tic Tac Toe using minimax algorithm with alpha-beta pruning.
    Player 1 (us) is maximizing, Player -1 (opponent) is minimizing.
    """
    board_array = np.array(board)
    
    def is_terminal(state):
        # Check rows, columns, and diagonals for a win
        for i in range(3):
            if abs(np.sum(state[i, :])) == 3 or abs(np.sum(state[:, i])) == 3:
                return True, np.sum(state[i, :]) // 3 if abs(np.sum(state[i, :])) == 3 else np.sum(state[:, i]) // 3
        
        if abs(np.sum(np.diag(state))) == 3:
            return True, np.sum(np.diag(state)) // 3
        if abs(np.sum(np.diag(np.fliplr(state)))) == 3:
            return True, np.sum(np.diag(np.fliplr(state))) // 3
            
        # Check for draw
        if 0 not in state:
            return True, 0
            
        return False, 0
    
    def minimax(state, depth, alpha, beta, maximizing_player):
        terminal, winner = is_terminal(state)
        if terminal:
            if winner == 1:
                return 10 - depth
            elif winner == -1:
                return depth - 10
            else:
                return 0
                
        if maximizing_player:
            max_eval = float('-inf')
            for i in range(3):
                for j in range(3):
                    if state[i, j] == 0:
                        state[i, j] = 1
                        eval_score = minimax(state, depth + 1, alpha, beta, False)
                        state[i, j] = 0
                        max_eval = max(max_eval, eval_score)
                        alpha = max(alpha, eval_score)
                        if beta <= alpha:
                            break
            return max_eval
        else:
            min_eval = float('inf')
            for i in range(3):
                for j in range(3):
                    if state[i, j] == 0:
                        state[i, j] = -1
                        eval_score = minimax(state, depth + 1, alpha, beta, True)
                        state[i, j] = 0
                        min_eval = min(min_eval, eval_score)
                        beta = min(beta, eval_score)
                        if beta <= alpha:
                            break
            return min_eval
    
    # Find all valid moves
    valid_moves = []
    for i in range(3):
        for j in range(3):
            if board_array[i, j] == 0:
                valid_moves.append((i, j))
    
    # If it's the first move, take center or corner
    if len(valid_moves) == 9:
        return (1, 1)  # Take center
    if len(valid_moves) == 8 and board_array[1, 1] == 0:
        return (1, 1)  # Take center if available
    
    # Use minimax to find the best move
    best_move = valid_moves[0]
    best_value = float('-inf')
    
    for move in valid_moves:
        board_array[move] = 1
        move_value = minimax(board_array, 0, float('-inf'), float('inf'), False)
        board_array[move] = 0
        
        if move_value > best_value:
            best_value = move_value
            best_move = move
    
    return best_move
