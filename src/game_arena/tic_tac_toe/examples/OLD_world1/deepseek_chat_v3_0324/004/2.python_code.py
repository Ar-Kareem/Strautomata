
import math
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    def is_terminal(b):
        # Check rows
        for row in b:
            if row[0] == row[1] == row[2] != 0:
                return True
        
        # Check columns
        for col in range(3):
            if b[0][col] == b[1][col] == b[2][col] != 0:
                return True
        
        # Check diagonals
        if b[0][0] == b[1][1] == b[2][2] != 0:
            return True
        if b[0][2] == b[1][1] == b[2][0] != 0:
            return True
        
        # Check if board is full
        if all(cell != 0 for row in b for cell in row):
            return True
        
        return False
    
    def evaluate(b):
        # Check rows
        for row in b:
            if row[0] == row[1] == row[2] == 1:
                return 10
            elif row[0] == row[1] == row[2] == -1:
                return -10
        
        # Check columns
        for col in range(3):
            if b[0][col] == b[1][col] == b[2][col] == 1:
                return 10
            elif b[0][col] == b[1][col] == b[2][col] == -1:
                return -10
        
        # Check diagonals
        if b[0][0] == b[1][1] == b[2][2] == 1:
            return 10
        if b[0][0] == b[1][1] == b[2][2] == -1:
            return -10
        if b[0][2] == b[1][1] == b[2][0] == 1:
            return 10
        if b[0][2] == b[1][1] == b[2][0] == -1:
            return -10
        
        return 0
    
    def minimax(b, depth, alpha, beta, is_maximizing):
        score = evaluate(b)
        
        if score == 10:
            return score - depth
        if score == -10:
            return score + depth
        if is_terminal(b):
            return 0
        
        if is_maximizing:
            best = -math.inf
            for i in range(3):
                for j in range(3):
                    if b[i][j] == 0:
                        b[i][j] = 1
                        val = minimax(b, depth + 1, alpha, beta, False)
                        b[i][j] = 0
                        best = max(best, val)
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
                        val = minimax(b, depth + 1, alpha, beta, True)
                        b[i][j] = 0
                        best = min(best, val)
                        beta = min(beta, best)
                        if beta <= alpha:
                            break
            return best
    
    # First move optimization (center is best first move)
    empty_cells = sum(row.count(0) for row in board)
    if empty_cells == 9:
        return (1, 1)
    
    # Check if we can win in the next move
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = 1
                if evaluate(board) == 10:
                    board[i][j] = 0
                    return (i, j)
                board[i][j] = 0
    
    # Check if opponent can win in the next move (block them)
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = -1
                if evaluate(board) == -10:
                    board[i][j] = 0
                    return (i, j)
                board[i][j] = 0
    
    # Find the best move using minimax
    best_val = -math.inf
    best_move = (-1, -1)
    
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = 1
                move_val = minimax(board, 0, -math.inf, math.inf, False)
                board[i][j] = 0
                
                if move_val > best_val:
                    best_move = (i, j)
                    best_val = move_val
                elif move_val == best_val:
                    # Randomize among equally good moves
                    if random.random() < 0.5:
                        best_move = (i, j)
    
    return best_move
