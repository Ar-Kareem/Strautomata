
import numpy as np
import random
import time

# Constants
ROWS, COLS = 5, 5
BOARD_SIZE = 4  # 4x4 box grid

def get_legal_moves(horizontal, vertical):
    """Get all legal moves as list of (row, col, dir)"""
    moves = []
    for row in range(ROWS):
        for col in range(COLS):
            if horizontal[row, col] == 0:
                moves.append((row, col, 'H'))
            if vertical[row, col] == 0:
                moves.append((row, col, 'V'))
    return moves

def make_move(state, move, player):
    """Apply a move to the state and return new state, boxes captured, and whether bonus turn"""
    horizontal, vertical, capture = state
    row, col, dir = move
    
    new_horizontal = horizontal.copy()
    new_vertical = vertical.copy()
    new_capture = capture.copy()
    
    if dir == 'H':
        new_horizontal[row, col] = player
    else:
        new_vertical[row, col] = player
    
    boxes_captured = 0
    
    # Check if any boxes are completed
    if dir == 'H':
        # Check box above the edge
        if row > 0:
            if (new_horizontal[row-1, col] != 0 and 
                new_vertical[row-1, col] != 0 and 
                new_vertical[row-1, col+1] != 0 and 
                new_horizontal[row, col] != 0):
                if new_capture[row-1, col] == 0:
                    new_capture[row-1, col] = player
                    boxes_captured += 1
        # Check box below the edge
        if row < ROWS - 1:
            if (new_horizontal[row, col] != 0 and 
                new_vertical[row, col] != 0 and 
                new_vertical[row, col+1] != 0 and 
                new_horizontal[row+1, col] != 0):
                if new_capture[row, col] == 0:
                    new_capture[row, col] = player
                    boxes_captured += 1
    else:  # dir == 'V'
        # Check box to the left
        if col > 0:
            if (new_vertical[row, col-1] != 0 and 
                new_horizontal[row, col-1] != 0 and 
                new_horizontal[row+1, col-1] != 0 and 
                new_vertical[row, col] != 0):
                if new_capture[row, col-1] == 0:
                    new_capture[row, col-1] = player
                    boxes_captured += 1
        # Check box to the right
        if col < COLS - 1:
            if (new_vertical[row, col] != 0 and 
                new_horizontal[row, col] != 0 and 
                new_horizontal[row+1, col] != 0 and 
                new_vertical[row, col+1] != 0):
                if new_capture[row, col] == 0:
                    new_capture[row, col] = player
                    boxes_captured += 1
    
    return (new_horizontal, new_vertical, new_capture), boxes_captured

def is_terminal(state):
    """Check if all moves have been made"""
    horizontal, vertical, _ = state
    return np.all(horizontal != 0) and np.all(vertical != 0)

def evaluate(state):
    """Evaluate the state from player 1's perspective"""
    _, _, capture = state
    return np.sum(capture == 1) - np.sum(capture == -1)

def count_boxes_with_three_edges(state, player):
    """Count boxes that have exactly 3 edges drawn, with the missing edge being the one the player could draw"""
    horizontal, vertical, capture = state
    
    count = 0
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            if capture[row, col] != 0:
                continue
            
            # Count edges around this box
            edges = 0
            # Top edge
            if horizontal[row, col] != 0:
                edges += 1
            # Bottom edge
            if horizontal[row+1, col] != 0:
                edges += 1
            # Left edge
            if vertical[row, col] != 0:
                edges += 1
            # Right edge
            if vertical[row, col+1] != 0:
                edges += 1
            
            if edges == 3:
                # Check if the missing edge would give the box to the player
                # If the 3 edges are all from the current player, the box can be completed
                # But we count this as a dangerous situation
                count += 1
    
    return count

def get_completing_moves(state, player):
    """Get moves that complete at least one box"""
    moves = get_legal_moves(state[0], state[1])
    completing = []
    
    for move in moves:
        _, boxes = make_move(state, move, player)
        if boxes > 0:
            completing.append(move)
    
    return completing

def get_safe_moves(state, player):
    """Get moves that don't give away a box to the opponent"""
    moves = get_legal_moves(state[0], state[1])
    safe = []
    
    for move in moves:
        # Check if this move creates a box with 3 edges (dangerous)
        new_state, _ = make_move(state, move, player)
        if count_boxes_with_three_edges(new_state, -player) == 0:
            safe.append(move)
    
    return safe if safe else moves

def minimax(state, depth, alpha, beta, maximizing_player, player, start_time, time_limit):
    """Minimax with alpha-beta pruning"""
    if time.time() - start_time > time_limit:
        return None, 0
    
    if depth == 0 or is_terminal(state):
        return None, evaluate(state)
    
    current_player = player if maximizing_player else -player
    
    if maximizing_player:
        max_eval = float('-inf')
        best_move = None
        
        # Check for completing moves first
        completing = get_completing_moves(state, current_player)
        if completing:
            moves = completing
        else:
            # Get safe moves first
            moves = get_safe_moves(state, current_player)
            if not moves:
                moves = get_legal_moves(state[0], state[1])
        
        for move in moves:
            if time.time() - start_time > time_limit:
                return best_move, max_eval if best_move else 0
            
            new_state, boxes = make_move(state, move, current_player)
            
            if boxes > 0:
                # Bonus turn, same player continues
                _, eval_score = minimax(new_state, depth-1, alpha, beta, True, player, start_time, time_limit)
            else:
                _, eval_score = minimax(new_state, depth-1, alpha, beta, False, player, start_time, time_limit)
            
            if eval_score is None:
                continue
            
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = move
            
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        
        return best_move, max_eval
    else:
        min_eval = float('inf')
        best_move = None
        
        # Check for completing moves first
        completing = get_completing_moves(state, current_player)
        if completing:
            moves = completing
        else:
            moves = get_safe_moves(state, current_player)
            if not moves:
                moves = get_legal_moves(state[0], state[1])
        
        for move in moves:
            if time.time() - start_time > time_limit:
                return best_move, min_eval if best_move else 0
            
            new_state, boxes = make_move(state, move, current_player)
            
            if boxes > 0:
                # Bonus turn, same player continues
                _, eval_score = minimax(new_state, depth-1, alpha, beta, False, player, start_time, time_limit)
            else:
                _, eval_score = minimax(new_state, depth-1, alpha, beta, True, player, start_time, time_limit)
            
            if eval_score is None:
                continue
            
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = move
            
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        
        return best_move, min_eval

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    Policy function that returns the next move for Dots and Boxes.
    """
    state = (horizontal, vertical, capture)
    start_time = time.time()
    time_limit = 0.95  # Leave some margin
    
    # First, check for immediate box completions
    completing = get_completing_moves(state, 1)
    if completing:
        # Take the first completing move (usually best to complete boxes)
        move = completing[0]
        return f"{move[0]},{move[1]},{move[2]}"
    
    # Get all legal moves
    legal_moves = get_legal_moves(horizontal, vertical)
    if not legal_moves:
        return "0,0,H"  # Should not happen in a real game
    
    # If only one move available, just play it
    if len(legal_moves) == 1:
        move = legal_moves[0]
        return f"{move[0]},{move[1]},{move[2]}"
    
    # Try to find safe moves that don't give away boxes
    safe_moves = get_safe_moves(state, 1)
    
    # If we have safe moves, use iterative deepening minimax
    best_move = safe_moves[0] if safe_moves else legal_moves[0]
    
    try:
        # Iterative deepening
        for depth in range(2, 8):
            if time.time() - start_time > time_limit * 0.5:
                break
            
            move, _ = minimax(state, depth, float('-inf'), float('inf'), True, 1, start_time, time_limit)
            if move is not None:
                best_move = move
    except:
        pass
    
    return f"{best_move[0]},{best_move[1]},{best_move[2]}"
