
import numpy as np
import time
import random

# Precompute all 32 windows of length 5 on the 6x6 board
# Rows (12), Cols (12), Diagonals (8)
WINDOWS = []
# Rows
for r in range(6):
    for c in range(2):
        WINDOWS.append([(r, c + i) for i in range(5)])
# Cols
for c in range(6):
    for r in range(2):
        WINDOWS.append([(r + i, c) for i in range(5)])
# Diagonals (Top-Left to Bottom-Right)
for r in range(2):
    for c in range(2):
        WINDOWS.append([(r + i, c + i) for i in range(5)])
# Diagonals (Top-Right to Bottom-Left)
for r in range(2):
    for c in range(4, 6):
        WINDOWS.append([(r + i, c - i) for i in range(5)])

def evaluate(board):
    """
    Evaluates the board state.
    Returns a large positive value for a win, large negative for a loss.
    Otherwise returns a heuristic score based on aligned marbles.
    """
    score = 0
    for w in WINDOWS:
        # Extract values in the window
        vals = board[tuple(zip(*w))]
        s = np.sum(vals)
        
        # Win/Loss detection
        if s == 5: return 1000000
        if s == -5: return -1000000
        
        # Heuristic scoring
        # If a line has both players, it is dead (score 0)
        if s > 0: score += s ** 3
        elif s < 0: score -= abs(s) ** 3
        
    # Center control bonus
    center_coords = [(2, 2), (2, 3), (3, 2), (3, 3)]
    for r, c in center_coords:
        if board[r, c] == 1: score += 10
        elif board[r, c] == -1: score -= 10
        
    return score

def get_quad_slice(q):
    """Returns the slice for a given quadrant index."""
    if q == 0: return slice(0, 3), slice(0, 3)
    if q == 1: return slice(0, 3), slice(3, 6)
    if q == 2: return slice(3, 6), slice(0, 3)
    if q == 3: return slice(3, 6), slice(3, 6)

def rotate_board(board, q, d):
    """Rotates a quadrant in place."""
    r_slice, c_slice = get_quad_slice(q)
    sub = board[r_slice, c_slice]
    if d == 'L':
        board[r_slice, c_slice] = np.rot90(sub, 1)
    else: # 'R'
        board[r_slice, c_slice] = np.rot90(sub, 3)

def undo_rotate(board, q, d):
    """Undoes a rotation in place."""
    r_slice, c_slice = get_quad_slice(q)
    sub = board[r_slice, c_slice]
    # Inverse of Left (1) is Right (3), Inverse of Right (3) is Left (1)
    if d == 'L':
        board[r_slice, c_slice] = np.rot90(sub, 3)
    else: # 'R'
        board[r_slice, c_slice] = np.rot90(sub, 1)

def get_moves(board):
    """Generates all legal moves, optimizing for empty quadrants."""
    empties = np.argwhere(board == 0)
    moves = []
    
    for r, c in empties:
        for q in range(4):
            # Optimization: If a quadrant is empty, L and R rotations yield same state.
            # We only need to consider one rotation to reduce branching factor.
            rs, cs = get_quad_slice(q)
            quad = board[rs, cs]
            if np.sum(np.abs(quad)) == 0:
                moves.append((r, c, q, 'L'))
            else:
                moves.append((r, c, q, 'L'))
                moves.append((r, c, q, 'R'))
    
    # Sort moves by center proximity to improve alpha-beta pruning
    # (r-2.5)^2 approx distance from center
    moves.sort(key=lambda m: (m[0]-2.5)**2 + (m[1]-2.5)**2)
    return moves

def minimax(board, depth, alpha, beta, maximizingPlayer):
    score = evaluate(board)
    
    # Terminal state or depth limit
    if abs(score) >= 1000000 or depth == 0:
        return score
        
    moves = get_moves(board)
    if not moves: return 0 # Draw
    
    if maximizingPlayer:
        max_eval = -float('inf')
        for r, c, q, d in moves:
            board[r, c] = 1
            rotate_board(board, q, d)
            
            eval_val = minimax(board, depth-1, alpha, beta, False)
            
            undo_rotate(board, q, d)
            board[r, c] = 0
            
            if eval_val > max_eval: max_eval = eval_val
            alpha = max(alpha, eval_val)
            if beta <= alpha: break
        return max_eval
    else:
        min_eval = float('inf')
        for r, c, q, d in moves:
            board[r, c] = -1
            rotate_board(board, q, d)
            
            eval_val = minimax(board, depth-1, alpha, beta, True)
            
            undo_rotate(board, q, d)
            board[r, c] = 0
            
            if eval_val < min_eval: min_eval = eval_val
            beta = min(beta, eval_val)
            if beta <= alpha: break
        return min_eval

def policy(you, opponent):
    # Convert inputs to a single board: 1 for you, -1 for opponent, 0 for empty
    board = np.array(you, dtype=int) - np.array(opponent, dtype=int)
    
    start_time = time.time()
    time_limit = 0.9 # seconds
    
    moves = get_moves(board)
    if not moves: return "1,1,0,L" # Fallback, shouldn't happen
    
    # Default to first valid move in case of timeout
    best_move = moves[0] 
    
    # Iterative Deepening
    for depth in range(1, 4): # Search depth 1, 2, 3
        current_best_val = -float('inf')
        current_best_move = best_move
        
        # Order moves: Put previous best move first
        # (Simple move ordering persistence)
        if best_move in moves:
            moves.remove(best_move)
            ordered_moves = [best_move] + moves
        else:
            ordered_moves = moves
            
        for move in ordered_moves:
            r, c, q, d = move
            
            board[r, c] = 1
            rotate_board(board, q, d)
            
            val = minimax(board, depth-1, -float('inf'), float('inf'), False)
            
            undo_rotate(board, q, d)
            board[r, c] = 0
            
            if val > current_best_val:
                current_best_val = val
                current_best_move = move
        
        # Update best move from completed depth
        best_move = current_best_move
        
        # Check time limit
        if time.time() - start_time > time_limit:
            break
            
        # Early exit if win found
        if current_best_val >= 1000000:
            break
            
    r, c, q, d = best_move
    return f"{r+1},{c+1},{q},{d}"
