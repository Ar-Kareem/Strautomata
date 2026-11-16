
import numpy as np
from collections import defaultdict

def policy(state):
    # Extract state information
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = sorted(state['dice'], reverse=True)  # Sort highest first
    die1, die2 = dice[0], dice[1] if len(dice) > 1 else 0
    
    # Helper function to check if a move is valid
    def is_valid_move(from_point, die):
        if from_point == 'B':  # From bar
            target = 24 - die
            if target >= 0 and target <= 23 and opp_pts[target] <= 1:
                return target
        elif from_point == 'P':
            return None
        else:  # From point
            target = 23 - from_point + die
            if target >= 0 and target <= 23 and opp_pts[target] <= 1:
                return target
        return None
    
    # Get all legal moves for a given die from a point
    def get_legal_moves(from_point, die):
        moves = []
        if from_point == 'B':
            target = 24 - die
            if 0 <= target <= 23 and opp_pts[target] <= 1:
                moves.append((target, die))
        elif from_point == 'P':
            moves.append((None, die))
        else:  # from_point is index
            target = 23 - from_point + die
            if 0 <= target <= 23 and opp_pts[target] <= 1:
                moves.append((target, die))
        return moves
    
    # Check if we have checkers on the bar (must move them first)
    if my_bar > 0:
        # Try to move checkers from bar
        bar_moves = []
        if die1 > 0:
            target1 = 24 - die1
            if 0 <= target1 <= 23 and opp_pts[target1] <= 1:
                bar_moves.append(('B', target1, die1))
        if die2 > 0:
            target2 = 24 - die2
            if 0 <= target2 <= 23 and opp_pts[target2] <= 1:
                bar_moves.append(('B', target2, die2))
        
        if bar_moves:
            # Move checker from bar using higher die
            return f"H:B,{bar_moves[0][1]}" if len(bar_moves) == 1 else f"H:B,{bar_moves[0][1]}"
        else:
            # No valid bar move, pass
            return "H:P,P"
    
    # Generate all possible moves for both dice
    all_moves = []
    
    # Evaluate all possible moves
    def evaluate_move(start, die):
        if start == 'P':
            return 0
        if start == 'B':
            target = 24 - die
        else:
            target = 23 - start + die
        if target < 0 or target > 23:
            return -1000  # Invalid move
        # Evaluate based on distance from home board and safety
        safety_score = 2 if opp_pts[target] > 1 else 1  # Avoid points with many opponent checkers
        if 0 <= target <= 5:
            home_score = 100 - target  # Prefer getting closer to home
        elif 6 <= target <= 17:
            mid_score = 1000 + (17 - target)  # Mid game is valuable
        else:
            mid_score = 500 + (23 - target)  # Not too far from goal
        return safety_score + max(home_score, mid_score)
    
    # Check if bearing off is allowed (all my checkers in home board)
    def can_bear_off():
        # Check if all my checkers are in my home board (points 0-5)
        home_checkers = 0
        for i in range(6):
            home_checkers += my_pts[i]
        # Check for any checker that could bear off
        for i in range(6):
            if my_pts[i] > 0:
                target = 23 - i + die1
                if target > 23:  # Can bear off
                    return True
        return False
    
    # Get all legal moves from the board
    moves = []
    
    # Calculate if bearing off is possible
    bearing_off = True
    all_in_home = True
    for i in range(24):
        if my_pts[i] > 0 and i > 5:
            all_in_home = False
            break
    
    # Create moves from all possible starting points
    legal_moves = []
    
    # Create potential move list
    for point in range(24):
        if my_pts[point] > 0:
            # Try using the first die
            target1 = 23 - point + die1
            if 0 <= target1 <= 23 and opp_pts[target1] <= 1:
                legal_moves.append((point, target1, die1, 'H'))
            # Try using the second die
            if die2 > 0:
                target2 = 23 - point + die2
                if 0 <= target2 <= 23 and opp_pts[target2] <= 1:
                    legal_moves.append((point, target2, die2, 'L'))
    
    # Allow for using both dice in one turn
    if die1 == die2 and len(dice) > 1:
        # Double, so we can make 4 moves with 1 die
        double_moves = []
        for point in range(24):
            if my_pts[point] > 0:
                for i in range(4):
                    target = 23 - point + die1 * (i+1)
                    if target > 23:
                        break  # Can bear off
                    if 0 <= target <= 23 and opp_pts[target] <= 1:
                        double_moves.append((point, target, die1, 'H'))
                    else:
                        break  # Cannot continue going this way
        # If we have 2 duplicates, then fairly safe to try
        # For simplicity, just using two moves with different dice
        if len(legal_moves) >= 2:  # At least 2 legal moves
            # Two moves with different dice
            best_move = (legal_moves[0][0], legal_moves[1][0], 'H') if len(legal_moves) >= 2 else (legal_moves[0][0], 'P', 'H')
            if best_move[1] == 'P':
                return f"H:{best_move[0]},P"
            return f"H:{best_move[0]},{best_move[1]}"
    
    # Prioritize bearing off when reasonable, otherwise use strategic moves
    if all_in_home and die1 > 0 and die2 > 0:
        for point in range(6):
            if my_pts[point] > 0:
                target1 = 23 - point + die1
                target2 = 23 - point + die2
                if target1 > 23 and target2 > 23:  # Can both bear off
                    if point == 0 and die1 == 1 and die2 == 1 and my_pts[0] >= 2:
                        # Multi step - avoid being too conservative 
                        pass
                    else:
                        return f"H:A{point},A{point}"
                elif target1 > 23 or target2 > 23:  # One can bear off
                    better_point = point
                    if target1 > 23:
                        return f"H:A{point},P"
                    elif target2 > 23:
                        return f"L:A{point},P"
    
    # Basic heuristics when no good bearing-off cases
    best_move_score = -999999
    best_move = None
    
    # First, try standard dual move setup if we have 2 legal moves
    if len(legal_moves) >= 2:
        # Pick two moves that are most beneficial
        # Just use the highest scoring ones for now
        score1 = evaluate_move(legal_moves[0][0], legal_moves[0][2])
        score2 = evaluate_move(legal_moves[1][0], legal_moves[1][2])
        if score1 + score2 > best_move_score:
            best_move_score = score1 + score2
            direction1 = legal_moves[0][3]
            if direction1 == 'H':
                best_move = f"H:A{legal_moves[0][0]},A{legal_moves[1][0]}"
            else:
                best_move = f"L:A{legal_moves[0][0]},A{legal_moves[1][0]}"
    
    # If no good hierarchical moves, fall back to best single move or pass
    if best_move is None and len(legal_moves) > 0:
        best_m = legal_moves[0]
        if die1 == die2:
            return f"H:A{best_m[0]},A{best_m[0]}" # Double move
        else:
            return f"H:A{best_m[0]},P" # Single move
    
    # If no moves at all, must pass
    if best_move is None:
        return "H:P,P"
    
    return best_move
