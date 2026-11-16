
import numpy as np
from typing import List, Tuple, Literal

# Type alias for player
Player = Literal[1, -1]

# Constants for game state
BOARD_SIZE = 5  # 5x5 grid of dots
MAX_DEPTH = 3   # Depth for minimax search

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    Main policy function that chooses the next move.
    
    Args:
        horizontal: 5x5 array representing horizontal edges
        vertical: 5x5 array representing vertical edges  
        capture: 5x5 array representing captured boxes
    
    Returns:
        String in format 'row,col,dir' representing the chosen move
    """
    # Get all legal moves
    legal_moves = get_legal_moves(horizontal, vertical)
    
    if not legal_moves:
        # This shouldn't happen in a real game, but handle it gracefully
        return "0,0,H"
    
    # Use minimax to choose the best move
    best_move = None
    best_value = float('-inf')
    
    # Try to maximize score
    for move in legal_moves:
        # Simulate the move
        new_h, new_v, new_capture = simulate_move(horizontal, vertical, capture, move, 1)
        
        # Check if this move captures boxes
        captures = count_new_captures(capture, new_capture)
        
        # If we capture boxes, we get another turn - evaluate from our perspective
        if captures > 0:
            value = captures + evaluate_position(new_h, new_v, new_capture, 1, MAX_DEPTH - 1)
        else:
            # Opponent's turn - evaluate from their perspective (minimize our score)
            value = evaluate_position(new_h, new_v, new_capture, -1, MAX_DEPTH - 1)
        
        if value > best_value:
            best_value = value
            best_move = move
    
    # If no good moves found (unlikely), pick a random legal move
    if best_move is None:
        return legal_moves[0]
    
    return f"{best_move[0]},{best_move[1]},{best_move[2]}"


def get_legal_moves(horizontal: np.ndarray, vertical: np.ndarray) -> List[Tuple[int, int, str]]:
    """Get all legal moves from the current position."""
    moves = []
    
    # Check horizontal edges
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE - 1):
            if horizontal[r, c] == 0:
                moves.append((r, c, 'H'))
    
    # Check vertical edges
    for r in range(BOARD_SIZE - 1):
        for c in range(BOARD_SIZE):
            if vertical[r, c] == 0:
                moves.append((r, c, 'V'))
    
    return moves


def simulate_move(h: np.ndarray, v: np.ndarray, capture: np.ndarray, 
                  move: Tuple[int, int, str], player: Player) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Simulate making a move and return the new game state."""
    # Create copies to avoid modifying original arrays
    new_h = h.copy()
    new_v = v.copy()
    new_capture = capture.copy()
    
    r, c, dir = move
    
    if dir == 'H':
        new_h[r, c] = player
        # Check if this horizontal edge completed any boxes
        if r > 0 and is_box_complete(new_h, new_v, r-1, c):
            new_capture[r-1, c] = player
        if r < BOARD_SIZE-1 and is_box_complete(new_h, new_v, r, c):
            new_capture[r, c] = player
    else:  # dir == 'V'
        new_v[r, c] = player
        # Check if this vertical edge completed any boxes
        if c > 0 and is_box_complete(new_h, new_v, r, c-1):
            new_capture[r, c-1] = player
        if c < BOARD_SIZE-1 and is_box_complete(new_h, new_v, r, c):
            new_capture[r, c] = player
    
    return new_h, new_v, new_capture


def is_box_complete(h: np.ndarray, v: np.ndarray, r: int, c: int) -> bool:
    """Check if a box at position (r,c) is complete."""
    # A box at (r,c) is bounded by:
    # - horizontal edges at (r,c) and (r+1,c)
    # - vertical edges at (r,c) and (r,c+1)
    
    if h[r, c] != 0 and h[r+1, c] != 0 and v[r, c] != 0 and v[r, c+1] != 0:
        return True
    return False


def count_new_captures(old_capture: np.ndarray, new_capture: np.ndarray) -> int:
    """Count how many new boxes were captured."""
    return np.sum(new_capture != old_capture)


def evaluate_position(h: np.ndarray, v: np.ndarray, capture: np.ndarray, 
                     player: Player, depth: int) -> float:
    """Evaluate the position using minimax with alpha-beta pruning."""
    if depth == 0:
        return evaluate_heuristic(h, v, capture, player)
    
    legal_moves = get_legal_moves(h, v)
    
    if not legal_moves:
        # Game is over
        my_score = np.sum(capture == 1)
        opp_score = np.sum(capture == -1)
        return my_score - opp_score
    
    best_value = float('-inf') if player == 1 else float('inf')
    
    for move in legal_moves:
        new_h, new_v, new_capture = simulate_move(h, v, capture, move, player)
        captures = count_new_captures(capture, new_capture)
        
        if captures > 0:
            # We get another turn
            value = evaluate_position(new_h, new_v, new_capture, player, depth)
        else:
            # Opponent's turn
            value = evaluate_position(new_h, new_v, new_capture, -player, depth - 1)
        
        if player == 1:
            best_value = max(best_value, value)
        else:
            best_value = min(best_value, value)
    
    return best_value


def evaluate_heuristic(h: np.ndarray, v: np.ndarray, capture: np.ndarray, player: Player) -> float:
    """
    Heuristic evaluation function.
    
    This evaluates based on:
    1. Current score difference
    2. Number of nearly-complete boxes (2 or 3 edges)
    3. Mobility (number of available moves)
    """
    my_score = np.sum(capture == 1)
    opp_score = np.sum(capture == -1)
    score_diff = my_score - opp_score
    
    # Count nearly-complete boxes that could be captured next
    my_threats = 0
    opp_threats = 0
    
    for r in range(BOARD_SIZE - 1):
        for c in range(BOARD_SIZE - 1):
            if capture[r, c] == 0:  # Unclaimed box
                edges = count_box_edges(h, v, r, c)
                if edges == 3:
                    # This box can be captured on next move
                    if player == 1:
                        my_threats += 1
                    else:
                        opp_threats += 1
                elif edges == 2:
                    # This box is getting close
                    if player == 1:
                        my_threats += 0.5
                    else:
                        opp_threats += 0.5
    
    # Count available moves (mobility)
    my_moves = sum(1 for r in range(BOARD_SIZE) for c in range(BOARD_SIZE-1) if h[r, c] == 0)
    my_moves += sum(1 for r in range(BOARD_SIZE-1) for c in range(BOARD_SIZE) if v[r, c] == 0)
    
    # Combine heuristics
    return score_diff + 0.5 * (my_threats - opp_threats) + 0.1 * my_moves


def count_box_edges(h: np.ndarray, v: np.ndarray, r: int, c: int) -> int:
    """Count how many edges are filled for the box at (r,c)."""
    count = 0
    if h[r, c] != 0: count += 1
    if h[r+1, c] != 0: count += 1
    if v[r, c] != 0: count += 1
    if v[r, c+1] != 0: count += 1
    return count
