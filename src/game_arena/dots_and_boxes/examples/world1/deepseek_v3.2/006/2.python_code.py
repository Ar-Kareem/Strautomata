
import numpy as np
from typing import Tuple, List

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    return get_best_move(horizontal, vertical, capture)

def get_best_move(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """Return the best move as a 'row,col,dir' string."""
    board_state = (horizontal, vertical, capture)
    legal_moves = generate_legal_moves(board_state)
    
    # If we can capture immediately, do it (since we get another turn)
    for move in legal_moves:
        new_state = apply_move(board_state, move)
        if new_state[2].sum() > capture.sum():  # We captured at least one box
            return move
    
    # Order moves: safe moves (don't create 3-sided boxes) first
    safe_moves = []
    risky_moves = []
    for move in legal_moves:
        if not creates_three_sided_box(board_state, move):
            safe_moves.append(move)
        else:
            risky_moves.append(move)
    ordered_moves = safe_moves + risky_moves
    
    # If only risky moves remain, pick the one that creates the shortest chain
    if not safe_moves and len(risky_moves) > 1:
        ordered_moves.sort(key=lambda m: chain_length_after_move(board_state, m))
    
    # Use minimax with alpha-beta for deeper search
    best_move = ordered_moves[0]
    best_score = -float('inf')
    
    # Search depth: 3 for normal moves, but we'll do quiescence search for captures
    for move in ordered_moves[:min(10, len(ordered_moves))]:  # Limit to top 10 to save time
        new_state = apply_move(board_state, move)
        # Quiescence search: if we captured, search deeper in capture sequences
        score = alpha_beta(new_state, depth=2, alpha=-1000, beta=1000, 
                          maximizing_player=(new_state[2].sum() == capture.sum()))
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move

def alpha_beta(state: Tuple[np.ndarray, np.ndarray, np.ndarray], 
               depth: int, alpha: float, beta: float, 
               maximizing_player: bool) -> float:
    """Alpha-beta pruning search."""
    if depth == 0:
        return evaluate(state)
    
    horizontal, vertical, capture = state
    legal_moves = generate_legal_moves(state)
    
    # Check for terminal state
    if len(legal_moves) == 0:
        return evaluate(state)
    
    if maximizing_player:
        value = -float('inf')
        for move in legal_moves[:min(8, len(legal_moves))]:  # Limit branching
            new_state = apply_move(state, move)
            # If we captured, we get another turn (still maximizing)
            player_turn_again = (new_state[2].sum() > capture.sum())
            new_depth = depth - 1 if not player_turn_again else depth
            value = max(value, alpha_beta(new_state, new_depth, alpha, beta, player_turn_again))
            alpha = max(alpha, value)
            if value >= beta:
                break
        return value
    else:
        value = float('inf')
        for move in legal_moves[:min(8, len(legal_moves))]:
            new_state = apply_move(state, move)
            # If opponent captured, they get another turn (still minimizing for us)
            opponent_turn_again = (new_state[2].sum() > capture.sum())
            new_depth = depth - 1 if not opponent_turn_again else depth
            value = min(value, alpha_beta(new_state, new_depth, alpha, beta, not opponent_turn_again))
            beta = min(beta, value)
            if value <= alpha:
                break
        return value

def evaluate(state: Tuple[np.ndarray, np.ndarray, np.ndarray]) -> float:
    """Evaluate the board state from our perspective."""
    horizontal, vertical, capture = state
    
    # Base score: difference in captured boxes (we have 1, opponent has -1)
    score = float(capture.sum())
    
    # Bonus for having potential captures (boxes with 3 sides)
    potential_captures = 0
    for r in range(4):
        for c in range(4):
            sides = 0
            # Check top, bottom, left, right edges
            if horizontal[r, c] != 0: sides += 1
            if horizontal[r+1, c] != 0: sides += 1
            if vertical[r, c] != 0: sides += 1
            if vertical[r, c+1] != 0: sides += 1
            
            if sides == 3 and capture[r, c] == 0:
                # Count as potential capture, weight less than actual capture
                potential_captures += 0.2
    
    score += potential_captures
    
    # Penalty for giving opponent potential captures
    # We can approximate by counting boxes where we would complete the 4th side
    # This is complex, so we'll keep it simple for now
    
    return score

def generates_legal_moves(state: Tuple[np.ndarray, np.ndarray, np.ndarray]) -> List[str]:
    """Generate all legal moves."""
    horizontal, vertical, capture = state
    moves = []
    
    # Horizontal edges
    for r in range(5):
        for c in range(4):
            if horizontal[r, c] == 0:
                moves.append(f'{r},{c},H')
    
    # Vertical edges
    for r in range(4):
        for c in range(5):
            if vertical[r, c] == 0:
                moves.append(f'{r},{c},V')
    
    return moves

def apply_move(state: Tuple[np.ndarray, np.ndarray, np.ndarray], 
               move: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Apply a move and return new state (doesn't modify input)."""
    horizontal, vertical, capture = state
    h_copy = horizontal.copy()
    v_copy = vertical.copy()
    c_copy = capture.copy()
    
    r, c, dir = move.split(',')
    r, c = int(r), int(c)
    
    boxes_completed = []
    
    if dir == 'H':
        h_copy[r, c] = 1
        # Check boxes above and below this horizontal edge
        if r > 0:  # Box above
            # Check if all 4 edges of the box are filled
            if (h_copy[r-1, c] != 0 and h_copy[r, c] != 0 and 
                v_copy[r-1, c] != 0 and v_copy[r-1, c+1] != 0):
                if c_copy[r-1, c] == 0:
                    boxes_completed.append((r-1, c))
        
        if r < 4:  # Box below (for r < 4, since there are 4 boxes vertically)
            if r < 4 and c < 4:  # Valid box coordinate
                if (h_copy[r, c] != 0 and h_copy[r+1, c] != 0 and 
                    v_copy[r, c] != 0 and v_copy[r, c+1] != 0):
                    if c_copy[r, c] == 0:
                        boxes_completed.append((r, c))
    else:  # dir == 'V'
        v_copy[r, c] = 1
        # Check boxes left and right of this vertical edge
        if c > 0:  # Box to the left
            if (h_copy[r, c-1] != 0 and h_copy[r+1, c-1] != 0 and 
                v_copy[r, c-1] != 0 and v_copy[r, c] != 0):
                if c_copy[r, c-1] == 0:
                    boxes_completed.append((r, c-1))
        
        if c < 4:  # Box to the right (for c < 4, since there are 4 boxes horizontally)
            if r < 4 and c < 4:  # Valid box coordinate
                if (h_copy[r, c] != 0 and h_copy[r+1, c] != 0 and 
                    v_copy[r, c] != 0 and v_copy[r, c+1] != 0):
                    if c_copy[r, c] == 0:
                        boxes_completed.append((r, c))
    
    # Mark captured boxes
    for box_r, box_c in boxes_completed:
        c_copy[box_r, box_c] = 1
    
    return (h_copy, v_copy, c_copy)

def creates_three_sided_box(state: Tuple[np.ndarray, np.ndarray, np.ndarray], 
                           move: str) -> bool:
    """Check if a move creates a box with exactly 3 sides filled (dangerous)."""
    horizontal, vertical, capture = state
    r, c, dir = move.split(',')
    r, c = int(r), int(c)
    
    if dir == 'H':
        # Check box above
        if r > 0:
            sides = 0
            if horizontal[r-1, c] != 0: sides += 1
            if horizontal[r, c] != 0: sides += 1  # This move
            if vertical[r-1, c] != 0: sides += 1
            if vertical[r-1, c+1] != 0: sides += 1
            if sides == 3 and capture[r-1, c] == 0:
                return True
        
        # Check box below
        if r < 4:
            sides = 0
            if horizontal[r, c] != 0: sides += 1  # This move
            if horizontal[r+1, c] != 0: sides += 1
            if vertical[r, c] != 0: sides += 1
            if vertical[r, c+1] != 0: sides += 1
            if sides == 3 and capture[r, c] == 0:
                return True
    else:  # dir == 'V'
        # Check box to the left
        if c > 0:
            sides = 0
            if horizontal[r, c-1] != 0: sides += 1
            if horizontal[r+1, c-1] != 0: sides += 1
            if vertical[r, c-1] != 0: sides += 1
            if vertical[r, c] != 0: sides += 1  # This move
            if sides == 3 and capture[r, c-1] == 0:
                return True
        
        # Check box to the right
        if c < 4:
            sides = 0
            if horizontal[r, c] != 0: sides += 1
            if horizontal[r+1, c] != 0: sides += 1
            if vertical[r, c] != 0: sides += 1  # This move
            if vertical[r, c+1] != 0: sides += 1
            if sides == 3 and capture[r, c] == 0:
                return True
    
    return False

def chain_length_after_move(state: Tuple[np.ndarray, np.ndarray, np.ndarray], 
                           move: str) -> int:
    """Estimate the chain length created by a risky move (simplified)."""
    # Simple heuristic: count how many adjacent boxes would have 3 sides
    horizontal, vertical, capture = state
    r, c, dir = move.split(',')
    r, c = int(r), int(c)
    
    count = 0
    if dir == 'H':
        if r > 0 and capture[r-1, c] == 0:
            count += 1
        if r < 4 and capture[r, c] == 0:
            count += 1
    else:
        if c > 0 and capture[r, c-1] == 0:
            count += 1
        if c < 4 and capture[r, c] == 0:
            count += 1
    
    return count

# Alias for generate_legal_moves to fix typo
generate_legal_moves = generates_legal_moves
