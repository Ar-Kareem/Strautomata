
import numpy as np
from collections import defaultdict
import random
import time

def policy(you, opponent):
    # Convert input to numpy arrays for easier handling
    you = np.array(you)
    opponent = np.array(opponent)
    
    # Game state representation
    board = np.zeros((6, 6), dtype=int)
    board[you == 1] = 1  # 1 = my marble
    board[opponent == 1] = 2  # 2 = opponent marble
    
    # For faster board state lookups
    def check_winner(board_state):
        # Check rows
        for r in range(6):
            for c in range(2):
                if board_state[r,c] in [1,2] and board_state[r,c] == board_state[r,c+1] == board_state[r,c+2] == board_state[r,c+3] == board_state[r,c+4]:
                    return board_state[r,c]
        # Check cols
        for c in range(6):
            for r in range(2):
                if board_state[r,c] in [1,2] and board_state[r,c] == board_state[r+1,c] == board_state[r+2,c] == board_state[r+3,c] == board_state[r+4,c]:
                    return board_state[r,c]
        # Check diagonals
        for r in range(2):
            for c in range(2):
                if board_state[r,c] in [1,2] and board_state[r,c] == board_state[r+1,c+1] == board_state[r+2,c+2] == board_state[r+3,c+3] == board_state[r+4,c+4]:
                    return board_state[r,c]
        for r in range(4, 6):
            for c in range(2):
                if board_state[r,c] in [1,2] and board_state[r,c] == board_state[r-1,c+1] == board_state[r-2,c+2] == board_state[r-3,c+3] == board_state[r-4,c+4]:
                    return board_state[r,c]
        return 0
    
    def is_board_full(board_state):
        return not np.any(board_state == 0)
    
    def get_empty_positions(board_state):
        empty_positions = []
        for r in range(6):
            for c in range(6):
                if board_state[r,c] == 0:
                    empty_positions.append((r,c))
        return empty_positions
    
    def rotate_quadrant(board_state, quad, direction):
        # Define quadrant boundaries
        quads = [
            (slice(0,3), slice(0,3)),   # quad 0: top-left
            (slice(0,3), slice(3,6)),   # quad 1: top-right
            (slice(3,6), slice(0,3)),   # quad 2: bottom-left
            (slice(3,6), slice(3,6))    # quad 3: bottom-right
        ]
        
        # Create a copy of the board
        new_board = board_state.copy()
        
        # Extract the quadrant
        r_slice, c_slice = quads[quad]
        quadrant = new_board[r_slice, c_slice]
        
        # Rotate based on direction
        if direction == 'R':
            # Clockwise rotation
            new_board[r_slice, c_slice] = np.rot90(quadrant, k=-1)
        else:
            # Counter-clockwise rotation
            new_board[r_slice, c_slice] = np.rot90(quadrant, k=1)
            
        return new_board
    
    # Heuristic evaluation function
    def evaluate_board(board_state):
        score = 0
        # Check for immediate wins
        winner = check_winner(board_state)
        if winner == 1:  # My win
            return 100000
        if winner == 2:  # Opponent win
            return -100000
            
        # Look for my 4-in-a-row opportunities (worth 1000)
        for r in range(6):
            for c in range(2):
                if (board_state[r,c] == 1 and 
                    board_state[r,c+1] == 1 and 
                    board_state[r,c+2] == 1 and 
                    board_state[r,c+3] == 1 and 
                    board_state[r,c+4] == 0):
                    score += 1000
                if (board_state[r,c+4] == 1 and 
                    board_state[r,c+3] == 1 and 
                    board_state[r,c+2] == 1 and 
                    board_state[r,c+1] == 1 and 
                    board_state[r,c] == 0):
                    score += 1000
                    
        for c in range(6):
            for r in range(2):
                if (board_state[r,c] == 1 and 
                    board_state[r+1,c] == 1 and 
                    board_state[r+2,c] == 1 and 
                    board_state[r+3,c] == 1 and 
                    board_state[r+4,c] == 0):
                    score += 1000
                if (board_state[r+4,c] == 1 and 
                    board_state[r+3,c] == 1 and 
                    board_state[r+2,c] == 1 and 
                    board_state[r+1,c] == 1 and 
                    board_state[r,c] == 0):
                    score += 1000
                    
        # Count of 3-in-a-row (less valuable)
        for r in range(6):
            for c in range(3):
                if (board_state[r,c] == 1 and 
                    board_state[r,c+1] == 1 and 
                    board_state[r,c+2] == 1 and 
                    board_state[r,c+3] == 0):
                    score += 100
                if (board_state[r,c+3] == 1 and 
                    board_state[r,c+2] == 1 and 
                    board_state[r,c+1] == 1 and 
                    board_state[r,c] == 0):
                    score += 100
        for c in range(6):
            for r in range(3):
                if (board_state[r,c] == 1 and 
                    board_state[r+1,c] == 1 and 
                    board_state[r+2,c] == 1 and 
                    board_state[r+3,c] == 0):
                    score += 100
                if (board_state[r+3,c] == 1 and 
                    board_state[r+2,c] == 1 and 
                    board_state[r+1,c] == 1 and 
                    board_state[r,c] == 0):
                    score += 100
        
        # Check blocking opponent's 4-in-a-row
        for r in range(6):
            for c in range(2):
                if (board_state[r,c] == 2 and 
                    board_state[r,c+1] == 2 and 
                    board_state[r,c+2] == 2 and 
                    board_state[r,c+3] == 2 and 
                    board_state[r,c+4] == 0):
                    score -= 500
                if (board_state[r,c+4] == 2 and 
                    board_state[r,c+3] == 2 and 
                    board_state[r,c+2] == 2 and 
                    board_state[r,c+1] == 2 and 
                    board_state[r,c] == 0):
                    score -= 500
        for c in range(6):
            for r in range(2):
                if (board_state[r,c] == 2 and 
                    board_state[r+1,c] == 2 and 
                    board_state[r+2,c] == 2 and 
                    board_state[r+3,c] == 2 and 
                    board_state[r+4,c] == 0):
                    score -= 500
                if (board_state[r+4,c] == 2 and 
                    board_state[r+3,c] == 2 and 
                    board_state[r+2,c] == 2 and 
                    board_state[r+1,c] == 2 and 
                    board_state[r,c] == 0):
                    score -= 500
                    
        # Bonus for center positions (more control over board)
        center_positions = [(2,2), (2,3), (3,2), (3,3)]
        for r, c in center_positions:
            if board_state[r, c] == 1:
                score += 10
            elif board_state[r, c] == 2:
                score -= 10
                
        # Bonus for connected groups
        for r in range(6):
            for c in range(6):
                if board_state[r,c] == 1:
                    # Check horizontal and vertical neighbors
                    neighbors = 0
                    for dr, dc in [(0,1), (1,0), (1,1), (1,-1)]:
                        nr, nc = r+dr, c+dc
                        if 0 <= nr < 6 and 0 <= nc < 6 and board_state[nr, nc] == 1:
                            neighbors += 1
                    if neighbors > 0:
                        score += neighbors * 2
        return score
    
    def minimax(board_state, depth, alpha, beta, maximizing_player, max_depth):
        if max_depth == 0 or check_winner(board_state) != 0 or is_board_full(board_state):
            return evaluate_board(board_state)
            
        if maximizing_player:
            max_eval = float('-inf')
            for r in range(6):
                for c in range(6):
                    if board_state[r, c] == 0:  # Empty
                        for quad in range(4):
                            for rot in ['L', 'R']:
                                # Place marble and rotate
                                new_board = board_state.copy()
                                new_board[r, c] = 1  # Place my marble
                                new_board = rotate_quadrant(new_board, quad, rot)
                                # Recursively evaluate
                                eval_score = minimax(new_board, depth-1, alpha, beta, False, max_depth-1)
                                max_eval = max(max_eval, eval_score)
                                alpha = max(alpha, eval_score)
                                if beta <= alpha:
                                    break
            return max_eval
        else:
            min_eval = float('inf')
            for r in range(6):
                for c in range(6):
                    if board_state[r, c] == 0:  # Empty
                        for quad in range(4):
                            for rot in ['L', 'R']:
                                # Place marble and rotate
                                new_board = board_state.copy()
                                new_board[r, c] = 2  # Place opponent's marble
                                new_board = rotate_quadrant(new_board, quad, rot)
                                # Recursively evaluate
                                eval_score = minimax(new_board, depth-1, alpha, beta, True, max_depth-1)
                                min_eval = min(min_eval, eval_score)
                                beta = min(beta, eval_score)
                                if beta <= alpha:
                                    break
            return min_eval
    
    # Find possible moves and select best one
    def get_legal_moves():
        moves = []
        for r in range(6):
            for c in range(6):
                if board[r, c] == 0:  # Empty cell
                    for quad in range(4):
                        for rot in ['L', 'R']:
                            moves.append((r, c, quad, rot))
        return moves
    
    # Get all possible moves
    legal_moves = get_legal_moves()
    
    if not legal_moves:
        return "1,1,0,L"
    
    # Initial best move selection - let's try a simple strategy first
    # 1. Check for immediate win
    for move in legal_moves:
        r, c, quad, rot = move
        new_board = board.copy()
        new_board[r, c] = 1  # Place my marble
        new_board = rotate_quadrant(new_board, quad, rot)
        if check_winner(new_board) == 1:
            # This move leads to my win
            return f"{r+1},{c+1},{quad},{rot}"
    
    # 2. Check for immediate loss and block
    to_avoid = []
    for move in legal_moves:
        r, c, quad, rot = move
        new_board = board.copy()
        new_board[r, c] = 2  # Place opponent's marble
        # Rotate opponent's move
        new_board = rotate_quadrant(new_board, quad, rot)
        if check_winner(new_board) == 2:
            # This move leads to opponent's win
            to_avoid.append((r, c, quad, rot))
    
    # Avoid those immediate losses, otherwise choose best move
    if to_avoid:
        # Remove these moves from legal moves
        legal_moves = [move for move in legal_moves if move not in to_avoid]
    
    # Now proceed with a more sophisticated approach
    if not legal_moves:
        return "1,1,0,L"
    
    # Select an optimal move using minimax with alpha-beta pruning
    # Limit search depth for performance
    start_time = time.time()
    best_move = legal_moves[0]
    best_score = float('-inf')
    
    depth = 3  # Adjust based on time constraints
    
    # Try all moves with minimax to select the best
    for move in legal_moves:
        r, c, quad, rot = move
        new_board = board.copy()
        new_board[r, c] = 1  # Place my marble
        new_board = rotate_quadrant(new_board, quad, rot)
        score = minimax(new_board, depth-1, float('-inf'), float('inf'), False, depth-1)
        if score > best_score:
            best_score = score
            best_move = move
            
        # Stop early if time is running out
        if time.time() - start_time > 0.9:
            break
    
    r, c, quad, rot = best_move
    return f"{r+1},{c+1},{quad},{rot}"
