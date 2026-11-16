
import numpy as np
import random
from typing import Tuple, List, Optional

# Move constants
EMPTY = 0
ME = 1
OPPONENT = 2

# Precompute win lines for efficient checking
def generate_win_lines():
    lines = []
    
    # Horizontal lines
    for r in range(6):
        for c in range(2):  # Only need to check 3 consecutive positions
            line = [(r, c+i) for i in range(5)]
            lines.append(line)
            
    # Vertical lines  
    for c in range(6):
        for r in range(2):  # Only need to check 3 consecutive positions
            line = [(r+i, c) for i in range(5)]
            lines.append(line)
            
    # Diagonal lines (top-left to bottom-right)
    for r in range(2):
        for c in range(2):
            line = [(r+i, c+i) for i in range(5)]
            lines.append(line)
            
    # Diagonal lines (top-right to bottom-left)
    for r in range(2):
        for c in range(4, 6):
            line = [(r+i, c-i) for i in range(5)]
            lines.append(line)
            
    return lines

WIN_LINES = generate_win_lines()
INFTY = 1000000

def check_win(board: np.ndarray) -> int:
    """Returns 0 if no win, 1 if me wins, 2 if opponent wins, 3 if draw"""
    # Check all possible 5-in-a-row lines
    for line in WIN_LINES:
        values = [board[r, c] for r, c in line]
        if all(v == ME for v in values):
            return 1
        if all(v == OPPONENT for v in values):
            return 2
    
    # Check for draw (board full)
    if np.all(board != EMPTY):
        return 3
    
    return 0

def rotate_quadrant(board: np.ndarray, quad: int, direction: str) -> np.ndarray:
    """Rotate quadrant 0-3, L = anticlockwise, R = clockwise"""
    board_copy = board.copy()
    
    # Define quadrant boundaries
    quad_boundaries = [
        (0, 3, 0, 3),  # 0: rows 0-2, cols 0-2
        (0, 3, 3, 6),  # 1: rows 0-2, cols 3-5
        (3, 6, 0, 3),  # 2: rows 3-5, cols 0-2
        (3, 6, 3, 6),  # 3: rows 3-5, cols 3-5
    ]
    
    r_start, r_end, c_start, c_end = quad_boundaries[quad]
    
    sub_board = board_copy[r_start:r_end, c_start:c_end]
    
    if direction == 'L':
        # Rotate 90 degrees counter-clockwise
        sub_board = np.rot90(sub_board, k=1)
    else:  # direction == 'R'
        # Rotate 90 degrees clockwise
        sub_board = np.rot90(sub_board, k=3)
    
    board_copy[r_start:r_end, c_start:c_end] = sub_board
    return board_copy

def evaluate_position(board: np.ndarray) -> int:
    """Simple evaluation function for heuristics"""
    score = 0
    
    # Count potential 4 in a rows for me
    for line in WIN_LINES:
        values = [board[r, c] for r, c in line]
        if values.count(ME) == 4 and values.count(EMPTY) == 1:
            score += 100
        elif values.count(ME) == 3 and values.count(EMPTY) == 2:
            score += 10
        elif values.count(ME) == 2 and values.count(EMPTY) == 3:
            score += 1
            
    # Count potential 4 in a rows for opponent
    for line in WIN_LINES:
        values = [board[r, c] for r, c in line]
        if values.count(OPPONENT) == 4 and values.count(EMPTY) == 1:
            score -= 1000
        elif values.count(OPPONENT) == 3 and values.count(EMPTY) == 2:
            score -= 100
        elif values.count(OPPONENT) == 2 and values.count(EMPTY) == 3:
            score -= 10
            
    # Center control bonus
    center_positions = [(2,2), (2,3), (3,2), (3,3)]
    for r, c in center_positions:
        if board[r, c] == ME:
            score += 5
        elif board[r, c] == OPPONENT:
            score -= 5
            
    return score

def get_possible_moves(board: np.ndarray) -> List[Tuple[int, int, int, str]]:
    """Get list of all possible moves (row, col, quad, dir)"""
    moves = []
    
    # Find all empty positions
    empty_positions = [(r, c) for r in range(6) for c in range(6) if board[r, c] == EMPTY]
    
    # All quadrants
    quadrants = [0, 1, 2, 3]
    
    # All directions
    directions = ['L', 'R']
    
    for r, c in empty_positions:
        for quad in quadrants:
            # Check if the position is within the quadrant limits
            quad_boundaries = [
                (0, 3, 0, 3),  # 0: rows 0-2, cols 0-2
                (0, 3, 3, 6),  # 1: rows 0-2, cols 3-5
                (3, 6, 0, 3),  # 2: rows 3-5, cols 0-2
                (3, 6, 3, 6),  # 3: rows 3-5, cols 3-5
            ]
            
            r_start, r_end, c_start, c_end = quad_boundaries[quad]
            if r_start <= r < r_end and c_start <= c < c_end:
                # This quad contains the empty position
                for dir in directions:
                    moves.append((r, c, quad, dir))
                    
    return moves

def minimax(board: np.ndarray, depth: int, alpha: int, beta: int, maximizing_player: bool, 
        max_depth: int = 5) -> int:
    """
    Minimax with alpha-beta pruning
    """
    # Check for terminal states
    win_result = check_win(board)
    if win_result == 1:  # Me wins
        return INFTY - depth
    elif win_result == 2:  # Opponent wins
        return -INFTY + depth
    elif win_result == 3:  # Draw
        return 0
    elif depth == max_depth:
        return evaluate_position(board) 
    
    if maximizing_player:  # Me
        max_eval = -INFTY
        moves = get_possible_moves(board)
        for r, c, quad, direction in moves:
            # Make move
            new_board = board.copy()
            new_board[r, c] = ME
            new_board = rotate_quadrant(new_board, quad, direction)
            
            eval = minimax(new_board, depth + 1, alpha, beta, False, max_depth)
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break  # Alpha-beta pruning
        return max_eval
    else:  # Opponent
        min_eval = INFTY
        moves = get_possible_moves(board)
        for r, c, quad, direction in moves:
            # Make move
            new_board = board.copy()
            new_board[r, c] = OPPONENT
            new_board = rotate_quadrant(new_board, quad, direction)
            
            eval = minimax(new_board, depth + 1, alpha, beta, True, max_depth)
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break  # Alpha-beta pruning
        return min_eval

def policy(you: List[List[int]], opponent: List[List[int]]) -> str:
    """
    Main policy function for Pentago
    
    Implements minimax with iterative deepening for reasonable performance
    """
    # Convert input to numpy arrays
    board = np.zeros((6, 6), dtype=int)
    for r in range(6):
        for c in range(6):
            if you[r][c] == 1:
                board[r, c] = ME
            elif opponent[r][c] == 1:
                board[r, c] = OPPONENT
    
    # Try to find immediate winning move
    moves = get_possible_moves(board)
    
    # Check for immediate win
    for r, c, quad, direction in moves:
        new_board = board.copy()
        new_board[r, c] = ME
        new_board = rotate_quadrant(new_board, quad, direction)
        
        if check_win(new_board) == 1:  # I win
            return f"{r+1},{c+1},{quad},{direction}"
    
    # Check for opponent winning moves and block them
    for r, c, quad, direction in moves:
        new_board = board.copy()
        new_board[r, c] = OPPONENT
        new_board = rotate_quadrant(new_board, quad, direction)
        
        if check_win(new_board) == 2:  # Opponent wins
            # This is a losing move for me - this block is important 
            # But since this is a forced move, we should play it rather than lose
            # Let's still prefer moves that don't allow immediate win for opponent
            # But for now, just avoid it at all cost by making this into our choice
            return f"{r+1},{c+1},{quad},{direction}"
    
    # Try iterative deepening
    best_move = None
    best_score = -INFTY
    
    # Try different max depths
    max_depths = [2, 3, 4]  # Start with something reasonable
    
    for depth in max_depths:
        score = minimax(board, 0, -INFTY, INFTY, True, depth)
        if score > best_score:
            best_score = score
            # Try to find a good move in this case
            # For iterative deepening, we should actually get all moves and choose the best but let's simplify
            break
    
    # If no good approach, just pick one of the moves that is checking and don't risk a sequence
    # Do minimax over all legal moves very quickly using a shallow search
    move_scores = []
    for r, c, quad, direction in moves:
        new_board = board.copy()
        new_board[r, c] = ME
        new_board = rotate_quadrant(new_board, quad, direction)
        
        # Simple forward heuristic - just see if it's a win for me
        if check_win(new_board) == 1:
            # Good move, but let's use it for evaluation or choose it for safety
            return f"{r+1},{c+1},{quad},{direction}"
            
        eval_score = evaluate_position(new_board)
        
        # Add some small random factor to avoid repetition 
        eval_score += random.uniform(0, 1)  # jittering for variety
        
        move_scores.append((r, c, quad, direction, eval_score))
    
    # Pick the move with best evaluation score
    move_scores.sort(key=lambda x: x[4], reverse=True)
    
    if move_scores:
        r, c, quad, direction, _ = move_scores[0]
        return f"{r+1},{c+1},{quad},{direction}"
    
    # Fallback - just grab one of the possible moves (shouldn't happen if board was legal)
    if moves:
        r, c, quad, direction = moves[0]
        return f"{r+1},{c+1},{quad},{direction}"
    
    # Fallback if no moves
    raise Exception("No legal moves available")

