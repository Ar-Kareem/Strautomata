
import time
import copy
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    # Start timing
    start_time = time.time()
    
    # Find all empty cells
    empty_cells = []
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                empty_cells.append((i, j))
    
    # If no empty cells, return any valid position (shouldn't happen)
    if not empty_cells:
        return (0, 0)
    
    # If board is empty, take center
    if len(empty_cells) == 16:
        return (1, 1)  # Prefer center-left of center
    
    # We'll use iterative deepening minimax with alpha-beta pruning
    # Max depth will be set dynamically based on time and board state
    max_depth = 6  # Start with depth 6
    best_move = empty_cells[0]
    
    # Function to check if player has won
    def check_win(board, player):
        # Check rows
        for i in range(4):
            if all(board[i][j] == player for j in range(4)):
                return True
        # Check columns
        for j in range(4):
            if all(board[i][j] == player for i in range(4)):
                return True
        # Check diagonals
        if all(board[i][i] == player for i in range(4)):
            return True
        if all(board[i][3-i] == player for i in range(4)):
            return True
        return False
    
    # Evaluation function
    def evaluate(board, player):
        opponent = -player
        score = 0
        
        # Check for win
        if check_win(board, player):
            return 1000
        if check_win(board, opponent):
            return -1000
        
        # Count two-in-a-row and three-in-a-row patterns for player
        def count_patterns(line, p):
            # Count contiguous lines of p
            count = 0
            for i in range(4):
                if line[i] == p:
                    # Check for 2+ in a row
                    for length in range(2, 5):
                        if i + length <= 4:
                            if all(line[i + j] == p for j in range(length)):
                                # Add score based on line length
                                if length == 2:
                                    count += 100
                                elif length == 3:
                                    count += 300
                                elif length == 4:
                                    count += 1000  # already handled by win check
            return count
        
        # Check rows
        for i in range(4):
            row = board[i]
            score += count_patterns(row, player)
            score -= count_patterns(row, opponent)
        
        # Check columns
        for j in range(4):
            col = [board[i][j] for i in range(4)]
            score += count_patterns(col, player)
            score -= count_patterns(col, opponent)
        
        # Check main diagonal
        main_diag = [board[i][i] for i in range(4)]
        score += count_patterns(main_diag, player)
        score -= count_patterns(main_diag, opponent)
        
        # Check anti-diagonal
        anti_diag = [board[i][3-i] for i in range(4)]
        score += count_patterns(anti_diag, player)
        score -= count_patterns(anti_diag, opponent)
        
        # Center control bonus
        center_positions = [(1,1), (1,2), (2,1), (2,2)]
        for r, c in center_positions:
            if board[r][c] == player:
                score += 50
            elif board[r][c] == opponent:
                score -= 50
        
        # Corner control bonus
        corner_positions = [(0,0), (0,3), (3,0), (3,3)]
        for r, c in corner_positions:
            if board[r][c] == player:
                score += 20
            elif board[r][c] == opponent:
                score -= 20
        
        return score
    
    # Minimax with alpha-beta pruning + iterative deepening
    def minimax(board, depth, alpha, beta, maximizing_player, player):
        # Check time
        if time.time() - start_time > 0.8:  # Leave some buffer
            return 0, None
        
        # Check terminal states
        if check_win(board, player):
            return 1000, None
        if check_win(board, -player):
            return -1000, None
        # Check for draw
        empty_count = sum(row.count(0) for row in board)
        if empty_count == 0:
            return 0, None
        
        # Early depth cutoff for very deep searches
        if depth == 0:
            return evaluate(board, player), None
        
        # Get empty cells
        empty_cells = []
        for i in range(4):
            for j in range(4):
                if board[i][j] == 0:
                    empty_cells.append((i, j))
        
        if not empty_cells:
            return 0, None
            
        best_move = empty_cells[0]
        
        if maximizing_player:
            max_eval = float('-inf')
            for cell in empty_cells:
                r, c = cell
                board[r][c] = player
                eval_score, _ = minimax(board, depth - 1, alpha, beta, False, player)
                board[r][c] = 0  # Undo move
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = cell
                    
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break  # Beta cutoff
            return max_eval, best_move
        else:
            min_eval = float('inf')
            for cell in empty_cells:
                r, c = cell
                board[r][c] = -player
                eval_score, _ = minimax(board, depth - 1, alpha, beta, True, player)
                board[r][c] = 0  # Undo move
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = cell
                    
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break  # Alpha cutoff
            return min_eval, best_move
    
    # Try iterative deepening
    for depth in range(2, max_depth + 1):
        if time.time() - start_time > 0.8:
            break
            
        _, best_from_depth = minimax(board, depth, float('-inf'), float('inf'), True, 1)
        
        if best_from_depth is not None:
            best_move = best_from_depth
    
    # Fallback: pick first available move if something goes wrong
    if best_move is None:
        return empty_cells[0]
    
    return best_move
