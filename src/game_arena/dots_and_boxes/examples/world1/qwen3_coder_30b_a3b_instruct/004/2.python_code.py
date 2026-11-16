
import numpy as np
import copy
from typing import List, Tuple, Optional

# Constants
BOARD_SIZE = 4
GRID_SIZE = 5  # 5x5 grid of dots

def get_possible_moves(horizontal: np.ndarray, vertical: np.ndarray) -> List[str]:
    """Get all legal moves from current state."""
    moves = []
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            # Check horizontal edges
            if row < GRID_SIZE - 1 and horizontal[row, col] == 0:
                moves.append(f"{row},{col},H")
            # Check vertical edges
            if col < GRID_SIZE - 1 and vertical[row, col] == 0:
                moves.append(f"{row},{col},V")
    return moves

def make_move(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray, move_str: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray, bool]:
    """Apply a move and return the new state and whether a box was captured."""
    row, col, direction = move_str.split(',')
    row, col = int(row), int(col)
    
    # Create copies of the arrays
    new_horizontal = np.copy(horizontal)
    new_vertical = np.copy(vertical)
    new_capture = np.copy(capture)
    
    # Make the move
    if direction == 'H':
        new_horizontal[row, col] = 1  # Player 1 (us)
        # Check if any box is completed
        captured = False
        # Check boxes above the edge
        if row > 0:
            if (new_horizontal[row-1, col] != 0 and 
                new_vertical[row-1, col] != 0 and 
                new_vertical[row-1, col+1] != 0 and 
                new_horizontal[row, col] != 0):
                new_capture[row-1, col] = 1
                captured = True
        # Check boxes below the edge
        if row < GRID_SIZE - 1:
            if (new_horizontal[row, col] != 0 and 
                new_vertical[row, col] != 0 and 
                new_vertical[row, col+1] != 0 and 
                new_horizontal[row+1, col] != 0):
                new_capture[row, col] = 1
                captured = True
    else:  # direction == 'V'
        new_vertical[row, col] = 1  # Player 1 (us)
        # Check if any box is completed
        captured = False
        # Check boxes to the left of the edge
        if col > 0:
            if (new_horizontal[row, col-1] != 0 and 
                new_vertical[row, col-1] != 0 and 
                new_vertical[row+1, col-1] != 0 and 
                new_horizontal[row, col] != 0):
                new_capture[row, col-1] = 1
                captured = True
        # Check boxes to the right of the edge
        if col < GRID_SIZE - 1:
            if (new_horizontal[row, col] != 0 and 
                new_vertical[row, col] != 0 and 
                new_vertical[row+1, col] != 0 and 
                new_horizontal[row, col+1] != 0):
                new_capture[row, col] = 1
                captured = True
    
    return new_horizontal, new_vertical, new_capture, captured

def has_three_sides_open(row: int, col: int, horizontal: np.ndarray, vertical: np.ndarray) -> bool:
    """Check if a box has three sides already filled."""
    top = (row > 0) and (horizontal[row-1, col] != 0)
    bottom = (row < GRID_SIZE - 1) and (horizontal[row, col] != 0)
    left = (col > 0) and (vertical[row, col-1] != 0)
    right = (col < GRID_SIZE - 1) and (vertical[row, col] != 0)
    # If three sides are open, then it's a potential trap for opponent
    sides_filled = sum([top, bottom, left, right])
    return sides_filled >= 3

def heuristic_evaluation(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> int:
    """Evaluate the game state using a heuristic."""
    # Count our boxes minus opponent's boxes
    our_boxes = np.sum(capture == 1)
    opponent_boxes = np.sum(capture == -1)
    box_advantage = our_boxes - opponent_boxes
    
    # Count edges that would complete a box (good move incentive)
    immediate_capture_score = 0
    # Check if we have any possible immediate captures
    for row in range(GRID_SIZE - 1):
        for col in range(GRID_SIZE - 1):
            # Check if all four sides of this box are set except one, but only for our capture
            top = horizontal[row, col] != 0
            bottom = horizontal[row+1, col] != 0
            left = vertical[row, col] != 0
            right = vertical[row, col+1] != 0
            
            sides = [top, bottom, left, right]
            count_filled = sum(sides)
            if count_filled == 3:
                immediate_capture_score += 1
                
    # Avoid edges that would create boxes with three sides
    avoid_score = 0
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            if row < GRID_SIZE - 1 and horizontal[row, col] == 0:
                # See if this would create a future trap
                # We cannot evaluate this properly here in general, but we avoid 
                # creating opportunities where opponent can have 3 sides with one 
                # choice left to score
                pass
            if col < GRID_SIZE - 1 and vertical[row, col] == 0:
                # Same logic for vertical edge
                pass
    
    # Bonus for central edge positions (more strategic)
    central_bonus = 0
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            if row >= 2 and row <= 2 and col >= 2 and col <= 2:
                # More center positions
                central_bonus += 0.1

    total_score = box_advantage + immediate_capture_score + central_bonus
    
    return total_score

def minimax(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray, depth: int, alpha: float, beta: float, maximizing_player: bool) -> float:
    """Minimax with alpha-beta pruning."""
    # Base case: reached maximum depth or game over
    moves = get_possible_moves(horizontal, vertical)
    if depth == 0 or not moves:
        return heuristic_evaluation(horizontal, vertical, capture)

    if maximizing_player:
        max_eval = float('-inf')
        for move in moves:
            new_horizontal, new_vertical, new_capture, captured = make_move(horizontal, vertical, capture, move)
            # If we captured a box, we get another turn (doesn't change the turn state for next minimax call)
            if not captured:
                # Opponent's turn
                eval_score = minimax(new_horizontal, new_vertical, new_capture, depth - 1, alpha, beta, False)
            else:
                # Due to the nature of game rules, after a capture, we need to see if there are 
                # new moves from our side first, so call with the same player state  
                eval_score = minimax(new_horizontal, new_vertical, new_capture, depth - 1, alpha, beta, True)
            
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for move in moves:
            new_horizontal, new_vertical, new_capture, captured = make_move(horizontal, vertical, capture, move)
            if not captured:
                # Opponent's turn
                eval_score = minimax(new_horizontal, new_vertical, new_capture, depth - 1, alpha, beta, True)
            else:
                eval_score = minimax(new_horizontal, new_vertical, new_capture, depth - 1, alpha, beta, False)
                
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval

def get_best_move(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray, depth: int = 3) -> str:
    """Get the best move by running minimax."""
    possible_moves = get_possible_moves(horizontal, vertical)
    
    if not possible_moves:
        return "0,0,H"  # Default move, should not happen

    best_move = possible_moves[0]
    best_value = float('-inf')
    
    # Score each move
    for move in possible_moves:
        # Make the move and see what happens
        new_horizontal, new_vertical, new_capture, captured = make_move(horizontal, vertical, capture, move)
        
        # Analyze how good this move is
        # If it's an immediate capture, it's highly probable it's good
        if captured:
            # You're prioritizing immediate capture since you're getting another turn
            score = float('inf')  # high value
        else:
            # Player 2's turn now - evaluate using minimax
            score = -minimax(new_horizontal, new_vertical, new_capture, depth, float('-inf'), float('inf'), False)
            
        # Prefer moves that don't put you at a disadvantage
        if score > best_value:
            best_value = score
            best_move = move
    
    return best_move

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """Main policy function that returns a move."""
    return get_best_move(horizontal, vertical, capture, depth=3)
