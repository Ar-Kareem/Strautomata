
import numpy as np
import random
import time

# Global timing constraints
START_TIME = 0
TIME_LIMIT = 0.9  # seconds

def policy(you, opponent) -> str:
    global START_TIME
    START_TIME = time.time()
    
    # Convert to numpy arrays for faster operations
    you_board = np.array(you, dtype=np.int8)
    opp_board = np.array(opponent, dtype=np.int8)
    
    # Find all legal moves
    legal_moves = get_legal_moves(you_board, opp_board)
    
    if not legal_moves:
        # Should never happen as per constraints
        return "1,1,0,R"
    
    best_move = None
    best_score = float('-inf')
    
    # Iterative deepening
    for depth in range(1, 10):
        if time.time() - START_TIME > TIME_LIMIT:
            break
        
        current_best_move = None
        current_best_score = float('-inf')
        alpha = float('-inf')
        beta = float('inf')
        
        # Sort moves for better pruning (evaluate promising moves first)
        scored_moves = []
        for move in legal_moves:
            row, col, quad, direction = move
            # Quick heuristic: prefer center positions and positions that create lines
            score = quick_move_score(you_board, opp_board, row, col)
            scored_moves.append((score, move))
        
        scored_moves.sort(reverse=True, key=lambda x: x[0])
        
        for score, move in scored_moves:
            if time.time() - START_TIME > TIME_LIMIT:
                break
            
            r, c, q, d = move
            new_you, new_opp = apply_move(you_board, opp_board, r, c, q, d, is_you=True)
            
            move_score = minimax(new_you, new_opp, depth - 1, False, alpha, beta)
            
            if move_score > current_best_score:
                current_best_score = move_score
                current_best_move = move
            
            alpha = max(alpha, move_score)
        
        if current_best_move is not None:
            best_move = current_best_move
            best_score = current_best_score
    
    # Format the move string
    r, c, q, d = best_move
    return f"{r+1},{c+1},{q},{d}"

def get_legal_moves(you_board, opp_board):
    """Generate all legal moves: place marble in empty cell, then rotate a quadrant"""
    moves = []
    empty_cells = np.argwhere((you_board == 0) & (opp_board == 0))
    
    for cell in empty_cells:
        row, col = cell
        for quad in range(4):
            for direction in ['L', 'R']:
                moves.append((row, col, quad, direction))
    
    return moves

def apply_move(you_board, opp_board, row, col, quad, direction, is_you=True):
    """Apply a move and return new board states"""
    new_you = you_board.copy()
    new_opp = opp_board.copy()
    
    # Place marble
    if is_you:
        new_you[row, col] = 1
    else:
        new_opp[row, col] = 1
    
    # Rotate quadrant
    rotate_quadrant(new_you, new_opp, quad, direction)
    
    return new_you, new_opp

def rotate_quadrant(you_board, opp_board, quad, direction):
    """Rotate a quadrant in-place"""
    # Map quad to row/col ranges
    quad_ranges = {
        0: (slice(0, 3), slice(0, 3)),
        1: (slice(0, 3), slice(3, 6)),
        2: (slice(3, 6), slice(0, 3)),
        3: (slice(3, 6), slice(3, 6))
    }
    
    r_slice, c_slice = quad_ranges[quad]
    
    you_quad = you_board[r_slice, c_slice].copy()
    opp_quad = opp_board[r_slice, c_slice].copy()
    
    if direction == 'R':  # clockwise 90 degrees
        you_board[r_slice, c_slice] = np.rot90(you_quad, k=-1)
        opp_board[r_slice, c_slice] = np.rot90(opp_quad, k=-1)
    else:  # 'L' - anticlockwise 90 degrees
        you_board[r_slice, c_slice] = np.rot90(you_quad, k=1)
        opp_board[r_slice, c_slice] = np.rot90(opp_quad, k=1)

def minimax(you_board, opp_board, depth, is_maximizing, alpha, beta):
    """Minimax with alpha-beta pruning"""
    if time.time() - START_TIME > TIME_LIMIT:
        return evaluate_board(you_board, opp_board)
    
    # Check for terminal states
    you_win = check_win(you_board)
    opp_win = check_win(opp_board)
    
    if you_win and opp_win:
        return 0  # Draw
    elif you_win:
        return 10000 + depth  # Win is better sooner
    elif opp_win:
        return -10000 - depth  # Loss is worse sooner
    
    if depth == 0:
        return evaluate_board(you_board, opp_board)
    
    # Check if board is full
    if np.all((you_board == 1) | (opp_board == 1)):
        return 0  # Draw
    
    if is_maximizing:
        max_eval = float('-inf')
        legal_moves = get_legal_moves(you_board, opp_board)
        
        # Sort moves for better pruning
        if depth >= 3:
            scored_moves = []
            for move in legal_moves:
                r, c, q, d = move
                score = quick_move_score(you_board, opp_board, r, c)
                scored_moves.append((score, move))
            scored_moves.sort(reverse=True, key=lambda x: x[0])
        else:
            scored_moves = [(0, move) for move in legal_moves]
            random.shuffle(scored_moves)
        
        for _, move in scored_moves:
            if time.time() - START_TIME > TIME_LIMIT:
                return evaluate_board(you_board, opp_board)
            
            r, c, q, d = move
            new_you, new_opp = apply_move(you_board, opp_board, r, c, q, d, is_you=True)
            eval_score = minimax(new_you, new_opp, depth - 1, False, alpha, beta)
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        
        return max_eval if max_eval != float('-inf') else 0
    else:
        min_eval = float('inf')
        legal_moves = get_legal_moves(opp_board, you_board)  # Swap for opponent's perspective
        
        if depth >= 3:
            scored_moves = []
            for move in legal_moves:
                r, c, q, d = move
                score = quick_move_score(opp_board, you_board, r, c)
                scored_moves.append((score, move))
            scored_moves.sort(reverse=True, key=lambda x: x[0])
        else:
            scored_moves = [(0, move) for move in legal_moves]
            random.shuffle(scored_moves)
        
        for _, move in scored_moves:
            if time.time() - START_TIME > TIME_LIMIT:
                return evaluate_board(you_board, opp_board)
            
            r, c, q, d = move
            new_opp, new_you = apply_move(opp_board, you_board, r, c, q, d, is_you=True)
            eval_score = minimax(new_you, new_opp, depth - 1, True, alpha, beta)
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        
        return min_eval if min_eval != float('inf') else 0

def check_win(board):
    """Check if a player has 5 or more in a row"""
    # Check horizontal
    for r in range(6):
        for c in range(2):
            if np.sum(board[r, c:c+5]) >= 5:
                return True
    
    # Check vertical
    for r in range(2):
        for c in range(6):
            if np.sum(board[r:r+5, c]) >= 5:
                return True
    
    # Check diagonal (top-left to bottom-right)
    for r in range(2):
        for c in range(2):
            if np.sum(np.diag(board[r:r+5, c:c+5])) >= 5:
                return True
    
    # Check diagonal (top-right to bottom-left)
    for r in range(2):
        for c in range(2):
            if np.sum(np.diag(np.fliplr(board[r:r+5, c:c+5]))) >= 5:
                return True
    
    return False

def evaluate_board(you_board, opp_board):
    """Heuristic evaluation of the board"""
    score = 0
    
    # Evaluate all possible lines of 5
    score += evaluate_lines(you_board) * 10
    score -= evaluate_lines(opp_board) * 10
    
    # Center control bonus
    center_mask = np.array([[0,0,0,0,0,0],
                            [0,1,1,1,1,0],
                            [0,1,2,2,1,0],
                            [0,1,2,2,1,0],
                            [0,1,1,1,1,0],
                            [0,0,0,0,0,0]])
    score += np.sum(you_board * center_mask) * 2
    score -= np.sum(opp_board * center_mask) * 2
    
    return score

def evaluate_lines(board):
    """Evaluate the potential of a board based on lines of 5"""
    score = 0
    
    lines = []
    
    # Horizontal lines
    for r in range(6):
        for c in range(2):
            lines.append(board[r, c:c+5])
    
    # Vertical lines
    for r in range(2):
        for c in range(6):
            lines.append(board[r:r+5, c])
    
    # Diagonals (top-left to bottom-right)
    for r in range(2):
        for c in range(2):
            lines.append(np.diag(board[r:r+5, c:c+5]))
    
    # Diagonals (top-right to bottom-left)
    for r in range(2):
        for c in range(2):
            lines.append(np.diag(np.fliplr(board[r:r+5, c:c+5])))
    
    for line in lines:
        count = np.sum(line)
        if count == 1:
            score += 1
        elif count == 2:
            score += 10
        elif count == 3:
            score += 100
        elif count == 4:
            score += 1000
        elif count >= 5:
            score += 10000
    
    return score

def quick_move_score(you_board, opp_board, row, col):
    """Quick heuristic score for a potential move (for move ordering)"""
    score = 0
    
    # Prefer center positions
    center_score = 3 - abs(row - 2.5) - abs(col - 2.5)
    score += center_score * 2
    
    # Check if placing here could extend a line
    temp_board = you_board.copy()
    temp_board[row, col] = 1
    
    # Count stones in potential lines through this position
    lines = []
    
    # Horizontal
    for c_start in range(max(0, col-4), min(2, col+1)):
        c_end = c_start + 5
        if c_end <= 6:
            lines.append(temp_board[row, c_start:c_end])
    
    # Vertical
    for r_start in range(max(0, row-4), min(2, row+1)):
        r_end = r_start + 5
        if r_end <= 6:
            lines.append(temp_board[r_start:r_end, col])
    
    # Diagonals
    for dr, dc in [(1,1), (1,-1)]:
        for start in range(-4, 1):
            positions = []
            for i in range(5):
                r = row + (start + i) * dr
                c = col + (start + i) * dc
                if 0 <= r < 6 and 0 <= c < 6:
                    positions.append((r, c))
            if len(positions) == 5:
                lines.append(np.array([temp_board[r, c] for r, c in positions]))
    
    for line in lines:
        count = np.sum(line)
        score += count ** 2 * 5
    
    return score
