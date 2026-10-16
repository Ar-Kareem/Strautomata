
import numpy as np
from itertools import permutations

def policy(state):
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = sorted(state['dice'])
    
    # Ensure dice are ordered high to low for consistent processing
    high_die = dice[1] if len(dice) > 1 else dice[0]
    low_die = dice[0] if len(dice) > 1 else dice[0]
    
    # Check if we have checkers on the bar
    if my_bar > 0:
        return make_bar_move(my_pts, opp_pts, my_bar, high_die, low_die, dice)
    
    # Generate all possible moves
    moves = generate_all_moves(my_pts, opp_pts, high_die, low_die, dice)
    
    if not moves:
        return "H:P,P"
    
    # Score and select the best move
    best_move = max(moves, key=score_move)
    return best_move

def make_bar_move(my_pts, opp_pts, my_bar, high_die, low_die, dice):
    # Try to re-enter from bar with highest die if possible
    if my_pts[24 - high_die] == 0 or my_pts[24 - high_die] == 1:
        # Try to move from bar with high die first
        if dice[0] == high_die:
            return f"H:B,A{24 - high_die}"
        else:
            return f"L:B,A{24 - high_die}"
    else:
        # Try to use the low die if high die would hit a block
        if my_pts[24 - low_die] == 0 or my_pts[24 - low_die] == 1:
            if dice[0] == low_die:
                return f"H:B,A{24 - low_die}"
            else:
                return f"L:B,A{24 - low_die}"
    
    # If no good re-entry, pass
    return "H:P,P"

def generate_all_moves(my_pts, opp_pts, high_die, low_die, dice):
    moves = []
    
    # Get all points with our checkers
    my_points = [i for i in range(24) if my_pts[i] > 0]
    
    # If only one die, check if we can play it
    if len(dice) == 1:
        for point in my_points:
            if can_move(point, high_die, my_pts, opp_pts):
                moves.append(f"H:A{point},P")
        return moves
    
    # Two dice case - consider all possible orders and combinations
    # All possible combinations of points to move
    for point1 in my_points:
        if can_move(point1, high_die, my_pts, opp_pts):
            moves.append(f"H:A{point1},P")
            for point2 in my_points:
                if point2 != point1 and can_move(point2, low_die, my_pts, opp_pts):  
                    moves.append(f"L:A{point1},A{point2}")
                    moves.append(f"H:A{point1},A{point2}")
                
    # For two dice, check if we can use both dice
    if len(my_points) >= 2:
        # Try all combinations of two different points
        for point1 in my_points:
            if can_move(point1, high_die, my_pts, opp_pts):
                for point2 in my_points:
                    if point2 != point1 and can_move(point2, low_die, my_pts, opp_pts):
                        moves.append(f"L:A{point2},A{point1}")
                        # Note: Fails to consider the "first die, then second die" configurations properly
                        # So let's do a cleaner approach
    
    # Simpler approach: deterministic moves
    if len(dice) == 2:
        # Generate all possible move tuples that are valid  
        for point1 in my_points:
            if can_move(point1, high_die, my_pts, opp_pts):
                # Try high die first
                moves.append(f"H:A{point1},P")
                for point2 in my_points:
                    if point2 != point1 and can_move(point2, low_die, my_pts, opp_pts):  
                        moves.append(f"H:A{point1},A{point2}")
                        moves.append(f"L:A{point1},A{point2}")
                        # Note: This is a trival way to handle 2 moves
    
    # Just check if we can make a significant move with highest die
    # Return the first valid move we find
    for point1 in my_points:
        if can_move(point1, high_die, my_pts, opp_pts):
            return [f"H:A{point1},P"]
    
    # If cannot play high die, try low die 
    for point1 in my_points:
        if can_move(point1, low_die, my_pts, opp_pts):
            return [f"L:A{point1},P"]
            
    # If we can't play any dice, try very simple moves
    if len(dice) == 1:
        return ["H:P,P"]
    else:
        # Two dice case - try reasonable combinations
        return ["H:P,P"]

def can_move(point, die, my_pts, opp_pts):
    # Can we safely move from the point with die?
    target = (24 - (24 - point) - die) if (24 - point) >= die else 25
    if target == 25:  # If moving beyond board (bearing off)
        # We can only bear off if all pieces are in home board
        # pieces in home board = points 0-5 (index 0-5)
        return True 
    if target < 0 or target > 23:
        return False 
    # Check if target point has 2 or more opponent pieces
    if opp_pts[target] >= 2:
        return False
    # We can move if target is either empty or has exactly one opponent piece
    return True

def score_move(move_str):
    # A simple heuristic score: 
    # Higher score = better move
    # Specific scoring logic:
    score = 0
    
    # Assess the move correctness (potential for more advanced heuristic)
    if move_str == "H:P,P":
        return -100  # Worst move
    
    # Score based on moving checkers toward home, creating blocks, etc.
    # Simple version: if first move moves a checker in outer board to a safe position
    # This is a placeholder for a more sophisticated scoring system
    if len(move_str) > 3:
        # We made at least one move
        parts = move_str.split(":")[1].split(",")
        if parts[0] != "P":
            score += 10
        if len(parts) > 1 and parts[1] != "P":
            score += 5
    
    return score

# Simplified working approach
def policy(state):
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = sorted(state['dice'], reverse=True)  # High die first
    
    # If we have pieces on the bar, we must re-enter first
    if my_bar > 0:
        # Try to re-enter the piece closest to the required point
        for i in range(1, 7):  # Check points 1-6 (24-18 to 24-12)
            if my_pts[24 - i] == 0 or my_pts[24 - i] == 1:  # If point empty or 1 checker
                return f"H:B,A{24 - i}"
        # If no good enter point, try to move a checker from an accessible difficult point
        return "H:P,P"
    
    # Check if we can move both dice
    moves = []
    my_points = [i for i in range(24) if my_pts[i] > 0]
    
    if len(dice) < 2:
        # Just one die
        dice = dice + [0]
    
    # Try to find a valid series of moves        
    # Determine which dice can be used
    if len(dice) >= 2:
        # First check if both dice can be played in order
        for point1 in my_points:
            if (24 - point1) - dice[0] >= 0 and can_move_simple(point1, dice[0], my_pts, opp_pts):
                moves.append(f"H:A{point1},P")
                # If can play both dice:
                for point2 in my_points:
                    if point2 != point1 and (24 - point2) - dice[1] >= 0 and can_move_simple(point2, dice[1], my_pts, opp_pts):
                        return f"H:A{point1},A{point2}"
    
        # Try to play the first die (higher)
        for point1 in my_points:
            if can_move_simple(point1, dice[0], my_pts, opp_pts):
                return f"H:A{point1},P"
            
        # Try to play the second die (lower) 
        for point1 in my_points:
            if can_move_simple(point1, dice[1], my_pts, opp_pts):
                return f"L:A{point1},P"
    else:
        # Single die
        for point1 in my_points:
            if can_move_simple(point1, dice[0], my_pts, opp_pts):
                return f"H:A{point1},P"
    
    return "H:P,P"

def can_move_simple(point, die, my_pts, opp_pts):
    if point == 24:  # Use 0 for working point calculation
        target = 24 - die
    else:
        target = (24 - (24 - point)) - die
    target = 24 - die if point == 24 else (24 - (24 - point) - die)  
    # To make this more structured:
    if die == 0:
        return True if target >= 0 else False
    else:
        adjusted_target = 24 - die  # Simplified: we use point directly for simpler code
        if target >= 0 and target < 24:
            if opp_pts[target] <= 1:  # Not blocked by opponent with 2 or more
                return True
    
    # Actually, simpler approach for single move:
    # 24 is the home board end, targets 0-23 normally
    # If we're at point idx, and move by dice value, we go to (idx - dice)
    # But we should use current position calculation properly
    
    if target < 0:
        return False  # Can't go negative
    # Create the target point properly
    target_point = (24 - (24 - point)) - die 
    target_point = 24 - die  # Simplified placeholder logic
    
    # Actual clearer approach:
    if point - die < 0:
        return False
    if opp_pts[point - die] >= 2:
        return False
    return True

# A much cleaner approach built on actual game logic:

def policy(state):
    my_pts = state['my_pts']
    opp_pts = state['opp_pts'] 
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = sorted(state['dice'], reverse=True) 
    
    if my_bar > 0:
        # Must re-enter from bar - find a good entry point
        for point_idx in range(1, 7):  # Bar re-entry spots 1-6
            if my_pts[24 - point_idx] <= 1:  # Empty or one checker
                return f"H:B,A{24 - point_idx}"
        return "H:P,P"
    
    # Get all points we can move from
    my_points = [i for i in range(24) if my_pts[i] > 0]
    
    # Try various combinations of moves
    # For a basic implementation, just try to use higher die first
    if len(dice) == 2: 
        high_die = dice[0]
        low_die = dice[1]
        
        # Try first move with higher die
        for point1 in my_points:
            if point1 - high_die >= 0 and opp_pts[point1 - high_die] <= 1:
                # We can make this move
                for point2 in my_points:
                    if point2 != point1 and point2 - low_die >= 0 and opp_pts[point2 - low_die] <= 1:
                        return f"H:A{point1},A{point2}"
                # Return just first move if no second possible
                return f"H:A{point1},P"
                
        # If above failed, try with lower first
        for point1 in my_points:
            if point1 - low_die >= 0 and opp_pts[point1 - low_die] <= 1:
                return f"L:A{point1},P"
                
    elif len(dice) == 1:
        for point1 in my_points:
            if point1 - dice[0] >= 0 and opp_pts[point1 - dice[0]] <= 1:
                return f"H:A{point1},P"
    
    # Default pass if no valid move
    return "H:P,P"
