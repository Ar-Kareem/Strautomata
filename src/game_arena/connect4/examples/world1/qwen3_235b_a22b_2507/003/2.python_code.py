
import numpy as np
from typing import List, Tuple

def policy(board: List[List[int]]) -> int:
    # Convert to numpy array for easier manipulation
    grid = np.array(board)
    
    # Constants
    ROWS, COLS = 6, 7
    INF = float('inf')
    
    def is_valid_move(col):
        return grid[0][col] == 0
    
    def drop_piece(col, player):
        for row in range(ROWS-1, -1, -1):
            if grid[row][col] == 0:
                grid[row][col] = player
                return row
        return -1
    
    def undo_move(row, col):
        grid[row][col] = 0
    
    def get_valid_moves():
        return [c for c in range(COLS) if is_valid_move(c)]
    
    def check_winner(player):
        # Check horizontal
        for row in range(ROWS):
            for col in range(COLS-3):
                if all(grid[row][col+i] == player for i in range(4)):
                    return True
        
        # Check vertical
        for row in range(ROWS-3):
            for col in range(COLS):
                if all(grid[row+i][col] == player for i in range(4)):
                    return True
        
        # Check positive diagonal
        for row in range(ROWS-3):
            for col in range(COLS-3):
                if all(grid[row+i][col+i] == player for i in range(4)):
                    return True
        
        # Check negative diagonal
        for row in range(3, ROWS):
            for col in range(COLS-3):
                if all(grid[row-i][col+i] == player for i in range(4)):
                    return True
        
        return False
    
    def evaluate_position():
        score = 0
        player = 1
        opponent = -1
        
        # Center column preference
        center_col = 3
        center_count = np.sum(grid[:, center_col] == player)
        score += center_count * 3
        
        # Check for immediate win/loss opportunities
        if check_winner(player):
            return INF
        if check_winner(opponent):
            return -INF
            
        # Evaluate sequences
        def score_sequence(sequence):
            if len(sequence) < 4:
                return 0
                
            seq_score = 0
            for i in range(len(sequence) - 3):
                window = sequence[i:i+4]
                player_count = np.sum(window == player)
                empty_count = np.sum(window == 0)
                opponent_count = np.sum(window == opponent)
                
                if opponent_count == 0 and player_count > 0:
                    if player_count == 4:
                        return INF
                    elif player_count == 3:
                        seq_score += 100
                    elif player_count == 2:
                        seq_score += 10
                    elif player_count == 1:
                        seq_score += 1
                elif player_count == 0 and opponent_count > 0:
                    if opponent_count == 3:
                        return -INF
                    elif opponent_count == 2:
                        seq_score -= 20
                    elif opponent_count == 1:
                        seq_score -= 2
            
            return seq_score
        
        # Score horizontal
        for row in range(ROWS):
            row_seq = grid[row, :]
            score += score_sequence(row_seq)
        
        # Score vertical
        for col in range(COLS):
            col_seq = grid[:, col]
            score += score_sequence(col_seq)
        
        # Score positive diagonal
        for r in range(ROWS-3):
            for c in range(COLS-3):
                diag = [grid[r+i][c+i] for i in range(4)]
                score += score_sequence(diag)
        
        # Score negative diagonal
        for r in range(3, ROWS):
            for c in range(COLS-3):
                diag = [grid[r-i][c+i] for i in range(4)]
                score += score_sequence(diag)
        
        return score
    
    def minimax(depth, alpha, beta, maximizing_player):
        valid_moves = get_valid_moves()
        
        if depth == 0 or len(valid_moves) == 0:
            return evaluate_position()
        
        # Check for terminal states
        if check_winner(1):
            return INF
        if check_winner(-1):
            return -INF
            
        if maximizing_player:
            max_eval = -INF
            for col in valid_moves:
                row = drop_piece(col, 1)
                eval_score = minimax(depth - 1, alpha, beta, False)
                undo_move(row, col)
                
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = INF
            for col in valid_moves:
                row = drop_piece(col, -1)
                eval_score = minimax(depth - 1, alpha, beta, True)
                undo_move(row, col)
                
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    # Find best move
    valid_moves = get_valid_moves()
    if not valid_moves:
        return 0  # should not happen in normal play
    
    # Immediate win check
    for col in valid_moves:
        row = drop_piece(col, 1)
        if check_winner(1):
            undo_move(row, col)
            return col
        undo_move(row, col)
    
    # Block opponent's immediate win
    for col in valid_moves:
        row = drop_piece(col, -1)
        if check_winner(-1):
            undo_move(row, col)
            return col
        undo_move(row, col)
    
    # Use deeper search for early and mid game
    best_move = valid_moves[0]  # fallback
    best_value = -INF
    
    # Adjust depth based on game state
    empty_cells = np.sum(grid == 0)
    if empty_cells > 30:
        depth = 5
    elif empty_cells > 20:
        depth = 6
    else:
        depth = 7
    
    for col in valid_moves:
        row = drop_piece(col, 1)
        value = minimax(depth - 1, -INF, INF, False)
        undo_move(row, col)
        
        if value > best_value:
            best_value = value
            best_move = col
    
    return best_move
