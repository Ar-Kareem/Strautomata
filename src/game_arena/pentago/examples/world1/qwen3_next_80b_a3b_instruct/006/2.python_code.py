
import numpy as np
from itertools import product

def policy(you, opponent):
    # Convert to numpy arrays for efficient processing
    you = np.array(you, dtype=int)
    opponent = np.array(opponent, dtype=int)
    
    # Define board size and quadrant size
    BOARD_SIZE = 6
    QUAD_SIZE = 3
    WIN_LENGTH = 5
    
    # Precompute all possible lines of 5 in a 6x6 grid
    # Horizontal lines
    horizontal_lines = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE - WIN_LENGTH + 1):
            line = [(r, c + i) for i in range(WIN_LENGTH)]
            horizontal_lines.append(line)
    
    # Vertical lines
    vertical_lines = []
    for c in range(BOARD_SIZE):
        for r in range(BOARD_SIZE - WIN_LENGTH + 1):
            line = [(r + i, c) for i in range(WIN_LENGTH)]
            vertical_lines.append(line)
    
    # Diagonal lines (top-left to bottom-right)
    diagonal_lines_1 = []
    for r in range(BOARD_SIZE - WIN_LENGTH + 1):
        for c in range(BOARD_SIZE - WIN_LENGTH + 1):
            line = [(r + i, c + i) for i in range(WIN_LENGTH)]
            diagonal_lines_1.append(line)
    
    # Diagonal lines (top-right to bottom-left)
    diagonal_lines_2 = []
    for r in range(BOARD_SIZE - WIN_LENGTH + 1):
        for c in range(WIN_LENGTH - 1, BOARD_SIZE):
            line = [(r + i, c - i) for i in range(WIN_LENGTH)]
            diagonal_lines_2.append(line)
    
    all_lines = horizontal_lines + vertical_lines + diagonal_lines_1 + diagonal_lines_2
    
    def is_win(board):
        """Check if the given board has a 5-in-a-row for any player."""
        for line in all_lines:
            count = 0
            for r, c in line:
                if board[r, c] == 1:
                    count += 1
                else:
                    break
            if count == WIN_LENGTH:
                return True
        return False
    
    def check_win_after_placement(board, r, c):
        """Check if placing at (r,c) creates a win."""
        # Temporarily set the position
        temp_board = board.copy()
        temp_board[r, c] = 1
        return is_win(temp_board)
    
    def get_empty_cells():
        """Return list of empty cell coordinates (0-indexed)."""
        empty = []
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if you[r, c] == 0 and opponent[r, c] == 0:
                    empty.append((r, c))
        return empty
    
    def get_quadrant(r, c):
        """Convert 0-indexed coordinate to quadrant index."""
        qr = r // QUAD_SIZE
        qc = c // QUAD_SIZE
        return qr * 2 + qc
    
    def rotate_quadrant(board, quad, direction):
        """Rotate a quadrant (0-3) 90 degrees (L=anticlockwise, R=clockwise)"""
        # Convert quad to top-left corner of quadrant
        qr, qc = quad // 2, quad % 2
        start_r, start_c = qr * QUAD_SIZE, qc * QUAD_SIZE
        
        # Extract the 3x3 quadrant
        quad_board = board[start_r:start_r+QUAD_SIZE, start_c:start_c+QUAD_SIZE].copy()
        
        # Rotate the quadrant
        if direction == 'R':  # Clockwise
            rotated = np.rot90(quad_board, k=3)  # 90 degrees clockwise = 3x90 anticlockwise
        else:  # 'L' = anticlockwise
            rotated = np.rot90(quad_board, k=1)
        
        # Apply back to board
        result = board.copy()
        result[start_r:start_r+QUAD_SIZE, start_c:start_c+QUAD_SIZE] = rotated
        return result
    
    def evaluate_board(you_board, opp_board):
        """Heuristic evaluation of the board state."""
        score = 0
        
        # Control the center (prioritize center 2x2)
        center_cells = [(2,2), (2,3), (3,2), (3,3)]
        for r, c in center_cells:
            if you_board[r, c] == 1:
                score += 2
            elif opp_board[r, c] == 1:
                score -= 1.5
        
        # Count number of pieces
        score += (np.sum(you_board) - np.sum(opp_board)) * 0.5
        
        # Threat detection: 4-in-a-row with one empty for us
        for line in all_lines:
            you_count = sum(you_board[r, c] for r, c in line)
            opp_count = sum(opp_board[r, c] for r, c in line)
            empty_count = sum(1 for r, c in line if you_board[r, c] == 0 and opp_board[r, c] == 0)
            
            if you_count == WIN_LENGTH - 1 and empty_count == 1:
                score += 100  # Urgent threat
            elif opp_count == WIN_LENGTH - 1 and empty_count == 1:
                score -= 80   # Urgent threat we must block
        
        return score

    def minimax(depth, alpha, beta, is_maximizing, you_board, opp_board, current_player):
        """Minimax with alpha-beta pruning. current_player: True = you, False = opponent"""
        if depth == 0:
            return evaluate_board(you_board, opp_board), None
        
        empty_cells = get_empty_cells()
        if not empty_cells:
            return 0, None  # Draw
        
        best_move = None
        
        if is_maximizing:
            max_eval = -float('inf')
            # Order moves to improve pruning: wins first, then blocks, then center
            candidate_moves = []
            for r, c in empty_cells:
                # Check if this placement wins immediately
                if check_win_after_placement(you_board, r, c):
                    # Try all quadrant rotations
                    for quad in range(4):
                        for dir in ['L', 'R']:
                            new_you = you_board.copy()
                            new_you[r, c] = 1
                            # After placing, rotate
                            new_board = rotate_quadrant(new_you, quad, dir)
                            # Note: We also need to update opponent board (it rotates too)
                            new_opp = rotate_quadrant(opp_board, quad, dir)
                            return 10000, (r, c, quad, dir)
                
                # Check if opponent wins if we don't block
                temp_opp = opp_board.copy()
                temp_opp[r, c] = 1
                if is_win(temp_opp):
                    # This is a critical blocking move - evaluate it highly
                    for quad in range(4):
                        for dir in ['L', 'R']:
                            new_you = you_board.copy()
                            new_you[r, c] = 1
                            new_board = rotate_quadrant(new_you, quad, dir)
                            new_opp = rotate_quadrant(opp_board, quad, dir)
                            return 9999, (r, c, quad, dir)
                
                # Add to candidate list with priority
                priority = 0
                # Center preference
                if (r, c) in [(2,2), (2,3), (3,2), (3,3)]:
                    priority += 10
                # Any move with potential threat
                candidate_moves.append((r, c, priority))
            
            # Sort by priority
            candidate_moves.sort(key=lambda x: x[2], reverse=True)
            
            for r, c, _ in candidate_moves:
                # Place your marble
                new_you = you_board.copy()
                new_you[r, c] = 1
                
                # Try all 8 possible quadrant rotations (4 quads * 2 directions)
                for quad in range(4):
                    for dir in ['L', 'R']:
                        new_board_you = rotate_quadrant(new_you, quad, dir)
                        new_board_opp = rotate_quadrant(opp_board, quad, dir)
                        
                        # Check if move wins after rotation
                        if is_win(new_board_you):
                            return 10000, (r, c, quad, dir)
                        
                        eval, _ = minimax(depth - 1, alpha, beta, False, new_board_you, new_board_opp, False)
                        
                        if eval > max_eval:
                            max_eval = eval
                            best_move = (r, c, quad, dir)
                        
                        alpha = max(alpha, eval)
                        if beta <= alpha:
                            break
                    if beta <= alpha:
                        break
                if beta <= alpha:
                    break
            
            return max_eval, best_move
        else:
            min_eval = float('inf')
            for r, c in empty_cells:
                # Place opponent's marble
                new_opp = opp_board.copy()
                new_opp[r, c] = 1
                
                # Try all 8 possible quadrant rotations
                for quad in range(4):
                    for dir in ['L', 'R']:
                        new_board_opp = rotate_quadrant(new_opp, quad, dir)
                        new_board_you = rotate_quadrant(you_board, quad, dir)
                        
                        # Check if opponent wins after rotation
                        if is_win(new_board_opp):
                            return -10000, (r, c, quad, dir)
                        
                        eval, _ = minimax(depth - 1, alpha, beta, True, new_board_you, new_board_opp, True)
                        
                        if eval < min_eval:
                            min_eval = eval
                            best_move = (r, c, quad, dir)
                        
                        beta = min(beta, eval)
                        if beta <= alpha:
                            break
                    if beta <= alpha:
                        break
                if beta <= alpha:
                    break
            
            return min_eval, best_move

    # First, check if any immediate winning move exists (depth 0)
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if you[r, c] == 0 and opponent[r, c] == 0:
                # Try placing here and then any rotation
                temp_you = you.copy()
                temp_you[r, c] = 1
                for quad in range(4):
                    for dir in ['L', 'R']:
                        new_you = rotate_quadrant(temp_you, quad, dir)
                        new_opp = rotate_quadrant(opponent, quad, dir)
                        if is_win(new_you):
                            # Return immediately - this is a guaranteed win
                            return f"{r+1},{c+1},{quad},{dir}"
                
                # Check if this placement blocks an opponent win
                temp_opp = opponent.copy()
                temp_opp[r, c] = 1
                if is_win(temp_opp):
                    # Block move found - choose any rotation (we'll pick one that improves position)
                    # For simplicity, pick first valid rotation
                    for quad in range(4):
                        for dir in ['L', 'R']:
                            new_you = rotate_quadrant(temp_you, quad, dir)
                            new_opp = rotate_quadrant(opponent, quad, dir)
                            # After block, we still need to check if opponent has 5-in-a-row
                            if not is_win(new_opp):
                                return f"{r+1},{c+1},{quad},{dir}"
    
    # If no immediate win or block, use minimax with depth limit
    # We use depth=2 for speed (1 placement + 1 opponent placement + 1 our placement)
    # Since we're limited to 1 second, depth 2 is safe
    _, best_move = minimax(2, -float('inf'), float('inf'), True, you, opponent, True)
    
    # Fallback: if no move found (shouldn't happen), pick first available
    if best_move is None:
        empty_cells = get_empty_cells()
        r, c = empty_cells[0]
        quad = 0
        dir = 'L'
        best_move = (r, c, quad, dir)
    
    r, c, quad, dir = best_move
    return f"{r+1},{c+1},{quad},{dir}"
