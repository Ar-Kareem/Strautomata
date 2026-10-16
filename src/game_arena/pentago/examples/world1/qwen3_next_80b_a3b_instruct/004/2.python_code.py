
import numpy as np
from collections import defaultdict
import time

def policy(you, opponent):
    # Convert to numpy arrays for efficient computation
    you = np.array(you, dtype=int)
    opponent = np.array(opponent, dtype=int)
    
    # Combine into a single board representation for easier manipulation
    # 0: empty, 1: you, 2: opponent
    board = np.zeros((6, 6), dtype=int)
    board[you == 1] = 1
    board[opponent == 1] = 2
    
    # Precompute all 5-in-a-row positions
    lines = []
    # Horizontal lines
    for r in range(6):
        for c in range(2):
            lines.append([(r, c+i) for i in range(5)])
    # Vertical lines
    for c in range(6):
        for r in range(2):
            lines.append([(r+i, c) for i in range(5)])
    # Diagonal lines (top-left to bottom-right)
    for r in range(2):
        for c in range(2):
            lines.append([(r+i, c+i) for i in range(5)])
    # Diagonal lines (top-right to bottom-left)
    for r in range(2):
        for c in range(2, 6):
            lines.append([(r+i, c-i) for i in range(5)])
    
    # Check if a player has 5 in a row
    def has_five_in_row(board, player):
        for line in lines:
            count = 0
            for r, c in line:
                if board[r, c] == player:
                    count += 1
                else:
                    count = 0
                if count == 5:
                    return True
        return False
    
    # Get list of empty cells
    empty_cells = [(r, c) for r in range(6) for c in range(6) if board[r, c] == 0]
    
    # If no empty cells (shouldn't happen per constraints), return dummy
    if not empty_cells:
        return "1,1,0,L"  # Fallback
    
    # Try immediate winning moves
    for r, c in empty_cells:
        # Place your marble
        board[r, c] = 1
        if has_five_in_row(board, 1):
            # Find which quadrant this cell belongs to
            quad = (r // 3) * 2 + (c // 3)
            # Try rotating each quadrant (only need one valid rotation to return)
            for quad_try in range(4):
                for dir_try in ['L', 'R']:
                    return f"{r+1},{c+1},{quad_try},{dir_try}"
        # Revert
        board[r, c] = 0
    
    # Try blocking opponent's winning moves
    for r, c in empty_cells:
        # Place opponent's marble
        board[r, c] = 2
        if has_five_in_row(board, 2):
            # Block it
            board[r, c] = 1
            quad = (r // 3) * 2 + (c // 3)
            for quad_try in range(4):
                for dir_try in ['L', 'R']:
                    return f"{r+1},{c+1},{quad_try},{dir_try}"
        # Revert
        board[r, c] = 0
    
    # Heuristic evaluation function
    def evaluate_board(board):
        score = 0
        
        # Check for potential lines
        for player in [1, 2]:
            multiplier = 1 if player == 1 else -1
            for line in lines:
                # Count consecutive positions for this player
                count = 0
                for r, c in line:
                    if board[r, c] == player:
                        count += 1
                    elif board[r, c] != 0:  # opponent or blocked
                        count = 0
                        break
                
                # Add scores based on consecutive counts
                if count == 4:
                    score += multiplier * 1000
                elif count == 3:
                    score += multiplier * 100
                elif count == 2:
                    score += multiplier * 10
                elif count == 1:
                    score += multiplier * 1
        
        # Reward center control
        center_areas = [(1,1), (1,2), (2,1), (2,2), 
                       (3,1), (3,2), (4,1), (4,2),
                       (1,3), (1,4), (2,3), (2,4),
                       (3,3), (3,4), (4,3), (4,4)]
        
        for r, c in center_areas:
            if board[r, c] == 1:
                score += 5
            elif board[r, c] == 2:
                score -= 5
                
        return score
    
    # Rotates a quadrant (3x3 subgrid) in place
    def rotate_quadrant(board, quad, direction):
        # Map quadrant to its top-left corner
        qr, qc = (quad // 2) * 3, (quad % 2) * 3
        # Extract 3x3 quadrant
        quad_arr = board[qr:qr+3, qc:qc+3].copy()
        
        if direction == 'L':  # 90 degrees anticlockwise
            rotated = np.rot90(quad_arr, k=3)  # or k=-1
        else:  # 'R', 90 degrees clockwise
            rotated = np.rot90(quad_arr, k=1)
        
        # Place back
        board[qr:qr+3, qc:qc+3] = rotated
    
    # Generate all legal moves
    def get_legal_moves():
        moves = []
        for r in range(6):
            for c in range(6):
                if board[r, c] == 0:  # Empty cell
                    for quad in range(4):
                        for dir in ['L', 'R']:
                            moves.append((r, c, quad, dir))
        return moves
    
    # Try moves with minimax search
    start_time = time.time()
    max_depth = 2  # Depth 2 for safety within 1s
    
    # Check time and adjust depth if needed
    empty_count = len(empty_cells)
    if empty_count < 10:
        max_depth = 3
    elif empty_count < 5:
        max_depth = 4
    
    best_move = None
    best_score = float('-inf')
    
    # For efficiency, limit number of moves to evaluate (especially early game)
    legal_moves = get_legal_moves()
    
    # Prioritize moves: win, block, center, then rest
    prioritized_moves = []
    
    # Try moves that place in center
    center_moves = []
    edge_moves = []
    for r, c, quad, dir in legal_moves:
        if r in [2,3] and c in [2,3]:  # Center 2x2 (0-indexed: 2,3)
            center_moves.append((r, c, quad, dir))
        else:
            edge_moves.append((r, c, quad, dir))
    
    prioritized_moves = center_moves + edge_moves
    
    # If we have very few moves, try all
    max_eval_moves = min(len(prioritized_moves), 30)
    
    # For each move, simulate and evaluate
    for move in prioritized_moves[:max_eval_moves]:
        r, c, quad, dir = move
        
        # Simulate the move
        board[r, c] = 1  # Place your marble
        # Simulate rotation
        original_quad = board[quad//2*3:(quad//2*3)+3, quad%2*3:(quad%2*3)+3].copy()
        rotate_quadrant(board, quad, dir)
        
        if has_five_in_row(board, 1):
            # Immediate win
            board[r, c] = 0
            rotate_quadrant(board, quad, 'L' if dir == 'R' else 'R')  # Undo rotation
            return f"{r+1},{c+1},{quad},{dir}"
        
        # Evaluate position with minimax
        score = minimax(board, 1, alpha=float('-inf'), beta=float('inf'), 
                        depth=max_depth-1, is_maximizing=False, lines=lines)
        
        # Undo the move
        board[r, c] = 0
        # Undo the rotation by rotating back
        rotate_quadrant(board, quad, 'L' if dir == 'R' else 'R')
        
        if score > best_score:
            best_score = score
            best_move = move
            
        # Time limit check
        if time.time() - start_time > 0.8:  # Leave some buffer
            break
    
    # If no good move found, pick the first legal move as fallback
    if best_move is None:
        best_move = legal_moves[0]
    
    r, c, quad, dir = best_move
    return f"{r+1},{c+1},{quad},{dir}"

# Minimax with alpha-beta pruning
def minimax(board, player, alpha, beta, depth, is_maximizing, lines):
    if depth == 0:
        return evaluate_board(board)
    
    # Check if game is over
    if has_five_in_row(board, 1) or has_five_in_row(board, 2):
        if has_five_in_row(board, 1):
            return 10000
        elif has_five_in_row(board, 2):
            return -10000
        else:
            return 0  # Draw
    
    # Get empty cells and generate moves
    empty_cells = [(r, c) for r in range(6) for c in range(6) if board[r, c] == 0]
    if not empty_cells:
        return 0  # Draw
    
    # Generate moves for current player
    moves = []
    for r, c in empty_cells:
        for quad in range(4):
            for dir in ['L', 'R']:
                moves.append((r, c, quad, dir))
    
    # Sort moves by heuristic for better pruning
    moves_with_scores = []
    for r, c, quad, dir in moves:
        # Simulate move
        board[r, c] = player
        rotate_quadrant(board, quad, dir)
        score = evaluate_board(board)
        # Undo
        board[r, c] = 0
        rotate_quadrant(board, quad, 'L' if dir == 'R' else 'R')
        moves_with_scores.append((score, r, c, quad, dir))
    
    # Sort by score (descending if maximizing, ascending if minimizing)
    moves_with_scores.sort(key=lambda x: x[0], reverse=is_maximizing)
    moves = [(r, c, quad, dir) for _, r, c, quad, dir in moves_with_scores]
    
    if is_maximizing:
        max_eval = float('-inf')
        for r, c, quad, dir in moves:
            # Make move
            board[r, c] = player
            rotate_quadrant(board, quad, dir)
            
            eval_score = minimax(board, 3 - player, alpha, beta, depth - 1, False, lines)
            
            # Undo move
            board[r, c] = 0
            rotate_quadrant(board, quad, 'L' if dir == 'R' else 'R')
            
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break  # Beta cutoff
        return max_eval
    else:
        min_eval = float('inf')
        for r, c, quad, dir in moves:
            # Make move
            board[r, c] = player
            rotate_quadrant(board, quad, dir)
            
            eval_score = minimax(board, 3 - player, alpha, beta, depth - 1, True, lines)
            
            # Undo move
            board[r, c] = 0
            rotate_quadrant(board, quad, 'L' if dir == 'R' else 'R')
            
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break  # Alpha cutoff
        return min_eval

# Helper function: check if player has five in a row
def has_five_in_row(board, player):
    # Horizontal
    for r in range(6):
        for c in range(2):
            if all(board[r, c+i] == player for i in range(5)):
                return True
    
    # Vertical
    for c in range(6):
        for r in range(2):
            if all(board[r+i, c] == player for i in range(5)):
                return True
    
    # Diagonal main (top-left to bottom-right)
    for r in range(2):
        for c in range(2):
            if all(board[r+i, c+i] == player for i in range(5)):
                return True
    
    # Diagonal anti (top-right to bottom-left)
    for r in range(2):
        for c in range(2, 6):
            if all(board[r+i, c-i] == player for i in range(5)):
                return True
    
    return False

# Heuristic evaluation function
def evaluate_board(board):
    score = 0
    
    # Check for potential lines for both players
    # Horizontal lines
    for r in range(6):
        for c in range(2):
            line = [board[r, c+i] for i in range(5)]
            score += evaluate_line(line, 1)
            score -= evaluate_line(line, 2)
    
    # Vertical lines
    for c in range(6):
        for r in range(2):
            line = [board[r+i, c] for i in range(5)]
            score += evaluate_line(line, 1)
            score -= evaluate_line(line, 2)
    
    # Diagonal main (top-left to bottom-right)
    for r in range(2):
        for c in range(2):
            line = [board[r+i, c+i] for i in range(5)]
            score += evaluate_line(line, 1)
            score -= evaluate_line(line, 2)
    
    # Diagonal anti (top-right to bottom-left)
    for r in range(2):
        for c in range(2, 6):
            line = [board[r+i, c-i] for i in range(5)]
            score += evaluate_line(line, 1)
            score -= evaluate_line(line, 2)
    
    # Center control bonus
    center_2x2 = [(2,2), (2,3), (3,2), (3,3)]
    for r, c in center_2x2:
        if board[r, c] == 1:
            score += 5
        elif board[r, c] == 2:
            score -= 5
            
    return score

def evaluate_line(line, player):
    # Count consecutive player pieces in line
    count = 0
    score = 0
    
    for cell in line:
        if cell == player:
            count += 1
        elif cell == 0:
            # Empty cell - can still form line
            count *= 1  # Maintain current streak
        else:
            # Opponent piece or blocked
            if count > 1:
                if count == 4:
                    return 1000
                elif count == 3:
                    return 100
                elif count == 2:
                    return 10
                elif count == 1:
                    return 1
            count = 0
    
    # Check end of line
    if count > 1:
        if count == 4:
            return 1000
        elif count == 3:
            return 100
        elif count == 2:
            return 10
        elif count == 1:
            return 1
    
    return 0
