
from typing import List, Tuple
import math

def policy(board: List[List[int]]) -> Tuple[int, int]:
    def evaluate(b):
        # Check rows
        for row in b:
            if row[0] == row[1] == row[2]:
                if row[0] == 1:
                    return 10
                elif row[0] == -1:
                    return -10
        
        # Check columns
        for col in range(3):
            if b[0][col] == b[1][col] == b[2][col]:
                if b[0][col] == 1:
                    return 10
                elif b[0][col] == -1:
                    return -10
        
        # Check diagonals
        if b[0][0] == b[1][1] == b[2][2]:
            if b[0][0] == 1:
                return 10
            elif b[0][0] == -1:
                return -10
        
        if b[0][2] == b[1][1] == b[2][0]:
            if b[0][2] == 1:
                return 10
            elif b[0][2] == -1:
                return -10
        
        return 0  # Game not over yet
    
    def is_moves_left(b):
        for row in b:
            if 0 in row:
                return True
        return False
    
    def minimax(b, depth, is_max, alpha, beta):
        score = evaluate(b)
        
        if score == 10:
            return score - depth
        if score == -10:
            return score + depth
        if not is_moves_left(b):
            return 0
        
        if is_max:
            best = -math.inf
            for i in range(3):
                for j in range(3):
                    if b[i][j] == 0:
                        b[i][j] = 1
                        best = max(best, minimax(b, depth + 1, not is_max, alpha, beta))
                        b[i][j] = 0
                        alpha = max(alpha, best)
                        if beta <= alpha:
                            break
            return best
        else:
            best = math.inf
            for i in range(3):
                for j in range(3):
                    if b[i][j] == 0:
                        b[i][j] = -1
                        best = min(best, minimax(b, depth + 1, not is_max, alpha, beta))
                        b[i][j] = 0
                        beta = min(beta, best)
                        if beta <= alpha:
                            break
            return best
    
    # Find all empty spaces
    empty_spaces = []
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                empty_spaces.append((i, j))
    
    # If there are no empty spaces, something's wrong
    if not empty_spaces:
        return (0, 0)
    
    # First check if we can win immediately
    for i, j in empty_spaces:
        board[i][j] = 1
        if evaluate(board) == 10:
            board[i][j] = 0
            return (i, j)
        board[i][j] = 0
    
    # Then check if we need to block opponent from winning
    for i, j in empty_spaces:
        board[i][j] = -1
        if evaluate(board) == -10:
            board[i][j] = 0
            return (i, j)
        board[i][j] = 0
    
    # If no immediate win or block, use minimax
    best_move = (-1, -1)
    best_val = -math.inf
    
    for i, j in empty_spaces:
        board[i][j] = 1
        move_val = minimax(board, 0, False, -math.inf, math.inf)
        board[i][j] = 0
        if move_val > best_val:
            best_val = move_val
            best_move = (i, j)
    
    return best_move
