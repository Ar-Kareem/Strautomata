
import random
from typing import List, Dict, Tuple

def policy(state: Dict) -> str:
    """Return a legal move string for the given Backgammon state."""
    # Get all legal moves and choose the best according to evaluation function
    legal_moves = generate_legal_moves(state)
    
    if not legal_moves:
        return "H:P,P"
    
    # Evaluate each move and choose the best
    best_move = None
    best_score = float('-inf')
    
    for move in legal_moves:
        score = evaluate_move(state, move)
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move

def generate_legal_moves(state: Dict) -> List[str]:
    """Generate all legal moves for the current state."""
    # This is a simplified move generator that focuses on key cases
    # In practice, you'd want a more comprehensive generator
    
    moves = []
    dice = sorted(state['dice'])
    
    # If no dice or empty list
    if not dice:
        return ["H:P,P"]
    
    # If we have checkers on bar
    if state['my_bar'] > 0:
        return generate_bar_moves(state, dice)
    
    # Generate moves for normal positions
    return generate_normal_moves(state, dice)

def generate_bar_moves(state: Dict, dice: List[int]) -> List[str]:
    """Generate moves when we have checkers on the bar."""
    moves = []
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    
    # Try each die for re-entry
    for die in dice:
        # Calculate target point for re-entry
        target = die - 1  # Assuming point 0-5 for re-entry from bar
        
        # Check if re-entry is legal (point not blocked by 2+ opponent checkers)
        if opp_pts[target] < 2:
            # We can re-enter with this die
            # Try to use the other die if available
            if len(dice) == 2:
                other_die = dice[1] if dice[0] == die else dice[0]
                # Try to move another checker with the other die
                for from_pt in range(24):
                    if my_pts[from_pt] > 0:
                        target2 = from_pt - other_die
                        if 0 <= target2 < 24 and opp_pts[target2] < 2:
                            # Both moves legal
                            order = 'H' if die >= other_die else 'L'
                            moves.append(f"{order}:B,A{from_pt}")
    
    # If no double moves found, try single re-entry
    for die in dice:
        target = die - 1
        if opp_pts[target] < 2:
            # Create move with just bar move
            moves.append(f"H:B,P")
            break
    
    return moves if moves else ["H:P,P"]

def generate_normal_moves(state: Dict, dice: List[int]) -> List[str]:
    """Generate moves for normal positions (no bar)."""
    moves = []
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    
    # For single die
    if len(dice) == 1:
        die = dice[0]
        for from_pt in range(24):
            if my_pts[from_pt] > 0:
                target = from_pt - die
                if target >= 0 and opp_pts[target] < 2:
                    moves.append(f"H:A{from_pt},P")
        return moves if moves else ["H:P,P"]
    
    # For two dice
    die1, die2 = dice
    
    # Try all possible combinations
    for from1 in range(24):
        if my_pts[from1] > 0:
            target1 = from1 - die1
            if target1 >= 0 and opp_pts[target1] < 2:
                # Try second move from new position or different point
                for from2 in range(24):
                    if my_pts[from2] > 0:
                        target2 = from2 - die2
                        if target2 >= 0 and opp_pts[target2] < 2:
                            # Check if positions are valid
                            moves.append(f"H:A{from1},A{from2}")
                
                # Try second move from target1 position
                if my_pts[target1] > 0:
                    target2_2 = target1 - die2
                    if target2_2 >= 0 and opp_pts[target2_2] < 2:
                        moves.append(f"H:A{from1},A{target1}")
    
    # Try with L order as well
    for from1 in range(24):
        if my_pts[from1] > 0:
            target1 = from1 - die2
            if target1 >= 0 and opp_pts[target1] < 2:
                for from2 in range(24):
                    if my_pts[from2] > 0:
                        target2 = from2 - die1
                        if target2 >= 0 and opp_pts[target2] < 2:
                            moves.append(f"L:A{from1},A{from2}")
    
    return moves if moves else ["H:P,P"]

def evaluate_move(state: Dict, move: str) -> float:
    """Evaluate a move and return a score."""
    # Parse the move
    if move == "H:P,P":
        return -1000  # Passing is worst option
    
    parts = move.split(':')
    order = parts[0]
    from_moves = parts[1].split(',')
    
    # Simulate the move to evaluate resulting position
    score = 0
    
    # Base score for making any move
    score += 10
    
    # Parse source positions
    from_positions = []
    for fm in from_moves:
        if fm.startswith('A'):
            from_positions.append(int(fm[1:]))
        elif fm == 'B':
            from_positions.append(-1)  # Bar
        else:
            from_positions.append(-2)  # Pass
    
    # Get dice
    dice = sorted(state['dice'])
    
    # Evaluate each move component
    for i, from_pos in enumerate(from_positions):
        if from_pos == -2:  # Pass
            continue
        
        die = dice[1] if (i == 0 and order == 'H') or (i == 1 and order == 'L') else dice[0]
        
        if from_pos == -1:  # Bar move
            # Re-entering from bar is good
            score += 50
            target = die - 1
            # Hitting opponent is good if safe
            if state['opp_pts'][target] == 1:
                score += 30
        else:  # Normal move
            target = from_pos - die
            
            # Check if we're hitting opponent
            if target >= 0 and state['opp_pts'][target] == 1:
                score += 30
            
            # Check if we're leaving a blot
            if state['my_pts'][from_pos] == 1:
                score -= 20
            
            # Check if we're building a point (making 2+)
            if target >= 0 and state['my_pts'][target] == 1:
                score += 15
            
            # Bonus for moving into home board (last 6 points)
            if 0 <= target <= 5:
                score += 5
            
            # Bonus for bearing off
            if target < 0:
                score += 100
    
    # Strategic considerations
    # Count blots after move (simplified)
    blots = count_blots_after_move(state, move)
    score -= 50 * blots
    
    # Bonus for having points with 2+ checkers in home board
    home_points = 0
    for i in range(6):
        if state['my_pts'][i] >= 2:
            home_points += 1
    score += 10 * home_points
    
    # Penalty for having checkers far from home
    total_distance = 0
    for i in range(24):
        if state['my_pts'][i] > 0:
            total_distance += (i + 1) * state['my_pts'][i]
    score -= total_distance * 0.1
    
    return score

def count_blots_after_move(state: Dict, move: str) -> int:
    """Estimate number of blots after move (simplified)."""
    # Count current blots
    blots = 0
    for i in range(24):
        if state['my_pts'][i] == 1:
            blots += 1
    
    # Simple adjustment based on move type
    if 'B' in move:  # Bar move might reduce blots
        blots -= 1
    
    return max(0, blots)

# Fallback to random legal move if no moves found
if __name__ == "__main__":
    # Test with a sample state
    test_state = {
        'my_pts': [0]*24,
        'opp_pts': [0]*24,
        'my_bar': 0,
        'opp_bar': 0,
        'my_off': 0,
        'opp_off': 0,
        'dice': [3, 4]
    }
    test_state['my_pts'][10] = 2
    test_state['my_pts'][15] = 2
    print(policy(test_state))
