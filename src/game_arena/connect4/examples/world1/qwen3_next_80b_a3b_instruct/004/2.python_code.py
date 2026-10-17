
import numpy as np
import copy
from typing import List

def policy(board: List[List[int]]) -> int:
    # Convert to numpy array for easier manipulation
    board_np = np.array(board, dtype=int)
    
    # Find valid columns (not full)
    valid_cols = [col for col in range(7) if board_np[0][col] == 0]
    if not valid_cols:
        return 3  # Fallback (shouldn't happen per constraints)
    
    # If only one move available, take it
    if len(valid_cols) == 1:
        return valid_cols[0]
    
    # Check for immediate win
    for col in valid_cols:
        if is_winning_move(board_np, col, 1):
            return col
    
    # Check for immediate opponent win and block
    for col in valid_cols:
        if is_winning_move(board_np, col, -1):
            return col
    
    # Use minimax with alpha-beta pruning
    # Depth 5 is safe for 6x7 grid within 1 second
    best_col = choose_best_move(board_np, depth=5, alpha=float('-inf'), beta=float('inf'), maximizing_player=True)
    
    # Fallback to center if minimax fails (shouldn't happen)
    if best_col is None:
        # Prefer center columns
        center_dist = [(abs(col - 3), col) for col in valid_cols]
        center_dist.sort()
        return center_dist[0][1]
    
    return best_col

def is_winning_move(board: np.ndarray, col: int, player: int) -> bool:
    """Check if placing a piece in this column creates a winning line for player"""
    # Find the row where the piece would land
    row = 5
    while row >= 0 and board[row][col] != 0:
        row -= 1
    if row < 0:
        return False
    
    # Make temporary move
    board[row][col] = player
    
    # Check all possible 4-in-a-row directions
    win = check_win_at_position(board, row, col, player)
    
    # Undo move
    board[row][col] = 0
    
    return win

def check_win_at_position(board: np.ndarray, row: int, col: int, player: int) -> bool:
    """Check if placing a piece at (row, col) creates a win for player"""
    directions = [
        (0, 1),   # horizontal
        (1, 0),   # vertical
        (1, 1),   # diagonal up-right
        (1, -1)   # diagonal up-left
    ]
    
    for dr, dc in directions:
        count = 1  # count the piece we just placed
        
        # Check in positive direction
        r, c = row + dr, col + dc
        while 0 <= r < 6 and 0 <= c < 7 and board[r][c] == player:
            count += 1
            r += dr
            c += dc
        
        # Check in negative direction
        r, c = row - dr, col - dc
        while 0 <= r < 6 and 0 <= c < 7 and board[r][c] == player:
            count += 1
            r -= dr
            c -= dc
        
        if count >= 4:
            return True
    
    return False

def get_board_score(board: np.ndarray, player: int) -> float:
    """Heuristic evaluation function for the board state"""
    score = 0
    
    # Center column control (strong positional advantage)
    center_count = sum(1 for r in range(6) if board[r][3] == player)
    score += center_count * 3
    
    # Count potential connect-4 lines (3 in a row with one empty space)
    score += count_threats(board, player) * 2
    score -= count_threats(board, -player) * 1.5  # Penalize opponent threats
    
    # Positional advantage: bottom row pieces are more valuable
    for r in range(6):
        for c in range(7):
            if board[r][c] == player:
                # Discs in bottom rows are more valuable
                score += (6 - r) * 0.1
                # Center columns are valuable
                score += (3 - abs(c - 3)) * 0.1
    
    return score

def count_threats(board: np.ndarray, player: int) -> int:
    """Count number of 3-in-a-row patterns with an empty space (potential wins)"""
    threats = 0
    
    # Horizontal threats
    for r in range(6):
        for c in range(4):  # can start at col 0-3
            pieces = [board[r][c+i] for i in range(4)]
            if pieces.count(player) == 3 and pieces.count(0) == 1:
                # Make sure the empty space is at the end where disc would fall
                empty_idx = pieces.index(0)
                # If empty space is not at the top of a column, it's not a real threat
                if empty_idx == 3 and r == 5:
                    threats += 1
                elif empty_idx == 3 and r < 5 and board[r+1][c+empty_idx] != 0:
                    threats += 1
                elif empty_idx < 3 and board[r+1][c+empty_idx] == 0:
                    # This means the empty space can be "filled" from below
                    pass
                else:
                    threats += 1
    
    # Vertical threats
    for c in range(7):
        for r in range(3):  # can start at row 0-2
            pieces = [board[r+i][c] for i in range(4)]
            if pieces.count(player) == 3 and pieces.count(0) == 1:
                # The only possible empty space is at the top for vertical
                if pieces[0] == 0 and r == 0:
                    threats += 1
                elif pieces[0] != 0 and pieces[0] != player:
                    pass
                elif pieces.count(0) == 1:
                    # Empty space must be at position 0 (top) to be valid threat
                    if pieces[0] == 0:
                        threats += 1
    
    # Diagonal threats (positive slope: bottom-left to top-right)
    for r in range(3):
        for c in range(4):
            pieces = [board[r+i][c+i] for i in range(4)]
            if pieces.count(player) == 3 and pieces.count(0) == 1:
                empty_idx = pieces.index(0)
                # For diagonal, need to check if space can be filled from below
                if empty_idx == 3:  # empty at top-right
                    if r + 3 == 5 or board[r+4][c+4] != 0:
                        threats += 1
                elif empty_idx < 3:
                    if r + empty_idx < 5 and board[r+empty_idx+1][c+empty_idx+1] == 0:
                        # Space below is empty, not a valid immediate threat
                        pass
                    else:
                        threats += 1
    
    # Diagonal threats (negative slope: bottom-right to top-left)
    for r in range(3):
        for c in range(3, 7):
            pieces = [board[r+i][c-i] for i in range(4)]
            if pieces.count(player) == 3 and pieces.count(0) == 1:
                empty_idx = pieces.index(0)
                if empty_idx == 3:  # empty at top-left
                    if r + 3 == 5 or board[r+4][c-4] != 0:
                        threats += 1
                elif empty_idx < 3:
                    if r + empty_idx < 5 and board[r+empty_idx+1][c-empty_idx-1] == 0:
                        pass  # not valid threat
                    else:
                        threats += 1
    
    return threats

def choose_best_move(board: np.ndarray, depth: int, alpha: float, beta: float, maximizing_player: bool) -> int:
    """Minimax with alpha-beta pruning to choose the best move"""
    valid_cols = [col for col in range(7) if board[0][col] == 0]
    if not valid_cols:
        return 3
    
    # Base case: depth 0 or terminal state
    if depth == 0:
        return None
    
    # Check for immediate win/loss
    for col in valid_cols:
        if is_winning_move(board, col, 1 if maximizing_player else -1):
            return col
    
    best_col = valid_cols[0]
    
    if maximizing_player:
        max_eval = float('-inf')
        # Prioritize center columns for better pruning
        sorted_cols = sorted(valid_cols, key=lambda x: abs(x - 3))
        
        for col in sorted_cols:
            # Simulate move
            row = 5
            while row >= 0 and board[row][col] != 0:
                row -= 1
            if row < 0:
                continue
                
            board[row][col] = 1
            
            # Recursively evaluate
            eval = minimax_value(board, depth - 1, alpha, beta, False)
            
            # Undo move
            board[row][col] = 0
            
            if eval > max_eval:
                max_eval = eval
                best_col = col
            
            alpha = max(alpha, eval)
            if beta <= alpha:
                break  # Alpha-beta pruning
                
        return best_col
    
    else:  # Minimizing player (opponent)
        min_eval = float('inf')
        # Prioritize center columns for better pruning
        sorted_cols = sorted(valid_cols, key=lambda x: abs(x - 3))
        
        for col in sorted_cols:
            # Simulate move
            row = 5
            while row >= 0 and board[row][col] != 0:
                row -= 1
            if row < 0:
                continue
                
            board[row][col] = -1
            
            # Recursively evaluate
            eval = minimax_value(board, depth - 1, alpha, beta, True)
            
            # Undo move
            board[row][col] = 0
            
            if eval < min_eval:
                min_eval = eval
                best_col = col
            
            beta = min(beta, eval)
            if beta <= alpha:
                break  # Alpha-beta pruning
                
        return best_col

def minimax_value(board: np.ndarray, depth: int, alpha: float, beta: float, maximizing_player: bool) -> float:
    """Helper function for minimax evaluation"""
    valid_cols = [col for col in range(7) if board[0][col] == 0]
    
    # Check terminal states
    if depth == 0:
        return get_board_score(board, 1)
    
    # Check for immediate win/loss
    if maximizing_player:
        for col in valid_cols:
            if is_winning_move(board, col, 1):
                return 10000  # Large positive score for immediate win
    else:
        for col in valid_cols:
            if is_winning_move(board, col, -1):
                return -10000  # Large negative score for opponent win
    
    if not valid_cols:  # Draw
        return 0
    
    if maximizing_player:
        max_eval = float('-inf')
        sorted_cols = sorted(valid_cols, key=lambda x: abs(x - 3))
        
        for col in sorted_cols:
            row = 5
            while row >= 0 and board[row][col] != 0:
                row -= 1
            if row < 0:
                continue
                
            board[row][col] = 1
            eval = minimax_value(board, depth - 1, alpha, beta, False)
            board[row][col] = 0
            
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
                
        return max_eval
    
    else:
        min_eval = float('inf')
        sorted_cols = sorted(valid_cols, key=lambda x: abs(x - 3))
        
        for col in sorted_cols:
            row = 5
            while row >= 0 and board[row][col] != 0:
                row -= 1
            if row < 0:
                continue
                
            board[row][col] = -1
            eval = minimax_value(board, depth - 1, alpha, beta, True)
            board[row][col] = 0
            
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
                
        return min_eval
