
import numpy as np
from typing import Dict, List, Tuple

def policy(state: Dict) -> str:
    """
    Main policy function that determines the next move for a Backgammon game.
    
    Args:
        state: Dictionary containing the current game state with keys:
            - 'my_pts': List of 24 integers representing our checkers on each point
            - 'opp_pts': List of 24 integers representing opponent checkers on each point
            - 'my_bar': Number of our checkers on the bar
            - 'opp_bar': Number of opponent checkers on the bar
            - 'my_off': Number of our checkers borne off
            - 'opp_off': Number of opponent checkers borne off
            - 'dice': List of 0, 1, or 2 integers representing the current roll
    
    Returns:
        A move string in the format "<ORDER>:<FROM1>,<FROM2>" where:
        - <ORDER> is 'H' or 'L' (higher or lower die first)
        - <FROM1> and <FROM2> are the starting positions for the moves
    """
    
    # Extract state information
    my_pts = np.array(state['my_pts'])
    opp_pts = np.array(state['opp_pts'])
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = state['dice']
    
    # Handle edge cases
    if not dice:
        return "H:P,P"
    
    if len(dice) == 1:
        dice = [dice[0], dice[0]]
    
    # Sort dice in descending order
    dice = sorted(dice, reverse=True)
    high_die, low_die = dice[0], dice[1]
    
    # Check if we can bear off
    can_bear_off = check_bear_off_possible(my_pts, my_off)
    
    # Get all legal moves
    legal_moves = get_legal_moves(my_pts, opp_pts, my_bar, high_die, low_die, can_bear_off)
    
    if not legal_moves:
        return f"H:P,P"
    
    # Evaluate moves and select the best one
    best_score = float('-inf')
    best_move = legal_moves[0]
    
    for move in legal_moves:
        score = evaluate_move(move, my_pts, opp_pts, my_bar, my_off, opp_off, can_bear_off)
        if score > best_score:
            best_score = score
            best_move = move
    
    # Format the move string
    return format_move_string(best_move, high_die, low_die)

def check_bear_off_possible(my_pts: np.ndarray, my_off: int) -> bool:
    """Check if we can bear off checkers."""
    # Can bear off if all checkers are in home board (points 0-5)
    return np.sum(my_pts[6:]) == 0

def get_legal_moves(my_pts: np.ndarray, opp_pts: np.ndarray, my_bar: int, 
                   high_die: int, low_die: int, can_bear_off: bool) -> List[Tuple[str, str]]:
    """Get all legal moves for the current state."""
    moves = []
    
    # If we have checkers on the bar, we must re-enter them first
    if my_bar > 0:
        # Try to re-enter with high die
        if opp_pts[high_die - 1] < 2:
            moves.append(("B", get_reenter_destination(high_die)))
        
        # Try to re-enter with low die
        if low_die != high_die and opp_pts[low_die - 1] < 2:
            moves.append(("B", get_reenter_destination(low_die)))
    
    # If no checkers on bar or we can make additional moves
    else:
        # Generate all possible moves
        for i in range(24):
            if my_pts[i] > 0:
                # Try moving with high die
                dest = i - high_die
                if dest >= 0 and opp_pts[dest] < 2:
                    moves.append((f"A{i}", get_move_destination(i, high_die)))
                
                # Try moving with low die
                dest = i - low_die
                if dest >= 0 and opp_pts[dest] < 2:
                    moves.append((f"A{i}", get_move_destination(i, low_die)))
        
        # Add bear off moves if possible
        if can_bear_off:
            for i in range(6):
                if my_pts[i] > 0:
                    # Can bear off from this point
                    moves.append((f"A{i}", "OFF"))
    
    return moves

def get_reenter_destination(die: int) -> str:
    """Get the destination point when re-entering from the bar."""
    return f"A{die - 1}"

def get_move_destination(start: int, die: int) -> str:
    """Get the destination point when moving from a given point."""
    return f"A{start - die}"

def evaluate_move(move: Tuple[str, str], my_pts: np.ndarray, opp_pts: np.ndarray,
                 my_bar: int, my_off: int, opp_off: int, can_bear_off: bool) -> float:
    """Evaluate a move and return a score."""
    score = 0.0
    
    # Extract move information
    from1, from2 = move
    
    # Prefer moves that bear off checkers
    if from1.endswith("OFF") or from2.endswith("OFF"):
        score += 10.0
    
    # Prefer moves that don't leave blots (single checkers)
    if from1.startswith("A"):
        point_idx = int(from1[1:])
        if my_pts[point_idx] == 1:
            # This move would leave a blot
            score -= 5.0
    
    # Prefer moves that build points (stacks of 2 or more)
    if from1.startswith("A") and from2.startswith("A"):
        dest1 = int(from1[1:]) - (6 if from2.endswith("OFF") else int(from2[1:]))
        if dest1 >= 0 and my_pts[dest1] == 1:
            # This move would create a point
            score += 3.0
    
    # Prefer moves that move checkers forward (closer to bearing off)
    if from1.startswith("A") and from2.startswith("A"):
        point1, point2 = int(from1[1:]), int(from2[1:])
        if point1 > point2:
            score += 1.0
    
    # Avoid moves that hit opponent checkers unless necessary
    # (This is a simplified check - the actual engine handles hit detection)
    
    return score

def format_move_string(move: Tuple[str, str], high_die: int, low_die: int) -> str:
    """Format a move tuple into the required string format."""
    from1, from2 = move
    
    # Determine if we should use H or L ordering
    # For simplicity, we'll use H (higher die first) as default
    # In a more sophisticated implementation, we might analyze which ordering is better
    
    return f"H:{from1},{from2}"
