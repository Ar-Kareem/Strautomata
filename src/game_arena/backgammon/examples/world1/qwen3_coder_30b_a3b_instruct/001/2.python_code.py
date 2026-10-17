
import itertools
import numpy as np

def policy(state):
    # Extract state information
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = state['dice']
    
    # Sort dice in descending order for easier handling
    dice_sorted = sorted(dice, reverse=True)
    d1, d2 = dice_sorted[0], dice_sorted[1] if len(dice_sorted) > 1 else 0
    
    # Generate all legal moves
    moves = generate_legal_moves(my_pts, opp_pts, my_bar, opp_bar, dice_sorted)
    
    # If no moves are available, pass
    if not moves:
        return "H:P,P"
    
    # Score moves
    scored_moves = []
    for move in moves:
        score = score_move(move, my_pts, opp_pts, my_bar, dice_sorted)
        scored_moves.append((score, move))
    
    # Return the best move
    best_move = max(scored_moves, key=lambda x: x[0])[1]
    return best_move

def generate_legal_moves(my_pts, opp_pts, my_bar, opp_bar, dice):
    """
    Generate all legal moves based on current state and dice roll.
    Returns a list of move strings in the format "H:A0,A1" or "L:B,A5"
    """
    moves = []
    dice_used = [False, False]
    
    # First, try to move bar pieces if any
    if my_bar > 0:
        # Try to move bar piece with first die
        first_die = dice[0]
        target_point = 24 - first_die
        if target_point >= 0 and target_point < 24:
            if opp_pts[target_point] <= 1:  # Can't move to point with 2+ opposing checkers
                if len(dice) == 2:
                    # Try using both dice
                    second_die = dice[1]
                    target_point2 = 24 - second_die
                    if target_point2 >= 0 and target_point2 < 24:
                        if opp_pts[target_point2] <= 1:
                            moves.append(f"H:B,{target_point2+100}")
                else:
                    moves.append(f"H:B,A{target_point}")
    else:
        # No bar pieces, find valid moves
        for i in range(24):
            if my_pts[i] > 0:
                # Try moving with first die
                target_point = i - dice[0] 
                if target_point >= 0 and target_point < 24:
                    if opp_pts[target_point] <= 1:
                        original_move = f"H:A{i},P"
                        if len(dice) == 2:
                            # Try using both dice
                            second_target_point = target_point - dice[1]
                            if second_target_point >= 0 and second_target_point < 24:
                                if opp_pts[second_target_point] <= 1:
                                    moves.append(f"H:A{i},A{second_target_point}")
                        else:
                            moves.append(original_move)
            
                # Try second die if first die was already used
                if len(dice) == 2 and not dice_used[0]:
                    target_point2 = i - dice[1]
                    if target_point2 >= 0 and target_point2 < 24:
                        if opp_pts[target_point2] <= 1:
                            moves.append(f"L:A{i},P")
    
    # Edge case: if only one die can be used but wasn't used, add it
    # or pass if no valid moves
    if not moves:
        return ["H:P,P"]
    
    return moves

def score_move(move, my_pts, opp_pts, my_bar, dice):
    """Score a move based on strategic value"""
    score = 0
    
    # Determine the move type
    if move == "H:P,P":
        return 0  # Pass move, minimal score
    
    parts = move.split(':')
    order = parts[0]
    froms = parts[1].split(',')
    
    # Score for bringing bar checkers back in
    if froms[0] == 'B':
        score += 100
    
    # Check if we're bearing off
    if does_bear_off(my_pts, froms, dice, order):
        score += 50
    
    # Score for blocking opponent primes or creating advantages
    score += score_blocking(move, my_pts, opp_pts)
    
    # Try to get checkers into home board area
    for start in froms:
        if start != 'P' and start != 'B':
            point = int(start[1:]) if len(start) > 1 else 0
            if point <= 5:  # Home board
                score += 5
    
    return score

def does_bear_off(my_pts, froms, dice, order):
    """Check if the move allows for bearing off (simplified version)"""
    # This is a simplified check - in a real implementation
    # we'd need to be more careful about remaining checkers
    return False  # For now, not bearing off in this policy

def score_blocking(move, my_pts, opp_pts):
    """Score move based on blocking opponent moves (primes, etc)"""
    score = 0
    
    # Check if we're setting up blockers against opponent's 5-point prime
    return score
